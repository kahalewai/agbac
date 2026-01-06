"""
AGBAC-Min Out-of-Session Token Request

Request dual-subject tokens when agent runs in different process/server.

Process:
1. Agent receives act JWT from application over TLS
2. Agent verifies JWT signature
3. Agent extracts act from verified JWT
4. Agent requests token using adapter

Security: Act sent as signed JWT over TLS, signature verified, replay protected.
Vendor Support: All vendors (Keycloak, Auth0, Okta, EntraID)

Logging:
- IAM identifiers logged directly for audit correlation
- Structured logging with extra={} throughout
- No PII (email, name) logged
- JWT metadata (exp, jti) logged for security audit

Author: AGBAC-Min Project
License: Apache 2.0
Version: 1.0.1
"""

import logging
import time
from typing import Dict, List, Set
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from adapters.base_adapter import BaseAdapter, TokenResponse, TokenRequestError

logger = logging.getLogger(__name__)


class OutOfSessionTokenRequest:
    """
    Handle token requests for out-of-session agents.
    
    Out-of-session means the agent runs in a different process/server
    from the application. The act claim is transmitted as a signed JWT
    over TLS and must be verified before use.
    
    Logging:
        - IAM identifiers logged directly for audit correlation
        - JWT metadata (exp, jti) logged for security audit
        - No PII logged
    """
    
    def __init__(self, adapter: BaseAdapter, app_public_key_path: str):
        """
        Initialize handler with vendor adapter and application public key.
        
        Args:
            adapter: Vendor-specific adapter
            app_public_key_path: Path to application's public key (PEM) for verifying act JWTs
            
        Security: Public key used to verify act JWT signatures from application.
        """
        self.adapter = adapter
        self._load_app_public_key(app_public_key_path)
        self._used_jtis: Set[str] = set()  # Simple replay protection (use Redis in production)
        
        logger.info(
            "Out-of-session handler initialized",
            extra={
                'adapter_type': adapter.__class__.__name__,
                'key_path': app_public_key_path,
                'event': 'outofsession_handler_init'
            }
        )
    
    def _load_app_public_key(self, key_path: str) -> None:
        """Load application public key for JWT verification."""
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            self._app_public_key = serialization.load_pem_public_key(
                key_data, backend=default_backend()
            )
            
            logger.info(
                "Application public key loaded",
                extra={
                    'key_path': key_path,
                    'event': 'public_key_loaded'
                }
            )
        except Exception as e:
            logger.error(
                "Failed to load public key",
                extra={
                    'error_type': e.__class__.__name__,
                    'key_path': key_path,
                    'event': 'public_key_load_error'
                }
            )
            raise ValueError(f"Cannot load public key: {e.__class__.__name__}")
    
    def receive_and_verify_act_jwt(
        self, act_jwt: str, expected_audience: str
    ) -> Dict[str, str]:
        """
        Receive and verify act JWT from application.
        
        Args:
            act_jwt: Signed JWT from application containing act
            expected_audience: Expected audience (agent endpoint URL)
            
        Returns:
            Verified act dictionary
            
        Raises:
            ValueError: If JWT invalid, expired, or fails verification
            
        Security:
            - Verifies RS256 signature with application public key
            - Checks expiration
            - Validates audience
            - Prevents replay via JTI tracking
        """
        try:
            # Verify and decode JWT
            decoded = jwt.decode(
                act_jwt,
                self._app_public_key,
                algorithms=['RS256'],
                audience=expected_audience,
                options={'verify_exp': True}
            )
            
            # Check for replay (jti)
            jti = decoded.get('jti')
            if jti:
                if jti in self._used_jtis:
                    logger.error(
                        "Act JWT replay detected",
                        extra={
                            'jti': jti,
                            'event': 'jwt_replay_detected'
                        }
                    )
                    raise ValueError("Act JWT replay detected")
                self._used_jtis.add(jti)
            
            # Extract act
            act = decoded.get('act')
            if not act or 'sub' not in act:
                logger.error(
                    "Act JWT missing valid act claim",
                    extra={
                        'has_act': act is not None,
                        'has_sub': 'sub' in act if act else False,
                        'event': 'jwt_invalid_act'
                    }
                )
                raise ValueError("Act JWT must contain act.sub")
            
            # Log successful verification with IAM identifier (v1.1)
            logger.info(
                "Act JWT verified",
                extra={
                    'human_id': act.get('sub'),  # IAM identifier - safe to log
                    'exp': decoded.get('exp'),
                    'jti': jti,  # Random nonce - safe to log
                    'audience': expected_audience,
                    'event': 'jwt_verified'
                }
            )
            
            return act
            
        except jwt.ExpiredSignatureError:
            logger.error(
                "Act JWT expired",
                extra={'event': 'jwt_expired'}
            )
            raise ValueError("Act JWT expired")
        except jwt.InvalidAudienceError:
            logger.error(
                "Act JWT invalid audience",
                extra={
                    'expected_audience': expected_audience,
                    'event': 'jwt_invalid_audience'
                }
            )
            raise ValueError("Act JWT invalid audience")
        except jwt.InvalidSignatureError:
            logger.error(
                "Act JWT signature verification failed",
                extra={'event': 'jwt_invalid_signature'}
            )
            raise ValueError("Act JWT signature invalid")
        except jwt.InvalidTokenError as e:
            logger.error(
                "Act JWT invalid",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'jwt_invalid'
                }
            )
            raise ValueError(f"Act JWT invalid: {e.__class__.__name__}")
    
    def request_token(
        self, agent_id: str, act: Dict[str, str], scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject token after receiving verified act.
        
        Args:
            agent_id: Agent client ID (IAM identifier)
            act: Human identity (verified from JWT)
            scope: Requested scopes
            
        Returns:
            TokenResponse with access_token (and act_assertion for EntraID)
            
        Raises:
            ValueError: If required inputs are missing
            TokenRequestError: If token request fails
            
        Security: Act already verified by receive_and_verify_act_jwt.
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
        
        # Log token request start with IAM identifiers (v1.1)
        logger.info(
            "Out-of-session token request starting",
            extra={
                'agent_id': agent_id,  # IAM client ID - safe to log
                'human_id': act.get('sub'),  # IAM user ID - safe to log
                'scope': scope,
                'event': 'outofsession_token_request_start'
            }
        )
        
        try:
            token_response = self.adapter.request_token(agent_id, act, scope)
            
            # Log success with metadata (v1.1)
            logger.info(
                "Token request successful",
                extra={
                    'agent_id': agent_id,
                    'expires_in': token_response.expires_in,
                    'token_type': token_response.token_type,
                    'has_act_assertion': token_response.act_assertion is not None,
                    'event': 'outofsession_token_request_success'
                }
            )
            
            return token_response
            
        except TokenRequestError:
            # Re-raise TokenRequestError (already logged by adapter)
            raise
        except Exception as e:
            logger.error(
                "Unexpected error in token request",
                extra={
                    'error_type': e.__class__.__name__,
                    'agent_id': agent_id,
                    'event': 'outofsession_token_request_error'
                }
            )
            raise TokenRequestError(f"Unexpected error: {e.__class__.__name__}")


__all__ = ['OutOfSessionTokenRequest']
