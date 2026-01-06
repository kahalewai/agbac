"""
AGBAC-Min Configuration Module

Centralized configuration loading from environment variables for all IAM vendors.
This module provides a simple interface to load AGBAC-Min configuration from
environment variables, supporting Keycloak, Auth0, Okta, and EntraID.

Security Features:
- All secrets loaded from environment variables (never hardcoded)
- HTTPS validation for all URLs
- URL format validation
- File existence and permission validation
- Comprehensive input validation
- Structured error messages with examples

Author: AGBAC-Min Project
License: Apache 2.0
Version: 1.0.1
"""

import os
import logging
from typing import Dict, Optional
from urllib.parse import urlparse

# Configure module logger
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """
    Exception raised when configuration is invalid or incomplete.
    
    This specific exception type distinguishes configuration errors from other
    types of errors, enabling precise error handling in applications.
    
    Example:
        try:
            config = get_config()
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
    """
    pass


def get_config(vendor: Optional[str] = None) -> Dict:
    """
    Load AGBAC-Min configuration from environment variables.
    
    Reads environment variables, validates all inputs, and returns a configuration
    dictionary ready for adapter initialization. Supports vendor selection via
    parameter or AGBAC_VENDOR environment variable.
    
    Args:
        vendor: IAM vendor name (keycloak, auth0, okta, entraid).
                If None, reads from AGBAC_VENDOR environment variable (default: keycloak)
    
    Returns:
        Dictionary containing validated configuration for the selected vendor.
        
        For Keycloak:
            {'token_url': str, 'client_id': str, 'client_secret': str, 'audience': None}
        
        For Auth0/Okta:
            {'token_url': str, 'client_id': str, 'client_secret': str, 'audience': str}
        
        For EntraID:
            {'token_url': str, 'client_id': str, 'client_secret': str, 'scope': str,
             'app_private_key_path': str, 'app_id': str, 'act_audience': str}
        
    Environment Variables:
        Common (all vendors):
            AGBAC_VENDOR: Vendor name (keycloak, auth0, okta, entraid) - default: keycloak
            AGENT_CLIENT_ID: Agent's client/application ID
            AGENT_CLIENT_SECRET: Agent's client secret
        
        Keycloak specific:
            KEYCLOAK_TOKEN_URL: Token endpoint (HTTPS required)
        
        Auth0 specific:
            AUTH0_TOKEN_URL: Token endpoint (HTTPS required)
            API_AUDIENCE: API identifier
        
        Okta specific:
            OKTA_TOKEN_URL: Token endpoint (HTTPS required)
            API_AUDIENCE: API identifier
        
        EntraID specific:
            ENTRAID_TOKEN_URL: Token endpoint (HTTPS required)
            API_SCOPE: API scope (e.g., https://api.example.com/.default)
            APP_PRIVATE_KEY_PATH: Path to application private key (PEM format)
            APP_ID: Application identifier
            API_AUDIENCE: API audience for act assertions
    
    Raises:
        ConfigurationError: If required environment variables are missing, empty,
                          invalid format, or fail validation checks.
        
    Security:
        - Validates all URLs use HTTPS
        - Validates URL format (scheme and hostname required)
        - Validates file existence and readability for EntraID
        - Warns about suspicious configurations (localhost, short secrets, etc.)
        - Never logs secrets or sensitive data
    
    Example:
        # Set environment variables
        os.environ['AGBAC_VENDOR'] = 'keycloak'
        os.environ['AGENT_CLIENT_ID'] = 'finance-agent'
        os.environ['AGENT_CLIENT_SECRET'] = 'secret123'
        os.environ['KEYCLOAK_TOKEN_URL'] = 'https://keycloak.example.com/realms/prod/protocol/openid-connect/token'
        
        # Load configuration
        config = get_config()
        
        # Use with adapter
        from adapters.keycloak_adapter import KeycloakAdapter
        adapter = KeycloakAdapter(config)
    """
    try:
        # Get vendor from parameter or environment
        if vendor is None:
            vendor = os.getenv('AGBAC_VENDOR', 'keycloak').lower().strip()
        else:
            # Validate vendor parameter type
            if not isinstance(vendor, str):
                raise ConfigurationError(
                    f"Vendor parameter must be a string, got {type(vendor).__name__}"
                )
            vendor = vendor.lower().strip()
        
        # Validate vendor not empty
        if not vendor:
            raise ConfigurationError(
                "Vendor cannot be empty. "
                "Set AGBAC_VENDOR environment variable or pass vendor parameter. "
                "Valid values: keycloak, auth0, okta, entraid"
            )
        
        # Validate vendor is supported
        valid_vendors = ['keycloak', 'auth0', 'okta', 'entraid']
        if vendor not in valid_vendors:
            raise ConfigurationError(
                f"Invalid vendor: '{vendor}'. Must be one of: {', '.join(valid_vendors)}"
            )
        
        # Load common configuration (required for all vendors)
        client_id = os.getenv('AGENT_CLIENT_ID', '').strip()
        client_secret = os.getenv('AGENT_CLIENT_SECRET', '').strip()
        
        # Validate common configuration
        if not client_id:
            raise ConfigurationError(
                "AGENT_CLIENT_ID environment variable is required and cannot be empty. "
                "Example: export AGENT_CLIENT_ID=finance-agent"
            )
        
        if not client_secret:
            raise ConfigurationError(
                "AGENT_CLIENT_SECRET environment variable is required and cannot be empty. "
                "Example: export AGENT_CLIENT_SECRET=your-secret-here"
            )
        
        # Validate client_id format (basic sanity check)
        if len(client_id) < 3:
            raise ConfigurationError(
                f"AGENT_CLIENT_ID appears invalid (too short: {len(client_id)} characters). "
                "Client IDs should be at least 3 characters long."
            )
        
        # Warn about short secrets (security concern)
        if len(client_secret) < 8:
            logger.warning(
                "AGENT_CLIENT_SECRET is very short (%d characters). "
                "This may indicate a configuration error.",
                len(client_secret)
            )
        
        # Load vendor-specific configuration
        if vendor == 'keycloak':
            config = _get_keycloak_config(client_id, client_secret)
        elif vendor == 'auth0':
            config = _get_auth0_config(client_id, client_secret)
        elif vendor == 'okta':
            config = _get_okta_config(client_id, client_secret)
        elif vendor == 'entraid':
            config = _get_entraid_config(client_id, client_secret)
        else:
            # Defense in depth - should never reach here due to validation above
            raise ConfigurationError(f"Unsupported vendor: {vendor}")
        
        # Validate HTTPS (critical security requirement)
        _validate_https_url(config['token_url'], 'token_url')
        
        # Validate URL format
        _validate_url_format(config['token_url'], 'token_url')
        
        # Log successful configuration load (no secrets)
        logger.info(
            "Configuration loaded successfully",
            extra={
                'vendor': vendor,
                'client_id_length': len(client_id),
                'has_audience': 'audience' in config and config['audience'] is not None,
                'event': 'config_loaded'
            }
        )
        
        return config
        
    except ConfigurationError:
        # Re-raise ConfigurationError as-is
        raise
    except Exception as e:
        # Catch and wrap unexpected errors
        logger.error(
            "Unexpected error loading configuration",
            extra={
                'error_type': e.__class__.__name__,
                'event': 'config_error'
            }
        )
        raise ConfigurationError(
            f"Unexpected error loading configuration: {e.__class__.__name__}: {str(e)}"
        ) from e


def _validate_https_url(url: str, field_name: str) -> None:
    """
    Validate that URL uses HTTPS protocol.
    
    Args:
        url: URL string to validate
        field_name: Name of field being validated (for error messages)
        
    Raises:
        ConfigurationError: If URL is empty or doesn't use HTTPS
        
    Security:
        Enforces HTTPS to ensure all communications with IAM providers
        are encrypted in transit. HTTP is never acceptable for tokens.
        
    Example:
        _validate_https_url('https://keycloak.example.com/token', 'token_url')  # OK
        _validate_https_url('http://keycloak.example.com/token', 'token_url')   # Raises
    """
    if not url:
        raise ConfigurationError(f"{field_name} cannot be empty")
    
    if not url.startswith('https://'):
        # Extract scheme for better error message
        if '://' in url:
            scheme = url.split('://')[0]
            raise ConfigurationError(
                f"{field_name} must use HTTPS for security. "
                f"Got scheme: {scheme}. "
                f"Change to https://"
            )
        else:
            raise ConfigurationError(
                f"{field_name} must use HTTPS and include full URL with scheme. "
                f"Got: {url[:50]}... "
                f"Example: https://example.com/path"
            )


def _validate_url_format(url: str, field_name: str) -> None:
    """
    Validate URL has correct format with required components.
    
    Args:
        url: URL string to validate
        field_name: Name of field being validated (for error messages)
        
    Raises:
        ConfigurationError: If URL format is invalid or missing required components
        
    Warnings:
        Logs warnings for suspicious patterns like localhost or .local domains
        
    Example:
        _validate_url_format('https://api.example.com/path', 'token_url')  # OK
        _validate_url_format('https://localhost/path', 'token_url')        # OK but warns
        _validate_url_format('example.com', 'token_url')                   # Raises (no scheme)
    """
    try:
        parsed = urlparse(url)
        
        # Validate required components
        if not parsed.scheme:
            raise ConfigurationError(
                f"{field_name} missing URL scheme. "
                f"Got: {url[:50]}... "
                f"Example: https://example.com/path"
            )
        
        if not parsed.netloc:
            raise ConfigurationError(
                f"{field_name} missing hostname. "
                f"Got: {url[:50]}... "
                f"Example: https://example.com/path"
            )
        
        # Warn about suspicious patterns
        if parsed.netloc == 'localhost' or parsed.netloc.startswith('127.'):
            logger.warning(
                "%s uses localhost (%s). This should only be used in development.",
                field_name,
                parsed.netloc
            )
        
        if parsed.netloc.endswith('.local'):
            logger.warning(
                "%s uses .local domain (%s). Ensure this is resolvable in your environment.",
                field_name,
                parsed.netloc
            )
            
    except Exception as e:
        raise ConfigurationError(
            f"{field_name} has invalid URL format: {e.__class__.__name__}"
        ) from e


def _validate_file_exists(file_path: str, field_name: str) -> None:
    """
    Validate that file exists and is readable.
    
    Args:
        file_path: Path to file to validate
        field_name: Name of field being validated (for error messages)
        
    Raises:
        ConfigurationError: If file doesn't exist, isn't a file, or isn't readable
        
    Warnings:
        Logs warning if file has world-readable permissions (security risk)
        
    Security:
        - Verifies file exists before attempting to use it
        - Checks file is actually a file (not directory or special file)
        - Verifies read permissions
        - Warns if private key has insecure permissions
        
    Example:
        _validate_file_exists('/keys/app_private_key.pem', 'APP_PRIVATE_KEY_PATH')
    """
    if not file_path:
        raise ConfigurationError(f"{field_name} cannot be empty")
    
    if not os.path.exists(file_path):
        raise ConfigurationError(
            f"{field_name} file does not exist: {file_path}"
        )
    
    if not os.path.isfile(file_path):
        raise ConfigurationError(
            f"{field_name} path is not a file: {file_path}"
        )
    
    # Check if readable
    if not os.access(file_path, os.R_OK):
        raise ConfigurationError(
            f"{field_name} file is not readable: {file_path}. "
            f"Check file permissions."
        )
    
    # Warn about world-readable files (security risk for private keys)
    try:
        stat_info = os.stat(file_path)
        mode = stat_info.st_mode
        if mode & 0o004:  # World-readable bit set
            logger.warning(
                "%s file is world-readable: %s. "
                "This is a security risk for private keys. "
                "Recommended: chmod 600 %s",
                field_name,
                file_path,
                file_path
            )
    except OSError as e:
        logger.debug("Could not check file permissions: %s", e)


def _get_keycloak_config(client_id: str, client_secret: str) -> Dict:
    """
    Load Keycloak-specific configuration from environment.
    
    Args:
        client_id: Agent client ID (already validated)
        client_secret: Agent client secret (already validated)
        
    Returns:
        Dictionary with Keycloak configuration:
        {'token_url': str, 'client_id': str, 'client_secret': str, 'audience': None}
        
    Raises:
        ConfigurationError: If KEYCLOAK_TOKEN_URL is missing or empty
        
    Example:
        config = _get_keycloak_config('finance-agent', 'secret123')
        # Returns: {
        #   'token_url': 'https://keycloak.example.com/realms/prod/protocol/openid-connect/token',
        #   'client_id': 'finance-agent',
        #   'client_secret': 'secret123',
        #   'audience': None
        # }
    """
    token_url = os.getenv('KEYCLOAK_TOKEN_URL', '').strip()
    
    if not token_url:
        raise ConfigurationError(
            "KEYCLOAK_TOKEN_URL environment variable is required for Keycloak. "
            "Example: export KEYCLOAK_TOKEN_URL=https://keycloak.example.com/realms/prod/protocol/openid-connect/token"
        )
    
    return {
        'token_url': token_url,
        'client_id': client_id,
        'client_secret': client_secret,
        'audience': None  # Keycloak auto-derives audience from token_url
    }


def _get_auth0_config(client_id: str, client_secret: str) -> Dict:
    """
    Load Auth0-specific configuration from environment.
    
    Args:
        client_id: Agent client ID (already validated)
        client_secret: Agent client secret (already validated)
        
    Returns:
        Dictionary with Auth0 configuration:
        {'token_url': str, 'client_id': str, 'client_secret': str, 'audience': str}
        
    Raises:
        ConfigurationError: If AUTH0_TOKEN_URL or API_AUDIENCE is missing/empty/invalid
        
    Example:
        config = _get_auth0_config('finance-agent', 'secret123')
        # Returns: {
        #   'token_url': 'https://tenant.auth0.com/oauth/token',
        #   'client_id': 'finance-agent',
        #   'client_secret': 'secret123',
        #   'audience': 'https://api.example.com'
        # }
    """
    token_url = os.getenv('AUTH0_TOKEN_URL', '').strip()
    audience = os.getenv('API_AUDIENCE', '').strip()
    
    if not token_url:
        raise ConfigurationError(
            "AUTH0_TOKEN_URL environment variable is required for Auth0. "
            "Example: export AUTH0_TOKEN_URL=https://tenant.auth0.com/oauth/token"
        )
    
    if not audience:
        raise ConfigurationError(
            "API_AUDIENCE environment variable is required for Auth0. "
            "Example: export API_AUDIENCE=https://api.example.com"
        )
    
    # Validate audience format (basic sanity check)
    if len(audience) < 3:
        raise ConfigurationError(
            f"API_AUDIENCE appears invalid (too short: {len(audience)} characters)"
        )
    
    return {
        'token_url': token_url,
        'client_id': client_id,
        'client_secret': client_secret,
        'audience': audience
    }


def _get_okta_config(client_id: str, client_secret: str) -> Dict:
    """
    Load Okta-specific configuration from environment.
    
    Args:
        client_id: Agent client ID (already validated)
        client_secret: Agent client secret (already validated)
        
    Returns:
        Dictionary with Okta configuration:
        {'token_url': str, 'client_id': str, 'client_secret': str, 'audience': str}
        
    Raises:
        ConfigurationError: If OKTA_TOKEN_URL or API_AUDIENCE is missing/empty/invalid
        
    Example:
        config = _get_okta_config('finance-agent', 'secret123')
        # Returns: {
        #   'token_url': 'https://dev-123.okta.com/oauth2/aus123/v1/token',
        #   'client_id': 'finance-agent',
        #   'client_secret': 'secret123',
        #   'audience': 'https://api.example.com'
        # }
    """
    token_url = os.getenv('OKTA_TOKEN_URL', '').strip()
    audience = os.getenv('API_AUDIENCE', '').strip()
    
    if not token_url:
        raise ConfigurationError(
            "OKTA_TOKEN_URL environment variable is required for Okta. "
            "Example: export OKTA_TOKEN_URL=https://dev-123.okta.com/oauth2/aus123/v1/token"
        )
    
    if not audience:
        raise ConfigurationError(
            "API_AUDIENCE environment variable is required for Okta. "
            "Example: export API_AUDIENCE=https://api.example.com"
        )
    
    # Validate audience format (basic sanity check)
    if len(audience) < 3:
        raise ConfigurationError(
            f"API_AUDIENCE appears invalid (too short: {len(audience)} characters)"
        )
    
    return {
        'token_url': token_url,
        'client_id': client_id,
        'client_secret': client_secret,
        'audience': audience
    }


def _get_entraid_config(client_id: str, client_secret: str) -> Dict:
    """
    Load EntraID-specific configuration from environment.
    
    EntraID requires additional configuration for the hybrid approach where
    the application creates act assertions separately from the agent token.
    
    Args:
        client_id: Agent client ID (already validated)
        client_secret: Agent client secret (already validated)
        
    Returns:
        Dictionary with EntraID configuration:
        {'token_url': str, 'client_id': str, 'client_secret': str, 'scope': str,
         'app_private_key_path': str, 'app_id': str, 'act_audience': str}
        
    Raises:
        ConfigurationError: If any required EntraID variable is missing/empty/invalid
        
    Warnings:
        Logs warning if API_SCOPE doesn't end with /.default (typical for EntraID)
        
    Example:
        config = _get_entraid_config('finance-agent', 'secret123')
        # Returns: {
        #   'token_url': 'https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token',
        #   'client_id': 'finance-agent',
        #   'client_secret': 'secret123',
        #   'scope': 'https://api.example.com/.default',
        #   'app_private_key_path': '/keys/app_private_key.pem',
        #   'app_id': 'https://app.example.com',
        #   'act_audience': 'https://api.example.com'
        # }
    """
    token_url = os.getenv('ENTRAID_TOKEN_URL', '').strip()
    scope = os.getenv('API_SCOPE', '').strip()
    app_private_key_path = os.getenv('APP_PRIVATE_KEY_PATH', '').strip()
    app_id = os.getenv('APP_ID', '').strip()
    act_audience = os.getenv('API_AUDIENCE', '').strip()
    
    # Validate all required fields
    if not token_url:
        raise ConfigurationError(
            "ENTRAID_TOKEN_URL environment variable is required for EntraID. "
            "Example: export ENTRAID_TOKEN_URL=https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token"
        )
    
    if not scope:
        raise ConfigurationError(
            "API_SCOPE environment variable is required for EntraID. "
            "Example: export API_SCOPE=https://api.example.com/.default"
        )
    
    if not app_private_key_path:
        raise ConfigurationError(
            "APP_PRIVATE_KEY_PATH environment variable is required for EntraID. "
            "Example: export APP_PRIVATE_KEY_PATH=/keys/app_private_key.pem"
        )
    
    if not app_id:
        raise ConfigurationError(
            "APP_ID environment variable is required for EntraID. "
            "Example: export APP_ID=https://app.example.com"
        )
    
    if not act_audience:
        raise ConfigurationError(
            "API_AUDIENCE environment variable is required for EntraID. "
            "Example: export API_AUDIENCE=https://api.example.com"
        )
    
    # Validate scope format (EntraID typically uses /.default suffix)
    if not scope.endswith('/.default'):
        logger.warning(
            "API_SCOPE for EntraID typically ends with '/.default'. "
            "Got: %s. Ensure this is correct for your configuration.",
            scope
        )
    
    # Validate file exists and is readable
    _validate_file_exists(app_private_key_path, 'APP_PRIVATE_KEY_PATH')
    
    # Validate app_id format (basic sanity check)
    if len(app_id) < 3:
        raise ConfigurationError(
            f"APP_ID appears invalid (too short: {len(app_id)} characters)"
        )
    
    # Validate act_audience format (basic sanity check)
    if len(act_audience) < 3:
        raise ConfigurationError(
            f"API_AUDIENCE appears invalid (too short: {len(act_audience)} characters)"
        )
    
    return {
        'token_url': token_url,
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope,
        'app_private_key_path': app_private_key_path,
        'app_id': app_id,
        'act_audience': act_audience
    }


def get_vendor() -> str:
    """
    Get configured vendor name from environment.
    
    Returns:
        Lowercase vendor name from AGBAC_VENDOR environment variable.
        Returns 'keycloak' if AGBAC_VENDOR is not set.
        
    Note:
        This function does not validate the vendor. Use get_config() for
        full validation and configuration loading.
        
    Example:
        vendor = get_vendor()  # Returns 'keycloak', 'auth0', 'okta', or 'entraid'
    """
    return os.getenv('AGBAC_VENDOR', 'keycloak').lower().strip()


__all__ = ['get_config', 'get_vendor', 'ConfigurationError']
