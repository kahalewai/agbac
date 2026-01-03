"""
AGBAC-Min Phase 2: Out-of-Session API Call

Make API calls with dual-subject tokens (out-of-session scenario).

Security:
- Enforces HTTPS for all API calls
- Handles token format differences automatically
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


class OutOfSessionAPICall:
    """
    Make API calls with dual-subject tokens (out-of-session).
    
    Identical to in-session API calls, but used in out-of-session context.
    Handles vendor differences automatically.
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize API call handler.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.session = self._create_secure_session()
        
        logger.info("Out-of-session API call handler initialized")
    
    def _create_secure_session(self) -> requests.Session:
        """Create HTTP session with security best practices."""
        session = requests.Session()
        
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
            token_response: Token from adapter (access_token and possibly act_assertion)
            api_url: API endpoint URL (must be HTTPS)
            method: HTTP method
            json_data: Optional JSON payload
            
        Returns:
            HTTP response
            
        Security:
            - Enforces HTTPS
            - Adapts headers for vendor differences
            - No token logging
            - Proper error handling
        """
        # Validate HTTPS
        if not api_url.startswith('https://'):
            logger.error("API URL must use HTTPS")
            raise ValueError("API URL must use HTTPS")
        
        # Prepare headers
        headers = self._prepare_headers(token_response)
        
        if json_data:
            headers['Content-Type'] = 'application/json'
        
        logger.info(
            "API call starting",
            extra={
                'method': method,
                'has_act_assertion': token_response.act_assertion is not None,
                'event': 'api_call_start'
            }
        )
        
        try:
            response = self.session.request(
                method=method,
                url=api_url,
                headers=headers,
                json=json_data,
                timeout=self.timeout,
                verify=True
            )
            
            logger.info(
                "API call completed",
                extra={
                    'status_code': response.status_code,
                    'event': 'api_call_complete'
                }
            )
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error("API call timed out")
            raise
        except requests.exceptions.SSLError:
            logger.error("API call SSL/TLS error")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e.__class__.__name__}")
            raise
    
    def _prepare_headers(self, token_response: TokenResponse) -> Dict[str, str]:
        """
        Prepare HTTP headers based on token structure.
        
        Automatically adapts to vendor:
        - Keycloak/Auth0/Okta: Authorization header only
        - EntraID: Authorization + X-Act-Assertion headers
        """
        headers = {
            'Authorization': f"Bearer {token_response.access_token}"
        }
        
        if token_response.act_assertion:
            headers['X-Act-Assertion'] = token_response.act_assertion
            logger.debug("Added X-Act-Assertion header (EntraID)")
        
        return headers
    
    def __del__(self):
        """Cleanup HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()


__all__ = ['OutOfSessionAPICall']
