import logging
import requests
from .base_adapter import BaseAdapter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Auth0Adapter(BaseAdapter):
    """
    Adapter for Auth0 OAuth2 token requests.
    Supports dual-subject tokens with sub (agent) and act (human).
    """

    def __init__(self, domain: str, client_id: str, client_secret: str):
        self.token_url = f"https://{domain}/oauth/token"
        self.client_id = client_id
        self.client_secret = client_secret

    def request_token(self, sub: str, act: dict, scope: list) -> dict:
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": "https://api.example.com/",
            "scope": " ".join(scope),
            "sub": sub,
            "act": act
        }

        try:
            response = requests.post(self.token_url, json=payload)
            response.raise_for_status()
            token_data = response.json()
            logger.info(f"Auth0 token issued for agent {sub} with human act {act}")
            return token_data
        except requests.HTTPError as e:
            logger.error(f"Auth0 token request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Auth0Adapter: {e}")
            raise
