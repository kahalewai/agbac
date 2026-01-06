"""
AGBAC-Min Out-of-Session API Call

Make API calls with dual-subject tokens (out-of-session scenario).

Security:
- Enforces HTTPS for all API calls
- Handles token format differences automatically
- IAM identifier logging (no PII)
- Proper error handling

Logging:
- API URLs logged directly (not PII, needed for audit correlation)
- No hashing - enables direct correlation with API server logs
- Structured logging with extra={} throughout
- Tokens never logged

Vendor Support: All vendors with automatic header adaptation

Author: AGBAC-Min Project
License: Apache 2.0
Version: 1.0.1
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
    
    Identical to in-session API calls, but used in out-of-session context
    where the agent runs in a different process/server from the application.
    Handles vendor differences automatically.
    
    Logging:
        - API URLs logged directly for audit trail correlation
        - HTTP methods and status codes logged
        - Tokens never logged
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize API call handler.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.session = self._create_secure_session()
        
        logger.info(
            "Out-of-session API call handler initialized",
            extra={
                'timeout': timeout,
                'event': 'outofsession_api_handler_init'
            }
        )
    
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
    
    def _get_url_for_logging(self, url: str) -> str:
        """
        Extract loggable portion of URL.
        
        Returns the URL without query parameters for safe logging.
        API URLs are not PII - they are endpoint identifiers needed for audit correlation.
        
        Args:
            url: Full URL
            
        Returns:
            URL safe for logging (without query params)
        """
        if not url:
            return "unknown"
        # Remove query parameters if present (may contain sensitive data)
        return url.split('?')[0]
    
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
            logger.error(
                "API URL must use HTTPS",
                extra={
                    'url_scheme': api_url.split(':')[0] if api_url else 'empty',
                    'event': 'insecure_api_url'
                }
            )
            raise ValueError("API URL must use HTTPS")
        
        # Prepare headers
        headers = self._prepare_headers(token_response)
        
        if json_data:
            headers['Content-Type'] = 'application/json'
        
        # Log request start with URL (v1.1 - no hashing, URLs are not PII)
        logger.info(
            "API call starting",
            extra={
                'method': method,
                'api_url': self._get_url_for_logging(api_url),
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
            
            # Log response with URL for correlation
            logger.info(
                "API call completed",
                extra={
                    'status_code': response.status_code,
                    'method': method,
                    'api_url': self._get_url_for_logging(api_url),
                    'event': 'api_call_complete'
                }
            )
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error(
                "API call timed out",
                extra={
                    'timeout': self.timeout,
                    'api_url': self._get_url_for_logging(api_url),
                    'event': 'api_call_timeout'
                }
            )
            raise
        except requests.exceptions.SSLError:
            logger.error(
                "API call SSL/TLS error",
                extra={
                    'api_url': self._get_url_for_logging(api_url),
                    'event': 'api_call_ssl_error'
                }
            )
            raise
        except requests.exceptions.RequestException as e:
            logger.error(
                "API call failed",
                extra={
                    'error_type': e.__class__.__name__,
                    'api_url': self._get_url_for_logging(api_url),
                    'event': 'api_call_error'
                }
            )
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
            logger.debug(
                "Added X-Act-Assertion header (EntraID)",
                extra={'event': 'entraid_header_added'}
            )
        
        return headers
    
    def __del__(self):
        """Cleanup HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()


__all__ = ['OutOfSessionAPICall']
