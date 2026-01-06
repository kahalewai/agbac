"""
AGBAC-Min Keycloak Adapter

This module implements the Keycloak-specific adapter for AGBAC-Min dual-subject authorization.
Keycloak uses a protocol mapper to extract the 'act' claim from client assertions.

Security Features:
- Client assertion JWT created with proper signing
- HTTPS-only communication
- Secure secret handling
- IAM identifier logging (pseudonymous, not PII)
- Comprehensive error handling

Compatible with: Keycloak 23.0+

Author: AGBAC-Min Project
License: Apache 2.0
Version: 1.0.1
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


class KeycloakAdapter(BaseAdapter):
    """
    Keycloak implementation of BaseAdapter.
    
    This adapter creates client assertion JWTs containing the 'act' claim
    and sends them to Keycloak's token endpoint. Keycloak's protocol mapper
    extracts the 'act' claim and includes it in the issued access token.
    
    Configuration:
        token_url: Keycloak token endpoint (e.g., https://keycloak.example.com/realms/agbac-min/protocol/openid-connect/token)
        client_id: Agent client ID
        client_secret: Client secret for signing client assertions
        audience: Optional audience claim (defaults to Keycloak realm URL)
        
    Security:
        - Client assertions signed with HS256
        - Unique JTI (nonce) per request for replay protection
        - All HTTP requests use HTTPS with certificate verification
        - Timeouts prevent hanging connections
        - Retry logic for transient failures
        
    Logging:
        - IAM identifiers logged directly for audit correlation
        - No hashing - enables direct correlation with Keycloak logs
        - PII (email, name) never logged
    """
    
    def __init__(self, config: Dict[str, any]):
        """
        Initialize Keycloak adapter.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(config)
        
        # Extract Keycloak realm URL from token URL for audience
        # Example: https://keycloak.example.com/realms/agbac-min/protocol/openid-connect/token
        #       -> https://keycloak.example.com/realms/agbac-min
        if not self.audience:
            # Remove /protocol/openid-connect/token from URL
            self.audience = self.token_url.rsplit('/protocol/', 1)[0]
        
        # Configure HTTP client with security best practices
        self.session = self._create_secure_session()
        
        # Log initialization with IAM identifiers (v1.1 - no hashing)
        logger.info(
            "Keycloak adapter initialized",
            extra={
                'token_url': self._get_url_for_logging(self.token_url),
                'audience': self.audience,  # Realm URL - not PII
                'event': 'keycloak_adapter_init'
            }
        )
    
    def _create_secure_session(self) -> requests.Session:
        """
        Create HTTP session with security best practices.
        
        Returns:
            Configured requests.Session
            
        Security Features:
            - Automatic retries for transient failures (3 retries, exponential backoff)
            - Connection pooling for efficiency
            - Timeout enforcement (10 seconds)
            - TLS certificate verification enforced
        """
        session = requests.Session()
        
        # Retry configuration: 3 retries with exponential backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s delays
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
            allowed_methods=["POST"]  # Only retry POST for token requests
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        # Set default timeout (will be overridden per request)
        session.timeout = 10
        
        return session
    
    def request_token(
        self,
        agent_id: str,
        act: Dict[str, str],
        scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject token from Keycloak.
        
        Process:
        1. Validate inputs
        2. Create client assertion JWT with act claim
        3. Send token request with client assertion
        4. Parse and return response
        
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
        
        # Log request start with IAM identifiers
        self._log_token_request_start(agent_id, act, scope)
        
        try:
            # Step 1: Create client assertion JWT
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
                "Sending token request to Keycloak",
                extra={
                    'scope': scope,
                    'event': 'keycloak_token_request'
                }
            )
            
            response = self.session.post(
                self.token_url,
                data=payload,  # Form-encoded
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                timeout=10,  # 10 second timeout
                verify=True  # Enforce TLS certificate verification
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
            
            # Log success
            self._log_token_request_success(token_response)
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            # Network/HTTP errors
            logger.error(
                "Keycloak token request failed - network error",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'keycloak_network_error'
                }
            )
            raise TokenRequestError(
                f"Network error connecting to Keycloak: {e.__class__.__name__}"
            )
        except (KeyError, ValueError) as e:
            # Response parsing errors
            logger.error(
                "Keycloak token response invalid",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'keycloak_response_error'
                }
            )
            raise TokenRequestError(
                f"Invalid response from Keycloak: {e.__class__.__name__}"
            )
        except Exception as e:
            # Unexpected errors
            logger.error(
                "Unexpected error in Keycloak token request",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'keycloak_unexpected_error'
                }
            )
            raise TokenRequestError(
                f"Unexpected error: {e.__class__.__name__}"
            )
    
    def _create_client_assertion(self, agent_id: str, act: Dict[str, str]) -> str:
        """
        Create client assertion JWT with act claim.
        
        The client assertion is a JWT that contains:
        - iss: Issuer (agent client ID)
        - sub: Subject (agent client ID)
        - aud: Audience (Keycloak realm URL)
        - exp: Expiration (5 minutes from now)
        - iat: Issued at (current time)
        - jti: Unique nonce for replay protection
        - act: Human identity claim
        
        Args:
            agent_id: Agent's client ID
            act: Human identity dictionary
            
        Returns:
            Signed JWT string
            
        Security:
            - Signed with client secret (HS256)
            - Short expiration (5 minutes) limits exposure window
            - Unique jti prevents replay attacks
            - act claim contains human identity for Keycloak mapper
        """
        now = int(time.time())
        
        # Generate unique nonce for replay protection
        jti = secrets.token_urlsafe(32)
        
        payload = {
            'iss': agent_id,
            'sub': agent_id,
            'aud': self.audience,
            'exp': now + 300,  # 5 minutes
            'iat': now,
            'jti': jti,
            'act': act  # Human identity - Keycloak mapper will extract this
        }
        
        # Sign with client secret (HS256)
        client_assertion = jwt.encode(
            payload,
            self._get_client_secret(),
            algorithm='HS256'
        )
        
        # Log with IAM identifiers (v1.1 - no hashing)
        logger.debug(
            "Client assertion created",
            extra={
                'agent_id': agent_id,  # IAM client ID - safe to log
                'jti': jti,  # Random nonce - safe to log
                'exp': now + 300,
                'event': 'client_assertion_created'
            }
        )
        
        return client_assertion
    
    def _handle_token_error(self, response: requests.Response) -> None:
        """
        Handle token request error responses.
        
        Args:
            response: HTTP response object
            
        Raises:
            TokenRequestError: With appropriate error message
            
        Security: Extracts safe error information without exposing
        sensitive details from Keycloak error responses.
        """
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_description = error_data.get('error_description', 'Unknown error')
            error_type = error_data.get('error', 'unknown_error')
        except Exception:
            error_description = response.text[:100]  # Truncate
            error_type = 'parse_error'
        
        # Log error (sanitized - no sensitive data)
        logger.error(
            "Keycloak returned error response",
            extra={
                'status_code': status_code,
                'error_type': error_type,
                'event': 'keycloak_token_error'
            }
        )
        
        # Provide helpful error messages based on status code
        if status_code == 400:
            raise TokenRequestError(
                "Bad request to Keycloak - check client assertion format",
                status_code=status_code
            )
        elif status_code == 401:
            raise TokenRequestError(
                "Authentication failed - check client credentials",
                status_code=status_code
            )
        elif status_code == 403:
            raise TokenRequestError(
                "Access forbidden - check client permissions",
                status_code=status_code
            )
        else:
            raise TokenRequestError(
                f"Keycloak error ({status_code}): {error_type}",
                status_code=status_code
            )
    
    def __del__(self):
        """
        Cleanup when adapter is destroyed.
        
        Security: Properly close HTTP session to free resources.
        """
        if hasattr(self, 'session'):
            self.session.close()


# Export public API
__all__ = ['KeycloakAdapter']
