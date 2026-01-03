"""
AGBAC-Min Base Adapter Module

This module provides the abstract base class for all IAM vendor adapters.
All vendor-specific adapters (Keycloak, Auth0, Okta, EntraID) inherit from this base.

Security Features:
- Secrets never logged or exposed
- All network calls use HTTPS/TLS
- JWT tokens handled securely (no logging of token content)
- PII protection in logs (only log sanitized identifiers)
- Proper error handling without exposing sensitive data

Author: AGBAC-Min Project
License: Apache 2.0
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class TokenResponse:
    """
    Container for token responses from IAM providers.
    
    Attributes:
        access_token: OAuth access token (SENSITIVE - never logged)
        token_type: Type of token (typically "Bearer")
        expires_in: Token lifetime in seconds
        scope: Granted scopes as string or list
        act_assertion: Optional act assertion JWT for EntraID (SENSITIVE - never logged)
        
    Security: This class contains SENSITIVE data. Never log the full object.
    """
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    act_assertion: Optional[str] = None
    
    def __repr__(self) -> str:
        """
        Safe representation that masks sensitive data.
        
        Security: Masks access_token and act_assertion to prevent accidental logging.
        """
        return (
            f"TokenResponse("
            f"token_type={self.token_type}, "
            f"expires_in={self.expires_in}, "
            f"scope={self.scope}, "
            f"access_token=***REDACTED***, "
            f"act_assertion={'***REDACTED***' if self.act_assertion else None})"
        )


class BaseAdapter(ABC):
    """
    Abstract base class for IAM vendor adapters.
    
    All vendor-specific adapters must implement the request_token method.
    This ensures consistent interface across Keycloak, Auth0, Okta, and EntraID.
    
    Security Principles:
    - All secrets stored securely (never logged)
    - All network calls require HTTPS
    - All errors handled without exposing sensitive data
    - All logging uses sanitized identifiers only
    
    Usage:
        adapter = KeycloakAdapter(config)
        token_response = adapter.request_token(agent_id, act, scope)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize base adapter with vendor configuration.
        
        Args:
            config: Configuration dictionary containing:
                - token_url: OAuth token endpoint (must be HTTPS)
                - client_id: Agent client/application ID
                - client_secret: Client secret (SENSITIVE)
                - audience: API audience/identifier (optional)
                - Additional vendor-specific settings
        
        Raises:
            ValueError: If required config missing or token_url not HTTPS
            
        Security:
            - Validates HTTPS requirement for token_url
            - Stores client_secret securely (never logged)
            - Logs sanitized configuration only
        """
        self.config = config
        
        # Validate required configuration
        required_fields = ['token_url', 'client_id', 'client_secret']
        missing_fields = [f for f in required_fields if f not in config]
        if missing_fields:
            logger.error(
                "Missing required configuration fields",
                extra={
                    'missing_fields': missing_fields,
                    'event': 'adapter_init_failed'
                }
            )
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        # Security: Enforce HTTPS for token endpoint
        self.token_url = config['token_url']
        if not self.token_url.startswith('https://'):
            logger.error(
                "Token URL must use HTTPS for security",
                extra={
                    'token_url_scheme': self.token_url.split(':')[0],
                    'event': 'insecure_token_url'
                }
            )
            raise ValueError("Token URL must use HTTPS (https://)")
        
        self.client_id = config['client_id']
        self._client_secret = config['client_secret']  # Private: never expose
        self.audience = config.get('audience')
        
        # Log initialization (sanitized)
        logger.info(
            "Adapter initialized",
            extra={
                'adapter_type': self.__class__.__name__,
                'client_id': self._sanitize_identifier(self.client_id),
                'token_url_hash': self._hash_url(self.token_url),
                'event': 'adapter_initialized'
            }
        )
    
    @abstractmethod
    def request_token(
        self,
        agent_id: str,
        act: Dict[str, str],
        scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject token from IAM provider.
        
        This is the core method that must be implemented by all vendor adapters.
        
        Args:
            agent_id: Agent's client/application ID
            act: Human identity dictionary containing:
                - sub: Human's subject identifier (email, username, etc.)
                - email: Human's email (optional)
                - name: Human's display name (optional)
            scope: List of requested scopes/permissions
            
        Returns:
            TokenResponse: Contains access_token and metadata
            
        Raises:
            TokenRequestError: If token request fails
            
        Security:
            - Never log act data directly (contains PII)
            - Never log returned tokens
            - Use HTTPS for all requests
            - Handle errors without exposing sensitive data
        """
        pass
    
    def _get_client_secret(self) -> str:
        """
        Secure accessor for client secret.
        
        Returns:
            Client secret string
            
        Security: This method provides controlled access to the secret.
        The secret is never logged and should only be used for authentication.
        """
        return self._client_secret
    
    def _sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize identifier for safe logging.
        
        Takes an identifier (client_id, user_id, etc.) and creates a
        non-reversible but consistent representation for logging.
        
        Args:
            identifier: Original identifier (may contain PII)
            
        Returns:
            Sanitized identifier safe for logging
            
        Security: Uses SHA-256 hash to create consistent but anonymous identifier.
        Same input always produces same output, enabling log correlation without
        exposing PII.
        
        Example:
            "alice@corp.example.com" -> "user_a1b2c3d4..."
        """
        if not identifier:
            return "unknown"
        
        # Hash the identifier
        hash_obj = hashlib.sha256(identifier.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:12]  # First 12 chars for brevity
        
        # Determine prefix based on identifier format
        if '@' in identifier:
            prefix = 'user'
        elif identifier.startswith('0oa') or identifier.startswith('a1b2'):
            prefix = 'app'
        else:
            prefix = 'id'
        
        return f"{prefix}_{hash_hex}"
    
    def _hash_url(self, url: str) -> str:
        """
        Create hash of URL for logging without exposing full URL.
        
        Args:
            url: Full URL
            
        Returns:
            Hash of URL for logging
            
        Security: Prevents exposing full URLs in logs which may contain
        sensitive path parameters or query strings.
        """
        hash_obj = hashlib.sha256(url.encode('utf-8'))
        return f"url_{hash_obj.hexdigest()[:12]}"
    
    def _sanitize_act(self, act: Dict[str, str]) -> Dict[str, str]:
        """
        Create sanitized version of act claim for logging.
        
        Args:
            act: Original act dictionary (contains PII)
            
        Returns:
            Sanitized act dictionary safe for logging
            
        Security: Replaces PII (email, name) with hashed identifiers.
        Allows correlation in logs without exposing sensitive data.
        
        Example:
            Input:  {"sub": "alice@corp.com", "email": "alice@corp.com", "name": "Alice Smith"}
            Output: {"sub_hash": "user_a1b2c3d4", "fields": ["sub", "email", "name"]}
        """
        return {
            'sub_hash': self._sanitize_identifier(act.get('sub', '')),
            'fields': list(act.keys()),
            'field_count': len(act)
        }
    
    def _validate_act(self, act: Dict[str, str]) -> None:
        """
        Validate act claim structure.
        
        Args:
            act: Act dictionary to validate
            
        Raises:
            ValueError: If act is invalid
            
        Security: Ensures act contains minimum required fields before
        using it in token requests. Prevents sending malformed data.
        """
        if not act:
            logger.error(
                "Act claim is empty",
                extra={'event': 'invalid_act_claim'}
            )
            raise ValueError("Act claim cannot be empty")
        
        if 'sub' not in act:
            logger.error(
                "Act claim missing required 'sub' field",
                extra={
                    'act_fields': list(act.keys()),
                    'event': 'invalid_act_claim'
                }
            )
            raise ValueError("Act claim must contain 'sub' field")
        
        if not act['sub']:
            logger.error(
                "Act claim 'sub' field is empty",
                extra={'event': 'invalid_act_claim'}
            )
            raise ValueError("Act claim 'sub' field cannot be empty")
    
    def _log_token_request_start(
        self,
        agent_id: str,
        act: Dict[str, str],
        scope: List[str]
    ) -> None:
        """
        Log token request initiation (sanitized).
        
        Args:
            agent_id: Agent identifier
            act: Human identity (will be sanitized)
            scope: Requested scopes
            
        Security: Logs only sanitized identifiers, never PII or secrets.
        """
        logger.info(
            "Token request initiated",
            extra={
                'agent_id_hash': self._sanitize_identifier(agent_id),
                'act_sanitized': self._sanitize_act(act),
                'scope': scope,
                'adapter_type': self.__class__.__name__,
                'event': 'token_request_start'
            }
        )
    
    def _log_token_request_success(
        self,
        response: TokenResponse
    ) -> None:
        """
        Log successful token request (sanitized).
        
        Args:
            response: Token response (will be sanitized)
            
        Security: Logs metadata only, never the actual token.
        """
        logger.info(
            "Token request successful",
            extra={
                'token_type': response.token_type,
                'expires_in': response.expires_in,
                'scope': response.scope,
                'has_act_assertion': response.act_assertion is not None,
                'event': 'token_request_success'
            }
        )
    
    def _log_token_request_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """
        Log token request error (sanitized).
        
        Args:
            error: Exception that occurred
            context: Additional context (will be sanitized)
            
        Security: Logs error type and safe context only.
        Never logs sensitive data from error messages.
        """
        logger.error(
            "Token request failed",
            extra={
                'error_type': error.__class__.__name__,
                'error_message': str(error)[:100],  # Truncate to prevent log flooding
                'context': {k: v for k, v in context.items() if k not in ['client_secret', 'token', 'act']},
                'event': 'token_request_error'
            },
            exc_info=False  # Don't include full traceback in logs (may contain sensitive data)
        )


class TokenRequestError(Exception):
    """
    Exception raised when token request fails.
    
    This exception is raised by adapters when they cannot obtain a token
    from the IAM provider.
    
    Security: Error messages should not contain sensitive data like
    client secrets, tokens, or PII.
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        """
        Initialize token request error.
        
        Args:
            message: Error description (should not contain sensitive data)
            status_code: HTTP status code if applicable
        """
        self.status_code = status_code
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation of error."""
        if self.status_code:
            return f"Token request failed (HTTP {self.status_code}): {super().__str__()}"
        return f"Token request failed: {super().__str__()}"


# Module-level configuration validation
def validate_adapter_config(config: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate adapter configuration contains required fields.
    
    Args:
        config: Configuration dictionary
        required_fields: List of required field names
        
    Raises:
        ValueError: If required fields are missing
        
    Security: Validates configuration before use to prevent
    runtime errors that might expose sensitive data.
    """
    missing = [f for f in required_fields if f not in config]
    if missing:
        logger.error(
            "Invalid adapter configuration",
            extra={
                'missing_fields': missing,
                'event': 'config_validation_failed'
            }
        )
        raise ValueError(f"Missing required configuration fields: {', '.join(missing)}")


# Export public API
__all__ = [
    'BaseAdapter',
    'TokenResponse',
    'TokenRequestError',
    'validate_adapter_config'
]
