# AGBAC-Min Changelog

All notable changes to the AGBAC-Min project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<br>

## [1.0.1] - 2026-01-03

### Added

#### Core Functionality
- **UserSession dataclass** with `user_id` field for storing IAM user identifiers
  - Enables pseudonymous logging instead of PII
  - Supports privacy compliance (GDPR/CCPA)
  - Located in: `sender/hybrid_sender.py`

- **IAM Identifier Logging** throughout all adapters and modules
  - New `_prepare_act_for_logging()` method in BaseAdapter
  - Logs IAM user IDs instead of email addresses
  - Perfect correlation with IAM provider audit logs
  - Affected files: All 5 adapter files, HybridSender

- **Production-Grade Configuration Module** (`agbac_config.py`)
  - Custom `ConfigurationError` exception for precise error handling
  - Comprehensive input validation (empty strings, types, lengths)
  - URL validation with HTTPS enforcement
  - File validation (existence, permissions, security warnings)
  - Vendor-specific validation (scope formats, audience checks)
  - Structured logging with audit-friendly fields
  - 490 lines of robust configuration management

#### Security Enhancements
- HTTPS validation for all URLs (token endpoints, API endpoints)
- File permission validation with security warnings
- World-readable file detection for private keys
- Short secret length warnings
- Input sanitization and validation throughout

#### Documentation
- **IAM Identifier Guidance** added to all 5 guides
  - Step-by-step extraction from OIDC tokens
  - Vendor-specific identifier format tables
  - Correlation with IAM audit logs documentation
  - Privacy and GDPR compliance explanations

- **Logging Best Practices** sections in all guides
  - What to log (IAM identifiers) vs what NOT to log (PII)
  - Structured logging examples
  - Audit log correlation queries

- **Troubleshooting Sections** for IAM identifiers
  - Common mistakes and solutions
  - OIDC token extraction guidance
  - EntraID Object ID handling

### Changed

#### Breaking Changes
- **UserSession** now requires `user_id` parameter
  - Previously optional, now expected to contain IAM user identifier
  - Applications must extract user ID from OIDC `sub` claim
  - Migration: Update `UserSession` calls to include `user_id=oidc_token['sub']`

- **act.sub Field** now contains IAM user identifier (not email)
  - Keycloak: UUID format (e.g., `f1234567-89ab-cdef-0123-456789abcdef`)
  - Auth0: User ID with prefix (e.g., `auth0|63f1234567890abcdef12345`)
  - Okta: User ID starting with 00u (e.g., `00u123abc456xyz`)
  - EntraID: UPN in `sub` + Object ID in `oid` (dual identifiers)
  - Migration: Update application code to use `oidc_token['sub']` not `user.email`

#### Non-Breaking Changes
- **All adapter modules** updated with enhanced error handling
  - More descriptive error messages
  - Better exception wrapping
  - Improved logging context

- **Configuration loading** now uses environment variable pattern
  - Applications load config via `get_config()` function
  - No direct `os.environ` access in library code
  - Makes testing easier and deployment more flexible

- **Documentation terminology** improved
  - "PII-free logging" → "IAM identifier logging" (more accurate)
  - Consistent use of "IAM user identifier" throughout
  - Vendor-specific terminology where appropriate

### Fixed
- Package `__init__.py` files added to all directories
  - `adapters/__init__.py`
  - `sender/__init__.py`
  - `phase1/__init__.py`
  - `phase2/__init__.py`
  - Ensures proper Python package imports

### Security
- **Enhanced privacy protection**
  - IAM identifiers (pseudonymous) logged instead of email/name (PII)
  - GDPR/CCPA compliant logging practices
  - Correlation with IAM audit logs maintained

- **Validation improvements**
  - All URLs validated for HTTPS
  - File permissions checked before use
  - Input validation prevents common configuration errors

### Documentation
- **5 guides updated** with v1.0.1 features:
  - `KEYCLOAK_IAM_CONFIGURATION_GUIDE.md` (1,137 → 1,465 lines)
  - `AUTH0_IAM_CONFIGURATION_GUIDE.md` (1,393 → 1,492 lines)
  - `OKTA_IAM_CONFIGURATION_GUIDE.md` (1,342 → 1,458 lines)
  - `ENTRAID_IAM_CONFIGURATION_GUIDE.md` (1,323 → 1,499 lines)
  - `APPLICATION_AGENT_IMPLEMENTATION_GUIDE.md` (2,144 → 2,497 lines)

- **New sections in all guides:**
  - "Get User ID" / "Get Object ID" (IAM identifier extraction)
  - "Logging Best Practices" (pseudonymous logging)
  - "Troubleshooting" (IAM identifier issues)
  - Field explanation tables with IAM identifier emphasis

---

## [1.0.0] - 2025-12-XX (Baseline)

### Added

#### Initial Release
- Base adapter architecture (`BaseAdapter`)
- Four IAM vendor adapters:
  - `KeycloakAdapter` - Keycloak support
  - `Auth0Adapter` - Auth0 support
  - `OktaAdapter` - Okta support
  - `EntraIDAdapter` - EntraID (Azure AD) support with hybrid approach

- Human identity extraction (`HybridSender`)
- In-session agent flows (Phase 1)
  - `InSessionTokenRequest`
  - `InSessionAPICall`

- Out-of-session agent flows (Phase 2)
  - `OutOfSessionTokenRequest` with JWT verification
  - `OutOfSessionAPICall`

- Basic configuration loading (`agbac_config.py`)
- Environment variable support for all vendors

#### Documentation
- Initial IAM Configuration Guides (4 guides)
- Initial Application/Agent Implementation Guide
- Architecture documentation
- Flow diagrams and examples

<br>

## Migration Guide (v1.0.0 → v1.0.1)

### Code Changes Required

#### 1. Update UserSession Calls
```python
# OLD (v1.0)
user_session = UserSession(
    user_email=session['email'],
    user_name=session['name']
)

# NEW (v1.1) - Add user_id from OIDC token
id_token = session['id_token']
decoded = jwt.decode(id_token, options={"verify_signature": False})

user_session = UserSession(
    user_email=session['email'],
    user_name=session['name'],
    user_id=decoded['sub']  # IAM user identifier
)
```

#### 2. Update Logging Code
```python
# OLD (v1.0) - Logged PII
logger.info(f"User {act['email']} accessed resource")

# NEW (v1.1) - Log IAM identifier
logger.info(
    "Resource accessed",
    extra={
        "human_id": act['sub'],  # IAM user ID (pseudonymous)
        "action": "read",
        "resource": "/api/data"
    }
)
```

#### 3. Update act Claim Expectations
```python
# OLD (v1.0) - Email in act.sub
act = {
    'sub': 'alice@corp.example.com',  # Email
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}

# NEW (v1.1) - IAM user ID in act.sub
act = {
    'sub': 'f1234567-89ab-cdef-0123-456789abcdef',  # Keycloak user ID
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}
```

### No Changes Required

- IAM provider configurations (no changes needed)
- Token request flows (work the same)
- API call methods (work the same)
- Adapter interface (backward compatible)

### Recommended Actions

1. **Update logging** to use IAM identifiers for privacy compliance
2. **Store OIDC ID token** in session for user ID extraction
3. **Review audit log correlation** using new IAM identifiers
4. **Update documentation references** to use IAM identifier terminology

<br>

## Version History Summary

| Version | Date | Key Changes | Files Changed |
|---------|------|-------------|---------------|
| 1.0.1 | 2026-01-03 | IAM identifier logging, UserSession.user_id, production config | 11 Python + 5 Docs |
| 1.0.0 | 2025-12-XX | Initial release | 11 Python + 5 Docs |

<br>

## Deprecation Notices

### v1.0.1
- **None** - All v1.0 functionality remains available

### Future Versions
- No deprecations planned
- Backward compatibility commitment maintained

<br>

## Upgrade Path

```
v1.0.0 → v1.0.1: Update UserSession calls, update logging (recommended but not required)
```

<br>

## Contributors

- AGBAC-Min Project Team

<br>

## License

Apache License 2.0

<br>

