import logging
import requests
from .base_adapter import BaseAdapter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class EntraIDAdapter(BaseAdapter):
    """
    Adapter for Microsoft EntraID (Azure AD) token requests.
    Supports dual-subject tokens in in-session scenarios only.
    """

    def __init__(self, token_url: str, client_id: str, client_secret: str, tenant_id: str):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    def request_token(self, sub: str, act: dict, scope: list) -> dict:
        """
        Request token from EntraID (in-session only).
        Note: Out-of-session dual-subject tokens are not supported in EntraID today.
        """
        payload = {
            "grant_type": "client_credentials",
            "scope": " ".join(scope),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "sub": sub,
            "act": act
        }

        try:
            response = requests.post(self.token_url, data=payload)
            response.raise_for_status()
            token_data = response.json()
            logger.info(f"EntraID token issued for agent {sub} with human act {act}")
            return token_data
        except requests.HTTPError as e:
            logger.error(f"EntraID token request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in EntraIDAdapter: {e}")
            raise
