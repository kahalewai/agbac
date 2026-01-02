import logging
from typing import Dict
from adapters.base_adapter import IAMAdapterBase
from sender.hybrid_sender import HybridSender

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class InSessionTokenRequester:
    """
    Phase 1: In-Session Token Requester.
    Uses the HybridSender to retrieve human 'act' data from the in-session application.
    Requests an OAuth token from the IAM vendor including both:
        - sub (agent identity)
        - act (human identity)
    """

    def __init__(self, adapter: IAMAdapterBase, sender: HybridSender):
        """
        :param adapter: Vendor-specific adapter implementing IAMAdapterBase
        :param sender: HybridSender instance for in-session act data
        """
        self.adapter = adapter
        self.sender = sender

    def request_token(self, agent_identity: str, human_identity: Dict) -> Dict:
        """
        Request an OAuth token for the in-session agent with dual-subject authorization.
        :param agent_identity: Unique identifier of the agent
        :param human_identity: Dict representing human user's 'act' data
        :return: Token response dict from IAM
        """
        try:
            # Extract 'act' from the session via HybridSender
            act_data = self.sender.prepare_in_session_act(human_identity)

            # Make token request via adapter
            token_response = self.adapter.request_token(
                agent_identity=agent_identity,
                act=act_data
            )

            logger.info(f"In-session token successfully obtained for agent {agent_identity}")
            return token_response
        except Exception as e:
            logger.error(f"Failed to request in-session token: {e}")
            raise
