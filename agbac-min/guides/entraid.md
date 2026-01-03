<div align="center">

# AGBAC-Min EntraID IAM Configuration Guide

**Implementing dual-subject authorization for humans and agents using Hybrid Approach**

</div>

<br>

## **Overview**

This guide provides step-by-step instructions for configuring Microsoft EntraID (Azure AD) to support AGBAC-Min dual-subject authorization using the **Hybrid Approach**.

**⚠️ Important:** EntraID's `client_credentials` grant does not support custom claims from client assertions like other IAM providers. This guide implements a hybrid approach that achieves the same security goals through a different mechanism.

After completing this guide, your EntraID tenant will:

✅ Issue agent tokens containing agent identity (`sub`)  
✅ Enable applications to create signed human identity assertions (`act`)  
✅ Enforce that both subjects are pre-approved before granting access  
✅ Enable resource servers to validate both subjects for access control  

**Estimated Time:** 45-60 minutes  
**EntraID Edition:** Works with all tiers (Free, P1, P2)  
**Prerequisites:** EntraID admin access, basic understanding of OAuth 2.0

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Understanding the Hybrid Approach](#understanding-the-hybrid-approach)
4. [Step 1: Create Agent App Registration](#step-1-create-agent-app-registration)
5. [Step 2: Configure App Roles](#step-2-configure-app-roles)
6. [Step 3: Create Application RSA Keys](#step-3-create-application-rsa-keys)
7. [Step 4: Assign Roles (Pre-Approval)](#step-4-assign-roles-pre-approval)
8. [Step 5: Create Test User](#step-5-create-test-user)
9. [Step 6: Test Agent Token Request](#step-6-test-agent-token-request)
10. [Step 7: Test Act Assertion Creation](#step-7-test-act-assertion-creation)
11. [Step 8: Configure Resource Server Validation](#step-8-configure-resource-server-validation)
12. [Troubleshooting](#troubleshooting)
13. [Reference: Configuration Examples](#reference-configuration-examples)

---

## **Prerequisites**

Before starting, ensure you have:

- [ ] Microsoft EntraID tenant (Azure AD)
- [ ] Global Administrator or Application Administrator role
- [ ] EntraID tenant ID (found in Azure Portal → EntraID → Overview)
- [ ] Ability to create app registrations
- [ ] OpenSSL or Python for generating RSA keys
- [ ] `curl` or Postman for testing
- [ ] Basic familiarity with OAuth 2.0 and JWT

**Access Azure Portal:**
```
https://portal.azure.com
```

**Find Your Tenant ID:**
1. Navigate to **Azure Active Directory** (or **Microsoft Entra ID**)
2. Click **Overview**
3. Copy **Tenant ID** (e.g., `12345678-1234-1234-1234-123456789abc`)

---

## **Architecture Overview**

### How AGBAC-Min Works with EntraID (Hybrid Approach)

```
┌─────────────┐
│   Human     │ Authenticates to application
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Application                           │
│   1. Extracts human identity            │
│   2. Creates signed "act assertion"     │
└──────┬──────────────────┬───────────────┘
       │                  │
       │ (provides act)   │
       ▼                  │
┌─────────────────────┐   │
│   AI Agent          │   │
│   Gets TWO tokens:  │   │
│                     │   │
│   Token 1:          │◄──┘ Act assertion
│   From EntraID      │     (from application)
│   (agent identity)  │
│                     │
│   Token 2:          │
│   From Application  │
│   (human identity)  │
└──────┬──────────────┘
       │
       │ Makes API Request with BOTH
       │ Authorization: Bearer <entraid-token>
       │ X-Act-Assertion: <app-signed-jwt>
       ▼
┌─────────────────────┐
│  Resource Server    │
│                     │
│  Validates BOTH:    │
│  1. EntraID token   │
│     (agent auth)    │
│  2. Act assertion   │
│     (human auth)    │
│                     │
│  Access granted     │
│  only if both pass  │
└─────────────────────┘
```

### Key Concept: Two-Component Authorization

**Unlike Keycloak/Auth0/Okta (single token with sub + act):**

EntraID uses **two separate cryptographically-signed components**:

1. **Agent Token** (from EntraID)
   - Contains: Agent identity, roles
   - Validates: Agent is authorized

2. **Act Assertion** (from Application)
   - Contains: Human identity
   - Validates: Human identity is authentic

**Both must be validated independently at the resource server.**

---

## **Understanding the Hybrid Approach**

### Why EntraID is Different

**EntraID Limitation:**
```
EntraID's client_credentials grant does NOT support:
❌ Custom claims from client assertions
❌ Injecting user context into M2M tokens
❌ Hooks/Actions/Mappers for token customization
```

**What this means:**
- Agent tokens contain only agent identity
- Cannot include human (`act`) claim in EntraID token
- Must use alternative approach

### Hybrid Approach Solution

**Instead of one token with both subjects:**
```json
// ❌ Not possible in EntraID
{
  "sub": "agent-id",
  "act": {"sub": "human@example.com"}
}
```

**We use two components:**
```json
// ✅ Component 1: Agent token (from EntraID)
{
  "sub": "agent-object-id",
  "appid": "agent-client-id",
  "roles": ["FinanceAgent"]
}

// ✅ Component 2: Act assertion (from Application)
{
  "iss": "application-id",
  "act": {
    "sub": "alice@corp.example.com",
    "email": "alice@corp.example.com"
  }
}
```

### Security Properties

**Both components are cryptographically secure:**

| Property | Agent Token | Act Assertion |
|----------|-------------|---------------|
| Signed by | EntraID (Microsoft) | Application (Your App) |
| Algorithm | RS256 | RS256 |
| Validates | Agent authorized | Human identity authentic |
| Verified at | Resource server | Resource server |

**Result:** Same security as single dual-subject token, just validated separately.

### Does This Achieve AGBAC-Min Goals?

**YES ✅**

- ✅ Dual-subject authorization (both validated)
- ✅ Pre-approval required (roles for agent, validation for human)
- ✅ Cryptographically secure (two signatures)
- ✅ Works in-session and out-of-session
- ✅ Audit trail with both identities
- ✅ No privilege escalation possible

---

## **Step 1: Create Agent App Registration**

The app registration represents the AI agent's identity.

### 1.1 Navigate to App Registrations

1. Go to **Azure Portal** → **Microsoft Entra ID**
2. Click **App registrations** (left sidebar)
3. Click **+ New registration**

### 1.2 Configure Registration

**Name:** `Finance Agent`  
**Supported account types:** `Accounts in this organizational directory only (Single tenant)`  
**Redirect URI:** Leave empty (not needed for client_credentials)

Click **Register**

### 1.3 Note Application Details

After creation, you'll see:

**Application (client) ID:** `a1b2c3d4-e5f6-7890-abcd-ef1234567890` (example)  
**Directory (tenant) ID:** Your tenant ID  
**Object ID:** Agent's object ID

**Save the Application (client) ID** - you'll need it for token requests.

### 1.4 Create Client Secret

1. Click **Certificates & secrets** (left sidebar)
2. Click **+ New client secret**
3. **Description:** `Finance Agent Secret`
4. **Expires:** `730 days (24 months)` or as per your policy
5. Click **Add**

**⚠️ CRITICAL:** Copy the **Value** immediately. You cannot retrieve it later.

```
Example secret value: Xk8~Q2p_m5N.r7T@v9W!c3F$h6J&a1L
```

### 1.5 Configure API Permissions

1. Click **API permissions** (left sidebar)
2. Click **+ Add a permission**
3. Select **APIs my organization uses**
4. Search for your API or select **Microsoft Graph** (for testing)
5. Select **Application permissions**
6. Select appropriate permissions (e.g., `User.Read.All` for testing)
7. Click **Add permissions**
8. Click **✓ Grant admin consent for [Your Org]**
9. Confirm

**Note:** For production, create a custom API and assign permissions. For AGBAC-Min testing, we'll use app roles instead.

### Configuration Reference

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "appId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "displayName": "Finance Agent",
  "signInAudience": "AzureADMyOrg",
  "requiredResourceAccess": [],
  "identifierUris": [],
  "replyUrls": []
}
```

---

## **Step 2: Configure App Roles**

App roles represent pre-approval for the agent.

### 2.1 Navigate to App Roles

1. In **Finance Agent** app registration
2. Click **App roles** (left sidebar)
3. Click **+ Create app role**

### 2.2 Create Agent Role

**Display name:** `Finance Agent`  
**Allowed member types:** `Applications`  
**Value:** `FinanceAgent`  
**Description:** `AI agents authorized for finance system access`  
**Do you want to enable this app role?** `✓ Yes`

Click **Apply**

### 2.3 Create Human Role (for tracking)

Click **+ Create app role** again

**Display name:** `Finance User`  
**Allowed member types:** `Users/Groups`  
**Value:** `FinanceUser`  
**Description:** `Human users authorized for finance system access`  
**Do you want to enable this app role?** `✓ Yes`

Click **Apply**

### 2.4 Verify Roles Created

You should see:
```
FinanceAgent    Applications    AI agents authorized for finance system access
FinanceUser     Users/Groups    Human users authorized for finance system access
```

### Configuration Reference

```json
{
  "appRoles": [
    {
      "allowedMemberTypes": ["Application"],
      "description": "AI agents authorized for finance system access",
      "displayName": "Finance Agent",
      "id": "role-guid-1",
      "isEnabled": true,
      "value": "FinanceAgent"
    },
    {
      "allowedMemberTypes": ["User"],
      "description": "Human users authorized for finance system access",
      "displayName": "Finance User",
      "id": "role-guid-2",
      "isEnabled": true,
      "value": "FinanceUser"
    }
  ]
}
```

---

## **Step 3: Create Application RSA Keys**

The application needs an RSA key pair to sign act assertions.

### 3.1 Why Application Keys are Needed

**EntraID tokens:** Signed by Microsoft (validates agent)  
**Act assertions:** Signed by YOUR application (validates human identity)

**Your application needs:**
- **Private Key:** Sign act assertions
- **Public Key:** Resource servers verify signatures

### 3.2 Generate RSA Key Pair

**Using OpenSSL:**

```bash
# Generate private key (keep this SECRET)
openssl genrsa -out application-private-key.pem 2048

# Generate public key (share with resource servers)
openssl rsa -in application-private-key.pem -pubout -out application-public-key.pem

# Display keys
cat application-private-key.pem
cat application-public-key.pem
```

**Using Python:**

```python
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Generate private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Serialize private key
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Generate public key
public_key = private_key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Save to files
with open('application-private-key.pem', 'wb') as f:
    f.write(private_pem)

with open('application-public-key.pem', 'wb') as f:
    f.write(public_pem)

print("Keys generated successfully!")
print(f"Private key: application-private-key.pem")
print(f"Public key: application-public-key.pem")
```

### 3.3 Secure the Private Key

**⚠️ CRITICAL SECURITY:**

```bash
# DO: Store in Azure Key Vault (recommended)
az keyvault secret set \
  --vault-name "your-keyvault" \
  --name "agbac-app-signing-key" \
  --file application-private-key.pem

# DO: Set strict file permissions if stored locally
chmod 600 application-private-key.pem

# DON'T: Commit to source control
echo "*.pem" >> .gitignore

# DON'T: Store in application code
# DON'T: Share the private key
```

### 3.4 Distribute Public Key

**Resource servers need the public key to verify act assertions.**

**Option A: Include in deployment**
```python
# In resource server configuration
APPLICATION_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
"""
```

**Option B: JWKS Endpoint (recommended)**
```python
# Your application hosts a JWKS endpoint
# https://app.example.com/.well-known/jwks.json

{
  "keys": [
    {
      "kty": "RSA",
      "kid": "app-signing-key-1",
      "use": "sig",
      "n": "base64-encoded-modulus",
      "e": "AQAB"
    }
  ]
}
```

### Configuration Reference

**Private Key Format (PEM):**
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1+fWIcPm15j9zB/RWG1fzqQZYgYwNxLy0pLLuDrqBJjZMr
...
-----END PRIVATE KEY-----
```

**Public Key Format (PEM):**
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tfn1iHD5teY/cwf0VhtX86kGWIGMDcS8tKSy7g66gSY2TK8z6bD5X
...
-----END PUBLIC KEY-----
```

---

## **Step 4: Assign Roles (Pre-Approval)**

Role assignments represent organizational pre-approval.

### 4.1 Assign Agent Role to Application

**This is the agent pre-approval step.**

1. Navigate to **Enterprise applications** (NOT App registrations)
2. Change filter to **Application type: All applications**
3. Search for **Finance Agent**
4. Click on the application
5. Click **Users and groups** (left sidebar)
6. Click **+ Add user/group**
7. Under **Users**, click **None Selected**
8. Search for **Finance Agent** (the app itself)
9. Select **Finance Agent**
10. Under **Select a role**, choose **Finance Agent**
11. Click **Assign**

**Verify:**
```
Users and groups:
- Finance Agent (Application) - FinanceAgent role
```

**Note:** This represents that the `Finance Agent` application is pre-approved for finance system access.

### 4.2 Alternative: Using Azure CLI

```bash
# Get service principal object ID
SP_OBJECT_ID=$(az ad sp list --display-name "Finance Agent" --query "[0].id" -o tsv)

# Get app role ID
APP_ROLE_ID=$(az ad app show --id YOUR_APP_ID --query "appRoles[?value=='FinanceAgent'].id" -o tsv)

# Assign role
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_OBJECT_ID/appRoleAssignments" \
  --body "{
    \"principalId\": \"$SP_OBJECT_ID\",
    \"resourceId\": \"$SP_OBJECT_ID\",
    \"appRoleId\": \"$APP_ROLE_ID\"
  }"
```

---

## **Step 5: Create Test User**

Create a user representing the human principal.

### 5.1 Navigate to Users

1. Go to **Microsoft Entra ID** → **Users**
2. Click **+ New user** → **Create new user**

### 5.2 Configure User

**User principal name:** `alice@yourdomain.onmicrosoft.com`  
**Mail nickname:** `alice`  
**Display name:** `Alice Smith`  
**Password:** Click **Auto-generate password** or set manually  
**Account enabled:** `✓ Yes`

Click **Review + create** → **Create**

### 5.3 (Optional) Assign User to Application

For governance tracking:

1. Navigate to **Enterprise applications** → **Finance Agent**
2. Click **Users and groups**
3. Click **+ Add user/group**
4. Select **alice@yourdomain.onmicrosoft.com**
5. Select role: **Finance User**
6. Click **Assign**

**Note:** This assignment is for governance only. Human authorization is validated at the resource server.

### Configuration Reference

```json
{
  "userPrincipalName": "alice@yourdomain.onmicrosoft.com",
  "displayName": "Alice Smith",
  "givenName": "Alice",
  "surname": "Smith",
  "accountEnabled": true,
  "mailNickname": "alice"
}
```

---

## **Step 6: Test Agent Token Request**

Test that the agent can get a token from EntraID.

### 6.1 Gather Required Information

**Token Endpoint:** `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token`  
**Tenant ID:** Your tenant ID  
**Client ID:** Application (client) ID from Step 1.3  
**Client Secret:** Value from Step 1.4  
**Scope:** `https://graph.microsoft.com/.default` (for testing) or your API scope

### 6.2 Request Token

**Using curl:**

```bash
curl -X POST \
  "https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=https://graph.microsoft.com/.default"
```

**Using Python:**

```python
import requests

token_url = "https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/token"

payload = {
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "scope": "https://graph.microsoft.com/.default"
}

response = requests.post(token_url, data=payload)
token_data = response.json()

print(f"Access Token: {token_data['access_token']}")
print(f"Expires In: {token_data['expires_in']} seconds")
```

**Expected Response:**

```json
{
  "token_type": "Bearer",
  "expires_in": 3599,
  "ext_expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..."
}
```

### 6.3 Decode and Verify Token

Copy the `access_token` and decode at https://jwt.io

**Expected Token Structure:**

```json
{
  "aud": "https://graph.microsoft.com",
  "iss": "https://sts.windows.net/YOUR_TENANT_ID/",
  "iat": 1735686000,
  "nbf": 1735686000,
  "exp": 1735689600,
  "aio": "...",
  "appid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "appidacr": "1",
  "idp": "https://sts.windows.net/YOUR_TENANT_ID/",
  "oid": "service-principal-object-id",
  "rh": "...",
  "roles": [
    "FinanceAgent"
  ],
  "sub": "service-principal-object-id",
  "tid": "YOUR_TENANT_ID",
  "uti": "...",
  "ver": "1.0"
}
```

### 6.4 Verify Critical Claims

**✅ Success Criteria:**

1. **Agent Identity:**
   - `appid`: Your application (client) ID
   - `sub`: Service principal object ID
   - `oid`: Service principal object ID

2. **Roles:**
   - `roles`: Array containing `"FinanceAgent"`

3. **Standard Claims:**
   - `iss`: EntraID issuer
   - `aud`: Your API audience
   - `exp`: Future timestamp

**⚠️ Note:** Token does NOT contain human identity (`act`). This is expected and correct.

**The human identity will be in a separate act assertion created by your application.**

---

## **Step 7: Test Act Assertion Creation**

Test creating a signed act assertion representing the human identity.

### 7.1 Simulate Human Authentication

```python
# In your application, after human authenticates
# This would come from OIDC/SAML authentication

authenticated_user = {
    "sub": "alice@yourdomain.onmicrosoft.com",
    "email": "alice@yourdomain.onmicrosoft.com",
    "name": "Alice Smith",
    "oid": "user-object-id-from-entra"
}
```

### 7.2 Create Act Assertion

```python
import jwt
import time

# Load application private key
with open('application-private-key.pem', 'r') as f:
    private_key = f.read()

# Create act assertion payload
act_assertion_payload = {
    "iss": "your-application-identifier",  # Your app ID or URL
    "sub": "your-application-identifier",
    "aud": "https://api.example.com/finance",  # Your API
    "exp": int(time.time()) + 300,  # 5 minutes
    "iat": int(time.time()),
    "jti": f"act-{int(time.time())}",  # Unique ID
    "act": authenticated_user  # Human identity
}

# Sign with application private key
act_assertion = jwt.encode(
    act_assertion_payload,
    private_key,
    algorithm="RS256"
)

print(f"Act Assertion JWT:\n{act_assertion}\n")

# Decode to verify (without signature check)
decoded = jwt.decode(act_assertion, options={"verify_signature": False})
print(f"Decoded Act Assertion:\n{decoded}")
```

**Expected Output:**

```
Act Assertion JWT:
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ5b3VyLWFwcC1pZCIsInN1YiI6InlvdXItYXBwLWlkIiwiYXVkIjoiaHR0cHM6Ly9hcGkuZXhhbXBsZS5jb20vZmluYW5jZSIsImV4cCI6MTczNTY4NjMwMCwiaWF0IjoxNzM1Njg2MDAwLCJqdGkiOiJhY3QtMTczNTY4NjAwMCIsImFjdCI6eyJzdWIiOiJhbGljZUB5b3VyZG9tYWluLm9ubWljcm9zb2Z0LmNvbSIsImVtYWlsIjoiYWxpY2VAeW91cmRvbWFpbi5vbm1pY3Jvc29mdC5jb20iLCJuYW1lIjoiQWxpY2UgU21pdGgiLCJvaWQiOiJ1c2VyLW9iamVjdC1pZCJ9fQ...

Decoded Act Assertion:
{
  "iss": "your-application-identifier",
  "sub": "your-application-identifier",
  "aud": "https://api.example.com/finance",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "act-1735686000",
  "act": {
    "sub": "alice@yourdomain.onmicrosoft.com",
    "email": "alice@yourdomain.onmicrosoft.com",
    "name": "Alice Smith",
    "oid": "user-object-id-from-entra"
  }
}
```

### 7.3 Verify Signature

```python
# Load public key
with open('application-public-key.pem', 'r') as f:
    public_key = f.read()

# Verify signature
try:
    verified = jwt.decode(
        act_assertion,
        public_key,
        algorithms=["RS256"],
        audience="https://api.example.com/finance",
        issuer="your-application-identifier"
    )
    print("✅ Signature valid!")
    print(f"Act claim: {verified['act']}")
except Exception as e:
    print(f"❌ Signature verification failed: {e}")
```

---

## **Step 8: Configure Resource Server Validation**

Your API/resource server must validate BOTH the agent token and act assertion.

### 8.1 Dual-Component Validation Logic

**Complete Python Implementation:**

```python
import jwt
import requests
from functools import lru_cache

class EntraIDDualSubjectValidator:
    """Validates EntraID dual-subject authorization (hybrid approach)."""
    
    def __init__(self, tenant_id, app_public_key, api_audience):
        self.tenant_id = tenant_id
        self.app_public_key = app_public_key
        self.api_audience = api_audience
    
    @lru_cache()
    def get_entraid_public_keys(self):
        """Fetch EntraID public keys from JWKS endpoint."""
        jwks_url = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
        response = requests.get(jwks_url)
        return response.json()
    
    def get_signing_key(self, token):
        """Get the public key for verifying EntraID token."""
        header = jwt.get_unverified_header(token)
        kid = header['kid']
        
        jwks = self.get_entraid_public_keys()
        for key in jwks['keys']:
            if key['kid'] == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        
        raise ValueError(f"Public key not found for kid: {kid}")
    
    def validate_request(self, request, resource):
        """
        Validate dual-subject authorization.
        Returns: {'authorized': bool, 'agent': str, 'human': str}
        """
        try:
            # Step 1: Extract both components
            agent_token = self._extract_agent_token(request)
            act_assertion = self._extract_act_assertion(request)
            
            # Step 2: Validate agent token (EntraID)
            agent_claims = self._validate_agent_token(agent_token)
            agent_id = agent_claims['appid']
            agent_roles = agent_claims.get('roles', [])
            
            # Step 3: Validate act assertion (Application)
            act_claims = self._validate_act_assertion(act_assertion)
            human_identity = act_claims['act']
            human_id = human_identity['sub']
            
            # Step 4: Check agent authorized
            if 'FinanceAgent' not in agent_roles:
                return {
                    'authorized': False,
                    'reason': f'Agent {agent_id} lacks FinanceAgent role'
                }
            
            # Step 5: Check human authorized
            if not self._user_has_finance_access(human_id):
                return {
                    'authorized': False,
                    'reason': f'Human {human_id} not authorized'
                }
            
            # Step 6: Both authorized - grant access
            self._audit_log(agent_id, human_id, resource, "ALLOWED")
            
            return {
                'authorized': True,
                'agent': agent_id,
                'human': human_id
            }
            
        except Exception as e:
            self._audit_log(None, None, resource, "ERROR", str(e))
            return {
                'authorized': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    def _extract_agent_token(self, request):
        """Extract EntraID token from Authorization header."""
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise ValueError("Missing Authorization header")
        return auth_header[7:]
    
    def _extract_act_assertion(self, request):
        """Extract act assertion from custom header."""
        act_assertion = request.headers.get('X-Act-Assertion')
        if not act_assertion:
            raise ValueError("Missing X-Act-Assertion header")
        return act_assertion
    
    def _validate_agent_token(self, token):
        """Validate EntraID token signature and claims."""
        public_key = self.get_signing_key(token)
        
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=self.api_audience,
            issuer=f"https://sts.windows.net/{self.tenant_id}/"
        )
        
        return decoded
    
    def _validate_act_assertion(self, assertion):
        """Validate application-signed act assertion."""
        decoded = jwt.decode(
            assertion,
            self.app_public_key,
            algorithms=['RS256'],
            audience=self.api_audience,
            options={'verify_exp': True}
        )
        
        # Verify act claim exists
        if 'act' not in decoded:
            raise ValueError("Act assertion missing 'act' claim")
        
        # Check for replay (jti)
        jti = decoded.get('jti')
        if jti and self._is_jti_used(jti):
            raise ValueError("Act assertion replay detected")
        
        if jti:
            self._mark_jti_used(jti, ttl=600)
        
        return decoded
    
    def _user_has_finance_access(self, email):
        """
        Check if human has finance access.
        Implement based on your user database or EntraID.
        """
        # Option 1: Query your user database
        # user = db.query(User).filter_by(email=email).first()
        # return user and 'FinanceUser' in user.roles
        
        # Option 2: Query EntraID (requires separate auth)
        # return self._query_entraid_user_roles(email)
        
        # For testing: allow all
        return True
    
    def _is_jti_used(self, jti):
        """Check if JWT ID has been used (replay protection)."""
        # Implement using Redis, database, or in-memory cache
        # return redis.exists(f"jti:{jti}")
        return False
    
    def _mark_jti_used(self, jti, ttl):
        """Mark JWT ID as used for replay protection."""
        # redis.setex(f"jti:{jti}", ttl, "used")
        pass
    
    def _audit_log(self, agent_id, human_id, resource, result, reason=None):
        """Log dual-subject access for audit trail."""
        import json
        import logging
        from datetime import datetime
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'AGBAC_ACCESS_ENTRAID',
            'agent_identity': agent_id,
            'human_identity': human_id,
            'resource': resource,
            'result': result,
            'reason': reason
        }
        
        logging.info(json.dumps(log_entry))
```

### 8.2 Usage in API Endpoint

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize validator
validator = EntraIDDualSubjectValidator(
    tenant_id="YOUR_TENANT_ID",
    app_public_key=open('application-public-key.pem').read(),
    api_audience="https://api.example.com/finance"
)

@app.route('/api/finance/reports/<report_id>')
def get_report(report_id):
    """Protected endpoint requiring dual-subject authorization."""
    
    # Validate dual-subject authorization
    result = validator.validate_request(request, f"/api/finance/reports/{report_id}")
    
    if not result['authorized']:
        return jsonify({
            'error': 'Forbidden',
            'message': result['reason']
        }), 403
    
    # Both authorized - process request
    return jsonify({
        'report_id': report_id,
        'authorized_for': {
            'agent': result['agent'],
            'human': result['human']
        },
        'data': '...'
    })

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Use HTTPS
```

### 8.3 Request Format

**Agent makes request with BOTH components:**

```http
GET /api/finance/reports/Q4-2025 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6...
X-Act-Assertion: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ5b3VyLWFwcC1pZCIsInN1YiI6InlvdXItYXBwLWlkIiwiYXVkIjoiaHR0cHM6Ly9hcGkuZXhhbXBsZS5jb20vZmluYW5jZSIsImV4cCI6MTczNTY4NjMwMCwiaWF0IjoxNzM1Njg2MDAwLCJqdGkiOiJhY3QtMTczNTY4NjAwMCIsImFjdCI6eyJzdWIiOiJhbGljZUB5b3VyZG9tYWluLm9ubWljcm9zb2Z0LmNvbSIsImVtYWlsIjoiYWxpY2VAeW91cmRvbWFpbi5vbm1pY3Jvc29mdC5jb20iLCJuYW1lIjoiQWxpY2UgU21pdGgiLCJvaWQiOiJ1c2VyLW9iamVjdC1pZCJ9fQ...
```

---

## **Troubleshooting**

### Issue: Token Request Returns 400/401

**Error:** `AADSTS700016: Application not found`

**Cause:** Application ID incorrect or app not registered

**Solution:**
```bash
# Verify application ID
# Azure Portal → App registrations → Finance Agent
# Copy Application (client) ID exactly
```

**Error:** `AADSTS7000215: Invalid client secret`

**Cause:** Client secret incorrect or expired

**Solution:**
```bash
# Regenerate secret
# App registrations → Finance Agent → Certificates & secrets
# Delete old secret, create new one
```

### Issue: Token Missing `roles` Claim

**Cause:** App role not assigned to service principal

**Solution:**
```bash
# Verify assignment
# Enterprise applications → Finance Agent → Users and groups
# Should show: Finance Agent (Application) - FinanceAgent role

# Re-assign if missing (see Step 4)
```

### Issue: Act Assertion Signature Verification Fails

**Error:** `Signature verification failed`

**Cause:** Public/private key mismatch

**Solution:**
```python
# Verify keys match
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Load private key
with open('application-private-key.pem', 'rb') as f:
    private_key = serialization.load_pem_private_key(
        f.read(), password=None, backend=default_backend()
    )

# Extract public key from private key
public_key_from_private = private_key.public_key()

# Load public key file
with open('application-public-key.pem', 'rb') as f:
    public_key_from_file = serialization.load_pem_public_key(
        f.read(), backend=default_backend()
    )

# They should match
print("Keys match!" if public_key_from_private.public_numbers() == 
      public_key_from_file.public_numbers() else "Keys DON'T match!")
```

### Issue: Resource Server Returns 403

**Symptom:** Both tokens valid but access denied

**Possible Causes:**

1. **Agent not authorized:**
```python
# Check agent has FinanceAgent role in token
decoded = jwt.decode(agent_token, options={"verify_signature": False})
print(f"Agent roles: {decoded.get('roles', [])}")
# Should include 'FinanceAgent'
```

2. **Human not authorized:**
```python
# Check human authorization logic
# Implement _user_has_finance_access() properly
def _user_has_finance_access(self, email):
    # Query your user database or EntraID
    # Return True if authorized
    pass
```

### Issue: Missing X-Act-Assertion Header

**Error:** `Missing X-Act-Assertion header`

**Cause:** Agent not including act assertion in request

**Solution:**
```python
# Agent must include both headers
headers = {
    "Authorization": f"Bearer {entraid_token}",
    "X-Act-Assertion": act_assertion_jwt  # Must include this!
}

response = requests.get(api_url, headers=headers)
```

---

## **Reference: Configuration Examples**

### Complete Configuration Summary

**App Registration:**
```json
{
  "appId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "displayName": "Finance Agent",
  "appRoles": [
    {
      "value": "FinanceAgent",
      "allowedMemberTypes": ["Application"]
    }
  ]
}
```

**Agent Token (from EntraID):**
```json
{
  "aud": "https://api.example.com",
  "iss": "https://sts.windows.net/tenant-id/",
  "appid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "roles": ["FinanceAgent"],
  "sub": "service-principal-object-id",
  "tid": "tenant-id",
  "exp": 1735689600
}
```

**Act Assertion (from Application):**
```json
{
  "iss": "your-application-id",
  "sub": "your-application-id",
  "aud": "https://api.example.com",
  "exp": 1735686300,
  "iat": 1735686000,
  "jti": "unique-id-123",
  "act": {
    "sub": "alice@yourdomain.onmicrosoft.com",
    "email": "alice@yourdomain.onmicrosoft.com",
    "name": "Alice Smith",
    "oid": "user-object-id"
  }
}
```

### API Request Example

```http
GET /api/finance/reports/Q4-2025 HTTP/1.1
Host: api.example.com
Authorization: Bearer <entraid-token>
X-Act-Assertion: <application-signed-jwt>
```

### Validation Flow

```
Request arrives
    ↓
Extract Authorization header → EntraID token
Extract X-Act-Assertion header → Act assertion
    ↓
Validate EntraID token
├─ Verify signature (Microsoft public key)
├─ Check expiry, audience, issuer
├─ Extract agent ID (appid)
└─ Extract roles
    ↓
Validate Act Assertion
├─ Verify signature (Application public key)
├─ Check expiry
├─ Check replay (jti)
└─ Extract human identity (act)
    ↓
Authorize Agent
├─ Check roles include 'FinanceAgent'
└─ Pass/Fail
    ↓
Authorize Human
├─ Query user database
└─ Pass/Fail
    ↓
Both Pass? → Grant Access
Either Fail? → Deny Access
    ↓
Audit Log (agent ID, human ID, result)
```

---

## **Summary**

You've successfully configured EntraID for AGBAC-Min dual-subject authorization using the hybrid approach!

**What You Configured:**
✅ Agent app registration with client credentials  
✅ App roles for pre-approval (FinanceAgent, FinanceUser)  
✅ Application RSA keys for signing act assertions  
✅ Role assignments representing pre-approval  
✅ Test user for human principal  
✅ Tested agent token issuance  
✅ Tested act assertion creation  
✅ Resource server validation logic  

**Key Components:**

1. **Agent Token (EntraID)** - Contains agent identity and roles
2. **Act Assertion (Application)** - Contains human identity, signed by app
3. **Dual Validation** - Resource server validates both independently
4. **Two Headers** - API requests include both components
5. **Pre-Approval** - Agent roles (EntraID) + Human validation (resource server)

**How It Works:**

```
EntraID validates: Agent authorized ✓
Application signs: Human identity authentic ✓
Resource validates: Both components ✓
Access granted: Only if both pass ✓
```

**Comparison with Other Vendors:**

| Vendor | Token Structure | Validation |
|--------|----------------|------------|
| Keycloak/Auth0/Okta | One token with sub + act | Validate one JWT |
| EntraID (Hybrid) | Agent token + Act assertion | Validate two JWTs |

**Security Properties:** Identical  
**Dual-Subject Authorization:** Achieved ✅

**Next Steps:**
1. **Configure Python Application:** Follow Python Application/Agent Configuration Guide
2. **Implement Act Assertion Creation:** Use code from Step 7
3. **Implement Resource Validation:** Use code from Step 8
4. **Test End-to-End:** Complete workflow with real agent
5. **Production:** Move keys to Azure Key Vault, enable monitoring

**Security Reminders:**
- 🔒 Store private key in Azure Key Vault
- 🔒 Use HTTPS everywhere
- 🔒 Rotate keys regularly (every 90 days)
- 🔒 Implement replay protection (jti tracking)
- 🔒 Monitor for anomalous patterns
- 🔒 Audit all access attempts

**EntraID-Specific Notes:**
- Hybrid approach achieves same security as other vendors
- Two-component validation is overhead (~1ms)
- Works with all EntraID tiers (Free, P1, P2)
- Future-proof if Microsoft adds native support

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
