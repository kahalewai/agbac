<div align="center">

# AGBAC-Min Auth0 IAM Configuration Guide

**Implementing dual-subject authorization for humans and agents**

</div>

<br>

## **Overview**

This guide provides step-by-step instructions for configuring Auth0 to support AGBAC-Min dual-subject authorization. After completing this guide, your Auth0 tenant will:

✅ Accept token requests from AI agents including human identity (`act`)  
✅ Issue tokens containing both agent identity (`sub`) and human identity (`act`)  
✅ Enforce that both subjects are pre-approved before issuing tokens  
✅ Enable resource servers to validate both subjects for access control  

**Estimated Time:** 30-45 minutes  
**Auth0 Plan:** Works with Free tier; Actions available on all plans  
**Prerequisites:** Auth0 tenant admin access, basic understanding of OAuth 2.0

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step 1: Create API (Resource Server)](#step-1-create-api-resource-server)
4. [Step 2: Define Permissions](#step-2-define-permissions)
5. [Step 3: Create Agent Application (M2M)](#step-3-create-agent-application-m2m)
6. [Step 4: Create Roles for Pre-Approval](#step-4-create-roles-for-pre-approval)
7. [Step 5: Create Credentials Exchange Action](#step-5-create-credentials-exchange-action)
8. [Step 6: Assign Roles (Pre-Approval)](#step-6-assign-roles-pre-approval)
9. [Step 7: Create Test User](#step-7-create-test-user)
10. [Step 8: Test Configuration](#step-8-test-configuration)
11. [Step 9: Configure Resource Server Validation](#step-9-configure-resource-server-validation)
12. [Troubleshooting](#troubleshooting)
13. [Reference: Configuration Examples](#reference-configuration-examples)

---

## **Prerequisites**

Before starting, ensure you have:

- [ ] Auth0 tenant (free tier works)
- [ ] Admin access to Auth0 Dashboard
- [ ] Auth0 domain (e.g., `your-tenant.us.auth0.com`)
- [ ] Basic familiarity with OAuth 2.0 and JWT
- [ ] `curl` or Postman for testing

**Access Auth0 Dashboard:**
```
https://manage.auth0.com
```

**Find Your Auth0 Domain:**
1. Log in to Auth0 Dashboard
2. Look in top-left corner: `your-tenant.us.auth0.com` or `your-tenant.eu.auth0.com`
3. Note this domain - you'll need it throughout the guide

---

## **Architecture Overview**

### How AGBAC-Min Works with Auth0

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
│   Auth0             │ 1. Validates client assertion
│                     │ 2. Credentials Exchange Action fires
│                     │ 3. Action extracts act from assertion
│                     │ 4. Action injects act into token
│                     │ 5. Validates both subjects (RBAC)
│                     │ 6. Issues token with sub + act
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

**Machine-to-Machine (M2M) Application:**  
Represents the AI agent in Auth0. Uses `client_credentials` grant.

**API (Resource Server):**  
Represents the protected system/resource the agent will access.

**Credentials Exchange Action:**  
Custom code that runs during M2M token requests. Extracts `act` from client assertion and injects it into the token.

**RBAC (Role-Based Access Control):**  
Auth0's built-in authorization system. Used for pre-approval of both agents and humans.

---

## **Step 1: Create API (Resource Server)**

The API represents the protected resource that agents will access.

### 1.1 Navigate to APIs

1. Log in to Auth0 Dashboard
2. Navigate to **Applications → APIs** (left sidebar)
3. Click **"+ Create API"**

### 1.2 Configure API

**Name:** `AGBAC-Min Finance API`  
**Identifier:** `https://api.example.com/finance`  
**Signing Algorithm:** `RS256` (default)

**Important Notes:**
- The **Identifier** is the `audience` for tokens. Use your actual API URL in production.
- Cannot be changed after creation, so choose carefully.

Click **"Create"**

### 1.3 Enable RBAC

1. Click on the newly created API
2. Navigate to **"Settings"** tab
3. Scroll to **"RBAC Settings"**
4. Toggle **"Enable RBAC"**: `ON` ✅
5. Toggle **"Add Permissions in the Access Token"**: `ON` ✅

Click **"Save"**

### 1.4 Why This Matters

RBAC ensures that:
- Permissions appear in access tokens (not just as scopes)
- Auth0 enforces permission assignments
- Tokens contain verifiable authorization data

### Configuration Reference

```json
{
  "name": "AGBAC-Min Finance API",
  "identifier": "https://api.example.com/finance",
  "signing_alg": "RS256",
  "allow_offline_access": false,
  "skip_consent_for_verifiable_first_party_clients": true,
  "token_lifetime": 86400,
  "token_lifetime_for_web": 7200,
  "enforce_policies": true,
  "token_dialect": "access_token_authz"
}
```

---

## **Step 2: Define Permissions**

Permissions represent the actions agents and users can perform.

### 2.1 Add Permission

1. In your API settings, click **"Permissions"** tab
2. Click **"+ Add Permission"**

**Permission:** `read:finance-data`  
**Description:** `Read access to finance system data`

Click **"Add"**

### 2.2 Add Additional Permissions (Optional)

You can add more granular permissions:

**Permission:** `write:finance-data`  
**Description:** `Write access to finance system data`

**Permission:** `delete:finance-data`  
**Description:** `Delete finance system data`

For this guide, we'll use `read:finance-data`.

### 2.3 Verify Permissions

You should see:
```
read:finance-data    Read access to finance system data
```

### Configuration Reference

```json
{
  "permissions": [
    {
      "permission_name": "read:finance-data",
      "description": "Read access to finance system data",
      "resource_server_name": "AGBAC-Min Finance API",
      "resource_server_identifier": "https://api.example.com/finance"
    }
  ]
}
```

---

## **Step 3: Create Agent Application (M2M)**

The M2M application represents the AI agent.

### 3.1 Navigate to Applications

1. Navigate to **Applications → Applications** (left sidebar)
2. Click **"+ Create Application"**

### 3.2 Configure Application

**Name:** `Finance Agent`  
**Type:** Select **"Machine to Machine Applications"**

Click **"Create"**

### 3.3 Authorize API Access

1. Select the API: **"AGBAC-Min Finance API"**
2. Click **"Authorize"**

### 3.4 Grant Permissions

1. In the permissions list, select: ✅ `read:finance-data`
2. Click **"Continue"**

### 3.5 Save Application Credentials

You'll see the application settings page.

**Important - Save These Values:**

**Domain:** `your-tenant.us.auth0.com`  
**Client ID:** `abc123xyz...` (example: `K8xDp2NqR5vTbY3wZcF7`)  
**Client Secret:** `def456uvw...` (click "Show" to reveal)

**⚠️ CRITICAL:** Copy and securely store the Client Secret. You cannot retrieve it again.

### 3.6 Verify Configuration

Navigate to **APIs** tab of the application:

You should see:
```
Authorized APIs:
- AGBAC-Min Finance API
  Permissions: read:finance-data
```

### Configuration Reference

```json
{
  "name": "Finance Agent",
  "description": "AI agent for finance system operations",
  "app_type": "non_interactive",
  "is_first_party": true,
  "callbacks": [],
  "allowed_origins": [],
  "web_origins": [],
  "grant_types": [
    "client_credentials"
  ],
  "jwt_configuration": {
    "alg": "RS256",
    "lifetime_in_seconds": 36000
  }
}
```

---

## **Step 4: Create Roles for Pre-Approval**

Roles represent organizational pre-approval for both agents and humans.

### 4.1 Navigate to Roles

1. Navigate to **User Management → Roles** (left sidebar)
2. Click **"+ Create Role"**

### 4.2 Create Agent Role

**Name:** `FinanceAgent`  
**Description:** `AI agents authorized for finance system access`

Click **"Create"**

### 4.3 Assign Permissions to Agent Role

1. Click on the `FinanceAgent` role
2. Navigate to **"Permissions"** tab
3. Click **"Add Permissions"**
4. Select **"AGBAC-Min Finance API"**
5. Select: ✅ `read:finance-data`
6. Click **"Add Permissions"**

### 4.4 Create Human Role

1. Navigate back to **Roles**
2. Click **"+ Create Role"**

**Name:** `FinanceUser`  
**Description:** `Human users authorized for finance system access`

Click **"Create"**

### 4.5 Assign Permissions to Human Role

1. Click on the `FinanceUser` role
2. Navigate to **"Permissions"** tab
3. Click **"Add Permissions"**
4. Select **"AGBAC-Min Finance API"**
5. Select: ✅ `read:finance-data`
6. Click **"Add Permissions"**

### 4.6 Verify Roles

Navigate to **Roles** and verify:
```
FinanceAgent    AI agents authorized for finance system access
FinanceUser     Human users authorized for finance system access
```

### Configuration Reference

```json
{
  "roles": [
    {
      "name": "FinanceAgent",
      "description": "AI agents authorized for finance system access",
      "permissions": [
        {
          "permission_name": "read:finance-data",
          "resource_server_identifier": "https://api.example.com/finance"
        }
      ]
    },
    {
      "name": "FinanceUser",
      "description": "Human users authorized for finance system access",
      "permissions": [
        {
          "permission_name": "read:finance-data",
          "resource_server_identifier": "https://api.example.com/finance"
        }
      ]
    }
  ]
}
```

---

## **Step 5: Create Credentials Exchange Action**

This is the **most critical step**. The Action extracts `act` from the client assertion and injects it into the token.

### 5.1 Navigate to Actions

1. Navigate to **Actions → Flows** (left sidebar)
2. Find **"Machine to Machine"** flow
3. Click on **"Machine to Machine"**

### 5.2 Create Custom Action

1. Click **"+"** button (or "Add Action" → "Build Custom")
2. Click **"Build Custom"**

**Name:** `Inject Act Claim`  
**Trigger:** `Machine to Machine / Credentials Exchange` (should be pre-selected)  
**Runtime:** `Node 18` (recommended) or latest available

Click **"Create"**

### 5.3 Implement Action Code

Replace the default code with the following:

```javascript
/**
 * AGBAC-Min Credentials Exchange Action
 * Extracts 'act' claim from client assertion and injects into access token
 * 
 * @param {Event} event - Details about the client credentials grant request
 * @param {CredentialsExchangeAPI} api - Interface to modify the access token
 */
exports.onExecuteCredentialsExchange = async (event, api) => {
  
  // Log the client making the request
  console.log(`AGBAC-Min: Token request from client: ${event.client.client_id}`);
  
  // Extract client assertion from request body
  const clientAssertion = event.request.body?.client_assertion;
  
  // Check if client assertion was provided
  if (!clientAssertion) {
    console.log('AGBAC-Min: No client assertion provided - standard M2M flow');
    return;
  }
  
  try {
    // Decode the client assertion JWT (Auth0 has already verified the signature)
    // We're decoding to extract claims, not to verify authenticity
    const base64Payload = clientAssertion.split('.')[1];
    const payload = JSON.parse(Buffer.from(base64Payload, 'base64').toString());
    
    // Log decoded assertion for debugging
    console.log('AGBAC-Min: Client assertion decoded successfully');
    
    // Extract the 'act' claim
    const act = payload.act;
    
    // Verify act claim exists
    if (!act) {
      console.warn('AGBAC-Min: Client assertion present but missing act claim');
      return;
    }
    
    // Verify act has required fields
    if (!act.sub) {
      console.warn('AGBAC-Min: Act claim missing required sub field');
      return;
    }
    
    // Log act extraction (remove in production if sensitive)
    console.log(`AGBAC-Min: Act claim extracted - Human: ${act.sub}`);
    
    // Inject act claim into the access token
    api.accessToken.setCustomClaim('act', act);
    
    // Optional: Add namespace to act claim for better organization
    // api.accessToken.setCustomClaim('https://agbac.example.com/act', act);
    
    console.log('AGBAC-Min: Act claim successfully injected into access token');
    
  } catch (error) {
    // Log error but don't fail the token request
    // This allows standard M2M flows to continue working
    console.error('AGBAC-Min: Error processing client assertion:', error.message);
  }
};
```

Click **"Deploy"** (top-right)

### 5.4 Add Action to Flow

1. Click **"Back to flow"** (or navigate back to Machine to Machine flow)
2. You should see your action in the right sidebar under "Custom"
3. **Drag** the `Inject Act Claim` action into the flow
4. Place it **between "Start" and "Complete"**

The flow should look like:
```
Start → Inject Act Claim → Complete
```

Click **"Apply"** (top-right)

### 5.5 Verify Action Deployed

The flow should show:
```
✓ Inject Act Claim - Deployed
```

### Action Code Explanation

**What the Action Does:**

1. **Receives token request** with client assertion
2. **Decodes client assertion JWT** (Auth0 already verified signature)
3. **Extracts `act` claim** from assertion payload
4. **Validates `act` structure** (has required `sub` field)
5. **Injects `act` into access token** via `api.accessToken.setCustomClaim()`
6. **Logs all steps** for debugging (check Auth0 logs)

**Error Handling:**

- If no client assertion → continues normally (standard M2M flow)
- If assertion missing `act` → logs warning, continues
- If decoding fails → logs error, continues
- Never fails the token request (allows fallback to standard flow)

### Configuration Reference

```json
{
  "name": "Inject Act Claim",
  "code": "exports.onExecuteCredentialsExchange = async (event, api) => { /* see above */ }",
  "deployed": true,
  "supported_triggers": [
    {
      "id": "credentials-exchange",
      "version": "v2"
    }
  ],
  "dependencies": [],
  "runtime": "node18",
  "status": "built"
}
```

---

## **Step 6: Assign Roles (Pre-Approval)**

Assigning roles represents organizational approval for both the agent and humans.

### 6.1 Assign Role to Agent Application

⚠️ **Important:** Auth0 does NOT support role assignments to M2M applications via the Dashboard UI. We must use the Management API.

**Option A: Use Auth0 Management API (Recommended)**

See Section 6.3 below for complete instructions.

**Option B: Manual Validation at Resource Server**

Your resource server validates that the agent has the `FinanceAgent` role by checking the `permissions` array in the token.

For AGBAC-Min, **Option B is sufficient** because:
- Agent permissions are granted when authorizing the API (Step 3.4)
- Permissions appear in token (RBAC enabled)
- Resource server validates permissions

### 6.2 Verify Agent Permissions

1. Navigate to **Applications → Applications → Finance Agent**
2. Click **"APIs"** tab
3. Expand **"AGBAC-Min Finance API"**

Verify:
```
Permissions:
✓ read:finance-data
```

This represents the agent's pre-approval.

### 6.3 (Optional) Assign Role via Management API

If you want to formally assign the `FinanceAgent` role to the application:

**Step 1: Get Management API Token**

```bash
curl --request POST \
  --url https://YOUR_DOMAIN/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "YOUR_MANAGEMENT_API_CLIENT_ID",
    "client_secret": "YOUR_MANAGEMENT_API_CLIENT_SECRET",
    "audience": "https://YOUR_DOMAIN/api/v2/",
    "grant_type": "client_credentials"
  }'
```

**Step 2: Get Role ID**

```bash
curl --request GET \
  --url https://YOUR_DOMAIN/api/v2/roles \
  --header 'authorization: Bearer YOUR_MANAGEMENT_API_TOKEN'
```

Find the `FinanceAgent` role and copy its `id`.

**Step 3: Get Client's Resource Server (API) ID**

```bash
curl --request GET \
  --url 'https://YOUR_DOMAIN/api/v2/resource-servers' \
  --header 'authorization: Bearer YOUR_MANAGEMENT_API_TOKEN'
```

**Step 4: Assign Role to Client**

```bash
curl --request POST \
  --url https://YOUR_DOMAIN/api/v2/clients/YOUR_CLIENT_ID/roles \
  --header 'authorization: Bearer YOUR_MANAGEMENT_API_TOKEN' \
  --header 'content-type: application/json' \
  --data '{
    "roles": ["FINANCE_AGENT_ROLE_ID"]
  }'
```

---

## **Step 7: Create Test User**

Create a test user representing the human principal.

### 7.1 Navigate to Users

1. Navigate to **User Management → Users** (left sidebar)
2. Click **"+ Create User"**

### 7.2 Configure User

**Email:** `alice@corp.example.com`  
**Password:** `Test123!@#` (use strong password in production)  
**Connection:** `Username-Password-Authentication` (default)

Click **"Create"**

### 7.3 Assign Role to User

1. Click on the newly created user `alice@corp.example.com`
2. Navigate to **"Roles"** tab
3. Click **"Assign Roles"**
4. Select: ✅ `FinanceUser`
5. Click **"Assign"**

### 7.4 Verify User Configuration

**Roles tab should show:**
```
FinanceUser    Human users authorized for finance system access
```

**Permissions tab should show:**
```
API: AGBAC-Min Finance API
Permission: read:finance-data
```

### Configuration Reference

```json
{
  "email": "alice@corp.example.com",
  "email_verified": true,
  "blocked": false,
  "user_metadata": {},
  "app_metadata": {},
  "roles": [
    {
      "id": "rol_xxx",
      "name": "FinanceUser",
      "description": "Human users authorized for finance system access"
    }
  ]
}
```

---

## **Step 8: Test Configuration**

Test that the complete flow works by requesting a token.

### 8.1 Gather Required Information

**Auth0 Domain:** `your-tenant.us.auth0.com`  
**Token Endpoint:** `https://your-tenant.us.auth0.com/oauth/token`  
**Client ID:** (from Step 3.5)  
**Client Secret:** (from Step 3.5)  
**Audience:** `https://api.example.com/finance`

### 8.2 Create Client Assertion JWT

The agent creates this JWT. For testing, we'll create it manually.

**Client Assertion Payload:**
```json
{
  "iss": "YOUR_CLIENT_ID",
  "sub": "YOUR_CLIENT_ID",
  "aud": "https://your-tenant.us.auth0.com/",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "test-assertion-abc123",
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

**Important:**
- Replace `YOUR_CLIENT_ID` with your actual client ID
- Replace `aud` with your Auth0 domain (must end with `/`)
- Replace `exp` with current timestamp + 300 seconds
- Replace `iat` with current timestamp
- Replace `jti` with unique ID

**Sign the JWT with Client Secret (HS256):**

**Using Python:**
```python
import jwt
import time

payload = {
    "iss": "YOUR_CLIENT_ID",
    "sub": "YOUR_CLIENT_ID",
    "aud": "https://your-tenant.us.auth0.com/",
    "exp": int(time.time()) + 300,
    "iat": int(time.time()),
    "jti": "test-assertion-abc123",
    "act": {
        "sub": "alice@corp.example.com",
        "email": "alice@corp.example.com",
        "name": "Alice Smith"
    }
}

client_secret = "YOUR_CLIENT_SECRET"

client_assertion = jwt.encode(payload, client_secret, algorithm="HS256")
print(client_assertion)
```

**Using https://jwt.io:**
1. Go to https://jwt.io
2. Paste payload in "Decoded" section
3. Select algorithm: HS256
4. Paste your client secret in "Verify Signature"
5. Copy the encoded JWT from "Encoded" section

### 8.3 Request Token

**Using curl:**
```bash
curl --request POST \
  --url https://your-tenant.us.auth0.com/oauth/token \
  --header 'content-type: application/x-www-form-urlencoded' \
  --data grant_type=client_credentials \
  --data client_id=YOUR_CLIENT_ID \
  --data audience=https://api.example.com/finance \
  --data 'client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer' \
  --data 'client_assertion=YOUR_SIGNED_JWT_HERE'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlJ6RXpOME...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### 8.4 Decode and Verify Token

Copy the `access_token` and decode at https://jwt.io

**Expected Token Structure:**
```json
{
  "iss": "https://your-tenant.us.auth0.com/",
  "sub": "YOUR_CLIENT_ID@clients",
  "aud": "https://api.example.com/finance",
  "iat": 1735686000,
  "exp": 1735772400,
  "azp": "YOUR_CLIENT_ID",
  "scope": "read:finance-data",
  "gty": "client-credentials",
  "permissions": [
    "read:finance-data"
  ],
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

### 8.5 Verify Critical Claims

**✅ Success Criteria:**

1. **Agent Identity:**
   - `sub`: `YOUR_CLIENT_ID@clients`
   - Format: `{client_id}@clients`

2. **Human Identity:**
   - `act`: Object containing human data
   - `act.sub`: `alice@corp.example.com`
   - `act.email`: `alice@corp.example.com`
   - `act.name`: `Alice Smith`

3. **Permissions:**
   - `permissions`: Array containing `read:finance-data`
   - `scope`: String containing `read:finance-data`

4. **Standard Claims:**
   - `iss`: Auth0 domain
   - `aud`: Your API identifier
   - `exp`: Future timestamp
   - `iat`: Past timestamp

### 8.6 Check Action Logs

1. Navigate to **Monitoring → Logs** (left sidebar)
2. Filter by: **Type: `sce` (Success Exchange)**
3. Find your recent token request
4. Click to expand

**Look for Action Logs:**
```
AGBAC-Min: Token request from client: YOUR_CLIENT_ID
AGBAC-Min: Client assertion decoded successfully
AGBAC-Min: Act claim extracted - Human: alice@corp.example.com
AGBAC-Min: Act claim successfully injected into access token
```

### 8.7 Troubleshooting Token Request

**HTTP 401 Unauthorized:**
- Client secret incorrect
- Client assertion signature invalid
- Client assertion `aud` incorrect (must be `https://your-tenant.us.auth0.com/`)

**HTTP 403 Forbidden:**
- Client not authorized for API
- Check: Applications → Finance Agent → APIs tab

**Token issued but missing `act` claim:**
- Action not deployed
- Action not in M2M flow
- Client assertion missing `act`
- Check Action logs (see 8.6)

**Token issued but missing `permissions` array:**
- RBAC not enabled on API
- "Add Permissions in the Access Token" not enabled
- Re-check Step 1.3

---

## **Step 9: Configure Resource Server Validation**

Your API/resource server must validate that BOTH subjects are authorized.

### 9.1 Token Validation Logic

**Pseudocode:**
```python
def validate_dual_subject_token(token, resource):
    # 1. Verify JWT signature
    decoded = verify_jwt_signature(token, auth0_public_key)
    
    # 2. Validate standard claims
    validate_expiry(decoded['exp'])
    validate_issuer(decoded['iss'], 'https://your-tenant.us.auth0.com/')
    validate_audience(decoded['aud'], 'https://api.example.com/finance')
    
    # 3. Extract subjects
    agent_id = decoded['sub']  # client-id@clients
    act_claim = decoded.get('act')
    
    if not act_claim:
        raise Unauthorized("Token missing human identity (act)")
    
    human_id = act_claim['sub']  # alice@corp.example.com
    
    # 4. Validate agent permissions
    agent_permissions = decoded.get('permissions', [])
    if 'read:finance-data' not in agent_permissions:
        raise Forbidden("Agent not authorized for finance data access")
    
    # 5. Validate human authorization
    # Query your user database or Auth0 Management API
    if not user_has_permission(human_id, 'read:finance-data'):
        raise Forbidden("Human not authorized for finance data access")
    
    # 6. Log for audit
    audit_log(agent_id, human_id, resource, "ALLOWED")
    
    return True
```

### 9.2 Get Auth0 Public Key (JWKS)

**JWKS Endpoint:**
```
https://your-tenant.us.auth0.com/.well-known/jwks.json
```

**Example Python Code:**
```python
import jwt
import requests
from functools import lru_cache

@lru_cache()
def get_auth0_public_key(token):
    """Get Auth0 public key from JWKS endpoint."""
    # Decode header to get key ID
    header = jwt.get_unverified_header(token)
    kid = header['kid']
    
    # Fetch JWKS
    jwks_url = "https://your-tenant.us.auth0.com/.well-known/jwks.json"
    response = requests.get(jwks_url)
    jwks = response.json()
    
    # Find matching key
    for key in jwks['keys']:
        if key['kid'] == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    
    raise ValueError(f"Public key not found for kid: {kid}")

def validate_agbac_token(token, resource):
    """Validate AGBAC dual-subject token from Auth0."""
    try:
        # Get public key and verify
        public_key = get_auth0_public_key(token)
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience='https://api.example.com/finance',
            issuer='https://your-tenant.us.auth0.com/'
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
        
        # Validate agent permissions
        permissions = decoded.get('permissions', [])
        if 'read:finance-data' not in permissions:
            return {
                'authorized': False,
                'reason': f'Agent {agent_id} lacks required permission'
            }
        
        # Validate human authorization
        # Option 1: Query your database
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

def user_has_finance_access(email):
    """
    Check if human has FinanceUser role.
    Implement based on your user management system.
    """
    # Option 1: Query your database
    user = db.query(User).filter_by(email=email).first()
    return user and 'FinanceUser' in user.roles
    
    # Option 2: Query Auth0 Management API
    # (Requires management API token)
    # See Auth0 Management API docs
```

### 9.3 Validate Human Using Auth0 Management API

If you store user roles in Auth0, query the Management API:

```python
import requests

def get_management_api_token():
    """Get Auth0 Management API token."""
    response = requests.post(
        'https://your-tenant.us.auth0.com/oauth/token',
        json={
            'client_id': 'YOUR_MANAGEMENT_API_CLIENT_ID',
            'client_secret': 'YOUR_MANAGEMENT_API_CLIENT_SECRET',
            'audience': 'https://your-tenant.us.auth0.com/api/v2/',
            'grant_type': 'client_credentials'
        }
    )
    return response.json()['access_token']

def user_has_finance_role(email):
    """Check if user has FinanceUser role in Auth0."""
    mgmt_token = get_management_api_token()
    
    # Search for user by email
    response = requests.get(
        f'https://your-tenant.us.auth0.com/api/v2/users-by-email',
        params={'email': email},
        headers={'Authorization': f'Bearer {mgmt_token}'}
    )
    
    users = response.json()
    if not users:
        return False
    
    user_id = users[0]['user_id']
    
    # Get user's roles
    response = requests.get(
        f'https://your-tenant.us.auth0.com/api/v2/users/{user_id}/roles',
        headers={'Authorization': f'Bearer {mgmt_token}'}
    )
    
    roles = response.json()
    return any(role['name'] == 'FinanceUser' for role in roles)
```

### 9.4 Audit Logging

Log every dual-subject access attempt:

```python
import json
import logging
from datetime import datetime

def audit_log(agent_id, human_id, resource, result, reason=None):
    """Log dual-subject access for compliance."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': 'AGBAC_ACCESS',
        'agent_identity': agent_id,
        'human_identity': human_id,
        'resource': resource,
        'result': result,  # ALLOWED or DENIED
        'reason': reason
    }
    
    logging.info(json.dumps(log_entry))
    
    # Also send to your SIEM/audit system
    # send_to_siem(log_entry)
```

**Example Log Output:**
```json
{
  "timestamp": "2026-01-02T15:30:45.123Z",
  "event_type": "AGBAC_ACCESS",
  "agent_identity": "K8xDp2NqR5vTbY3wZcF7@clients",
  "human_identity": "alice@corp.example.com",
  "resource": "/api/finance/reports/Q4-2025",
  "result": "ALLOWED",
  "reason": null
}
```

---

## **Troubleshooting**

### Issue: Token Request Returns 401

**Possible Causes:**
1. Client secret incorrect
2. Client assertion signature invalid
3. Client ID mismatch

**Solutions:**

```bash
# Verify client credentials
# Dashboard → Applications → Finance Agent → Settings
# Regenerate secret if needed

# Check client assertion aud claim
# Must be: https://your-tenant.us.auth0.com/
# Common mistake: missing trailing slash

# Verify client assertion iss and sub
# Both should be: YOUR_CLIENT_ID
```

### Issue: Token Request Returns 403

**Possible Causes:**
1. Client not authorized for API
2. Permissions not granted

**Solutions:**

```bash
# Check API authorization
# Dashboard → Applications → Finance Agent → APIs tab
# Should show: AGBAC-Min Finance API with permissions

# Re-authorize if needed
# Applications → Finance Agent → APIs → Authorize
```

### Issue: Token Missing `act` Claim

**Possible Causes:**
1. Action not deployed
2. Action not in flow
3. Client assertion missing `act`
4. Action error (check logs)

**Solutions:**

```bash
# Verify Action deployed
# Actions → Flows → Machine to Machine
# Should show: Inject Act Claim (Deployed)

# Check Action logs
# Monitoring → Logs → Filter by type: sce
# Look for AGBAC-Min log messages

# Verify client assertion
# Decode at jwt.io
# Should contain "act" claim

# Check for Action errors
# Logs → Filter by type: fce (Failed Exchange)
```

### Issue: Token Missing `permissions` Array

**Possible Causes:**
1. RBAC not enabled on API
2. "Add Permissions in Access Token" disabled
3. Permissions not granted to application

**Solutions:**

```bash
# Enable RBAC
# APIs → AGBAC-Min Finance API → Settings
# Enable RBAC: ON
# Add Permissions in Access Token: ON

# Grant permissions
# Applications → Finance Agent → APIs
# Expand AGBAC-Min Finance API
# Should show: read:finance-data
```

### Issue: Action Logs Not Appearing

**Possible Causes:**
1. Action not in flow
2. Token request using client_secret instead of client_assertion
3. Logs filtered incorrectly

**Solutions:**

```bash
# Verify Action in flow
# Actions → Flows → Machine to Machine
# Should have: Start → Inject Act Claim → Complete

# Check request includes client_assertion
# Standard client_secret auth won't trigger Action logs

# Adjust log filters
# Monitoring → Logs
# Remove all filters, search "AGBAC"
```

### Issue: Human Authorization Fails

**Expected behavior!** Human authorization is validated at your resource server.

**Implementation:**

```python
def user_has_finance_access(email):
    """
    Validate human authorization.
    This is YOUR business logic, not Auth0's.
    """
    # Implement based on:
    # - Your user database
    # - Auth0 Management API
    # - External authorization service
    # - LDAP/Active Directory
    
    return check_user_permissions(email, 'read:finance-data')
```

---

## **Reference: Configuration Examples**

### Complete Configuration Summary

**API:**
```json
{
  "name": "AGBAC-Min Finance API",
  "identifier": "https://api.example.com/finance",
  "signing_alg": "RS256",
  "enforce_policies": true,
  "rbac": {
    "enabled": true,
    "add_permissions_in_access_token": true
  },
  "permissions": [
    {
      "permission_name": "read:finance-data",
      "description": "Read access to finance system data"
    }
  ]
}
```

**M2M Application:**
```json
{
  "name": "Finance Agent",
  "app_type": "non_interactive",
  "grant_types": ["client_credentials"],
  "authorized_apis": [
    {
      "api_identifier": "https://api.example.com/finance",
      "permissions": ["read:finance-data"]
    }
  ]
}
```

**Roles:**
```json
{
  "roles": [
    {
      "name": "FinanceAgent",
      "description": "AI agents authorized for finance system access",
      "permissions": [
        {
          "permission_name": "read:finance-data",
          "resource_server_identifier": "https://api.example.com/finance"
        }
      ]
    },
    {
      "name": "FinanceUser",
      "description": "Human users authorized for finance system access",
      "permissions": [
        {
          "permission_name": "read:finance-data",
          "resource_server_identifier": "https://api.example.com/finance"
        }
      ]
    }
  ]
}
```

### Client Assertion JWT Example

```json
{
  "iss": "K8xDp2NqR5vTbY3wZcF7",
  "sub": "K8xDp2NqR5vTbY3wZcF7",
  "aud": "https://your-tenant.us.auth0.com/",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "unique-assertion-id-123",
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
  "iss": "https://your-tenant.us.auth0.com/",
  "sub": "K8xDp2NqR5vTbY3wZcF7@clients",
  "aud": "https://api.example.com/finance",
  "iat": 1735686000,
  "exp": 1735772400,
  "azp": "K8xDp2NqR5vTbY3wZcF7",
  "scope": "read:finance-data",
  "gty": "client-credentials",
  "permissions": [
    "read:finance-data"
  ],
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

---

## **Summary**

You've successfully configured Auth0 for AGBAC-Min dual-subject authorization!

**What You Configured:**
✅ API representing protected resource  
✅ Permissions for finance system access  
✅ M2M application representing AI agent  
✅ Roles for pre-approval (FinanceAgent, FinanceUser)  
✅ Credentials Exchange Action to inject `act` claim  
✅ Role assignments for agent and test user  
✅ Tested token issuance with dual subjects  

**Key Components:**

1. **API (Resource Server)** - Represents protected system
2. **M2M Application** - Represents AI agent identity
3. **Credentials Exchange Action** - Extracts and injects `act` claim
4. **RBAC** - Enforces pre-approval via roles and permissions
5. **Dual-Subject Token** - Contains both agent (`sub`) and human (`act`)

**Next Steps:**
1. **Configure Python Application:** Follow Python Application/Agent Configuration Guide
2. **Implement Resource Server Validation:** Use code from Step 9
3. **Test End-to-End:** Run complete workflow with real agent
4. **Add More Agents/Users:** Create additional M2M apps and users as needed
5. **Production Hardening:** Rotate secrets, enable monitoring, implement rate limiting

**Security Reminders:**
- 🔒 Use HTTPS everywhere
- 🔒 Rotate client secrets regularly
- 🔒 Monitor Auth0 logs for anomalies
- 🔒 Implement rate limiting
- 🔒 Audit all dual-subject access

**Auth0-Specific Notes:**
- Actions are powerful - review code before deploying
- RBAC is automatic once enabled
- Logs are retained for 2 days (free tier) or longer (paid tiers)
- Management API useful for programmatic configuration

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
