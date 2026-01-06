"""
AGBAC-Min In-Session Token Request

Request dual-subject tokens when agent runs in same process as application.

Security: Act passed in-memory, no network transmission, HTTPS for IAM.
Vendor Support: All vendors (Keycloak, Auth0, Okta, EntraID)

Logging:
- IAM identifiers logged directly for audit correlation
- Structured logging with extra={} throughout
- No PII (email, name) logged

Author: AGBAC-Min Project
License: Apache 2.0
Version: 1.0.1
"""

import logging
from typing import Dict, List
from adapters.base_adapter import BaseAdapter, TokenResponse, TokenRequestError

logger = logging.getLogger(__name__)


class InSessionTokenRequest:
    """
    Handle token requests for in-session agents.
    
    In-session means the agent runs in the same process as the application,
    so the act claim can be passed directly in memory without network transmission.
    
    Logging:
        - Agent IDs and adapter types logged directly
        - Scope information logged for audit
        - Token metadata logged (expiration, type)
        - Tokens themselves never logged
    """
    
    def __init__(self, adapter: BaseAdapter):
        """
        Initialize handler with vendor adapter.
        
        Args:
            adapter: Vendor-specific adapter (KeycloakAdapter, Auth0Adapter, etc.)
        """
        self.adapter = adapter
        logger.info(
            "In-session handler initialized",
            extra={
                'adapter_type': adapter.__class__.__name__,
                'event': 'insession_handler_init'
            }
        )
    
    def request_token(
        self, agent_id: str, act: Dict[str, str], scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject token.
        
        Args:
            agent_id: Agent client ID (IAM identifier)
            act: Human identity dictionary (passed in-memory)
            scope: Requested scopes/permissions
            
        Returns:
            TokenResponse with access_token (and act_assertion for EntraID)
            
        Raises:
            ValueError: If required inputs are missing
            TokenRequestError: If token request fails
            
        Security: 
            - Act passed in-memory, not over network
            - Validated before use
            - IAM identifiers logged (pseudonymous)
            - No PII logged
        """
        # Validate inputs
        if not agent_id:
            logger.error(
                "Missing agent_id",
                extra={'event': 'invalid_input_agent_id'}
            )
            raise ValueError("Invalid inputs: agent_id required")
        
        if not act or 'sub' not in act:
            logger.error(
                "Missing or invalid act claim",
                extra={
                    'has_act': act is not None,
                    'has_sub': 'sub' in act if act else False,
                    'event': 'invalid_input_act'
                }
            )
            raise ValueError("Invalid inputs: act with 'sub' field required")
        
        if not scope:
            logger.error(
                "Missing scope",
                extra={'event': 'invalid_input_scope'}
            )
            raise ValueError("Invalid inputs: scope required")
        
        # Log token request start with IAM identifiers (v1.1 - no hashing)
        logger.info(
            "In-session token request starting",
            extra={
                'agent_id': agent_id,  # IAM client ID - safe to log
                'human_id': act.get('sub'),  # IAM user ID - safe to log
                'scope': scope,
                'event': 'insession_token_request_start'
            }
        )
        
        try:
            # Adapter handles vendor-specific logic
            token_response = self.adapter.request_token(agent_id, act, scope)
            
            # Log success with metadata (v1.1)
            logger.info(
                "Token request successful",
                extra={
                    'agent_id': agent_id,
                    'expires_in': token_response.expires_in,
                    'token_type': token_response.token_type,
                    'has_act_assertion': token_response.act_assertion is not None,
                    'event': 'insession_token_request_success'
                }
            )
            
            return token_response
            
        except TokenRequestError:
            # Re-raise TokenRequestError (already logged by adapter)
            raise
        except Exception as e:
            # Log unexpected errors with structured logging
            logger.error(
                "Unexpected error in token request",
                extra={
                    'error_type': e.__class__.__name__,
                    'agent_id': agent_id,
                    'event': 'insession_token_request_error'
                }
            )
            raise TokenRequestError(f"Unexpected error: {e.__class__.__name__}")


__all__ = ['InSessionTokenRequest']
