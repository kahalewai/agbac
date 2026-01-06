"""
AGBAC-Min EntraID (Azure AD) Adapter

This module implements the EntraID-specific adapter for AGBAC-Min dual-subject authorization.
EntraID uses a HYBRID APPROACH because client_credentials does not support custom claims.

Hybrid Approach:
- Agent token obtained from EntraID (contains agent identity only)
- Act assertion created by application (contains human identity)
- Both components returned together for use in API requests

Security Features:
- Standard client_credentials for agent token
- RSA-signed act assertion for human identity
- HTTPS-only communication
- Secure secret handling
- IAM identifier logging (pseudonymous, not PII)
- Comprehensive error handling

Compatible with: Microsoft EntraID (Azure AD) - all tiers

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
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from .base_adapter import BaseAdapter, TokenResponse, TokenRequestError

# Configure module logger
logger = logging.getLogger(__name__)


class EntraIDAdapter(BaseAdapter):
    """
    EntraID (Azure AD) implementation of BaseAdapter using hybrid approach.
    
    Unlike other adapters, EntraID cannot include custom claims (act) in tokens
    obtained via client_credentials. Therefore, this adapter:
    1. Obtains agent token from EntraID (standard client_credentials)
    2. Creates separate act assertion signed by application
    3. Returns both components together
    
    The resource server validates both components independently.
    
    Configuration:
        token_url: EntraID token endpoint
        client_id: Agent client/application ID
        client_secret: Client secret for EntraID authentication
        scope: API scope (e.g., https://api.example.com/.default)
        app_private_key_path: Path to application's private key (PEM)
        app_id: Application identifier for act assertion issuer
        act_audience: Audience for act assertion (API URL)
        
    Security:
        - Agent token from EntraID (RS256)
        - Act assertion signed with RSA (RS256)
        - Unique JTI per act assertion
        - Private key never logged
        - All HTTP requests use HTTPS
        
    Logging:
        - IAM identifiers logged directly for audit correlation
        - No hashing - enables direct correlation with EntraID logs
        - PII (email, name) never logged
    """
    
    def __init__(self, config: Dict[str, any]):
        """Initialize EntraID adapter with hybrid approach configuration."""
        super().__init__(config)
        
        # EntraID-specific required configuration
        required_entraid_fields = ['scope', 'app_private_key_path', 'app_id', 'act_audience']
        missing = [f for f in required_entraid_fields if f not in config]
        if missing:
            logger.error(
                "EntraID adapter missing required configuration",
                extra={'missing_fields': missing, 'event': 'entraid_config_error'}
            )
            raise ValueError(f"EntraID adapter requires: {', '.join(missing)}")
        
        self.scope = config['scope']
        self.app_id = config['app_id']
        self.act_audience = config['act_audience']
        
        # Load application private key
        try:
            self._load_private_key(config['app_private_key_path'])
        except Exception as e:
            logger.error(
                "Failed to load application private key",
                extra={'error_type': e.__class__.__name__, 'event': 'entraid_key_load_error'}
            )
            raise ValueError(f"Cannot load private key: {e.__class__.__name__}")
        
        # Extract tenant ID from token URL
        # Example: https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token
        try:
            self.tenant_id = self.token_url.split('/')[3]
        except IndexError:
            self.tenant_id = 'unknown'
        
        self.session = self._create_secure_session()
        
        # Log initialization with IAM identifiers (v1.1 - no hashing)
        logger.info(
            "EntraID adapter initialized (hybrid approach)",
            extra={
                'token_url': self._get_url_for_logging(self.token_url),
                'app_id': self.app_id,  # Application ID - not PII
                'tenant_id': self.tenant_id,  # Tenant ID - not PII
                'act_audience': self.act_audience,  # API audience - not PII
                'event': 'entraid_adapter_init'
            }
        )
    
    def _load_private_key(self, key_path: str) -> None:
        """Load application private key for signing act assertions."""
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        self._app_private_key = serialization.load_pem_private_key(
            key_data, password=None, backend=default_backend()
        )
        
        # Log key loaded (path only, not key content)
        logger.info(
            "Application private key loaded",
            extra={
                'key_path': key_path,  # File path - not sensitive
                'event': 'entraid_key_loaded'
            }
        )
    
    def _create_secure_session(self) -> requests.Session:
        """Create HTTP session with security best practices."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3, backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session
    
    def request_token(
        self, agent_id: str, act: Dict[str, str], scope: List[str]
    ) -> TokenResponse:
        """
        Request dual-subject components from EntraID (hybrid approach).
        
        EntraID uses a hybrid approach where the agent token and act assertion
        are separate components that must be sent together to resource servers.
        
        Args:
            agent_id: Agent client ID
            act: Human identity dictionary
            scope: Requested scopes (ignored - uses configured scope)
            
        Returns:
            TokenResponse with access_token and act_assertion
            
        Raises:
            TokenRequestError: If token request fails
        """
        self._validate_act(act)
        self._log_token_request_start(agent_id, act, scope)
        
        try:
            # Step 1: Get standard agent token from EntraID
            agent_token_data = self._request_agent_token()
            
            # Step 2: Create act assertion signed by application
            act_assertion = self._create_act_assertion(act)
            
            # Step 3: Create token response with both components
            token_response = TokenResponse(
                access_token=agent_token_data['access_token'],
                token_type=agent_token_data.get('token_type', 'Bearer'),
                expires_in=agent_token_data.get('expires_in', 3599),
                scope=agent_token_data.get('scope', self.scope),
                act_assertion=act_assertion
            )
            
            self._log_token_request_success(token_response)
            
            return token_response
            
        except TokenRequestError:
            raise
        except requests.exceptions.RequestException as e:
            # Network errors
            logger.error(
                "EntraID token request failed - network error",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'entraid_network_error'
                }
            )
            raise TokenRequestError(
                f"Network error connecting to EntraID: {e.__class__.__name__}"
            )
        except (KeyError, ValueError) as e:
            # Response parsing errors
            logger.error(
                "EntraID token response invalid",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'entraid_response_error'
                }
            )
            raise TokenRequestError(
                f"Invalid response from EntraID: {e.__class__.__name__}"
            )
        except Exception as e:
            # Unexpected errors
            logger.error(
                "Unexpected error in EntraID token request",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'entraid_unexpected_error'
                }
            )
            raise TokenRequestError(f"Unexpected error: {e.__class__.__name__}")
    
    def _request_agent_token(self) -> Dict:
        """Request standard agent token from EntraID."""
        try:
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self._get_client_secret(),
                'scope': self.scope
            }
            
            response = self.session.post(
                self.token_url, data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10, verify=True
            )
            
            if response.status_code != 200:
                self._handle_token_error(response)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "EntraID agent token request failed",
                extra={'error_type': e.__class__.__name__, 'event': 'entraid_network_error'}
            )
            raise TokenRequestError(f"Network error: {e.__class__.__name__}")
    
    def _create_act_assertion(self, act: Dict[str, str]) -> str:
        """
        Create application-signed act assertion JWT.
        
        Args:
            act: Human identity dictionary
            
        Returns:
            Signed JWT containing act claim
            
        Raises:
            ValueError: If JWT creation fails
        """
        # Generate unique nonce
        jti = secrets.token_urlsafe(32)
        
        # Build payload
        now = int(time.time())
        payload = {
            'iss': self.app_id,
            'sub': self.app_id,
            'aud': self.act_audience,
            'exp': now + 300,  # 5 minutes
            'iat': now,
            'jti': jti,
            'act': act
        }
        
        # Sign with application private key
        try:
            act_assertion = jwt.encode(
                payload,
                self._app_private_key,
                algorithm='RS256'
            )
            
            # Log with IAM identifiers (v1.1 - no hashing)
            logger.debug(
                "Act assertion created",
                extra={
                    'human_id': act.get('sub'),  # IAM identifier - safe to log
                    'oid': act.get('oid'),  # EntraID Object ID if present
                    'jti': jti,  # Random nonce - safe to log
                    'exp': payload['exp'],
                    'event': 'entraid_act_assertion_created'
                }
            )
            
            return act_assertion
            
        except Exception as e:
            logger.error(
                "Failed to create act assertion JWT",
                extra={
                    'error_type': e.__class__.__name__,
                    'event': 'act_assertion_error'
                }
            )
            raise ValueError(f"Cannot create act assertion: {e.__class__.__name__}")
    
    def _handle_token_error(self, response: requests.Response) -> None:
        """Handle EntraID token error responses."""
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_type = error_data.get('error', 'unknown_error')
            error_codes = error_data.get('error_codes', [])
        except Exception:
            error_type = 'parse_error'
            error_codes = []
        
        logger.error(
            "EntraID returned error",
            extra={
                'status_code': status_code,
                'error_type': error_type,
                'error_codes': error_codes,
                'event': 'entraid_token_error'
            }
        )
        
        if status_code == 400:
            raise TokenRequestError("Bad request - check credentials", status_code)
        elif status_code == 401:
            raise TokenRequestError("Authentication failed", status_code)
        elif status_code == 403:
            raise TokenRequestError("Access forbidden", status_code)
        else:
            raise TokenRequestError(f"EntraID error ({status_code})", status_code)
    
    def __del__(self):
        """Cleanup HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()


__all__ = ['EntraIDAdapter']
