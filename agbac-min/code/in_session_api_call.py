"""
AGBAC-Min Phase 1: In-Session API Call

Make API calls with dual-subject tokens (in-session scenario).

Security:
- Enforces HTTPS for all API calls
- Handles token format differences (single token vs hybrid)
- No PII logged
- Proper error handling

Vendor Support: All vendors with automatic header adaptation

Author: AGBAC-Min Project
"""

import logging
from typing import Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from adapters.base_adapter import TokenResponse

logger = logging.getLogger(__name__)


class InSessionAPICall:
    """
    Make API calls with dual-subject tokens (in-session).
    
    Handles vendor differences:
    - Keycloak/Auth0/Okta: Single Authorization header
    - EntraID: Authorization header + X-Act-Assertion header
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize API call handler.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
            
        Security: Configures secure HTTP session with retries.
        """
        self.timeout = timeout
        self.session = self._create_secure_session()
        
        logger.info("In-session API call handler initialized")
    
    def _create_secure_session(self) -> requests.Session:
        """Create HTTP session with security best practices."""
        session = requests.Session()
        
        # Retry configuration
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        return session
    
    def call_api(
        self,
        token_response: TokenResponse,
        api_url: str,
        method: str = 'GET',
        json_data: Optional[Dict] = None
    ) -> requests.Response:
        """
        Make API call with dual-subject token.
        
        Args:
            token_response: Token response from adapter (contains access_token and possibly act_assertion)
            api_url: API endpoint URL (must be HTTPS)
            method: HTTP method (GET, POST, PUT, DELETE)
            json_data: Optional JSON payload for POST/PUT
            
        Returns:
            HTTP response object
            
        Raises:
            ValueError: If API URL not HTTPS
            requests.RequestException: If HTTP request fails
            
        Security:
            - Enforces HTTPS
            - Adapts headers based on token structure (EntraID hybrid vs others)
            - Token never logged
            - Proper error handling
            
        Example:
            # Keycloak/Auth0/Okta
            response = api_call.call_api(
                token_response,
                'https://api.example.com/finance/reports/Q4'
            )
            
            # EntraID (automatic handling)
            response = api_call.call_api(
                token_response,  # Contains access_token + act_assertion
                'https://api.example.com/finance/reports/Q4'
            )
        """
        # Validate HTTPS
        if not api_url.startswith('https://'):
            logger.error("API URL must use HTTPS")
            raise ValueError("API URL must use HTTPS")
        
        # Prepare headers based on token structure
        headers = self._prepare_headers(token_response)
        
        # Add content type for POST/PUT
        if json_data:
            headers['Content-Type'] = 'application/json'
        
        # Log request start (sanitized)
        logger.info(
            "API call starting",
            extra={
                'method': method,
                'api_url_hash': self._hash_url(api_url),
                'has_act_assertion': token_response.act_assertion is not None,
                'event': 'api_call_start'
            }
        )
        
        try:
            # Make HTTP request
            response = self.session.request(
                method=method,
                url=api_url,
                headers=headers,
                json=json_data,
                timeout=self.timeout,
                verify=True  # Enforce TLS certificate verification
            )
            
            # Log response (sanitized)
            logger.info(
                "API call completed",
                extra={
                    'status_code': response.status_code,
                    'method': method,
                    'event': 'api_call_complete'
                }
            )
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error("API call timed out", extra={'timeout': self.timeout})
            raise
        except requests.exceptions.SSLError:
            logger.error("API call SSL/TLS error")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(
                "API call failed",
                extra={'error_type': e.__class__.__name__}
            )
            raise
    
    def _prepare_headers(self, token_response: TokenResponse) -> Dict[str, str]:
        """
        Prepare HTTP headers based on token structure.
        
        Args:
            token_response: Token response from adapter
            
        Returns:
            Dictionary of HTTP headers
            
        Security: Adapts to vendor differences automatically.
        
        Keycloak/Auth0/Okta:
            Authorization: Bearer <token>
        
        EntraID:
            Authorization: Bearer <entraid-token>
            X-Act-Assertion: <app-signed-jwt>
        """
        headers = {
            'Authorization': f"Bearer {token_response.access_token}"
        }
        
        # EntraID: Add act assertion header
        if token_response.act_assertion:
            headers['X-Act-Assertion'] = token_response.act_assertion
            logger.debug("Added X-Act-Assertion header (EntraID hybrid)")
        
        return headers
    
    def _hash_url(self, url: str) -> str:
        """Hash URL for logging without exposing full URL."""
        import hashlib
        hash_obj = hashlib.sha256(url.encode('utf-8'))
        return f"url_{hash_obj.hexdigest()[:12]}"
    
    def __del__(self):
        """Cleanup HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()


__all__ = ['InSessionAPICall']
