import os
from .analytics import AnalyticsChannelClient
from .inference import InferenceChannelClient

__all__ = ["AnalyticsChannelClient", "InferenceChannelClient", "from_env", "analytics_from_env", "inference_from_env"]


def from_env():
    """
    Factory to initialize both clients from environment variables.

    Environment variables:
    - DLT_SIDECAR_URL: URL of the REST API sidecar (default: http://localhost:9337)
    - DLT_TIMEOUT: Request timeout in seconds (default: 10.0)

    Returns:
        tuple: (AnalyticsChannelClient, InferenceChannelClient)
    """
    sidecar_url = os.getenv("DLT_SIDECAR_URL", "http://localhost:9337")
    timeout = float(os.getenv("DLT_TIMEOUT", "10.0"))

    return (
        AnalyticsChannelClient(sidecar_url, timeout),
        InferenceChannelClient(sidecar_url, timeout),
    )

def analytics_from_env():
    """
    Factory to initialize analytics client from environment variables.

    Environment variables:
    - DLT_SIDECAR_URL: URL of the REST API sidecar (default: http://localhost:9337)
    - DLT_TIMEOUT: Request timeout in seconds (default: 10.0)

    Returns:
        AnalyticsChannelClient
    """
    sidecar_url = os.getenv("DLT_SIDECAR_URL", "http://localhost:9337")
    timeout = float(os.getenv("DLT_TIMEOUT", "10.0"))

    return AnalyticsChannelClient(sidecar_url, timeout)

def inference_from_env():
    """
    Factory to initialize inference client from environment variables.

    Environment variables:
    - DLT_SIDECAR_URL: URL of the REST API sidecar (default: http://localhost:9337)
    - DLT_TIMEOUT: Request timeout in seconds (default: 10.0)

    Returns:
        InferenceChannelClient
    """
    sidecar_url = os.getenv("DLT_SIDECAR_URL", "http://localhost:9337")
    timeout = float(os.getenv("DLT_TIMEOUT", "10.0"))

    return InferenceChannelClient(sidecar_url, timeout)
