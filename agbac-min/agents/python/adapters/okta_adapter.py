import logging
import requests
from .base_adapter import BaseAdapter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OktaAdapter(BaseAdapter):
    """
    Adapter for Okta OAuth2 token requests.
    Supports dual-subject tokens with sub (agent) and act (human).
    """

    def __init__(self, token_url: str, client_id: str, client_secret: str):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret

    def request_token(self, sub: str, act: dict, scope: list) -> dict:
        """
        Request token from Okta including agent and human act data.
        """
        payload = {
            "grant_type": "client_credentials",
            "scope": " ".join(scope),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            # Okta custom claim for act
            "act": act,
            "sub": sub
        }

        try:
            response = requests.post(self.token_url, json=payload)
            response.raise_for_status()
            token_data = response.json()
            logger.info(f"Okta token issued for agent {sub} with human act {act}")
            return token_data
        except requests.HTTPError as e:
            logger.error(f"Okta token request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OktaAdapter: {e}")
            raise
