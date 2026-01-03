<div align="center">

# AGBAC-Min Okta IAM Configuration Guide

**Implementing dual-subject authorization for humans and agents**

</div>

<br>

## **Overview**

This guide provides step-by-step instructions for configuring Okta to support AGBAC-Min dual-subject authorization. After completing this guide, your Okta instance will:

✅ Accept token requests from AI agents including human identity (`act`)  
✅ Issue tokens containing both agent identity (`sub`) and human identity (`act`)  
✅ Enforce that both subjects are pre-approved before issuing tokens  
✅ Enable resource servers to validate both subjects for access control  

**Estimated Time:** 60-75 minutes  
**Okta Edition:** Workforce Identity (requires Custom Authorization Server feature)  
**Prerequisites:** Okta admin access, basic understanding of OAuth 2.0

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step 1: Create Custom Authorization Server](#step-1-create-custom-authorization-server)
4. [Step 2: Define Scopes](#step-2-define-scopes)
5. [Step 3: Create Agent Application](#step-3-create-agent-application)
6. [Step 4: Configure Custom Claim for Act](#step-4-configure-custom-claim-for-act)
7. [Step 5: Configure Access Policy](#step-5-configure-access-policy)
8. [Step 6: Assign Applications and Users](#step-6-assign-applications-and-users)
9. [Step 7: Create Test User](#step-7-create-test-user)
10. [Step 8: Test Configuration](#step-8-test-configuration)
11. [Step 9: Configure Resource Server Validation](#step-9-configure-resource-server-validation)
12. [Troubleshooting](#troubleshooting)
13. [Reference: Configuration Examples](#reference-configuration-examples)

---

## **Prerequisites**

Before starting, ensure you have:

- [ ] Okta Workforce Identity (Okta Developer account works)
- [ ] Admin access to Okta Admin Console
- [ ] Custom Authorization Server feature enabled
- [ ] Okta domain (e.g., `dev-123456.okta.com` or `your-company.okta.com`)
- [ ] Basic familiarity with OAuth 2.0
- [ ] `curl` or Postman for testing

**Access Okta Admin Console:**
```
https://your-okta-domain/admin
```

**Verify Custom Authorization Server Available:**
1. Log in to Okta Admin Console
2. Navigate to **Security → API → Authorization Servers**
3. If you see the option to create authorization servers, you're good to go
4. If not available, contact Okta support or use Okta Developer account

**Note:** The default authorization server (`default`) can be used for testing but custom authorization servers are recommended for production.

---

## **Architecture Overview**

### How AGBAC-Min Works with Okta

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
│   Okta Custom       │ 1. Validates client assertion
│   Authorization     │ 2. Custom claim extracts act from assertion
│   Server            │ 3. Validates agent authorized (policy)
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

**Custom Authorization Server:**  
A dedicated OAuth 2.0 server in Okta for issuing tokens. Required for custom claims.

**Client Assertion:**  
A JWT created by the agent containing both identities, signed with agent credentials.

**Custom Claim:**  
Okta expression that extracts `act` from the client assertion and adds it to the access token.

**Access Policy:**  
Rules determining which clients can get tokens and under what conditions.

---

## **Step 1: Create Custom Authorization Server**

A custom authorization server provides dedicated OAuth endpoints and allows custom claims.

### 1.1 Navigate to Authorization Servers

1. Log in to Okta Admin Console
2. Navigate to **Security → API** (left sidebar)
3. Click **Authorization Servers** tab
4. Click **Add Authorization Server**

### 1.2 Configure Authorization Server

**Name:** `AGBAC-Min-AS`  
**Audience:** `https://api.example.com/finance`  
**Description:** `Authorization Server for AGBAC-Min dual-subject authorization`

**Important Notes:**
- **Audience** is the identifier for your API (use your actual API URL in production)
- This value will appear in token `aud` claim
- Cannot be changed after creation

Click **Save**

### 1.3 Note the Authorization Server Details

After creation, you'll see:

**Issuer:** `https://your-okta-domain/oauth2/aus123abc456` (example)  
**Metadata URI:** `https://your-okta-domain/oauth2/aus123abc456/.well-known/oauth-authorization-server`

**Save the Authorization Server ID:** It's in the Issuer URL after `/oauth2/` (e.g., `aus123abc456`)

You'll need this for token requests.

### Configuration Reference

```json
{
  "id": "aus123abc456",
  "name": "AGBAC-Min-AS",
  "description": "Authorization Server for AGBAC-Min dual-subject authorization",
  "audiences": [
    "https://api.example.com/finance"
  ],
  "issuer": "https://your-okta-domain/oauth2/aus123abc456",
  "status": "ACTIVE",
  "created": "2026-01-02T10:00:00.000Z",
  "lastUpdated": "2026-01-02T10:00:00.000Z"
}
```

---

## **Step 2: Define Scopes**

Scopes represent permissions in Okta OAuth.

### 2.1 Navigate to Scopes

1. Click on your **AGBAC-Min-AS** authorization server
2. Click **Scopes** tab
3. Click **Add Scope**

### 2.2 Configure Scope

**Name:** `finance.read`  
**Display Name:** `Read Finance Data`  
**Description:** `Allows reading finance system data`  
**User Consent:** Not required (leave unchecked)  
**Default Scope:** No (leave unchecked)  
**Metadata:** Published (keep default)

Click **Create**

### 2.3 Add Additional Scopes (Optional)

**Name:** `finance.write`  
**Display Name:** `Write Finance Data`  
**Description:** `Allows writing finance system data`

For this guide, we'll use `finance.read`.

### 2.4 Verify Scopes

The **Scopes** tab should show:
```
finance.read    Read Finance Data    Not required
```

### Configuration Reference

```json
{
  "name": "finance.read",
  "displayName": "Read Finance Data",
  "description": "Allows reading finance system data",
  "consent": "REQUIRED",
  "default": false,
  "metadataPublish": "ALL_CLIENTS",
  "system": false
}
```

---

## **Step 3: Create Agent Application**

The application represents the AI agent's identity.

### 3.1 Navigate to Applications

1. Navigate to **Applications → Applications** (left sidebar)
2. Click **Create App Integration**

### 3.2 Configure Application Type

**Sign-in method:** `API Services` (OAuth 2.0 client credentials)

Click **Next**

### 3.3 Configure Application Settings

**App integration name:** `Finance Agent`

Click **Save**

### 3.4 Note Application Credentials

You'll see:

**Client ID:** `0oa123abc456xyz` (example)  
**Client Secret:** Click **Copy to clipboard**

**⚠️ CRITICAL:** Save the Client Secret securely. You cannot retrieve it again.

**Client authentication:** `Client Secret` (default)

### 3.5 Configure General Settings

1. Click **Edit** in General Settings section
2. Scroll to **Proof Key for Code Exchange (PKCE)**
3. Ensure it's set to: `Not required` (for client_credentials)
4. Click **Save**

### 3.6 Enable Client Credentials Grant

1. Scroll to **General Settings**
2. Under **Grant type**, verify:
   - ✅ **Client Credentials** is checked
3. If not, click **Edit**, check it, and **Save**

### Configuration Reference

```json
{
  "id": "0oa123abc456xyz",
  "name": "Finance Agent",
  "label": "Finance Agent",
  "status": "ACTIVE",
  "accessibility": {
    "selfService": false,
    "errorRedirectUrl": null,
    "loginRedirectUrl": null
  },
  "credentials": {
    "oauthClient": {
      "client_id": "0oa123abc456xyz",
      "client_secret": "***",
      "token_endpoint_auth_method": "client_secret_post"
    }
  },
  "settings": {
    "oauthClient": {
      "grant_types": [
        "client_credentials"
      ],
      "response_types": [
        "token"
      ],
      "application_type": "service"
    }
  }
}
```

---

## **Step 4: Configure Custom Claim for Act**

This is the **most critical step**. The custom claim extracts `act` from the client assertion.

### 4.1 Navigate to Claims

1. Go to **Security → API → Authorization Servers**
2. Click on **AGBAC-Min-AS**
3. Click **Claims** tab
4. Click **Add Claim**

### 4.2 Configure Act Claim

**Name:** `act`  
**Include in token type:** `Access Token` (select from dropdown)  
**Value type:** `Expression`  
**Value:** `clientAssertion.claims.act`  
**Disable claim:** Unchecked  
**Include in:** `Any scope`

**Alternative (scope-specific):**
If you want the claim only for specific scopes:
- **Include in:** `The following scopes`
- Select: `finance.read`

Click **Create**

### 4.3 Understanding the Expression

**Expression:** `clientAssertion.claims.act`

**What it means:**
- `clientAssertion` - The JWT the agent sends during token request
- `.claims` - Access the claims in that JWT
- `.act` - Extract the `act` claim specifically

**How it works:**
1. Agent creates client assertion JWT with `act` claim
2. Agent sends assertion during token request
3. Okta evaluates the expression
4. Okta extracts `act` from assertion
5. Okta adds `act` to the access token being issued

### 4.4 Verify Claim Created

The **Claims** tab should show:
```
Name    Value Type    Value                         Include In
act     Expression    clientAssertion.claims.act    Access Token
```

### Configuration Reference

```json
{
  "id": "ocl123abc456",
  "name": "act",
  "status": "ACTIVE",
  "claimType": "RESOURCE",
  "valueType": "EXPRESSION",
  "value": "clientAssertion.claims.act",
  "alwaysIncludeInToken": false,
  "conditions": {
    "scopes": []
  },
  "system": false
}
```

### Important Notes

**⚠️ Expression Limitations:**
- Okta expressions cannot perform complex logic
- The expression assumes `act` exists in client assertion
- If `act` is missing, the claim will be omitted (not cause error)

**✅ Best Practice:**
- Agent must always include `act` in client assertion
- Validate `act` presence at resource server
- Log when `act` is missing for debugging

---

## **Step 5: Configure Access Policy**

Access policies control which clients can obtain tokens.

### 5.1 Navigate to Access Policies

1. In **AGBAC-Min-AS** authorization server
2. Click **Access Policies** tab
3. Click **Add New Access Policy**

### 5.2 Configure Policy

**Name:** `AGBAC-Min-Policy`  
**Description:** `Access policy for AGBAC-Min dual-subject authorization`  
**Assign to:** `The following clients:`

Click **Create Policy**

### 5.3 Assign Client to Policy

1. In the **Assign to** section, click **Assign**
2. Search for: `Finance Agent`
3. Select the checkbox next to **Finance Agent**
4. Click **Done**

### 5.4 Add Policy Rule

1. Click **Add Rule** in the AGBAC-Min-Policy
2. Configure the rule:

**Rule Name:** `Allow Client Credentials with Act`

**IF Grant type is:** Check ✅ `Client Credentials`  
**AND User is:** `Any user assigned the app` (default is fine, not used for client_credentials)  
**AND Scopes requested:** `Any scopes`  
**THEN Access token lifetime is:** `1 hour` (3600 seconds)  
**Refresh token lifetime is:** Leave as is (not used for client_credentials)

Click **Create Rule**

### 5.5 Verify Policy Configuration

You should see:
```
Policy: AGBAC-Min-Policy
Assigned to: Finance Agent (1 client)
Rules: Allow Client Credentials with Act
```

### Configuration Reference

```json
{
  "type": "OAUTH_AUTHORIZATION_POLICY",
  "id": "pol123abc456",
  "name": "AGBAC-Min-Policy",
  "description": "Access policy for AGBAC-Min dual-subject authorization",
  "status": "ACTIVE",
  "priority": 1,
  "conditions": {
    "clients": {
      "include": ["0oa123abc456xyz"]
    }
  },
  "rules": [
    {
      "name": "Allow Client Credentials with Act",
      "status": "ACTIVE",
      "priority": 1,
      "conditions": {
        "grantTypes": {
          "include": ["client_credentials"]
        },
        "scopes": {
          "include": ["*"]
        }
      },
      "actions": {
        "token": {
          "accessTokenLifetimeMinutes": 60,
          "refreshTokenLifetimeMinutes": 0,
          "refreshTokenWindowMinutes": 10080
        }
      }
    }
  ]
}
```

---

## **Step 6: Assign Applications and Users**

In Okta, application assignments represent pre-approval.

### 6.1 Understanding Okta Assignments

**For Client Credentials Flow:**
- Agents don't have user context
- Assignment represents that the client (agent) is approved
- Human authorization validated at resource server

**Pre-Approval Model:**
1. Agent assigned to policy (Step 5.3) = Agent pre-approved
2. Human assigned to application (for governance) = Human tracked
3. Resource server validates both subjects independently

### 6.2 Verify Agent Assignment

1. Navigate to **Applications → Applications**
2. Click **Finance Agent**
3. Click **Assignments** tab

You should see the service client itself (no user assignments needed for client_credentials).

### 6.3 (Optional) Assign Human Users for Governance

While not required for token issuance, you can assign human users to the application for governance tracking.

1. In **Finance Agent** application
2. Click **Assignments** tab
3. Click **Assign → Assign to People**
4. Search for users (we'll create test user next)
5. Click **Assign** next to the user
6. Click **Save and Go Back**
7. Click **Done**

**Note:** This assignment is for governance only. The human's authorization is validated at the resource server, not by Okta during token issuance.

---

## **Step 7: Create Test User**

Create a test user representing the human principal.

### 7.1 Navigate to Users

1. Navigate to **Directory → People** (left sidebar)
2. Click **Add Person**

### 7.2 Configure User

**First name:** `Alice`  
**Last name:** `Smith`  
**Username:** `alice@corp.example.com`  
**Primary email:** `alice@corp.example.com`  
**Secondary email:** Leave empty  
**Groups:** Leave as default  
**Password:** `Set by admin`  
**Enter password:** `Test123!@#` (use secure password in production)  
**User must change password on first login:** Unchecked (for testing)

Click **Save**

### 7.3 Activate User

If the user is created in `Staged` status:
1. Click on the user
2. Click **Activate**
3. Confirm activation

### 7.4 (Optional) Assign User to Finance Agent

For governance tracking:
1. Navigate to **Applications → Applications → Finance Agent**
2. Click **Assignments** tab
3. Click **Assign → Assign to People**
4. Find `alice@corp.example.com`
5. Click **Assign**
6. Click **Save and Go Back**
7. Click **Done**

### Configuration Reference

```json
{
  "id": "00u123abc456xyz",
  "status": "ACTIVE",
  "profile": {
    "firstName": "Alice",
    "lastName": "Smith",
    "email": "alice@corp.example.com",
    "login": "alice@corp.example.com"
  },
  "credentials": {
    "password": {}
  }
}
```

---

## **Step 8: Test Configuration**

Test the complete flow by requesting a token with client assertion.

### 8.1 Gather Required Information

**Okta Domain:** `https://your-okta-domain`  
**Authorization Server ID:** `aus123abc456` (from Step 1.3)  
**Token Endpoint:** `https://your-okta-domain/oauth2/aus123abc456/v1/token`  
**Client ID:** (from Step 3.4)  
**Client Secret:** (from Step 3.4)  
**Scope:** `finance.read`

### 8.2 Create Client Assertion JWT

**Client Assertion Payload:**
```json
{
  "iss": "0oa123abc456xyz",
  "sub": "0oa123abc456xyz",
  "aud": "https://your-okta-domain/oauth2/aus123abc456",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "test-assertion-unique-123",
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

**Critical Values:**
- `iss`: Your client ID
- `sub`: Your client ID (same as iss)
- `aud`: Your authorization server URL (not the token endpoint!)
- `exp`: Current timestamp + 300 seconds
- `iat`: Current timestamp
- `jti`: Unique identifier (prevent replay)
- `act`: Human identity object

**Sign with Client Secret (HS256):**

**Using Python:**
```python
import jwt
import time

# Replace with your actual values
client_id = "0oa123abc456xyz"
client_secret = "YOUR_CLIENT_SECRET"
auth_server_id = "aus123abc456"
okta_domain = "https://dev-123456.okta.com"

payload = {
    "iss": client_id,
    "sub": client_id,
    "aud": f"{okta_domain}/oauth2/{auth_server_id}",
    "exp": int(time.time()) + 300,
    "iat": int(time.time()),
    "jti": f"assertion-{int(time.time())}",
    "act": {
        "sub": "alice@corp.example.com",
        "email": "alice@corp.example.com",
        "name": "Alice Smith"
    }
}

client_assertion = jwt.encode(payload, client_secret, algorithm="HS256")
print(f"Client Assertion:\n{client_assertion}")
```

**Using https://jwt.io:**
1. Go to https://jwt.io
2. Paste the payload above (update values)
3. Select algorithm: `HS256`
4. In "Verify Signature", paste your client secret
5. Copy the encoded JWT

### 8.3 Request Token

**Using curl:**
```bash
curl --request POST \
  --url 'https://your-okta-domain/oauth2/aus123abc456/v1/token' \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'scope=finance.read' \
  --data-urlencode 'client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer' \
  --data-urlencode "client_assertion=YOUR_SIGNED_JWT_HERE"
```

**Replace:**
- `your-okta-domain` with your actual domain
- `aus123abc456` with your auth server ID
- `YOUR_SIGNED_JWT_HERE` with the JWT from step 8.2

**Expected Response:**
```json
{
  "token_type": "Bearer",
  "expires_in": 3600,
  "access_token": "eyJraWQiOiJGSkE4...",
  "scope": "finance.read"
}
```

### 8.4 Decode and Verify Token

Copy the `access_token` and decode at https://jwt.io

**Expected Token Structure:**
```json
{
  "ver": 1,
  "jti": "AT.abc123xyz",
  "iss": "https://your-okta-domain/oauth2/aus123abc456",
  "aud": "https://api.example.com/finance",
  "iat": 1735686000,
  "exp": 1735689600,
  "cid": "0oa123abc456xyz",
  "scp": [
    "finance.read"
  ],
  "sub": "0oa123abc456xyz",
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
   - `sub`: Your client ID
   - `cid`: Your client ID (client ID claim)

2. **Human Identity:**
   - `act`: Object with human data
   - `act.sub`: `alice@corp.example.com`
   - `act.email`: `alice@corp.example.com`
   - `act.name`: `Alice Smith`

3. **Authorization:**
   - `scp`: Array containing `finance.read`
   - `aud`: Your API audience

4. **Issuer:**
   - `iss`: Your authorization server URL

**If all claims are present → Configuration successful! ✅**

### 8.6 Troubleshooting Token Request

**HTTP 401 Unauthorized:**
```
Possible causes:
1. Client secret incorrect
2. Client assertion signature invalid
3. Client assertion aud doesn't match auth server URL

Solutions:
- Verify client secret in Applications → Finance Agent → Credentials
- Check client assertion is signed with correct secret
- Ensure aud is: https://your-okta-domain/oauth2/aus123abc456
  NOT the token endpoint URL
```

**HTTP 400 Bad Request:**
```
Error: "The client assertion is invalid"

Causes:
1. Client assertion exp is expired
2. Client assertion iat is in the future
3. Client assertion iss doesn't match client_id

Solutions:
- Use current timestamp for iat
- Set exp to iat + 300 seconds
- Ensure iss and sub both equal client ID
```

**Token issued but missing `act` claim:**
```
Possible causes:
1. Custom claim not configured
2. Client assertion missing act
3. Claim expression incorrect

Solutions:
- Verify claim exists: Security → API → AGBAC-Min-AS → Claims
- Check claim value: clientAssertion.claims.act
- Decode client assertion at jwt.io - verify it has act claim
```

---

## **Step 9: Configure Resource Server Validation**

Your API/resource server must validate both subjects.

### 9.1 Token Validation Logic

**Pseudocode:**
```python
def validate_dual_subject_token(token, resource):
    # 1. Verify token signature
    decoded = verify_jwt_signature(token, okta_public_key)
    
    # 2. Validate standard claims
    validate_expiry(decoded['exp'])
    validate_issuer(decoded['iss'], expected_issuer)
    validate_audience(decoded['aud'], expected_audience)
    
    # 3. Extract subjects
    agent_id = decoded['sub']  # Client ID
    act_claim = decoded.get('act')
    
    if not act_claim:
        raise Unauthorized("Token missing human identity (act)")
    
    human_id = act_claim['sub']  # alice@corp.example.com
    
    # 4. Validate agent authorization
    agent_scopes = decoded.get('scp', [])
    if 'finance.read' not in agent_scopes:
        raise Forbidden("Agent not authorized for finance.read")
    
    # 5. Validate human authorization
    # Check against your user database or Okta API
    if not user_has_finance_access(human_id):
        raise Forbidden("Human not authorized for finance access")
    
    # 6. Log for audit
    audit_log(agent_id, human_id, resource, "ALLOWED")
    
    return True
```

### 9.2 Get Okta Public Key (JWKS)

**JWKS Endpoint:**
```
https://your-okta-domain/oauth2/aus123abc456/v1/keys
```

**Example Python Implementation:**
```python
import jwt
import requests
from functools import lru_cache

@lru_cache()
def get_okta_public_key(token):
    """Fetch Okta public key from JWKS endpoint."""
    # Decode header to get key ID
    header = jwt.get_unverified_header(token)
    kid = header['kid']
    
    # Fetch JWKS
    auth_server_id = "aus123abc456"  # Your auth server ID
    okta_domain = "https://your-okta-domain"
    jwks_url = f"{okta_domain}/oauth2/{auth_server_id}/v1/keys"
    
    response = requests.get(jwks_url)
    jwks = response.json()
    
    # Find matching key
    for key in jwks['keys']:
        if key['kid'] == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    
    raise ValueError(f"Public key not found for kid: {kid}")

def validate_agbac_token(token, resource):
    """Validate AGBAC dual-subject token from Okta."""
    try:
        # Get public key and verify
        public_key = get_okta_public_key(token)
        
        # Expected values
        auth_server_id = "aus123abc456"
        okta_domain = "https://your-okta-domain"
        expected_issuer = f"{okta_domain}/oauth2/{auth_server_id}"
        expected_audience = "https://api.example.com/finance"
        
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=expected_audience,
            issuer=expected_issuer
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
        
        # Validate agent scopes
        scopes = decoded.get('scp', [])
        if 'finance.read' not in scopes:
            return {
                'authorized': False,
                'reason': f'Agent {agent_id} lacks required scope'
            }
        
        # Validate human authorization
        if not user_has_finance_access(human_id):
            return {
                'authorized': False,
                'reason': f'Human {human_id} not authorized'
            }
        
        # Success
        return {
            'authorized': True,
            'agent': agent_id,
            'human': human_id
        }
        
    except jwt.ExpiredSignatureError:
        return {'authorized': False, 'reason': 'Token expired'}
    except jwt.InvalidAudienceError:
        return {'authorized': False, 'reason': 'Invalid audience'}
    except jwt.InvalidIssuerError:
        return {'authorized': False, 'reason': 'Invalid issuer'}
    except jwt.InvalidTokenError as e:
        return {'authorized': False, 'reason': f'Invalid token: {e}'}

def user_has_finance_access(email):
    """
    Validate human has finance access.
    Implement based on your system.
    """
    # Option 1: Query your database
    user = db.query(User).filter_by(email=email).first()
    return user and 'FinanceUser' in user.roles
    
    # Option 2: Query Okta Users API
    # (Requires Okta API token)
    # See Okta API documentation
```

### 9.3 Validate Human Using Okta API

If you manage users in Okta, you can query the Okta Users API:

```python
import requests

def get_okta_api_token():
    """
    Get Okta API token using API Services application.
    Create separate M2M app with Okta API scopes.
    """
    # This requires setting up Okta API Access Management
    # See: https://developer.okta.com/docs/guides/implement-oauth-for-okta/
    pass

def user_has_finance_access_okta(email):
    """Check if user exists in Okta and has appropriate groups."""
    okta_domain = "https://your-okta-domain"
    api_token = get_okta_api_token()
    
    # Search for user
    response = requests.get(
        f"{okta_domain}/api/v1/users",
        params={"filter": f'profile.email eq "{email}"'},
        headers={"Authorization": f"SSWS {api_token}"}
    )
    
    users = response.json()
    if not users:
        return False
    
    user_id = users[0]['id']
    
    # Check user's groups or app assignments
    response = requests.get(
        f"{okta_domain}/api/v1/users/{user_id}/groups",
        headers={"Authorization": f"SSWS {api_token}"}
    )
    
    groups = response.json()
    
    # Check if user in FinanceUsers group
    return any(group['profile']['name'] == 'FinanceUsers' for group in groups)
```

### 9.4 Audit Logging

Log every dual-subject access:

```python
import json
import logging
from datetime import datetime

def audit_log(agent_id, human_id, resource, result, reason=None):
    """Log dual-subject access for audit trail."""
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
```

**Example Log:**
```json
{
  "timestamp": "2026-01-02T15:30:45.123Z",
  "event_type": "AGBAC_ACCESS",
  "agent_identity": "0oa123abc456xyz",
  "human_identity": "alice@corp.example.com",
  "resource": "/api/finance/reports/Q4-2025",
  "result": "ALLOWED",
  "reason": null
}
```

---

## **Troubleshooting**

### Issue: Cannot Create Custom Authorization Server

**Symptom:**
"Authorization Servers" option not available or grayed out.

**Cause:**
Custom Authorization Servers require Okta Workforce Identity or Developer Edition.

**Solutions:**
1. **Use Okta Developer Account** (free):
   - Sign up at https://developer.okta.com/signup/
   - Provides custom authorization servers

2. **Use Default Authorization Server** (limited):
   - URL: `https://your-okta-domain/oauth2/default`
   - Limited customization options
   - Not recommended for production

3. **Contact Okta Sales:**
   - Upgrade to Workforce Identity

### Issue: Token Request Returns 401

**Error:** `invalid_client`

**Possible Causes:**
1. Client secret incorrect
2. Client assertion signature invalid
3. Client ID wrong

**Solutions:**
```bash
# Verify client credentials
# Applications → Finance Agent → General Settings
# Client ID should match iss/sub in assertion
# Regenerate secret if needed

# Check client assertion signature
# Decode at jwt.io
# Verify HS256 selected and secret correct

# Verify client_assertion_type parameter
# Must be: urn:ietf:params:oauth:client-assertion-type:jwt-bearer
```

### Issue: Token Request Returns 400

**Error:** `The client assertion is invalid`

**Possible Causes:**
1. Client assertion expired
2. Client assertion aud incorrect
3. Client assertion iss/sub mismatch

**Solutions:**
```bash
# Check timestamps
# iat should be current time
# exp should be iat + 300 seconds

# Verify aud claim
# Must match: https://your-okta-domain/oauth2/aus123abc456
# Common error: using token endpoint instead of auth server URL

# Verify iss and sub
# Both must equal client_id
```

### Issue: Token Missing `act` Claim

**Possible Causes:**
1. Custom claim not configured
2. Claim expression incorrect
3. Client assertion missing `act`

**Solutions:**
```bash
# Verify custom claim exists
# Security → API → AGBAC-Min-AS → Claims
# Should show: act with expression clientAssertion.claims.act

# Decode client assertion
# Use jwt.io
# Verify it contains act claim with proper structure

# Check claim conditions
# Ensure claim is set to "Any scope" or includes your scope
```

### Issue: `invalid_scope` Error

**Error:** `The requested scope is invalid, unknown, or malformed`

**Possible Causes:**
1. Scope doesn't exist in authorization server
2. Scope not assigned to client

**Solutions:**
```bash
# Verify scope exists
# Security → API → AGBAC-Min-AS → Scopes
# Should show: finance.read

# Check policy allows scope
# AGBAC-Min-AS → Access Policies → AGBAC-Min-Policy → Rule
# Scopes requested: Any scopes (or specifically finance.read)
```

### Issue: Token Validation Fails

**Error:** `Signature verification failed`

**Possible Causes:**
1. Using wrong public key
2. Token from different authorization server
3. Token expired

**Solutions:**
```python
# Verify JWKS endpoint
correct_jwks = f"https://{okta_domain}/oauth2/{auth_server_id}/v1/keys"

# Check token header for kid
header = jwt.get_unverified_header(token)
print(f"Key ID: {header['kid']}")

# Verify issuer matches
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"Issuer: {decoded['iss']}")
# Should be: https://your-okta-domain/oauth2/aus123abc456
```

---

## **Reference: Configuration Examples**

### Complete Configuration Summary

**Custom Authorization Server:**
```json
{
  "id": "aus123abc456",
  "name": "AGBAC-Min-AS",
  "audiences": ["https://api.example.com/finance"],
  "issuer": "https://your-okta-domain/oauth2/aus123abc456",
  "status": "ACTIVE"
}
```

**Scope:**
```json
{
  "name": "finance.read",
  "displayName": "Read Finance Data",
  "description": "Allows reading finance system data"
}
```

**Custom Claim:**
```json
{
  "name": "act",
  "claimType": "RESOURCE",
  "valueType": "EXPRESSION",
  "value": "clientAssertion.claims.act",
  "alwaysIncludeInToken": false
}
```

**Application:**
```json
{
  "name": "Finance Agent",
  "credentials": {
    "oauthClient": {
      "client_id": "0oa123abc456xyz",
      "token_endpoint_auth_method": "client_secret_post"
    }
  },
  "settings": {
    "oauthClient": {
      "grant_types": ["client_credentials"]
    }
  }
}
```

**Access Policy:**
```json
{
  "name": "AGBAC-Min-Policy",
  "conditions": {
    "clients": {
      "include": ["0oa123abc456xyz"]
    }
  },
  "rules": [
    {
      "name": "Allow Client Credentials with Act",
      "conditions": {
        "grantTypes": {
          "include": ["client_credentials"]
        }
      },
      "actions": {
        "token": {
          "accessTokenLifetimeMinutes": 60
        }
      }
    }
  ]
}
```

### Client Assertion JWT Example

```json
{
  "iss": "0oa123abc456xyz",
  "sub": "0oa123abc456xyz",
  "aud": "https://dev-123456.okta.com/oauth2/aus123abc456",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "unique-assertion-id-abc123",
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
  "ver": 1,
  "jti": "AT.abc123xyz789",
  "iss": "https://dev-123456.okta.com/oauth2/aus123abc456",
  "aud": "https://api.example.com/finance",
  "iat": 1735686000,
  "exp": 1735689600,
  "cid": "0oa123abc456xyz",
  "scp": [
    "finance.read"
  ],
  "sub": "0oa123abc456xyz",
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com",
    "name": "Alice Smith"
  }
}
```

---

## **Summary**

You've successfully configured Okta for AGBAC-Min dual-subject authorization!

**What You Configured:**
✅ Custom Authorization Server for dedicated OAuth endpoints  
✅ Scope representing finance system access  
✅ Agent application with client credentials grant  
✅ Custom claim to extract `act` from client assertion  
✅ Access policy controlling token issuance  
✅ Test user representing human principal  
✅ Tested token issuance with dual subjects  

**Key Components:**

1. **Custom Authorization Server** - Dedicated OAuth server
2. **Custom Claim** - Expression extracts `act` from client assertion
3. **Client Assertion** - JWT containing both agent and human identities
4. **Access Policy** - Controls which clients can get tokens
5. **Dual-Subject Token** - Contains `sub` (agent) and `act` (human)

**Next Steps:**
1. **Configure Python Application:** Follow Python Application/Agent Configuration Guide
2. **Implement Resource Server Validation:** Use code from Step 9
3. **Test End-to-End:** Run complete workflow with real agent
4. **Add More Agents/Users:** Create additional applications and users
5. **Production Hardening:** Enable MFA, rotate secrets, implement monitoring

**Security Reminders:**
- 🔒 Use HTTPS everywhere
- 🔒 Rotate client secrets regularly (Okta: Applications → Credentials)
- 🔒 Monitor Okta System Log for anomalies
- 🔒 Implement rate limiting at API layer
- 🔒 Audit all dual-subject access attempts

**Okta-Specific Notes:**
- Custom Authorization Servers provide isolation and customization
- Expression language limited but sufficient for `act` extraction
- System Log provides detailed audit trail
- Okta API enables programmatic user/group management
- Consider Okta Workflows for complex orchestration

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
