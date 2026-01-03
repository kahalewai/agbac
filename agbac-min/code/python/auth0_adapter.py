"""
AGBAC-Min Auth0 Adapter Module

This module implements the Auth0-specific adapter for AGBAC-Min dual-subject authorization.
Auth0 uses a Credentials Exchange Action to extract the 'act' claim from client assertions.

Security Features:
- Client assertion JWT created with proper signing
- HTTPS-only communication
- Secure secret handling
- PII-free logging
- Comprehensive error handling

Compatible with: Auth0 (all plans with Actions support)

Author: AGBAC-Min Project
License: Apache 2.0
"""

import logging
import time
import secrets
from typing import Dict, List
import jwt
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base_adapter import BaseAdapter, TokenResponse, TokenRequestError

# Configure module logger
logger = logging.getLogger(__name__)


class Auth0Adapter(BaseAdapter):
    """
    Auth0 implementation of BaseAdapter.
    
    This adapter creates client assertion JWTs containing the 'act' claim
    and sends them to Auth0's token endpoint. An Auth0 Credentials Exchange Action
    extracts the 'act' claim and includes it in the issued access token.
    
    Configuration:
        token_url: Auth0 token endpoint (e.g., https://tenant.auth0.com/oauth/token)
        client_id: Agent client ID (M2M application)
        client_secret: Client secret for signing client assertions
        audience: API identifier (e.g., https://api.example.com/finance)
        
    Security:
        - Client assertions signed with HS256
        - Unique JTI (nonce) per request for replay protection
        - All HTTP requests use HTTPS with certificate verification
        - Timeouts prevent hanging connections
        - Retry logic for transient failures
        
    Note: The Auth0 tenant must have a Credentials Exchange Action deployed
    to extract and inject the act claim.
    """
    
    def __init__(self, config: Dict[str, any]):
        """
        Initialize Auth0 adapter.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid or audience missing
        """
        super().__init__(config)
        
        # Auth0 requires audience for M2M tokens
        if not self.audience:
            logger.error(
                "Auth0 adapter requires 'audience' in configuration",
                extra={'event': 'auth0_config_error'}
            )
            raise ValueError("Auth0 adapter requires 'audience' configuration")
        
        # Extract Auth0 domain from token URL
        # Example: https://tenant.auth0.com/oauth/token -> https://tenant.auth0.com/
        self.auth0_domain = self.token_url.rsplit('/oauth/', 1)[0] + '/'
        
        # Configure HTTP client with security best practices
        self.session = self._create_secure_session()
        
        logger.info(
            "Auth0 adapter initialized",
            extra={
                'token_url_hash': self._hash_url(self.token_url),
                'audience_hash': self._hash_url(self.audience),
                'domain_hash': self._hash_url(self.auth0_domain),
                'event': 'auth0_adapter_init'
            }
        )
    
    def _create_secure_session(self) -> requests.Session:
        """
        Create HTTP session with security best practices.
        
        Returns:
            Configured requests.Session
            
        Security Features:
            - Automatic retries for transient failures
            - Connection pooling for efficiency
            - Timeout enforcement
            - TLS certificate verification enforced
        """
        session = requests.Session()
        
        # Retry configuration
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        return session
    
    def request_token(
        self,
        agent_id: str,
        act: Dict[str, str],
        scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject token from Auth0.
        
        Process:
        1. Validate inputs
        2. Create client assertion JWT with act claim
        3. Send token request to Auth0 with client assertion
        4. Auth0 Credentials Exchange Action extracts act and injects into token
        5. Parse and return response
        
        Args:
            agent_id: Agent's client ID (M2M application)
            act: Human identity dictionary (must contain 'sub')
            scope: List of requested scopes
            
        Returns:
            TokenResponse containing access token and metadata
            
        Raises:
            TokenRequestError: If token request fails
            
        Security:
            - Validates act claim before use
            - Client assertion includes unique nonce (jti)
            - All network calls use HTTPS
            - Errors don't expose sensitive data
        """
        # Validate inputs
        self._validate_act(act)
        
        # Log request start (sanitized)
        self._log_token_request_start(agent_id, act, scope)
        
        try:
            # Step 1: Create client assertion JWT with act
            client_assertion = self._create_client_assertion(agent_id, act)
            
            # Step 2: Prepare token request payload
            payload = {
                'grant_type': 'client_credentials',
                'client_id': agent_id,
                'audience': self.audience,
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': client_assertion
            }
            
            # Step 3: Send token request
            logger.debug(
                "Sending token request to Auth0",
                extra={
                    'audience': self.audience,
                    'scope': scope,
                    'event': 'auth0_token_request'
                }
            )
            
            response = self.session.post(
                self.token_url,
                data=payload,  # Form-encoded
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                timeout=10,
                verify=True
            )
            
            # Step 4: Handle response
            if response.status_code != 200:
                self._handle_token_error(response)
            
            token_data = response.json()
            
            # Step 5: Create TokenResponse
            token_response = TokenResponse(
                access_token=token_data['access_token'],
                token_type=token_data.get('token_type', 'Bearer'),
                expires_in=token_data.get('expires_in', 86400),  # Auth0 default: 24h
                scope=token_data.get('scope', ' '.join(scope))
            )
            
            # Log success (sanitized)
            self._log_token_request_success(token_response)
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "Auth0 token request failed - network error",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'auth0_network_error'
                }
            )
            raise TokenRequestError(
                f"Network error connecting to Auth0: {e.__class__.__name__}"
            )
        except (KeyError, ValueError) as e:
            logger.error(
                "Auth0 token response invalid",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'auth0_response_error'
                }
            )
            raise TokenRequestError(
                f"Invalid response from Auth0: {e.__class__.__name__}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error in Auth0 token request",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'auth0_unexpected_error'
                }
            )
            raise TokenRequestError(
                f"Unexpected error: {e.__class__.__name__}"
            )
    
    def _create_client_assertion(self, agent_id: str, act: Dict[str, str]) -> str:
        """
        Create client assertion JWT with act claim for Auth0.
        
        The client assertion is a JWT that contains:
        - iss: Issuer (agent client ID)
        - sub: Subject (agent client ID)
        - aud: Audience (Auth0 domain)
        - exp: Expiration (5 minutes from now)
        - iat: Issued at (current time)
        - jti: Unique nonce for replay protection
        - act: Human identity claim (extracted by Auth0 Action)
        
        Args:
            agent_id: Agent's client ID
            act: Human identity dictionary
            
        Returns:
            Signed JWT string
            
        Security:
            - Signed with client secret (HS256)
            - Short expiration (5 minutes) limits exposure
            - Unique jti prevents replay
            - Audience set to Auth0 domain (not API)
        """
        now = int(time.time())
        jti = secrets.token_urlsafe(32)
        
        payload = {
            'iss': agent_id,
            'sub': agent_id,
            'aud': self.auth0_domain,  # Auth0 domain, not API audience
            'exp': now + 300,  # 5 minutes
            'iat': now,
            'jti': jti,
            'act': act  # Auth0 Action will extract this
        }
        
        # Sign with client secret
        client_assertion = jwt.encode(
            payload,
            self._get_client_secret(),
            algorithm='HS256'
        )
        
        logger.debug(
            "Auth0 client assertion created",
            extra={
                'agent_id_hash': self._sanitize_identifier(agent_id),
                'jti_hash': self._sanitize_identifier(jti),
                'exp': now + 300,
                'event': 'auth0_client_assertion_created'
            }
        )
        
        return client_assertion
    
    def _handle_token_error(self, response: requests.Response) -> None:
        """
        Handle Auth0 token request error responses.
        
        Args:
            response: HTTP response object
            
        Raises:
            TokenRequestError: With appropriate error message
            
        Security: Extracts safe error information without exposing
        sensitive details from Auth0 error responses.
        """
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_description = error_data.get('error_description', 'Unknown error')
            error_type = error_data.get('error', 'unknown_error')
        except Exception:
            error_description = response.text[:100]
            error_type = 'parse_error'
        
        # Log error (sanitized)
        logger.error(
            "Auth0 returned error response",
            extra={
                'status_code': status_code,
                'error_type': error_type,
                'event': 'auth0_token_error'
            }
        )
        
        # Provide helpful error messages
        if status_code == 400:
            raise TokenRequestError(
                "Bad request to Auth0 - check client assertion or audience",
                status_code=status_code
            )
        elif status_code == 401:
            raise TokenRequestError(
                "Authentication failed - check client credentials",
                status_code=status_code
            )
        elif status_code == 403:
            raise TokenRequestError(
                "Access forbidden - check client is authorized for API",
                status_code=status_code
            )
        elif status_code == 429:
            raise TokenRequestError(
                "Rate limit exceeded - too many requests to Auth0",
                status_code=status_code
            )
        else:
            raise TokenRequestError(
                f"Auth0 error ({status_code}): {error_type}",
                status_code=status_code
            )
    
    def __del__(self):
        """Cleanup HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()


# Export public API
__all__ = ['Auth0Adapter']
