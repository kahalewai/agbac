"""
AGBAC-Min Base Adapter Module

This module provides the abstract base class for all IAM vendor adapters.
All vendor-specific adapters (Keycloak, Auth0, Okta, EntraID) inherit from this base.

Security Features:
- Secrets never logged or exposed
- All network calls use HTTPS/TLS
- JWT tokens handled securely (no logging of token content)
- IAM identifier logging (pseudonymous, not PII)
- Proper error handling without exposing sensitive data

Author: AGBAC-Min Project
License: Apache 2.0
Version: 1.0.1
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

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
    - All logging uses IAM identifiers (pseudonymous, not PII)
    
    Logging:
    - IAM identifiers (client_id, agent_id, user sub) logged directly for audit correlation
    - These are pseudonymous identifiers that match IAM provider logs
    - PII (email, name) is NEVER logged
    - Secrets and tokens are NEVER logged
    
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
            - Logs IAM identifiers for audit correlation
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
        
        # Log initialization with IAM identifiers (not hashed)
        # These are IAM component identifiers, not PII
        logger.info(
            "Adapter initialized",
            extra={
                'adapter_type': self.__class__.__name__,
                'client_id': self.client_id,  # IAM identifier - safe to log
                'token_url': self._get_url_for_logging(self.token_url),
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
                - sub: Human's IAM identifier (user ID from IAM provider)
                - email: Human's email (optional, not logged)
                - name: Human's display name (optional, not logged)
            scope: List of requested scopes/permissions
            
        Returns:
            TokenResponse: Contains access_token and metadata
            
        Raises:
            TokenRequestError: If token request fails
            
        Security:
            - Never log PII (email, name) from act
            - Log IAM identifier (act.sub) for audit correlation
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
    
    def _get_url_for_logging(self, url: str) -> str:
        """
        Extract loggable portion of URL.
        
        Returns the URL without query parameters for safe logging.
        URLs themselves are not PII - they are IAM endpoint identifiers.
        
        Args:
            url: Full URL
            
        Returns:
            URL safe for logging (without query params)
            
        Security: Strips query parameters which might contain sensitive data.
        """
        if not url:
            return "unknown"
        # Remove query parameters if present
        return url.split('?')[0]
    
    def _prepare_act_for_logging(self, act: Dict[str, str]) -> Dict[str, str]:
        """
        Prepare act claim for logging using IAM identifiers.
        
        Uses IAM provider identifier (sub) which is:
        - Pseudonymous (not directly PII)
        - Stable across time
        - Matches IAM provider logs exactly
        - Traceable through IAM system with proper authorization
        
        Args:
            act: Act claim dictionary
            
        Returns:
            Act data safe for logging with IAM identifiers
            
        Best Practice:
            - Log IAM provider identifiers (sub, oid, user_id)
            - Do NOT log email or name (direct PII)
            - Correlation done via IAM identifier
            
        Example:
            Input:  {"sub": "f1234567-89ab-cdef-0123-456789abcdef", "email": "alice@corp.com", "name": "Alice Smith"}
            Output: {"human_id": "f1234567-89ab-cdef-0123-456789abcdef", "fields_present": ["sub", "email", "name"]}
        
        Security: IAM identifiers are pseudonymous - they don't reveal identity
        without access to the IAM system, providing privacy while enabling
        perfect log correlation with IAM provider logs.
        """
        log_act = {
            'human_id': act.get('sub'),  # IAM identifier (Keycloak user ID, Auth0 user ID, etc.)
            'fields_present': list(act.keys())
        }
        
        # Include explicit identifiers if present (e.g., EntraID OID)
        if 'user_id' in act:
            log_act['user_id'] = act['user_id']
        
        if 'oid' in act:  # EntraID Object ID
            log_act['oid'] = act['oid']
        
        # Note: Do NOT include email or name in logs
        
        return log_act
    
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
        Log token request initiation using IAM identifiers.
        
        Args:
            agent_id: Agent identifier (client ID - IAM component, not PII)
            act: Human identity (will use IAM identifier for logging)
            scope: Requested scopes
            
        Security: Logs IAM identifiers (pseudonymous), not email/name (PII).
        Enables perfect log correlation with IAM provider logs.
        """
        logger.info(
            "Token request initiated",
            extra={
                'agent_id': agent_id,  # IAM client ID - safe to log
                'act': self._prepare_act_for_logging(act),
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
        # Filter out sensitive fields from context
        safe_context = {
            k: v for k, v in context.items() 
            if k not in ['client_secret', 'token', 'access_token', 'act', 'assertion']
        }
        
        logger.error(
            "Token request failed",
            extra={
                'error_type': error.__class__.__name__,
                'error_message': str(error)[:100],  # Truncate to prevent log flooding
                'context': safe_context,
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
