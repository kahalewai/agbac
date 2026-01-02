import logging
from typing import List, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BaseAdapter:
    """
    Base adapter for all IAM vendors.
    Defines the interface for requesting dual-subject tokens including:
    - Agent subject (sub)
    - Human subject (act)
    """

    def request_token(self, sub: str, act: Dict, scope: List[str]) -> Dict:
        """
        Request a dual-subject token.
        :param sub: Agent identity
        :param act: Human 'act' data
        :param scope: List of scopes/permissions
        :return: Token dictionary (contains access_token and metadata)
        """
        raise NotImplementedError("Subclasses must implement this method.")
