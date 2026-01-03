"""
AGBAC-Min Hybrid Sender Module

This module provides the HybridSender class for extracting human identity from
application sessions and preparing it for transmission to AI agents.

Works for BOTH in-session and out-of-session scenarios with ALL IAM vendors.

Security Features:
- PII never logged (only sanitized identifiers)
- JWT signing for out-of-session (RS256)
- Replay protection via JTI nonce
- Short JWT expiration (60 seconds)
- Input validation

Author: AGBAC-Min Project
License: Apache 2.0
"""

import logging
import time
import secrets
import hashlib
from typing import Dict, Optional
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class HybridSender:
    """
    Extract and prepare human identity (act) for transmission to agents.
    
    Supports two scenarios:
    1. In-Session: Act passed directly in memory
    2. Out-of-Session: Act wrapped in signed JWT, sent over TLS
    
    Security:
        - Never logs PII
        - Signs JWTs with RSA (RS256)
        - Short JWT expiration (60s)
        - Unique nonce per JWT
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
                logger.info("HybridSender initialized with out-of-session capability")
            except Exception as e:
                logger.error(f"Failed to load private key: {e.__class__.__name__}")
                raise ValueError(f"Cannot load private key: {e.__class__.__name__}")
        else:
            logger.info("HybridSender initialized (in-session only)")
    
    def _load_private_key(self, key_path: str) -> None:
        """Load RSA private key from PEM file."""
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        self._private_key = serialization.load_pem_private_key(
            key_data, password=None, backend=default_backend()
        )
    
    def extract_act_from_session(self, session: Dict[str, any]) -> Dict[str, str]:
        """
        Extract human identity from authenticated session.
        
        Args:
            session: Authenticated session with user data
            
        Returns:
            Act dictionary with sub, email, and optionally name
            
        Security: Logs only sanitized identifiers, never actual PII.
        """
        if not session or not isinstance(session, dict):
            raise ValueError("Session must be a dictionary")
        
        # Extract email (required)
        email = (session.get('email') or session.get('user_email') or 
                session.get('userPrincipalName') or session.get('mail'))
        
        if not email:
            logger.error("Session missing email field")
            raise ValueError("Session must contain email")
        
        # Extract subject (use email if no explicit sub)
        sub = (session.get('sub') or session.get('user_id') or 
               session.get('oid') or email)
        
        # Extract name (optional)
        name = (session.get('name') or session.get('display_name') or 
                session.get('displayName'))
        
        # Build act
        act = {'sub': sub, 'email': email}
        if name:
            act['name'] = name
        
        logger.info(
            "Human identity extracted",
            extra={
                'sub_hash': self._sanitize_identifier(sub),
                'has_name': name is not None,
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
        logger.debug(
            "Act prepared for in-session",
            extra={
                'sub_hash': self._sanitize_identifier(act.get('sub', '')),
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
            act: Human identity dictionary
            agent_endpoint: Agent's endpoint URL (JWT audience)
            ttl_seconds: JWT expiration (default: 60s)
            
        Returns:
            Signed JWT string
            
        Security:
            - RS256 signature
            - Short expiration
            - Unique nonce (jti)
            - Must be sent over TLS
        """
        if not self._private_key:
            raise ValueError("HybridSender not configured for out-of-session")
        
        if not act or 'sub' not in act:
            raise ValueError("Act must contain 'sub' field")
        
        if not agent_endpoint or not agent_endpoint.startswith('https://'):
            raise ValueError("Agent endpoint must use HTTPS")
        
        # Create JWT
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
        
        act_jwt = jwt.encode(payload, self._private_key, algorithm='RS256')
        
        logger.info(
            "Act prepared for out-of-session",
            extra={
                'sub_hash': self._sanitize_identifier(act['sub']),
                'ttl_seconds': ttl_seconds,
                'event': 'act_prepared_out_of_session'
            }
        )
        
        return act_jwt
    
    def _sanitize_identifier(self, identifier: str) -> str:
        """Sanitize identifier for safe logging."""
        if not identifier:
            return "unknown"
        
        hash_obj = hashlib.sha256(identifier.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:12]
        prefix = 'user' if '@' in identifier else 'id'
        return f"{prefix}_{hash_hex}"


__all__ = ['HybridSender']
