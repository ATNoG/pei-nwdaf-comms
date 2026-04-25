import hashlib, json, uuid
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .models import InferenceRequest

_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError)

class InferenceChannelClient:
    """Records inference events on the inference channel."""

    def __init__(self, sidecar_url: str, timeout: float = 10.0):
        self._base = sidecar_url.rstrip("/") + "/api/v1/ledger"
        self._timeout = timeout

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def record_inference(
        self,
        mlflow_run_id: str,
        model_name: str,
        model_version: str,
        data_fetch_ref: str,    # requestId returned by AnalyticsChannelClient
        input_data,
        anomaly_score: float,
        decision: str,
    ) -> str:
        """
        Hash the input, write an InferenceRecord to inference-channel.
        Returns the inferenceId.
        """
        inference_id = str(uuid.uuid4())
        req = InferenceRequest(
            inference_id=inference_id,
            mlflow_run_id=mlflow_run_id,
            model_name=model_name,
            model_version=model_version,
            data_fetch_ref=data_fetch_ref,
            input_hash=hashlib.sha256(
                json.dumps(input_data, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            anomaly_score=anomaly_score,
            decision=decision,
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                f"{self._base}/inference",
                json={
                    "inferenceId": req.inference_id,
                    "mlflowRunId": req.mlflow_run_id,
                    "modelName": req.model_name,
                    "modelVersion": req.model_version,
                    "dataFetchRef": req.data_fetch_ref,
                    "inputHash": req.input_hash,
                    "anomalyScore": req.anomaly_score,
                    "decision": req.decision,
                })
            r.raise_for_status()
        return inference_id

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def get_record(self, inference_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{self._base}/inference/{inference_id}")
            r.raise_for_status()
            return r.json()

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def get_full_provenance(self, inference_id: str) -> dict:
        """Returns both the inference record and the originating data fetch record."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{self._base}/provenance/{inference_id}")
            r.raise_for_status()
            return r.json()
