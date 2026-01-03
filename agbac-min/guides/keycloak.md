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

---

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

---

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

---

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

**Dual-Subject Authorization:**  
Both the agent (`sub`) and human (`act`) must be independently authorized.

**Pre-Approval:**  
Both subjects are configured in Keycloak before any token requests occur.

**Client Assertion:**  
A JWT created by the agent containing both identities, signed with agent credentials.

**Protocol Mapper:**  
Keycloak extracts `act` from the client assertion and includes it in the issued token.

---

## **Step 1: Create Realm**

A realm in Keycloak is an isolated namespace for managing users, clients, and policies.

### 1.1 Navigate to Realm Creation

1. Log in to Keycloak Admin Console
2. Click the realm dropdown (top-left, currently shows "master")
3. Click **"Create Realm"**

### 1.2 Configure Realm

**Realm Name:** `agbac-min`

**Settings:**
- Display name: `AGBAC-Min Realm`
- Enabled: `ON`
- User registration: `OFF` (we'll create users manually)
- Forgot password: `OFF` (optional, can enable later)
- Remember me: `OFF` (optional)

Click **"Create"**

### 1.3 Verify Realm Created

You should now see `agbac-min` in the realm dropdown.

**Expected Result:**
```
Current realm: agbac-min
```

### Configuration Reference (JSON)

```json
{
  "realm": "agbac-min",
  "displayName": "AGBAC-Min Realm",
  "enabled": true,
  "registrationAllowed": false,
  "resetPasswordAllowed": false,
  "rememberMe": false,
  "sslRequired": "external"
}
```

---

## **Step 2: Create Roles for Pre-Approval**

Roles represent permissions in Keycloak. We'll create separate roles for agents and humans.

### 2.1 Create Human Role

1. Navigate to **Realm Roles** (left sidebar)
2. Click **"Create Role"**

**Configuration:**
- Role name: `FinanceUser`
- Description: `Human users authorized for finance system access`

Click **"Save"**

### 2.2 Create Agent Role

1. Click **"Create Role"** again

**Configuration:**
- Role name: `FinanceAgent`
- Description: `AI agents authorized for finance system access`

Click **"Save"**

### 2.3 Verify Roles Created

Navigate to **Realm Roles** and verify both roles appear:
- ✅ `FinanceAgent`
- ✅ `FinanceUser`

### Configuration Reference (JSON)

```json
{
  "roles": {
    "realm": [
      {
        "name": "FinanceAgent",
        "description": "AI agents authorized for finance system access",
        "composite": false,
        "clientRole": false
      },
      {
        "name": "FinanceUser",
        "description": "Human users authorized for finance system access",
        "composite": false,
        "clientRole": false
      }
    ]
  }
}
```

**Note:** These roles represent the pre-approval for accessing resources. Both the agent and human must have their respective roles assigned.

---

## **Step 3: Create Agent Client**

The agent client represents the AI agent's identity in Keycloak.

### 3.1 Navigate to Clients

1. Click **"Clients"** in left sidebar
2. Click **"Create client"**

### 3.2 Configure Client - General Settings

**Client type:** `OpenID Connect`  
**Client ID:** `finance-agent`

Click **"Next"**

### 3.3 Configure Client - Capability Config

**Client authentication:** `ON` ✅  
**Authorization:** `OFF`  
**Authentication flow:**
- ✅ Standard flow: `OFF`
- ✅ Direct access grants: `OFF`
- ✅ Implicit flow: `OFF`
- ✅ Service accounts roles: `ON` ✅
- ✅ OAuth 2.0 Device Authorization Grant: `OFF`
- ✅ OIDC CIAM Grant: `OFF`

Click **"Next"**

### 3.4 Configure Client - Login Settings

**Root URL:** Leave empty  
**Valid redirect URIs:** Leave empty (not needed for service accounts)  
**Web origins:** Leave empty

Click **"Save"**

### 3.5 Configure Client Credentials

1. Navigate to **"Credentials"** tab
2. **Client Authenticator:** `Client Id and Secret` (default)
3. Copy the **Client secret** - you'll need this for agent configuration

**Save this secret securely!**

```
Example client secret: 8xKd9P2mNqR5vTbY3wZcF7jL6hS4gA1e
```

### 3.6 Enable Service Account

1. Navigate to **"Service account roles"** tab
2. Verify service account is enabled
3. Note the service account username (e.g., `service-account-finance-agent`)

### Configuration Reference (JSON)

```json
{
  "clientId": "finance-agent",
  "name": "Finance Agent",
  "description": "AI agent for finance system operations",
  "enabled": true,
  "protocol": "openid-connect",
  "publicClient": false,
  "serviceAccountsEnabled": true,
  "standardFlowEnabled": false,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "authorizationServicesEnabled": false,
  "attributes": {
    "client.secret.creation.time": "1735686000",
    "oauth2.device.authorization.grant.enabled": "false",
    "oidc.ciba.grant.enabled": "false"
  }
}
```

---

## **Step 4: Configure Protocol Mapper for Act Claim**

This is the **most critical step**. The protocol mapper extracts the `act` claim from the client assertion JWT and includes it in the access token.

### 4.1 Navigate to Client Mappers

1. Go to **Clients** → `finance-agent`
2. Click **"Client scopes"** tab
3. Click on `finance-agent-dedicated` (the dedicated scope for this client)
4. Click **"Mappers"** tab
5. Click **"Add mapper"** → **"By configuration"**

### 4.2 Select Mapper Type

Select: **"Script Mapper"**

### 4.3 Configure Script Mapper

**Name:** `act-claim-mapper`  
**Token Claim Name:** `act`  
**Claim JSON Type:** `JSON`  
**Add to ID token:** `OFF`  
**Add to access token:** `ON` ✅  
**Add to userinfo:** `OFF`  
**Add to token introspection:** `ON` ✅ (optional but recommended)

**Script:**

```javascript
/**
 * AGBAC-Min Protocol Mapper
 * Extracts 'act' claim from client assertion JWT
 */

// Get the client assertion from the authentication session
var clientAssertion = context.getClientAssertion();

// Check if client assertion exists
if (clientAssertion !== null) {
    // Extract the 'act' claim from client assertion's other claims
    var act = clientAssertion.getOtherClaims().get('act');
    
    // If act claim exists, return it to be added to the access token
    if (act !== null) {
        // Log for debugging (optional - remove in production if logging is sensitive)
        LOG.info('AGBAC-Min: Act claim extracted from client assertion: ' + act);
        
        // Return the act claim to be included in the token
        exports = act;
    } else {
        LOG.warn('AGBAC-Min: Client assertion present but missing act claim');
    }
} else {
    LOG.warn('AGBAC-Min: No client assertion provided in token request');
}
```

**Multivalued:** `OFF`

Click **"Save"**

### 4.4 Verify Mapper Created

Navigate back to **Mappers** tab and verify:
- ✅ `act-claim-mapper` appears in the list
- ✅ Type: `Script Mapper`
- ✅ Token Claim Name: `act`

### Important Notes

⚠️ **Script Mapper Security:** Keycloak script mappers execute JavaScript. Ensure your Keycloak instance is properly secured.

⚠️ **Performance:** Script mappers run on every token request. This script is lightweight and should not impact performance.

✅ **Logging:** The script includes logging statements. Check Keycloak logs (`/opt/keycloak/data/log/keycloak.log`) if tokens don't contain `act`.

### Configuration Reference (JSON)

```json
{
  "name": "act-claim-mapper",
  "protocol": "openid-connect",
  "protocolMapper": "oidc-script-mapper",
  "consentRequired": false,
  "config": {
    "script": "var clientAssertion = context.getClientAssertion();\nif (clientAssertion !== null) {\n    var act = clientAssertion.getOtherClaims().get('act');\n    if (act !== null) {\n        LOG.info('AGBAC-Min: Act claim extracted: ' + act);\n        exports = act;\n    } else {\n        LOG.warn('AGBAC-Min: Missing act claim in assertion');\n    }\n} else {\n    LOG.warn('AGBAC-Min: No client assertion provided');\n}",
    "claim.name": "act",
    "jsonType.label": "JSON",
    "id.token.claim": "false",
    "access.token.claim": "true",
    "userinfo.token.claim": "false",
    "introspection.token.claim": "true",
    "multivalued": "false"
  }
}
```

---

## **Step 5: Assign Roles (Pre-Approval)**

Assigning roles represents the organizational pre-approval process. Both the agent and human must have their respective roles.

### 5.1 Assign Agent Role

1. Navigate to **Clients** → `finance-agent`
2. Click **"Service account roles"** tab
3. Click **"Assign role"**
4. **Filter by realm roles** (toggle if needed)
5. Select `FinanceAgent` role
6. Click **"Assign"**

**Verify:**
```
Assigned roles:
- FinanceAgent
```

### 5.2 Why This Matters

This role assignment represents organizational approval that the `finance-agent` is authorized to access finance system resources.

In a real deployment:
- Security team reviews agent capabilities
- Business approves agent use case
- Admin assigns role in Keycloak
- Agent can now request tokens

---

## **Step 6: Create Test User**

Create a test user to represent the human principal in dual-subject authorization.

### 6.1 Create User

1. Navigate to **Users** in left sidebar
2. Click **"Add user"**

**Configuration:**
- Username: `alice`
- Email: `alice@corp.example.com`
- First name: `Alice`
- Last name: `Smith`
- Email verified: `ON` ✅
- Enabled: `ON` ✅

Click **"Create"**

### 6.2 Set User Password

1. Click **"Credentials"** tab
2. Click **"Set password"**
3. Password: `Test123!` (use a secure password in production)
4. Temporary: `OFF`
5. Click **"Save"**
6. Confirm in dialog

### 6.3 Assign Role to User

1. Click **"Role mapping"** tab
2. Click **"Assign role"**
3. **Filter by realm roles**
4. Select `FinanceUser`
5. Click **"Assign"**

**Verify:**
```
Assigned roles:
- FinanceUser
- default-roles-agbac-min (automatically assigned)
```

### Configuration Reference (JSON)

```json
{
  "username": "alice",
  "email": "alice@corp.example.com",
  "firstName": "Alice",
  "lastName": "Smith",
  "emailVerified": true,
  "enabled": true,
  "credentials": [
    {
      "type": "password",
      "value": "Test123!",
      "temporary": false
    }
  ],
  "realmRoles": [
    "FinanceUser"
  ]
}
```

### 6.4 Why This Matters

This role assignment represents organizational approval that `alice@corp.example.com` is authorized to access finance system resources.

When the agent includes Alice's identity in the `act` claim, Keycloak will verify she has the `FinanceUser` role before issuing the token.

---

## **Step 7: Test Configuration**

Now we'll test that the configuration works by manually requesting a token with a client assertion containing the `act` claim.

### 7.1 Gather Required Information

**Keycloak Token Endpoint:**
```
https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/token
```

**Client ID:** `finance-agent`  
**Client Secret:** (from Step 3.5)

### 7.2 Create Client Assertion JWT

The agent will create this JWT. For testing, we'll create it manually.

**Client Assertion Payload:**
```json
{
  "iss": "finance-agent",
  "sub": "finance-agent",
  "aud": "https://your-keycloak-domain/realms/agbac-min",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "test-assertion-123",
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

**Important:** 
- Replace `exp` with current timestamp + 300 seconds
- Replace `iat` with current timestamp
- Replace `aud` with your actual Keycloak domain
- Replace `jti` with a unique ID (can be any unique string)

**Sign this JWT** with the client secret using HS256 algorithm.

**Using Python:**
```python
import jwt
import time

payload = {
    "iss": "finance-agent",
    "sub": "finance-agent",
    "aud": "https://your-keycloak-domain/realms/agbac-min",
    "exp": int(time.time()) + 300,
    "iat": int(time.time()),
    "jti": "test-assertion-123",
    "act": {
        "sub": "alice@corp.example.com",
        "email": "alice@corp.example.com",
        "name": "Alice Smith"
    }
}

client_secret = "YOUR_CLIENT_SECRET_HERE"

client_assertion = jwt.encode(payload, client_secret, algorithm="HS256")
print(client_assertion)
```

**Using https://jwt.io:**
1. Go to https://jwt.io
2. Paste the payload above
3. In "Verify Signature" section, paste your client secret
4. Select algorithm: HS256
5. Copy the encoded JWT

### 7.3 Request Token

**Using curl:**
```bash
curl -X POST https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=finance-agent" \
  -d "scope=openid" \
  -d "client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer" \
  -d "client_assertion=YOUR_SIGNED_JWT_HERE"
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
    "sub": "alice@corp.example.com",
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
  "preferred_username": "service-account-finance-agent",
  "clientHost": "192.168.1.100",
  "clientAddress": "192.168.1.100"
}
```

### 7.5 Verify Critical Claims

**✅ Required Claims Present:**
- `sub`: `service-account-finance-agent` (agent identity)
- `act`: Object containing human identity
  - `act.sub`: `alice@corp.example.com`
  - `act.email`: `alice@corp.example.com`
  - `act.name`: `Alice Smith`
- `realm_access.roles`: Contains `FinanceAgent`

**✅ Success Criteria:**
1. Token request succeeded (HTTP 200)
2. Token contains `sub` (agent)
3. Token contains `act` (human)
4. Token contains `realm_access.roles` with `FinanceAgent`

### 7.6 Troubleshooting Token Request

**If token request fails:**

**HTTP 401 Unauthorized:**
- Check client secret is correct
- Verify client assertion signature
- Ensure `aud` in client assertion matches Keycloak realm URL exactly

**HTTP 400 Bad Request:**
- Check client assertion is valid JWT
- Verify `exp` is in the future
- Ensure `iat` is not in the future
- Check `client_assertion_type` is correct

**Token issued but missing `act` claim:**
- Verify protocol mapper is configured correctly
- Check Keycloak logs: `/opt/keycloak/data/log/keycloak.log`
- Look for: `AGBAC-Min: Act claim extracted` or warning messages
- Verify client assertion contains `act` claim
- Ensure mapper is assigned to `finance-agent-dedicated` scope

---

## **Step 8: Configure Resource Server Validation**

The resource server (your API) must validate that BOTH the agent and human are authorized.

### 8.1 Token Validation Logic

**Pseudocode:**
```python
def validate_dual_subject_token(token, resource):
    # 1. Verify token signature
    decoded = verify_jwt_signature(token, keycloak_public_key)
    
    # 2. Validate standard claims
    validate_expiry(decoded['exp'])
    validate_issuer(decoded['iss'], expected_issuer)
    
    # 3. Extract subjects
    agent_id = decoded['sub']  # service-account-finance-agent
    act_claim = decoded.get('act')
    
    if not act_claim:
        raise Unauthorized("Token missing human identity (act)")
    
    human_id = act_claim['sub']  # alice@corp.example.com
    
    # 4. Validate agent authorization
    agent_roles = decoded['realm_access']['roles']
    if 'FinanceAgent' not in agent_roles:
        raise Forbidden("Agent not authorized for finance system")
    
    # 5. Validate human authorization (check against your user database)
    if not user_has_role(human_id, 'FinanceUser'):
        raise Forbidden("Human not authorized for finance system")
    
    # 6. Validate resource-specific permissions (optional)
    if not can_access_resource(agent_id, resource):
        raise Forbidden("Agent not authorized for this resource")
    
    if not can_access_resource(human_id, resource):
        raise Forbidden("Human not authorized for this resource")
    
    # 7. Log for audit
    audit_log(agent_id, human_id, resource, "ALLOWED")
    
    return True
```

### 8.2 Get Keycloak Public Key

**Method 1: JWKS Endpoint**
```
https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/certs
```

This returns a JSON Web Key Set (JWKS) containing public keys.

**Method 2: Admin Console**
1. Navigate to **Realm Settings** → **Keys** tab
2. Click **"Public key"** next to the active RS256 key
3. Copy the public key

### 8.3 Example Python Validation

```python
import jwt
import requests
from functools import lru_cache

@lru_cache()
def get_keycloak_public_key():
    """Fetch and cache Keycloak public key."""
    jwks_url = "https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/certs"
    response = requests.get(jwks_url)
    jwks = response.json()
    
    # Get first RS256 key
    for key in jwks['keys']:
        if key['alg'] == 'RS256':
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    
    raise ValueError("No RS256 key found in JWKS")

def validate_agbac_token(token, resource):
    """Validate AGBAC dual-subject token."""
    try:
        # Decode and verify
        public_key = get_keycloak_public_key()
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=None,  # Or specify expected audience
            issuer='https://your-keycloak-domain/realms/agbac-min'
        )
        
        # Extract subjects
        agent_id = decoded['sub']
        act = decoded.get('act')
        
        if not act or 'sub' not in act:
            return {
                'authorized': False,
                'reason': 'Missing human identity (act)'
            }
        
        human_id = act['sub']
        
        # Check agent role
        agent_roles = decoded.get('realm_access', {}).get('roles', [])
        if 'FinanceAgent' not in agent_roles:
            return {
                'authorized': False,
                'reason': f'Agent {agent_id} not authorized'
            }
        
        # Check human role (query your user database)
        if not user_has_finance_access(human_id):
            return {
                'authorized': False,
                'reason': f'Human {human_id} not authorized'
            }
        
        # Success - both authorized
        return {
            'authorized': True,
            'agent': agent_id,
            'human': human_id
        }
        
    except jwt.ExpiredSignatureError:
        return {'authorized': False, 'reason': 'Token expired'}
    except jwt.InvalidTokenError as e:
        return {'authorized': False, 'reason': f'Invalid token: {e}'}
```

### 8.4 Audit Logging

**Every access should be logged with both identities:**

```python
def audit_log(agent_id, human_id, resource, action, result):
    """Log dual-subject access for audit trail."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'agent_identity': agent_id,
        'human_identity': human_id,
        'resource': resource,
        'action': action,
        'result': result,  # ALLOWED or DENIED
        'reason': result.get('reason') if result == 'DENIED' else None
    }
    
    # Send to your logging system
    logger.info(json.dumps(log_entry))
```

**Example Log Entry:**
```json
{
  "timestamp": "2026-01-02T15:30:45.123Z",
  "agent_identity": "service-account-finance-agent",
  "human_identity": "alice@corp.example.com",
  "resource": "/api/finance/reports/Q4-2025",
  "action": "GET",
  "result": "ALLOWED",
  "reason": null
}
```

---

## **Troubleshooting**

### Issue: Token Request Returns 401 Unauthorized

**Possible Causes:**
1. Client secret incorrect
2. Client assertion signature invalid
3. Client assertion `aud` doesn't match realm URL

**Solutions:**
```bash
# Verify client secret
# Go to Clients → finance-agent → Credentials → Regenerate secret

# Check client assertion audience
# Should be: https://your-keycloak-domain/realms/agbac-min
# Common mistake: missing /realms/agbac-min

# Verify JWT signature
# Use https://jwt.io to decode and verify client assertion
```

### Issue: Token Issued But Missing `act` Claim

**Possible Causes:**
1. Protocol mapper not configured correctly
2. Client assertion doesn't contain `act`
3. Mapper not assigned to client scope

**Solutions:**
```bash
# Check Keycloak logs
tail -f /opt/keycloak/data/log/keycloak.log | grep AGBAC

# Should see: "AGBAC-Min: Act claim extracted: ..."
# If you see warning: "Missing act claim in assertion"
#   → Client assertion doesn't have act claim

# Verify mapper configuration
# Clients → finance-agent → Client scopes → finance-agent-dedicated → Mappers
# Ensure act-claim-mapper is present and enabled

# Test client assertion
# Decode your client assertion JWT at https://jwt.io
# Verify it contains the "act" claim
```

### Issue: Token Validation Fails at Resource Server

**Possible Causes:**
1. Public key mismatch
2. Token expired
3. Signature verification failed

**Solutions:**
```python
# Verify public key matches
# Get from: https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/certs

# Check token expiry
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"Token expires at: {decoded['exp']}")
print(f"Current time: {int(time.time())}")

# Test signature verification
try:
    jwt.decode(token, public_key, algorithms=['RS256'])
    print("Signature valid")
except jwt.InvalidSignatureError:
    print("Signature invalid - check public key")
```

### Issue: Agent Role Not Appearing in Token

**Possible Causes:**
1. Role not assigned to service account
2. Service account not enabled

**Solutions:**
```bash
# Verify role assignment
# Clients → finance-agent → Service account roles
# Should show: FinanceAgent

# Verify service account enabled
# Clients → finance-agent → Settings
# Service accounts roles: ON
```

### Issue: Human Authorization Check Fails

**This is expected!** The human role check happens at your resource server, not in Keycloak.

**Implementation:**
```python
def user_has_finance_access(human_email):
    """
    Check if human has FinanceUser role.
    This queries YOUR user database, not Keycloak.
    """
    # Option 1: Query your database
    user = db.query(User).filter_by(email=human_email).first()
    return 'FinanceUser' in user.roles
    
    # Option 2: Query Keycloak Admin API
    # (Only if you manage users in Keycloak)
    response = requests.get(
        f"https://keycloak/admin/realms/agbac-min/users",
        params={"email": human_email},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    users = response.json()
    if users:
        user_id = users[0]['id']
        roles_response = requests.get(
            f"https://keycloak/admin/realms/agbac-min/users/{user_id}/role-mappings/realm",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        roles = roles_response.json()
        return any(role['name'] == 'FinanceUser' for role in roles)
    
    return False
```

---

## **Reference: Configuration JSON**

### Complete Realm Export

This JSON represents the complete Keycloak realm configuration for AGBAC-Min.

```json
{
  "realm": "agbac-min",
  "enabled": true,
  "sslRequired": "external",
  "roles": {
    "realm": [
      {
        "name": "FinanceAgent",
        "description": "AI agents authorized for finance system access"
      },
      {
        "name": "FinanceUser",
        "description": "Human users authorized for finance system access"
      }
    ]
  },
  "clients": [
    {
      "clientId": "finance-agent",
      "enabled": true,
      "protocol": "openid-connect",
      "publicClient": false,
      "serviceAccountsEnabled": true,
      "standardFlowEnabled": false,
      "implicitFlowEnabled": false,
      "directAccessGrantsEnabled": false,
      "protocolMappers": [
        {
          "name": "act-claim-mapper",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-script-mapper",
          "config": {
            "script": "var clientAssertion = context.getClientAssertion();\nif (clientAssertion !== null) {\n    var act = clientAssertion.getOtherClaims().get('act');\n    if (act !== null) {\n        LOG.info('AGBAC-Min: Act claim extracted: ' + act);\n        exports = act;\n    }\n}",
            "claim.name": "act",
            "jsonType.label": "JSON",
            "access.token.claim": "true",
            "id.token.claim": "false"
          }
        }
      ]
    }
  ],
  "users": [
    {
      "username": "alice",
      "email": "alice@corp.example.com",
      "firstName": "Alice",
      "lastName": "Smith",
      "enabled": true,
      "emailVerified": true,
      "realmRoles": ["FinanceUser"]
    }
  ]
}
```

### Client Assertion JWT Example

```json
{
  "iss": "finance-agent",
  "sub": "finance-agent",
  "aud": "https://keycloak.example.com/realms/agbac-min",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "unique-nonce-abc123",
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

### Expected Access Token Example

```json
{
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "iss": "https://keycloak.example.com/realms/agbac-min",
  "sub": "service-account-finance-agent",
  "typ": "Bearer",
  "azp": "finance-agent",
  "act": {
    "sub": "alice@corp.example.com",
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
  "email_verified": false,
  "preferred_username": "service-account-finance-agent"
}
```

---

## **Summary**

You've successfully configured Keycloak for AGBAC-Min dual-subject authorization!

**What You Configured:**
✅ Realm for AGBAC-Min  
✅ Roles representing pre-approval (FinanceAgent, FinanceUser)  
✅ Agent client with service account  
✅ Protocol mapper to extract `act` from client assertion  
✅ Role assignments for agent and test user  
✅ Tested token issuance with dual subjects  

**Next Steps:**
1. **Configure Python Application:** Follow the Python Application/Agent Configuration Guide
2. **Implement Resource Server Validation:** Use code examples from Step 8
3. **Test End-to-End:** Run complete workflow with real agent
4. **Add More Agents/Users:** Repeat client and user creation as needed
5. **Production Hardening:** Enable TLS, secure secrets, implement monitoring

**Security Reminders:**
- 🔒 Use TLS/HTTPS in production
- 🔒 Rotate client secrets regularly
- 🔒 Monitor Keycloak logs for anomalies
- 🔒 Implement rate limiting on token endpoint
- 🔒 Audit all dual-subject access attempts

---

<br>
<br>
<br>
<br>
<br>
<br>
<p align="center">
▁ ▂ ▂ ▃ ▃ ▄ ▄ ▅ ▅ ▆ ▆ Created with Aloha by Kahalewai - 2026 ▆ ▆ ▅ ▅ ▄ ▄ ▃ ▃ ▂ ▂ ▁
</p>
