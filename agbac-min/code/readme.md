# AGBAC-Min Python Implementation

<br>

### Specify Vendor

Change this ONE variable to switch vendors

export AGBAC_VENDOR=keycloak  # or auth0, okta, entraid

### Keycloak Example

```bash
export AGBAC_VENDOR=keycloak
export KEYCLOAK_TOKEN_URL=https://keycloak.example.com/realms/agbac-min/protocol/openid-connect/token
export AGENT_CLIENT_ID=finance-agent
export AGENT_CLIENT_SECRET=***
```

### Auth0 Example

```bash
export AGBAC_VENDOR=auth0
export AUTH0_TOKEN_URL=https://tenant.auth0.com/oauth/token
export API_AUDIENCE=https://api.example.com/finance
export AGENT_CLIENT_ID=***
export AGENT_CLIENT_SECRET=***
```

### EntraID Example (Hybrid)

```bash
export AGBAC_VENDOR=entraid
export ENTRAID_TOKEN_URL=https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token
export API_SCOPE=https://api.example.com/.default
export APP_PRIVATE_KEY_PATH=/path/to/app-private-key.pem
export APP_ID=application-id
export API_AUDIENCE=https://api.example.com/finance
export AGENT_CLIENT_ID=***
export AGENT_CLIENT_SECRET=***
```


<br>


<br>

| File | Purpose |  Security Features |
|------|---------|-------------------|
| 1. base_adapter.py | Abstract base class |  PII sanitization, HTTPS enforcement, safe error handling |
| 2. keycloak_adapter.py | Keycloak implementation |  Client assertion (HS256), retry logic, safe errors |
| 3. auth0_adapter.py | Auth0 implementation |  Client assertion (HS256), rate limit handling |
| 4. okta_adapter.py | Okta implementation |  Client assertion (HS256), auth server parsing |
| 5. entraid_adapter.py | EntraID hybrid implementation |  Dual components (RS256 act assertion) |
| 6. hybrid_sender.py | Act extraction & preparation |  JWT signing (RS256), replay protection |
| 7. in_session_token_request.py | In-session tokens |  In-memory act passing, validation |
| 8. out_of_session_token_request.py | Out-of-session tokens |  JWT verification, replay protection |
| 9. in_session_api_call.py | In-session API calls |  HTTPS enforcement, vendor adaptation |
| 10. out_of_session_api_call.py | Out-of-session API calls |  HTTPS enforcement, vendor adaptation |


<br>

## Architecture

```
Application (Web App, FastAPI, etc.)
    ↓
HybridSender (extracts human identity from session)
    ↓
Adapter (Keycloak/Auth0/Okta/EntraID) ← Change ONE variable
    ↓
IAM Provider (token issuance)
    ↓
API Call (with dual-subject token)
    ↓
Resource Server (validates both subjects)
```

<br>

## Vendor Comparison

| Feature | Keycloak | Auth0 | Okta | EntraID |
|---------|----------|-------|------|---------|
| Token Structure | Single (sub + act) | Single (sub + act) | Single (sub + act) | Dual (agent + act) |
| API Headers | 1 header | 1 header | 1 header | 2 headers |
| Code Changes | None | None | None | Automatic |
| Complexity | Medium | Low | Medium | Medium |

