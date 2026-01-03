"""
AGBAC-Min Okta Adapter Module

This module implements the Okta-specific adapter for AGBAC-Min dual-subject authorization.
Okta uses a custom claim with expression to extract the 'act' claim from client assertions.

Security Features:
- Client assertion JWT created with proper signing
- HTTPS-only communication
- Secure secret handling
- PII-free logging
- Comprehensive error handling

Compatible with: Okta Workforce Identity with Custom Authorization Server

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


class OktaAdapter(BaseAdapter):
    """
    Okta implementation of BaseAdapter.
    
    This adapter creates client assertion JWTs containing the 'act' claim
    and sends them to Okta's custom authorization server token endpoint.
    Okta's custom claim expression (clientAssertion.claims.act) extracts
    the 'act' claim and includes it in the issued access token.
    
    Configuration:
        token_url: Okta token endpoint (e.g., https://dev-123.okta.com/oauth2/aus123/v1/token)
        client_id: Agent client ID (OAuth service app)
        client_secret: Client secret for signing client assertions
        audience: API audience (e.g., https://api.example.com)
        auth_server_id: Custom authorization server ID (extracted from token_url if not provided)
        
    Security:
        - Client assertions signed with HS256
        - Unique JTI (nonce) per request for replay protection
        - All HTTP requests use HTTPS with certificate verification
        - Timeouts prevent hanging connections
        - Retry logic for transient failures
        
    Note: Requires Okta Custom Authorization Server with configured act custom claim.
    """
    
    def __init__(self, config: Dict[str, any]):
        """
        Initialize Okta adapter.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid or audience missing
        """
        super().__init__(config)
        
        # Okta requires audience for tokens
        if not self.audience:
            logger.error(
                "Okta adapter requires 'audience' in configuration",
                extra={'event': 'okta_config_error'}
            )
            raise ValueError("Okta adapter requires 'audience' configuration")
        
        # Extract Okta domain and auth server ID from token URL
        # Example: https://dev-123.okta.com/oauth2/aus123abc/v1/token
        #       -> domain: https://dev-123.okta.com
        #       -> auth_server_id: aus123abc
        self._parse_token_url()
        
        # Configure HTTP client
        self.session = self._create_secure_session()
        
        logger.info(
            "Okta adapter initialized",
            extra={
                'token_url_hash': self._hash_url(self.token_url),
                'audience_hash': self._hash_url(self.audience),
                'domain_hash': self._hash_url(self.okta_domain),
                'auth_server_id': self.auth_server_id[:8] + '...',  # Partial for correlation
                'event': 'okta_adapter_init'
            }
        )
    
    def _parse_token_url(self) -> None:
        """
        Parse Okta domain and authorization server ID from token URL.
        
        Security: Validates URL structure to ensure proper configuration.
        """
        try:
            # Split: https://dev-123.okta.com/oauth2/aus123abc/v1/token
            parts = self.token_url.split('/oauth2/')
            self.okta_domain = parts[0]
            
            # Extract auth server ID
            auth_server_part = parts[1].split('/')[0]
            self.auth_server_id = auth_server_part
            
            # Audience for client assertion is the auth server URL
            self.assertion_audience = f"{self.okta_domain}/oauth2/{self.auth_server_id}"
            
        except (IndexError, ValueError) as e:
            logger.error(
                "Invalid Okta token URL format",
                extra={
                    'token_url_hash': self._hash_url(self.token_url),
                    'event': 'okta_url_parse_error'
                }
            )
            raise ValueError(
                "Invalid Okta token URL format. "
                "Expected: https://domain.okta.com/oauth2/aus123.../v1/token"
            )
    
    def _create_secure_session(self) -> requests.Session:
        """
        Create HTTP session with security best practices.
        
        Returns:
            Configured requests.Session
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
        Request dual-subject token from Okta.
        
        Process:
        1. Validate inputs
        2. Create client assertion JWT with act claim
        3. Send token request to Okta with client assertion
        4. Okta custom claim expression extracts act
        5. Parse and return response
        
        Args:
            agent_id: Agent's client ID
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
                'scope': ' '.join(scope),
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': client_assertion
            }
            
            # Step 3: Send token request
            logger.debug(
                "Sending token request to Okta",
                extra={
                    'scope': scope,
                    'event': 'okta_token_request'
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
                expires_in=token_data.get('expires_in', 3600),
                scope=token_data.get('scope', ' '.join(scope))
            )
            
            # Log success (sanitized)
            self._log_token_request_success(token_response)
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "Okta token request failed - network error",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'okta_network_error'
                }
            )
            raise TokenRequestError(
                f"Network error connecting to Okta: {e.__class__.__name__}"
            )
        except (KeyError, ValueError) as e:
            logger.error(
                "Okta token response invalid",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'okta_response_error'
                }
            )
            raise TokenRequestError(
                f"Invalid response from Okta: {e.__class__.__name__}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error in Okta token request",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'okta_unexpected_error'
                }
            )
            raise TokenRequestError(
                f"Unexpected error: {e.__class__.__name__}"
            )
    
    def _create_client_assertion(self, agent_id: str, act: Dict[str, str]) -> str:
        """
        Create client assertion JWT with act claim for Okta.
        
        The client assertion is a JWT that contains:
        - iss: Issuer (agent client ID)
        - sub: Subject (agent client ID)
        - aud: Audience (Okta authorization server URL)
        - exp: Expiration (5 minutes from now)
        - iat: Issued at (current time)
        - jti: Unique nonce for replay protection
        - act: Human identity claim (extracted by Okta expression)
        
        Args:
            agent_id: Agent's client ID
            act: Human identity dictionary
            
        Returns:
            Signed JWT string
            
        Security:
            - Signed with client secret (HS256)
            - Short expiration (5 minutes) limits exposure
            - Unique jti prevents replay
            - Audience is authorization server (not API audience)
        """
        now = int(time.time())
        jti = secrets.token_urlsafe(32)
        
        payload = {
            'iss': agent_id,
            'sub': agent_id,
            'aud': self.assertion_audience,  # Auth server URL, not API audience
            'exp': now + 300,  # 5 minutes
            'iat': now,
            'jti': jti,
            'act': act  # Okta expression: clientAssertion.claims.act
        }
        
        # Sign with client secret
        client_assertion = jwt.encode(
            payload,
            self._get_client_secret(),
            algorithm='HS256'
        )
        
        logger.debug(
            "Okta client assertion created",
            extra={
                'agent_id_hash': self._sanitize_identifier(agent_id),
                'jti_hash': self._sanitize_identifier(jti),
                'exp': now + 300,
                'event': 'okta_client_assertion_created'
            }
        )
        
        return client_assertion
    
    def _handle_token_error(self, response: requests.Response) -> None:
        """
        Handle Okta token request error responses.
        
        Args:
            response: HTTP response object
            
        Raises:
            TokenRequestError: With appropriate error message
            
        Security: Extracts safe error information without exposing
        sensitive details from Okta error responses.
        """
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_description = error_data.get('error_description', 'Unknown error')
            error_type = error_data.get('error', 'unknown_error')
            error_code = error_data.get('errorCode', '')
        except Exception:
            error_description = response.text[:100]
            error_type = 'parse_error'
            error_code = ''
        
        # Log error (sanitized)
        logger.error(
            "Okta returned error response",
            extra={
                'status_code': status_code,
                'error_type': error_type,
                'error_code': error_code,
                'event': 'okta_token_error'
            }
        )
        
        # Provide helpful error messages
        if status_code == 400:
            raise TokenRequestError(
                "Bad request to Okta - check client assertion or scope",
                status_code=status_code
            )
        elif status_code == 401:
            raise TokenRequestError(
                "Authentication failed - check client credentials",
                status_code=status_code
            )
        elif status_code == 403:
            raise TokenRequestError(
                "Access forbidden - check authorization policy",
                status_code=status_code
            )
        elif status_code == 429:
            raise TokenRequestError(
                "Rate limit exceeded - too many requests to Okta",
                status_code=status_code
            )
        else:
            raise TokenRequestError(
                f"Okta error ({status_code}): {error_type}",
                status_code=status_code
            )
    
    def __del__(self):
        """Cleanup HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()


# Export public API
__all__ = ['OktaAdapter']
