<div align="center">

# AGBAC-Min Keycloak IAM Configuration Guide

**Implementing dual-subject authorization for humans and agents**

</div>

<br>

## **Overview**

This guide provides step-by-step instructions for configuring Keycloak to support AGBAC-Min dual-subject authorization. After completing this guide, your Keycloak instance will:

✅ Accept token requests from AI agents including human identity (`act`)  
✅ Issue tokens containing both agent identity (`sub`) and human identity (`act`)  
✅ Enforce that both subjects are pre-approved before issuing tokens  
✅ Enable resource servers to validate both subjects for access control  

**Estimated Time:** 45-60 minutes  
**Keycloak Version:** 23.0 or higher recommended  
**Prerequisites:** Keycloak admin access, basic understanding of OAuth 2.0

<br>

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step 1: Create Realm](#step-1-create-realm)
4. [Step 2: Create Roles for Pre-Approval](#step-2-create-roles-for-pre-approval)
5. [Step 3: Create Agent Client](#step-3-create-agent-client)
6. [Step 4: Configure Protocol Mapper for Act Claim](#step-4-configure-protocol-mapper-for-act-claim)
7. [Step 5: Assign Roles (Pre-Approval)](#step-5-assign-roles-pre-approval)
8. [Step 6: Create Test User](#step-6-create-test-user)
9. [Step 7: Test Configuration](#step-7-test-configuration)
10. [Step 8: Configure Resource Server Validation](#step-8-configure-resource-server-validation)
11. [Troubleshooting](#troubleshooting)
12. [Reference: Configuration JSON](#reference-configuration-json)

<br>

## **Prerequisites**

Before starting, ensure you have:

- [ ] Keycloak 23.0+ installed and running
- [ ] Admin access to Keycloak Admin Console
- [ ] TLS/HTTPS enabled on Keycloak (required for production)
- [ ] Basic familiarity with OAuth 2.0 concepts
- [ ] `curl` or Postman for testing token requests

**Access Keycloak Admin Console:**
```
https://your-keycloak-domain/admin
```

**Default admin credentials** (change these in production):
- Username: `admin`
- Password: Set during Keycloak installation

<br>

## **Architecture Overview**

### How AGBAC-Min Works with Keycloak

```
┌─────────────┐
│   Human     │ Authenticates to application
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Application       │ Extracts human identity (act)
│   (Hybrid Sender)   │ Provides to agent
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   AI Agent          │ Creates client assertion JWT
│                     │ Includes: sub (agent) + act (human)
└──────┬──────────────┘
       │ Token Request
       │ (client_credentials + client_assertion)
       ▼
┌─────────────────────┐
│   Keycloak          │ 1. Validates client assertion
│                     │ 2. Extracts act from assertion
│                     │ 3. Validates both subjects pre-approved
│                     │ 4. Issues token with sub + act
└──────┬──────────────┘
       │
       ▼ Access Token (contains sub + act)
┌─────────────────────┐
│  Resource Server    │ 1. Validates token signature
│                     │ 2. Validates agent (sub) authorized
│                     │ 3. Validates human (act) authorized
│                     │ 4. Grants access if BOTH pass
└─────────────────────┘
```

### Key Concepts

**Agent Identity (`sub`)**: The AI agent's service account (e.g., `service-account-finance-agent`)  
**Human Identity (`act`)**: The human user's IAM identifier (e.g., Keycloak user ID: `f1234567-89ab-cdef-0123-456789abcdef`)  
**Client Assertion**: Signed JWT from agent containing the `act` claim  
**Protocol Mapper**: Keycloak configuration to extract `act` from client assertion into token  
**Pre-Approval**: Role assignments required for both agent and human before token issuance

**Important - IAM Identifier in act.sub:**
The `act.sub` field should contain the user's Keycloak user ID (UUID), not their email. This provides:
- **Privacy**: Pseudonymous identifier instead of PII (email)
- **Stability**: User ID doesn't change if email changes
- **Correlation**: Perfect correlation with Keycloak's internal user ID for audit logs

<br>

## **Step 1: Create Realm**

### 1.1 Access Admin Console

1. Navigate to Keycloak Admin Console
2. Log in with admin credentials

### 1.2 Create New Realm

1. Click dropdown in top-left (says "Master" by default)
2. Click **"Create Realm"**
3. Configure realm:

| Field | Value | Notes |
|-------|-------|-------|
| Realm name | `agbac-min` | Use lowercase, no spaces |
| Enabled | ✅ ON | Realm must be enabled |

4. Click **"Create"**

### 1.3 Configure Realm Settings

Navigate to: **Realm Settings** → **General**

| Setting | Value | Notes |
|---------|-------|-------|
| User-managed access | ✅ ON | Allows fine-grained permissions |
| Endpoints | Note the OpenID Endpoint Configuration URL | You'll need this later |

**OpenID Configuration URL** (bookmark this):
```
https://your-keycloak-domain/realms/agbac-min/.well-known/openid-configuration
```

**Token Endpoint** (you'll use this for token requests):
```
https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/token
```

<br>

## **Step 2: Create Roles for Pre-Approval**

Pre-approval roles ensure that both the agent AND the human are explicitly authorized before Keycloak issues a token.

### 2.1 Create Agent Role

Navigate to: **Realm Roles** → **Create Role**

| Field | Value |
|-------|-------|
| Role name | `FinanceAgent` |
| Description | `Pre-approved agent for finance operations` |

Click **"Save"**

### 2.2 Create Human Role

Navigate to: **Realm Roles** → **Create Role**

| Field | Value |
|-------|-------|
| Role name | `FinanceUser` |
| Description | `Pre-approved human for finance operations` |

Click **"Save"**

**Why Two Roles?**
- `FinanceAgent` = Agent pre-approved to ACT
- `FinanceUser` = Human pre-approved to AUTHORIZE the agent to act on their behalf
- Both must be present for token issuance (enforced by resource server)

<br>

## **Step 3: Create Agent Client**

The agent client represents the AI agent service account in Keycloak.

### 3.1 Create Client

Navigate to: **Clients** → **Create Client**

**General Settings:**

| Field | Value | Notes |
|-------|-------|-------|
| Client type | `OpenID Connect` | Standard OAuth/OIDC |
| Client ID | `finance-agent` | Unique identifier for the agent |

Click **"Next"**

### 3.2 Capability Config

| Setting | Value | Notes |
|---------|-------|-------|
| Client authentication | ✅ ON | Required for confidential clients |
| Authorization | ❌ OFF | Not needed for AGBAC |
| Authentication flow | |
| - Standard flow | ❌ OFF | Agent uses client_credentials |
| - Direct access grants | ❌ OFF | Agent uses client_credentials |
| - Service accounts roles | ✅ ON | **CRITICAL - Required for client_credentials** |

Click **"Next"**

### 3.3 Login Settings

Leave all fields empty (not used for service accounts)

Click **"Save"**

### 3.4 Configure Client Details

After creation, configure these settings:

Navigate to: **Clients** → **finance-agent** → **Settings**

**Access settings:**

| Field | Value | Notes |
|-------|-------|-------|
| Root URL | (empty) | Not needed for service accounts |
| Home URL | (empty) | Not needed |
| Valid redirect URIs | (empty) | Not needed for client_credentials |
| Valid post logout redirect URIs | (empty) | Not needed |
| Web origins | (empty) | Not needed |

**Capability config:**

| Field | Value | Notes |
|-------|-------|-------|
| Client authentication | ✅ ON | Must be enabled |
| Service accounts roles | ✅ ON | **Must be enabled** |

**Advanced:**

| Field | Value | Notes |
|-------|-------|-------|
| Access Token Lifespan | `300` seconds (5 min) | Security: Short-lived tokens |

Click **"Save"**

### 3.5 Get Client Secret

Navigate to: **Clients** → **finance-agent** → **Credentials**

| Field | Value |
|-------|-------|
| Client Authenticator | `Client Id and Secret` |

**Copy the Client Secret** - you'll need this for agent configuration and testing.

**Security Note:** Store this securely (use AWS Secrets Manager, Azure Key Vault, etc. in production)

<br>

## **Step 4: Configure Protocol Mapper for Act Claim**

This is the **most critical configuration** - it extracts the `act` claim from the client assertion and includes it in the access token.

### 4.1 Create Protocol Mapper

Navigate to: **Clients** → **finance-agent** → **Client scopes** → **finance-agent-dedicated** → **Add mapper** → **By configuration**

Select: **"User Attribute"**

**IMPORTANT:** Despite the name "User Attribute", this mapper works for extracting claims from client assertions. This is the correct mapper type to use.

### 4.2 Configure Mapper

| Field | Value | Notes |
|-------|-------|-------|
| Name | `act-claim-mapper` | Descriptive name |
| User Attribute | `act` | **EXACT** - This extracts `act` from client assertion |
| Token Claim Name | `act` | Name of claim in access token |
| Claim JSON Type | `JSON` | **CRITICAL** - Preserves act structure |
| Add to ID token | ✅ ON | Include in ID token |
| Add to access token | ✅ ON | **CRITICAL** - Must be enabled |
| Add to userinfo | ❌ OFF | Not needed |
| Multivalued | ❌ OFF | Act is a single object |
| Aggregate attribute values | ❌ OFF | Not needed |

Click **"Save"**

### 4.3 Verify Mapper Configuration

Navigate back to: **Clients** → **finance-agent** → **Client scopes** → **finance-agent-dedicated** → **Mappers**

You should see **"act-claim-mapper"** in the list.

**How It Works:**
1. Agent sends client assertion JWT with `act` claim
2. Keycloak receives token request
3. Protocol mapper extracts `act` from client assertion
4. Keycloak includes `act` in issued access token
5. Resource server receives token with both `sub` (agent) and `act` (human)

<br>

## **Step 5: Assign Roles (Pre-Approval)**

Both the agent service account and the human user must have their respective roles assigned.

### 5.1 Assign Role to Agent Service Account

Navigate to: **Users** → Search for `service-account-finance-agent`

**Why this name?** Keycloak automatically creates a service account user with the prefix `service-account-` when you enable "Service accounts roles" for a client.

Click on **service-account-finance-agent**

Navigate to: **Role mapping** → **Assign role**

| Field | Action |
|-------|--------|
| Filter by realm roles | Select filter |
| Search | (leave empty to see all) |
| Select | ✅ `FinanceAgent` |

Click **"Assign"**

**Verify:**
The "Assigned roles" section should now show:
- `FinanceAgent` ✅
- `default-roles-agbac-min`

### 5.2 Assign Role to Human User

This will be done in Step 6 when we create the test user.

<br>

## **Step 6: Create Test User**

Create a test user to represent a human who will be included in the `act` claim.

### 6.1 Create User

Navigate to: **Users** → **Add user**

| Field | Value | Notes |
|-------|-------|-------|
| Username | `alice` | Unique username |
| Email | `alice@corp.example.com` | User's email |
| Email verified | ✅ ON | Skip email verification |
| First name | `Alice` | User's first name |
| Last name | `Smith` | User's last name |
| Enabled | ✅ ON | User account active |

Click **"Create"**

### 6.2 Get User ID

After creating the user, you'll be on the user details page.

**Copy the User ID** from the URL or from the user details:
```
URL: https://keycloak/admin/master/console/#/agbac-min/users/f1234567-89ab-cdef-0123-456789abcdef
                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                                 This is the User ID (UUID)
```

**This User ID will be used in the `act.sub` field** when the application creates the act claim.

**Why User ID instead of email?**
- **Privacy**: User ID is pseudonymous (not PII like email)
- **Stability**: Doesn't change if user's email changes
- **Correlation**: Matches Keycloak's internal user ID for perfect audit log correlation

### 6.3 Set Password (Optional - for testing login flows)

Navigate to: **Users** → **alice** → **Credentials** → **Set password**

| Field | Value |
|-------|-------|
| Password | `test123` |
| Temporary | ❌ OFF |

Click **"Set password"** → **Confirm**

### 6.4 Assign Role to User

Navigate to: **Users** → **alice** → **Role mapping** → **Assign role**

| Field | Action |
|-------|--------|
| Filter by realm roles | Select filter |
| Select | ✅ `FinanceUser` |

Click **"Assign"**

**Verify:**
The "Assigned roles" section should show:
- `FinanceUser` ✅
- `default-roles-agbac-min`

<br>

## **Step 7: Test Configuration**

Now we'll test the complete flow by requesting a dual-subject token.

### 7.1 Gather Required Information

You'll need:

**Keycloak Configuration:**
- Token URL: `https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/token`
- Realm: `agbac-min`

**Agent Client:**
- Client ID: `finance-agent`  
- Client Secret: (from Step 3.5)

**Test User:**
- User ID: `f1234567-89ab-cdef-0123-456789abcdef` (from Step 6.2)
- Email: `alice@corp.example.com`
- Name: `Alice Smith`

### 7.2 Create Client Assertion JWT

The agent creates this JWT to prove its identity and include the human's identity in the `act` claim.

**Client Assertion Payload:**
```json
{
  "iss": "finance-agent",
  "sub": "finance-agent",
  "aud": "https://your-keycloak-domain/realms/agbac-min",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "unique-nonce-abc123",
  "act": {
    "sub": "f1234567-89ab-cdef-0123-456789abcdef",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

**Important Field Explanations:**

| Field | Value | Notes |
|-------|-------|-------|
| `iss` | `finance-agent` | Issuer = the agent client ID |
| `sub` | `finance-agent` | Subject = the agent client ID |
| `aud` | Keycloak realm URL | Must match exactly |
| `exp` | Current time + 300 | Expiration (5 minutes from now) |
| `iat` | Current time | Issued at timestamp |
| `jti` | Unique nonce | Prevents replay attacks |
| `act.sub` | **User ID (UUID)** | **Keycloak user ID from Step 6.2** |
| `act.email` | User's email | For human-readable logging |
| `act.name` | User's name | For human-readable logging |

**Critical: act.sub must be the Keycloak User ID**

The `act.sub` field should contain the user's Keycloak user ID (UUID like `f1234567-89ab-cdef-0123-456789abcdef`), not their email address. This provides:
- Better privacy (pseudonymous identifier)
- Stability (doesn't change if email changes)
- Perfect correlation with Keycloak audit logs

**Sign this JWT** with the client secret using HS256 algorithm.

**Using Python:**
```python
import jwt
import time

# Replace these with your actual values
CLIENT_ID = "finance-agent"
CLIENT_SECRET = "your-client-secret-here"
KEYCLOAK_REALM_URL = "https://your-keycloak-domain/realms/agbac-min"
USER_ID = "f1234567-89ab-cdef-0123-456789abcdef"  # From Step 6.2

payload = {
    "iss": CLIENT_ID,
    "sub": CLIENT_ID,
    "aud": KEYCLOAK_REALM_URL,
    "exp": int(time.time()) + 300,
    "iat": int(time.time()),
    "jti": f"test-{int(time.time())}",
    "act": {
        "sub": USER_ID,  # Keycloak user ID (UUID)
        "email": "alice@corp.example.com",
        "name": "Alice Smith"
    }
}

client_assertion = jwt.encode(payload, CLIENT_SECRET, algorithm="HS256")
print("Client Assertion JWT:")
print(client_assertion)
```

**Using https://jwt.io:**
1. Go to https://jwt.io
2. Paste the payload above (with your actual values)
3. In "Verify Signature" section, paste your client secret
4. Select algorithm: HS256
5. Copy the encoded JWT from the "Encoded" section

### 7.3 Request Token

**Using curl:**
```bash
# Replace these values
KEYCLOAK_URL="https://your-keycloak-domain"
CLIENT_ID="finance-agent"
CLIENT_ASSERTION="eyJhbGc..." # Your signed JWT from step 7.2

curl -X POST "${KEYCLOAK_URL}/realms/agbac-min/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=${CLIENT_ID}" \
  -d "scope=openid" \
  -d "client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer" \
  -d "client_assertion=${CLIENT_ASSERTION}"
```

**Using Python:**
```python
import requests

# Configuration
KEYCLOAK_URL = "https://your-keycloak-domain"
CLIENT_ID = "finance-agent"
CLIENT_ASSERTION = "eyJhbGc..."  # From step 7.2

# Request token
response = requests.post(
    f"{KEYCLOAK_URL}/realms/agbac-min/protocol/openid-connect/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "scope": "openid",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": CLIENT_ASSERTION
    }
)

if response.status_code == 200:
    token_data = response.json()
    print("✅ Token obtained successfully!")
    print(f"Access Token: {token_data['access_token'][:50]}...")
    print(f"Expires in: {token_data['expires_in']} seconds")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 0,
  "token_type": "Bearer",
  "not-before-policy": 0,
  "scope": "openid email profile"
}
```

### 7.4 Decode and Verify Token

Copy the `access_token` value and decode it at https://jwt.io

**Expected Token Structure:**
```json
{
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "iss": "https://your-keycloak-domain/realms/agbac-min",
  "sub": "service-account-finance-agent",
  "typ": "Bearer",
  "azp": "finance-agent",
  "act": {
    "sub": "f1234567-89ab-cdef-0123-456789abcdef",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  },
  "scope": "openid email profile",
  "realm_access": {
    "roles": [
      "FinanceAgent",
      "default-roles-agbac-min"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "view-profile"
      ]
    }
  },
  "clientId": "finance-agent",
  "email_verified": false,
  "preferred_username": "service-account-finance-agent"
}
```

### 7.5 Verify Key Fields

✅ **Check these fields in the decoded token:**

| Field | Expected Value | Status |
|-------|---------------|--------|
| `sub` | `service-account-finance-agent` | Agent identity ✅ |
| `act.sub` | `f1234567-89ab-cdef-0123-456789abcdef` | **User ID (UUID)** ✅ |
| `act.email` | `alice@corp.example.com` | User email ✅ |
| `act.name` | `Alice Smith` | User name ✅ |
| `realm_access.roles` | Contains `FinanceAgent` | Agent pre-approved ✅ |
| `azp` | `finance-agent` | Authorized party ✅ |

**Critical Verification:**
- The `act` claim is present ✅
- The `act.sub` contains the Keycloak user ID (UUID), not email ✅
- The `sub` is the agent's service account ✅
- The `FinanceAgent` role is in `realm_access.roles` ✅

**If any of these are missing**, review Steps 4-6.

<br>

## **Step 8: Configure Resource Server Validation**

Your resource server (API) must validate BOTH the agent and human identities.

### 8.1 Validation Logic

**Token Validation Flow:**

```python
import jwt
import requests
from functools import lru_cache

@lru_cache()
def get_keycloak_public_key(keycloak_url: str, realm: str) -> str:
    """Fetch Keycloak's public key for token validation."""
    url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
    response = requests.get(url)
    jwks = response.json()
    # Extract public key from JWKS (simplified - use python-jose in production)
    return jwks['keys'][0]

def validate_dual_subject_token(token: str, keycloak_url: str, realm: str) -> dict:
    """
    Validate dual-subject token and return decoded claims.
    
    Validates:
    1. Token signature (using Keycloak's public key)
    2. Token not expired
    3. Agent identity (sub) is authorized
    4. Human identity (act.sub) is authorized
    
    Returns decoded token if valid, raises exception otherwise.
    """
    # Get public key
    public_key = get_keycloak_public_key(keycloak_url, realm)
    
    # Decode and validate token
    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="account",  # Or your API audience
            options={"verify_exp": True}
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")
    
    # Validate agent identity (sub)
    agent_sub = decoded.get('sub')
    if not agent_sub:
        raise ValueError("Missing agent identity (sub)")
    
    if not agent_sub.startswith('service-account-'):
        raise ValueError(f"Invalid agent identity: {agent_sub}")
    
    # Validate agent has required role
    agent_roles = decoded.get('realm_access', {}).get('roles', [])
    if 'FinanceAgent' not in agent_roles:
        raise ValueError("Agent not authorized (missing FinanceAgent role)")
    
    # Validate human identity (act)
    act = decoded.get('act')
    if not act:
        raise ValueError("Missing human identity (act)")
    
    human_id = act.get('sub')
    if not human_id:
        raise ValueError("Missing human identifier (act.sub)")
    
    # Validate human has required role (check with Keycloak)
    # This requires additional API call to Keycloak to check user's roles
    # For production, implement caching to avoid repeated API calls
    if not check_user_has_role(keycloak_url, realm, human_id, 'FinanceUser'):
        raise ValueError("Human not authorized (missing FinanceUser role)")
    
    return decoded

def check_user_has_role(keycloak_url: str, realm: str, user_id: str, role_name: str) -> bool:
    """
    Check if user has specific role in Keycloak.
    
    Note: Requires Keycloak admin credentials or service account with user query permissions.
    In production, implement caching to reduce API calls.
    """
    # This is a simplified example - implement proper admin token management
    admin_token = get_admin_token(keycloak_url, realm)
    
    url = f"{keycloak_url}/admin/realms/{realm}/users/{user_id}/role-mappings/realm"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if response.status_code != 200:
        return False
    
    roles = response.json()
    return any(role['name'] == role_name for role in roles)

# Example usage in API endpoint
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency for token validation."""
    token = credentials.credentials
    
    try:
        decoded = validate_dual_subject_token(
            token,
            keycloak_url="https://your-keycloak-domain",
            realm="agbac-min"
        )
        return decoded
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

# Use in endpoint
@app.get("/api/finance/reports")
def get_finance_reports(token_claims: dict = Depends(verify_token)):
    """
    Protected endpoint that validates dual-subject authorization.
    """
    agent_id = token_claims['sub']
    human_id = token_claims['act']['sub']
    human_email = token_claims['act'].get('email')
    human_name = token_claims['act'].get('name')
    
    # Log access (using IAM identifier, not PII)
    logger.info(
        "Finance report access",
        extra={
            "agent_id": agent_id,
            "human_id": human_id,  # Keycloak user ID (pseudonymous)
            "action": "view_reports"
        }
    )
    
    # Business logic here
    return {"reports": [...]}
```

### 8.2 Logging Best Practices

**✅ DO: Log IAM identifiers**
```python
logger.info(
    "API access",
    extra={
        "agent_id": "service-account-finance-agent",
        "human_id": "f1234567-89ab-cdef-0123-456789abcdef",  # Keycloak user ID
        "action": "read",
        "resource": "/api/finance/reports"
    }
)
```

**❌ DON'T: Log PII (email, name)**
```python
# BAD - This logs PII
logger.info(f"Access by {human_email}")  # ❌ Email is PII
logger.info(f"User {human_name}")        # ❌ Name is PII
```

**Why log user ID instead of email?**
- **Privacy**: User ID is pseudonymous (not PII)
- **GDPR/CCPA compliance**: Reduces PII in logs
- **Correlation**: Can correlate with Keycloak audit logs using user ID
- **Stability**: Doesn't change if user's email changes

### 8.3 Authorization Policy Example

```python
def check_authorization(token_claims: dict, action: str, resource: str) -> bool:
    """
    Check if both agent and human are authorized for the action.
    
    Args:
        token_claims: Decoded JWT token claims
        action: Action being attempted (e.g., 'read', 'write')
        resource: Resource being accessed (e.g., '/finance/reports')
    
    Returns:
        True if authorized, raises HTTPException otherwise
    """
    agent_id = token_claims['sub']
    human_id = token_claims['act']['sub']
    
    # Check agent authorization
    agent_roles = token_claims.get('realm_access', {}).get('roles', [])
    if 'FinanceAgent' not in agent_roles:
        raise HTTPException(403, "Agent not authorized")
    
    # Check human authorization (from Keycloak or your policy store)
    if not is_human_authorized(human_id, action, resource):
        raise HTTPException(403, "Human not authorized")
    
    # Check combined policy (optional - additional restrictions)
    if not is_combination_allowed(agent_id, human_id, action, resource):
        raise HTTPException(403, "Agent-human combination not authorized")
    
    return True
```

<br>

## **Troubleshooting**

### Problem: Token doesn't contain `act` claim

**Symptoms:**
- Decoded token has `sub` but no `act`
- Client assertion is correct

**Solutions:**
1. **Verify Protocol Mapper:**
   - Navigate to: Clients → finance-agent → Client scopes → finance-agent-dedicated → Mappers
   - Ensure "act-claim-mapper" exists
   - Check that "Add to access token" is ✅ ON
   - Check that "Claim JSON Type" is `JSON` (not String)

2. **Verify Client Assertion:**
   - Decode your client assertion at https://jwt.io
   - Ensure it contains the `act` claim as a JSON object
   - Verify signature is valid

3. **Check Keycloak Logs:**
   ```bash
   # If using Docker
   docker logs keycloak-container-name
   
   # Look for errors related to protocol mappers or client assertions
   ```

### Problem: "Invalid client credentials" error

**Symptoms:**
```json
{
  "error": "invalid_client",
  "error_description": "Invalid client credentials"
}
```

**Solutions:**
1. **Verify Client Secret:**
   - Clients → finance-agent → Credentials
   - Regenerate if needed
   - Update your client assertion signature

2. **Verify Client Authentication:**
   - Clients → finance-agent → Settings
   - Ensure "Client authentication" is ✅ ON

3. **Verify Client Assertion:**
   - Check JWT signature uses correct client secret
   - Check `iss` and `sub` match client ID exactly
   - Check `aud` matches Keycloak realm URL exactly

### Problem: "Invalid grant" error

**Symptoms:**
```json
{
  "error": "invalid_grant",
  "error_description": "..."
}
```

**Solutions:**
1. **Check Token Request:**
   - Verify `grant_type=client_credentials`
   - Verify `client_assertion_type` is exactly: `urn:ietf:params:oauth:client-assertion-type:jwt-bearer`

2. **Check Client Assertion Expiration:**
   - Decode assertion at https://jwt.io
   - Verify `exp` is in the future
   - Verify `iat` is not in the future

3. **Check Service Account:**
   - Users → search for `service-account-finance-agent`
   - Verify it exists and is enabled
   - Verify it has `FinanceAgent` role assigned

### Problem: act.sub contains email instead of user ID

**Symptoms:**
- Token's `act.sub` contains email (e.g., `alice@corp.example.com`)
- Should contain Keycloak user ID (e.g., `f1234567-89ab-cdef-0123-456789abcdef`)

**Solutions:**
1. **Update Application Code:**
   - Application must extract user ID from OIDC token's `sub` claim
   - Use user ID (not email) when creating act claim
   - Example:
   ```python
   # ✅ Correct
   user_id = oidc_token['sub']  # Keycloak user ID (UUID)
   act = {"sub": user_id, "email": user_email, "name": user_name}
   
   # ❌ Wrong
   act = {"sub": user_email, ...}  # Don't use email
   ```

2. **Verify User ID in Keycloak:**
   - Users → alice → Details
   - Copy the user ID from URL or user details
   - This is the value that should be in `act.sub`

### Problem: User roles not showing in token

**Symptoms:**
- Human user roles not visible in access token
- Can't verify human authorization

**Solutions:**
This is expected behavior - human roles are NOT in the access token. The access token contains:
- Agent's service account roles
- Human's identity in `act` claim

To verify human roles:
1. **Query Keycloak API** to check user's roles (see Step 8.1)
2. **Cache role information** to avoid repeated API calls
3. **Use Keycloak Admin API** with proper service account credentials

### Problem: Cannot correlate logs with Keycloak audit

**Symptoms:**
- Logs show email/name but can't correlate with Keycloak user
- Need to identify which Keycloak user performed action

**Solutions:**
1. **Use user ID in logs:**
   ```python
   # ✅ Correct - logs user ID
   human_id = token_claims['act']['sub']  # User ID (UUID)
   logger.info("Access", extra={"human_id": human_id})
   
   # ❌ Wrong - logs email
   logger.info("Access", extra={"email": email})  # Can't correlate
   ```

2. **Correlate with Keycloak:**
   - Keycloak audit logs use user ID
   - Your application logs should use the same user ID
   - Perfect correlation for security investigations

<br>

## **Reference: Configuration JSON**

### Realm Configuration Export

For automated deployment, export your realm configuration:

**Admin Console:** Realm Settings → Partial Export

**Or via Keycloak Admin API:**
```bash
# Export realm configuration
curl -X GET "https://keycloak/admin/realms/agbac-min" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  > agbac-min-realm-config.json
```

### Protocol Mapper Configuration (JSON)

```json
{
  "name": "act-claim-mapper",
  "protocol": "openid-connect",
  "protocolMapper": "oidc-usermodel-attribute-mapper",
  "consentRequired": false,
  "config": {
    "userAttribute": "act",
    "claim.name": "act",
    "jsonType.label": "JSON",
    "id.token.claim": "true",
    "access.token.claim": "true",
    "userinfo.token.claim": "false",
    "multivalued": "false",
    "aggregate.attrs": "false"
  }
}
```

### Client Configuration (JSON)

```json
{
  "clientId": "finance-agent",
  "name": "Finance Agent",
  "description": "AI agent for finance operations",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "YOUR_CLIENT_SECRET",
  "publicClient": false,
  "serviceAccountsEnabled": true,
  "standardFlowEnabled": false,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "protocol": "openid-connect",
  "attributes": {
    "access.token.lifespan": "300"
  },
  "protocolMappers": [
    {
      "name": "act-claim-mapper",
      "protocol": "openid-connect",
      "protocolMapper": "oidc-usermodel-attribute-mapper",
      "config": {
        "userAttribute": "act",
        "claim.name": "act",
        "jsonType.label": "JSON",
        "id.token.claim": "true",
        "access.token.claim": "true"
      }
    }
  ]
}
```

<br>

## **Next Steps**

After completing Keycloak configuration:

1. ✅ **Configure your application** to extract user identity and create act claims
   - See: [Application Agent Implementation Guide](APPLICATION_AGENT_GUIDE.md)

2. ✅ **Implement resource server validation** (Step 8)
   - Validate both agent and human identities
   - Enforce authorization policies
   - Log using IAM identifiers (user IDs)

3. ✅ **Deploy to production**
   - Use HTTPS everywhere
   - Store client secrets in secure vault (AWS Secrets Manager, Azure Key Vault)
   - Configure short token lifespans (5 minutes recommended)
   - Enable Keycloak audit logging
   - Monitor token requests and failures

4. ✅ **Test thoroughly**
   - Test with different users
   - Test authorization denial scenarios
   - Test token expiration handling
   - Test with multiple agents

<br>

## **Security Checklist**

Before deploying to production, verify:

- [ ] HTTPS enabled on Keycloak
- [ ] Client secrets stored in secure vault (not environment variables or config files)
- [ ] Token lifespan set to 5 minutes or less
- [ ] Service account has only required roles (principle of least privilege)
- [ ] Human users have appropriate role assignments
- [ ] Resource server validates both `sub` and `act`
- [ ] Resource server validates token signature
- [ ] Resource server validates token expiration
- [ ] Logging uses IAM identifiers (user IDs), not PII
- [ ] Client assertion JTI validated to prevent replay attacks
- [ ] Keycloak audit logging enabled
- [ ] Regular security updates applied to Keycloak

<br>

## **Additional Resources**

**Keycloak Documentation:**
- [Service Accounts](https://www.keycloak.org/docs/latest/server_admin/#_service_accounts)
- [Protocol Mappers](https://www.keycloak.org/docs/latest/server_admin/#_protocol-mappers)
- [Client Authentication](https://www.keycloak.org/docs/latest/server_admin/#_client-credentials)

**OAuth 2.0 Specifications:**
- [RFC 8693 - Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693)
- [RFC 7523 - JWT Profile for OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc7523)

<br>
<br>
<br>
<br>
<br>
<br>
<br>
<p align="center">
▁ ▂ ▂ ▃ ▃ ▄ ▄ ▅ ▅ ▆ ▆ Created with Aloha by Kahalewai - 2026 ▆ ▆ ▅ ▅ ▄ ▄ ▃ ▃ ▂ ▂ ▁
</p>
