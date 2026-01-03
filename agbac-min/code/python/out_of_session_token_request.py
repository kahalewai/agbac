"""
AGBAC-Min Phase 2: Out-of-Session Token Request

Request dual-subject tokens when agent runs in different process/server.

Process:
1. Agent receives act JWT from application over TLS
2. Agent verifies JWT signature
3. Agent extracts act from verified JWT
4. Agent requests token using adapter

Security: Act sent as signed JWT over TLS, signature verified, replay protected.
Vendor Support: All vendors (Keycloak, Auth0, Okta, EntraID)

Author: AGBAC-Min Project
"""

import logging
import time
from typing import Dict, List
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from adapters.base_adapter import BaseAdapter, TokenResponse, TokenRequestError

logger = logging.getLogger(__name__)


class OutOfSessionTokenRequest:
    """Handle token requests for out-of-session agents."""
    
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
        self._used_jtis = set()  # Simple replay protection (use Redis in production)
        
        logger.info(
            "Out-of-session handler initialized",
            extra={'adapter_type': adapter.__class__.__name__}
        )
    
    def _load_app_public_key(self, key_path: str) -> None:
        """Load application public key for JWT verification."""
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            self._app_public_key = serialization.load_pem_public_key(
                key_data, backend=default_backend()
            )
            
            logger.info("Application public key loaded")
        except Exception as e:
            logger.error(f"Failed to load public key: {e.__class__.__name__}")
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
                    logger.error("Act JWT replay detected")
                    raise ValueError("Act JWT replay detected")
                self._used_jtis.add(jti)
            
            # Extract act
            act = decoded.get('act')
            if not act or 'sub' not in act:
                logger.error("Act JWT missing valid act claim")
                raise ValueError("Act JWT must contain act.sub")
            
            logger.info(
                "Act JWT verified",
                extra={
                    'exp': decoded.get('exp'),
                    'has_jti': jti is not None
                }
            )
            
            return act
            
        except jwt.ExpiredSignatureError:
            logger.error("Act JWT expired")
            raise ValueError("Act JWT expired")
        except jwt.InvalidAudienceError:
            logger.error("Act JWT invalid audience")
            raise ValueError("Act JWT invalid audience")
        except jwt.InvalidSignatureError:
            logger.error("Act JWT signature verification failed")
            raise ValueError("Act JWT signature invalid")
        except jwt.InvalidTokenError as e:
            logger.error(f"Act JWT invalid: {e}")
            raise ValueError(f"Act JWT invalid: {e}")
    
    def request_token(
        self, agent_id: str, act: Dict[str, str], scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject token after receiving verified act.
        
        Args:
            agent_id: Agent client ID
            act: Human identity (verified from JWT)
            scope: Requested scopes
            
        Returns:
            TokenResponse with access_token (and act_assertion for EntraID)
            
        Security: Act already verified by receive_and_verify_act_jwt.
        """
        if not agent_id or not act or 'sub' not in act or not scope:
            raise ValueError("Invalid inputs")
        
        logger.info("Out-of-session token request starting", extra={'scope': scope})
        
        try:
            token_response = self.adapter.request_token(agent_id, act, scope)
            
            logger.info(
                "Token request successful",
                extra={'expires_in': token_response.expires_in}
            )
            
            return token_response
            
        except TokenRequestError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e.__class__.__name__}")
            raise TokenRequestError(f"Unexpected error: {e.__class__.__name__}")


__all__ = ['OutOfSessionTokenRequest']
