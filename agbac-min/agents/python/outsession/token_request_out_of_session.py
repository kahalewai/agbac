import logging
from typing import Dict
from adapters.base_adapter import IAMAdapterBase
from sender.hybrid_sender import HybridSender

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OutOfSessionTokenRequester:
    """
    Phase 2: Out-of-Session Token Requester.
    Uses HybridSender to securely transmit the human 'act' data via TLS + JWT to the agent.
    Requests an OAuth token from the IAM vendor including both:
        - sub (agent identity)
        - act (human identity)
    """

    def __init__(self, adapter: IAMAdapterBase, sender: HybridSender):
        """
        :param adapter: Vendor-specific adapter implementing IAMAdapterBase
        :param sender: HybridSender instance for securely sending act data out-of-session
        """
        self.adapter = adapter
        self.sender = sender

    def request_token(self, agent_identity: str, human_identity: Dict) -> Dict:
        """
        Request an OAuth token for the out-of-session agent with dual-subject authorization.
        :param agent_identity: Unique identifier of the agent
        :param human_identity: Dict representing human user's 'act' data
        :return: Token response dict from IAM
        """
        try:
            # Securely generate JWT + TLS package for out-of-session agent
            act_package = self.sender.prepare_out_of_session_act(human_identity)

            # Make token request via adapter, including TLS + JWT package
            token_response = self.adapter.request_token(
                agent_identity=agent_identity,
                act=act_package
            )

            logger.info(f"Out-of-session token successfully obtained for agent {agent_identity}")
            return token_response
        except Exception as e:
            logger.error(f"Failed to request out-of-session token: {e}")
            raise
