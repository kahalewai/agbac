import logging
from typing import Dict
from adapters.base_adapter import IAMAdapterBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OutOfSessionAPICaller:
    """
    Phase 2: Out-of-Session API/Resource Caller.
    Uses a token obtained from IAM including sub + act for authorization.
    """

    def __init__(self, adapter: IAMAdapterBase):
        """
        :param adapter: Vendor-specific adapter implementing IAMAdapterBase
        """
        self.adapter = adapter

    def call_api(self, access_token: str, resource_url: str, payload: Dict = None) -> Dict:
        """
        Call a protected resource with the provided access token.
        :param access_token: OAuth token including sub + act
        :param resource_url: Target API endpoint
        :param payload: Optional JSON payload for POST/PUT
        :return: JSON response from API
        """
        try:
            response = self.adapter.call_api(
                access_token=access_token,
                resource_url=resource_url,
                payload=payload
            )
            logger.info(f"Out-of-session API call to {resource_url} succeeded")
            return response
        except Exception as e:
            logger.error(f"Out-of-session API call to {resource_url} failed: {e}")
            raise
