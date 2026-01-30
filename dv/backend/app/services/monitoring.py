"""
Service for monitoring HTTP endpoints and checking status.
"""
import httpx
import asyncio
from typing import Dict, Any
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class MonitoringService:
    """
    Service for checking HTTP endpoint status.
    """

    def __init__(self):
        self._polling_task = None
        self._should_poll = False

    async def start_polling(self, state_manager, connection_manager):
        """Start background polling when users are connected."""
        if self._polling_task is not None:
            return

        self._should_poll = True
        self._polling_task = asyncio.create_task(
            self._poll_loop(state_manager, connection_manager)
        )
        logger.info("Started status polling")

    async def stop_polling(self):
        """Stop background polling."""
        self._should_poll = False
        if self._polling_task:
            self._polling_task.cancel()
            self._polling_task = None
        logger.info("Stopped status polling")

    async def _poll_loop(self, state_manager, connection_manager):
        """Poll box status URLs and broadcast updates."""
        from ..api.websocket import serialize_state

        while self._should_poll:
            try:
                state = await state_manager.get_state()
                boxes_with_url = [b for b in state.boxes if b.status_url]
                logger.info(f"Polling {len(boxes_with_url)}/{len(state.boxes)} boxes with status_url")

                # Poll each box with a status_url
                for box in state.boxes:
                    # Convert HttpUrl to string if needed
                    status_url_str = str(box.status_url) if box.status_url else None

                    if status_url_str:
                        logger.info(f"Checking status for box '{box.name}': {status_url_str}")
                        results = {}
                        has_parameters = False

                        # Check each parameter
                        for param_name, param_config in box.parameters.items():
                            if param_config.get("type") in ["ok/nok", "text"]:
                                has_parameters = True
                                result = await self.check_url_status(
                                    status_url_str, param_config
                                )
                                results[param_name] = result
                                logger.info(f"  Parameter {param_name}: {result}")

                        # If no parameters configured, do a basic HTTP status check
                        if not has_parameters:
                            basic_result = await self.check_http_status(status_url_str)
                            results["_default"] = basic_result
                            logger.info(f"  Basic status check: {basic_result}")

                        overall_status = self.determine_overall_status(results)
                        status_data = {
                            "status": overall_status,
                            "parameters": results,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                        state_manager.set_status(box.id, status_data)
                        logger.info(f"  Overall status for '{box.name}': {overall_status}")

                # Fetch fresh state with updated status data
                updated_state = await state_manager.get_state()
                # Broadcast updated state with status data
                await connection_manager.send_state_update(updated_state)
                logger.info("Status broadcast complete")

            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)

            await asyncio.sleep(5)

    async def check_http_status(self, url: str) -> Dict[str, Any]:
        """
        Basic HTTP status check for URLs without parameters.

        Args:
            url: The URL to check

        Returns:
            Dictionary with status and value (HTTP status code)
        """
        try:
            if not url or not url.startswith(("http://", "https://")):
                return {"status": "nok", "value": "Invalid URL"}

            async with httpx.AsyncClient(timeout=settings.status_check_timeout) as client:
                response = await client.get(url, follow_redirects=True)

                if response.status_code == 200:
                    return {"status": "ok", "value": response.status_code}
                elif 500 <= response.status_code < 600:
                    return {"status": "warning", "value": response.status_code}
                else:
                    return {"status": "nok", "value": response.status_code}

        except httpx.TimeoutException:
            logger.warning(f"Timeout checking URL: {url}")
            return {"status": "nok", "value": "timeout"}
        except httpx.ConnectError:
            logger.warning(f"Connection error checking URL: {url}")
            return {"status": "nok", "value": "connection_error"}
        except Exception as e:
            logger.error(f"Error checking URL {url}: {e}")
            return {"status": "nok", "value": str(e)}

    async def check_url_status(self, url: str, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Check the status of a URL endpoint.

        Args:
            url: The URL to check
            params: Parameters including type (ok/nok or text) and length

        Returns:
            Dictionary with status and value
        """
        try:
            # Validate URL before making request
            if not url or not url.startswith(("http://", "https://")):
                return {"status": "nok", "value": "Invalid URL"}

            async with httpx.AsyncClient(timeout=settings.status_check_timeout) as client:
                param_type = params.get("type", "ok/nok")

                if param_type == "text":
                    # Get a portion of the response text
                    response = await client.get(url, follow_redirects=True)
                    if response.status_code == 200:
                        text = response.text[: params.get("length", 50)]
                        return {"status": "ok", "value": text}
                    elif 500 <= response.status_code < 600:
                        return {"status": "warning", "value": response.status_code}
                    else:
                        return {"status": "nok", "value": response.status_code}
                else:
                    # Check if request succeeds (ok/nok or default)
                    response = await client.get(url, follow_redirects=True)
                    if response.status_code == 200:
                        return {"status": "ok", "value": response.status_code}
                    elif 500 <= response.status_code < 600:
                        return {"status": "warning", "value": response.status_code}
                    else:
                        return {"status": "nok", "value": response.status_code}

        except httpx.TimeoutException:
            logger.warning(f"Timeout checking URL: {url}")
            return {"status": "nok", "value": "timeout"}
        except httpx.ConnectError:
            logger.warning(f"Connection error checking URL: {url}")
            return {"status": "nok", "value": "connection_error"}
        except Exception as e:
            logger.error(f"Error checking URL {url}: {e}")
            return {"status": "nok", "value": str(e)}

    def determine_overall_status(self, results: Dict[str, Dict]) -> str:
        """
        Determine overall status from parameter results.

        Args:
            results: Dictionary of parameter results

        Returns:
            Overall status (nok > warning > ok > unknown)
        """
        if not results:
            return "unknown"

        overall = "ok"
        for result in results.values():
            status = result.get("status", "unknown")
            if status == "nok":
                return "nok"
            elif status == "warning" and overall != "nok":
                overall = "warning"
        return overall


# Global monitoring service instance
monitoring_service = MonitoringService()
