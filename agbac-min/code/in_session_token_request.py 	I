"""
AGBAC-Min Phase 1: In-Session Token Request

Request dual-subject tokens when agent runs in same process as application.

Security: Act passed in-memory, no network transmission, HTTPS for IAM.
Vendor Support: All vendors (Keycloak, Auth0, Okta, EntraID)

Author: AGBAC-Min Project
"""

import logging
from typing import Dict, List
from adapters.base_adapter import BaseAdapter, TokenResponse, TokenRequestError

logger = logging.getLogger(__name__)


class InSessionTokenRequest:
    """Handle token requests for in-session agents."""
    
    def __init__(self, adapter: BaseAdapter):
        """
        Initialize handler with vendor adapter.
        
        Args:
            adapter: Vendor-specific adapter
        """
        self.adapter = adapter
        logger.info(
            "In-session handler initialized",
            extra={'adapter_type': adapter.__class__.__name__}
        )
    
    def request_token(
        self, agent_id: str, act: Dict[str, str], scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject token.
        
        Args:
            agent_id: Agent client ID
            act: Human identity (in-memory)
            scope: Requested scopes
            
        Returns:
            TokenResponse with access_token (and act_assertion for EntraID)
            
        Security: Act passed in-memory, validated before use, no PII logged.
        """
        # Validate inputs
        if not agent_id or not act or 'sub' not in act or not scope:
            raise ValueError("Invalid inputs: agent_id, act.sub, and scope required")
        
        logger.info("In-session token request starting", extra={'scope': scope})
        
        try:
            # Adapter handles vendor-specific logic
            token_response = self.adapter.request_token(agent_id, act, scope)
            
            logger.info(
                "Token request successful",
                extra={
                    'expires_in': token_response.expires_in,
                    'has_act_assertion': token_response.act_assertion is not None
                }
            )
            
            return token_response
            
        except TokenRequestError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e.__class__.__name__}")
            raise TokenRequestError(f"Unexpected error: {e.__class__.__name__}")


__all__ = ['InSessionTokenRequest']
