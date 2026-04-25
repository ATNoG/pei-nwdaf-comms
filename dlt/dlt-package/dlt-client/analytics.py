import hashlib, json, uuid
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .models import DataFetchRequest

_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError)

class AnalyticsChannelClient:
    """Records data fetch events on the analytics channel."""

    def __init__(self, sidecar_url: str, timeout: float = 10.0):
        self._base = sidecar_url.rstrip("/") + "/api/v1/ledger"
        self._timeout = timeout

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def record_data_fetch(
        self,
        mlflow_run_id: str,
        model_name: str,
        model_version: str,
        query_params: dict,
        data_payload,           # the raw data returned from Storage
        cell_ids: str = "",
        time_range_start: str = "",
        time_range_end: str = "",
    ) -> str:
        """
        Hash the payload, write a DataFetch record to analytics-channel.
        Returns the requestId (use it as dataFetchRef in InferenceChannelClient).
        """
        request_id = str(uuid.uuid4())
        data_hash = hashlib.sha256(
            json.dumps(data_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        req = DataFetchRequest(
            request_id=request_id,
            mlflow_run_id=mlflow_run_id,
            model_name=model_name,
            model_version=model_version,
            query_descriptor=json.dumps(query_params, sort_keys=True, default=str),
            data_hash=data_hash,
            cell_ids=cell_ids,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                f"{self._base}/analytics",
                json={
                    "requestId": req.request_id,
                    "mlflowRunId": req.mlflow_run_id,
                    "modelName": req.model_name,
                    "modelVersion": req.model_version,
                    "queryDescriptor": req.query_descriptor,
                    "dataHash": req.data_hash,
                    "cellIds": req.cell_ids or "",
                    "timeRangeStart": req.time_range_start or "",
                    "timeRangeEnd": req.time_range_end or "",
                })
            r.raise_for_status()
        return request_id

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def get_record(self, request_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{self._base}/analytics/{request_id}")
            r.raise_for_status()
            return r.json()
