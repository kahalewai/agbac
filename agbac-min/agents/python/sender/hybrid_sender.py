import logging
import jwt  # PyJWT library
import time
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class HybridSender:
    """
    Hybrid sender for dual-subject 'act' propagation.
    Supports:
      - In-session agents: pass 'act' data directly.
      - Out-of-session agents: send 'act' data securely using TLS + signed JWT.

    The sender ensures the agent token request will include both:
      - sub (agent identity)
      - act (human identity)
    """

    def __init__(self, private_key_pem: Optional[str] = None, tls_verify: bool = True):
        """
        :param private_key_pem: PEM-formatted private key for signing JWTs (out-of-session)
        :param tls_verify: whether to verify TLS certificates for out-of-session requests
        """
        self.private_key_pem = private_key_pem
        self.tls_verify = tls_verify

    def prepare_in_session_act(self, human_identity: Dict) -> Dict:
        """
        Prepare 'act' data for an in-session agent.
        The human identity is directly provided to the agent code.
        """
        logger.info(f"Preparing in-session 'act' data: {human_identity}")
        return human_identity

    def prepare_out_of_session_act(self, human_identity: Dict, agent_endpoint: str, ttl_seconds: int = 60) -> str:
        """
        Prepare 'act' data for an out-of-session agent.
        Uses a signed JWT to securely convey the human identity.
        
        :param human_identity: The 'act' data of the human user
        :param agent_endpoint: URL of the out-of-session agent to receive the JWT
        :param ttl_seconds: Time-to-live for the JWT
        :return: JWT string
        """
        if not self.private_key_pem:
            raise ValueError("Private key required for out-of-session JWT signing.")

        now = int(time.time())
        payload = {
            "act": human_identity,
            "iat": now,
            "exp": now + ttl_seconds,
            "aud": agent_endpoint
        }

        try:
            signed_jwt = jwt.encode(payload, self.private_key_pem, algorithm="RS256")
            logger.info(f"Signed JWT prepared for out-of-session agent at {agent_endpoint}")
            return signed_jwt
        except Exception as e:
            logger.error(f"Failed to generate JWT for out-of-session agent: {e}")
            raise

    def send_out_of_session_act(self, signed_jwt: str, agent_endpoint: str) -> Dict:
        """
        Send the signed JWT to the out-of-session agent over HTTPS.
        :param signed_jwt: The signed JWT containing 'act' data
        :param agent_endpoint: URL of the out-of-session agent
        :return: HTTP response JSON
        """
        headers = {"Authorization": f"Bearer {signed_jwt}"}
        try:
            response = requests.post(agent_endpoint, headers=headers, verify=self.tls_verify)
            response.raise_for_status()
            logger.info(f"'act' data successfully sent to out-of-session agent at {agent_endpoint}")
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP error sending 'act' to out-of-session agent: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending 'act' to out-of-session agent: {e}")
            raise
