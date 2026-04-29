from pydantic import BaseModel
from typing import Optional

class DataFetchRequest(BaseModel):
    request_id: str
    mlflow_run_id: str
    model_name: str
    model_version: str
    query_descriptor: str
    data_hash: str
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None

class InferenceRequest(BaseModel):
    inference_id: str
    mlflow_run_id: str
    model_name: str
    model_version: str
    data_fetch_ref: str       # requestId from DataFetchChaincode
    input_hash: str
    anomaly_score: float
    decision: str             # "ANOMALY" | "NORMAL"
