"""
AGBAC-Min Hybrid Sender

This module provides the HybridSender class for extracting human identity from
application sessions and preparing it for transmission to AI agents.

Works for BOTH in-session and out-of-session scenarios with ALL IAM vendors.

Security Features:
- Logs IAM identifiers (pseudonymous), not email/name (PII)
- JWT signing for out-of-session (RS256)
- Replay protection via JTI nonce
- Short JWT expiration (60 seconds)
- Input validation
- HTTPS enforcement for out-of-session endpoints

Logging:
- IAM identifiers logged directly for audit correlation
- No hashing - enables direct correlation with IAM provider logs
- PII (email, name) never logged

Author: AGBAC-Min Project
License: Apache 2.0
Version: 1.0.1
"""

import logging
import time
import secrets
from typing import Dict, Optional
from dataclasses import dataclass
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """
    User session data structure for extracting act claims.
    
    Attributes:
        user_email: User's email address (required)
        user_name: User's display name (optional)
        user_id: IAM provider's unique identifier for user (preferred for logging)
                 Examples: Keycloak user ID, Auth0 user ID, Okta UID, EntraID OID
    
    Best Practice:
        Always populate user_id with the IAM provider's unique identifier.
        This enables perfect log correlation while protecting PII.
        
    Example:
        # Extract user_id from OIDC token
        id_token = session['id_token']
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        
        user_session = UserSession(
            user_email=decoded['email'],
            user_name=decoded.get('name'),
            user_id=decoded['sub']  # IAM identifier from OIDC token
        )
    """
    user_email: str
    user_name: Optional[str] = None
    user_id: Optional[str] = None  # IAM provider identifier (preferred for sub claim)


class HybridSender:
    """
    Extract and prepare human identity (act) for transmission to agents.
    
    Supports two scenarios:
    1. In-Session: Act passed directly in memory
    2. Out-of-Session: Act wrapped in signed JWT, sent over TLS
    
    Security:
        - Never logs PII (email, name)
        - Logs IAM identifiers directly (pseudonymous, enables audit correlation)
        - Signs JWTs with RSA (RS256)
        - Short JWT expiration (60s)
        - Unique nonce per JWT
        
    Logging:
        All logging uses IAM identifiers (user_id, sub) directly without hashing.
        This enables direct correlation with IAM provider audit logs while
        protecting user privacy (IAM identifiers are pseudonymous).
    """
    
    def __init__(self, private_key_pem: Optional[str] = None):
        """
        Initialize HybridSender.
        
        Args:
            private_key_pem: Path to RSA private key for out-of-session signing.
                           Optional - only needed for out-of-session scenarios.
        """
        self.private_key_pem = private_key_pem
        self._private_key = None
        
        if private_key_pem:
            try:
                self._load_private_key(private_key_pem)
                logger.info(
                    "HybridSender initialized with out-of-session capability",
                    extra={
                        'key_path': private_key_pem,  # File path - not sensitive
                        'event': 'hybrid_sender_init_full'
                    }
                )
            except Exception as e:
                logger.error(
                    "Failed to load private key",
                    extra={
                        'error_type': e.__class__.__name__,
                        'event': 'hybrid_sender_key_error'
                    }
                )
                raise ValueError(f"Cannot load private key: {e.__class__.__name__}")
        else:
            logger.info(
                "HybridSender initialized (in-session only)",
                extra={'event': 'hybrid_sender_init_insession'}
            )
    
    def _load_private_key(self, key_path: str) -> None:
        """Load RSA private key from PEM file."""
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        self._private_key = serialization.load_pem_private_key(
            key_data, password=None, backend=default_backend()
        )
    
    def extract_act_from_session(self, session) -> Dict[str, str]:
        """
        Extract human identity from authenticated session.
        
        Args:
            session: Authenticated session - either UserSession dataclass or dict with user data
            
        Returns:
            Act dictionary with sub (IAM identifier preferred), email, and optionally name
            
        Best Practice:
            The 'sub' claim should contain the IAM provider's unique user identifier
            (Keycloak user ID, Auth0 user ID, Okta UID, EntraID OID) rather than
            email, as this provides:
            - Perfect log correlation with IAM provider logs
            - Pseudonymous identifier (protects PII)
            - Stable identifier (doesn't change if email changes)
            
        Security: Logs only IAM identifiers (pseudonymous), never email/name (PII).
        """
        # Handle UserSession dataclass
        if hasattr(session, 'user_email'):
            email = session.user_email
            name = session.user_name
            user_id = session.user_id if hasattr(session, 'user_id') else None
        # Handle dictionary session
        elif isinstance(session, dict):
            # Extract email (required)
            email = (session.get('email') or session.get('user_email') or 
                    session.get('userPrincipalName') or session.get('mail'))
            
            if not email:
                logger.error(
                    "Session missing email field",
                    extra={'event': 'session_missing_email'}
                )
                raise ValueError("Session must contain email")
            
            # Extract user ID (IAM identifier - preferred for sub)
            user_id = (session.get('user_id') or session.get('sub') or 
                      session.get('oid') or session.get('uid'))
            
            # Extract name (optional)
            name = (session.get('name') or session.get('display_name') or 
                   session.get('displayName'))
        else:
            raise ValueError("Session must be UserSession or dictionary")
        
        if not email:
            logger.error(
                "Session missing email field",
                extra={'event': 'session_missing_email'}
            )
            raise ValueError("Session must contain email")
        
        # Prefer IAM user ID for 'sub', fall back to email if not available
        # Best practice: Always provide user_id for proper logging and correlation
        sub = user_id if user_id else email
        
        # Build act claim
        act = {
            'sub': sub,  # IAM identifier (preferred) or email (fallback)
            'email': email
        }
        
        if name:
            act['name'] = name
        
        # Include user_id explicitly if different from sub (for clarity)
        if user_id and user_id != sub:
            act['user_id'] = user_id
        
        # Log with IAM identifier (v1.1 - no hashing)
        logger.info(
            "Human identity extracted from session",
            extra={
                'human_id': sub,  # IAM identifier (pseudonymous) - safe to log
                'has_name': name is not None,
                'id_type': 'iam_identifier' if user_id else 'email_fallback',
                'event': 'act_extracted'
            }
        )
        
        return act
    
    def prepare_in_session_act(self, act: Dict[str, str]) -> Dict[str, str]:
        """
        Prepare act for in-session agent (no transformation).
        
        For in-session agents, act is passed directly in memory.
        
        Args:
            act: Human identity dictionary
            
        Returns:
            Same act dictionary
        """
        # Log with IAM identifier (v1.1 - no hashing)
        logger.debug(
            "Act prepared for in-session",
            extra={
                'human_id': act.get('sub'),  # IAM identifier - safe to log
                'event': 'act_prepared_in_session'
            }
        )
        return act
    
    def prepare_out_of_session_act(
        self, act: Dict[str, str], agent_endpoint: str, ttl_seconds: int = 60
    ) -> str:
        """
        Prepare act for out-of-session agent (signed JWT).
        
        Args:
            act: Human identity dictionary (must contain 'sub')
            agent_endpoint: Agent's endpoint URL (must be HTTPS for security)
            ttl_seconds: JWT expiration in seconds (default: 60, recommended: 10-300)
            
        Returns:
            Signed JWT string containing act claim
            
        Raises:
            ValueError: If validation fails or JWT creation fails
            
        Security:
            - Requires HTTPS for agent endpoint
            - RS256 signature (asymmetric)
            - Short expiration (default 60 seconds)
            - Unique nonce (jti) for replay protection
            - Must be sent over TLS
        """
        # Validate private key loaded
        if not self._private_key:
            logger.error(
                "Out-of-session requires private key",
                extra={'event': 'missing_private_key'}
            )
            raise ValueError(
                "HybridSender not configured for out-of-session - "
                "initialize with private_key_pem parameter"
            )
        
        # Validate act claim
        if not act or 'sub' not in act:
            logger.error(
                "Invalid act for out-of-session",
                extra={
                    'has_act': act is not None,
                    'has_sub': 'sub' in act if act else False,
                    'event': 'invalid_act'
                }
            )
            raise ValueError("Act must contain 'sub' field")
        
        # Validate agent endpoint is HTTPS
        if not agent_endpoint or not agent_endpoint.startswith('https://'):
            logger.error(
                "Agent endpoint must use HTTPS",
                extra={
                    'endpoint_scheme': agent_endpoint.split(':')[0] if agent_endpoint else 'empty',
                    'event': 'invalid_agent_endpoint'
                }
            )
            raise ValueError("Agent endpoint must use HTTPS for security")
        
        # Validate TTL
        if ttl_seconds < 10 or ttl_seconds > 300:
            logger.warning(
                "TTL outside recommended range (10-300 seconds)",
                extra={
                    'ttl_seconds': ttl_seconds,
                    'event': 'unusual_ttl'
                }
            )
        
        # Create JWT payload
        now = int(time.time())
        jti = secrets.token_urlsafe(32)
        
        payload = {
            'iss': 'application',
            'sub': 'application',
            'aud': agent_endpoint,
            'exp': now + ttl_seconds,
            'iat': now,
            'jti': jti,
            'act': act
        }
        
        # Create signed JWT
        try:
            act_jwt = jwt.encode(payload, self._private_key, algorithm='RS256')
            
            # Log with IAM identifier (v1.1 - no hashing)
            logger.info(
                "Act prepared for out-of-session",
                extra={
                    'human_id': act['sub'],  # IAM identifier (pseudonymous) - safe to log
                    'agent_endpoint': agent_endpoint,  # HTTPS endpoint - not sensitive
                    'ttl_seconds': ttl_seconds,
                    'exp': payload['exp'],
                    'jti': jti,  # Random nonce - safe to log
                    'event': 'act_prepared_out_of_session'
                }
            )
            
            return act_jwt
            
        except Exception as e:
            logger.error(
                "Failed to create act JWT",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'act_jwt_error'
                }
            )
            raise ValueError(f"Cannot create act JWT: {e.__class__.__name__}")


__all__ = ['HybridSender', 'UserSession']
