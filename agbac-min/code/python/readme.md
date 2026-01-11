<div align="center">

# AGBAC-Min Application/Agent Configuration Guide

**Python Implementation Guide for Dual-Subject Authorization**

</div>

<br>

## **Overview**

This guide provides step-by-step instructions for implementing AGBAC-Min dual-subject authorization in your Python applications and AI agents using the provided codebase.

After completing this guide, your application and agents will:

✅ Extract human identity from authenticated sessions  
✅ Request dual-subject tokens from IAM providers (Keycloak, Auth0, Okta, EntraID)  
✅ Make authenticated API calls with both agent and human authorization  
✅ Work in both in-session and out-of-session scenarios  
✅ Switch between IAM vendors by changing one configuration variable  

**Estimated Time:** 60-90 minutes  
**Prerequisites:** Python 3.9+, IAM provider configured (see IAM Configuration Guides)  
**Skill Level:** Intermediate Python developer

<br>

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step 1: Install Dependencies](#step-1-install-dependencies)
4. [Step 2: Configure Environment Variables](#step-2-configure-environment-variables)
5. [Step 3: Implement Human Identity Extraction](#step-3-implement-human-identity-extraction)
6. [Step 4: Implement In-Session Agent](#step-4-implement-in-session-agent)
7. [Step 5: Test In-Session Flow](#step-5-test-in-session-flow)
8. [Step 6: Implement Out-of-Session Agent](#step-6-implement-out-of-session-agent)
9. [Step 7: Test Out-of-Session Flow](#step-7-test-out-of-session-flow)
10. [Step 8: Implement API Calls](#step-8-implement-api-calls)
11. [Step 9: Production Deployment](#step-9-production-deployment)
12. [Troubleshooting](#troubleshooting)
13. [Reference: Complete Examples](#reference-complete-examples)

<br>

## **Prerequisites**

Before starting, ensure you have:

### **IAM Configuration**
- [ ] IAM provider configured (choose one):
  - [ ] Keycloak (see [Keycloak IAM Configuration Guide](./keycloak_iam_guide.md))
  - [ ] Auth0 (see [Auth0 IAM Configuration Guide](./auth0_iam_guide.md))
  - [ ] Okta (see [Okta IAM Configuration Guide](./okta_iam_guide.md))
  - [ ] EntraID (see [EntraID IAM Configuration Guide](./entraid_iam_guide.md))

### **Technical Requirements**
- [ ] Python 3.9 or higher installed
- [ ] pip package manager
- [ ] Text editor or IDE (VS Code, PyCharm, etc.)
- [ ] Terminal/command line access

### **IAM Credentials**
- [ ] Agent client ID (from IAM configuration)
- [ ] Agent client secret (from IAM configuration)
- [ ] Token endpoint URL (from IAM configuration)
- [ ] API audience/scope (from IAM configuration)

### **For Out-of-Session Scenarios**
- [ ] RSA key pair generated (application signing keys)
- [ ] Agent endpoint URL (where agent is hosted)

<br>

## **Architecture Overview**

### **In-Session Flow**

```
┌──────────────────┐
│  Web Application │
│                  │
│  1. User logs in │
│  2. Session      │
│     created      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  HybridSender    │
│  (extracts act)  │
└────────┬─────────┘
         │ (in-memory)
         ▼
┌──────────────────┐
│  In-Session      │
│  Agent           │
│                  │
│  3. Gets act     │
│  4. Requests     │
│     token        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  IAM Adapter     │
│  (Keycloak/      │
│   Auth0/Okta/    │
│   EntraID)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  IAM Provider    │
│                  │
│  5. Issues token │
│     with sub+act │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  API Client      │
│                  │
│  6. Calls API    │
│     with token   │
└──────────────────┘
```

### **Out-of-Session Flow**

```
┌──────────────────┐
│  Web Application │
│                  │
│  1. User logs in │
│  2. Session      │
│     created      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  HybridSender    │
│  (creates signed │
│   act JWT)       │
└────────┬─────────┘
         │ (HTTPS)
         ▼
┌──────────────────┐
│  Out-of-Session  │
│  Agent (remote)  │
│                  │
│  3. Receives JWT │
│  4. Verifies JWT │
│  5. Requests     │
│     token        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  IAM Provider    │
│                  │
│  6. Issues token │
│     with sub+act │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  API Client      │
│                  │
│  7. Calls API    │
│     with token   │
└──────────────────┘
```

<br>

## **Step 1: Install Dependencies**

### 1.1 Download AGBAC-Min Codebase

Place the AGBAC-Min Python files in your project directory:

```
your-project/
├── adapters/
│   ├── __init__.py
│   ├── base_adapter.py
│   ├── keycloak_adapter.py
│   ├── auth0_adapter.py
│   ├── okta_adapter.py
│   └── entraid_adapter.py
├── sender/
│   ├── __init__.py
│   └── hybrid_sender.py
├── phase1/
│   ├── in_session_token_request.py
│   └── in_session_api_call.py
├── phase2/
│   ├── out_of_session_token_request.py
│   └── out_of_session_api_call.py
└── requirements.txt
```

### 1.2 Install Required Python Packages

```bash
cd your-project
pip install --break-system-packages -r requirements.txt
```

**Core dependencies installed:**
- `pyjwt[crypto]>=2.8.0` - JWT operations with RS256/HS256
- `requests>=2.31.0` - HTTP client
- `cryptography>=41.0.0` - Cryptographic operations

### 1.3 Verify Installation

```bash
python3 -c "import jwt, requests, cryptography; print('✅ Dependencies installed successfully')"
```

**Expected output:**
```
✅ Dependencies installed successfully
```

<br>

## **Step 2: Configure Environment Variables (Non-Prod)**

### 2.1 Create Environment File

Create a `.env` file in your project root:

```bash
touch .env
```

**⚠️ Security:** Add `.env` to `.gitignore` to prevent committing secrets:

```bash
echo ".env" >> .gitignore
```

### 2.2 Configure for Your IAM Vendor

**Choose your IAM provider and configure accordingly:**

#### **Option A: Keycloak**

```bash
# Vendor Selection
AGBAC_VENDOR=keycloak

# Keycloak Configuration
KEYCLOAK_TOKEN_URL=https://your-keycloak-domain/realms/agbac-min/protocol/openid-connect/token
AGENT_CLIENT_ID=finance-agent
AGENT_CLIENT_SECRET=your-client-secret-from-keycloak

# API Configuration
API_URL=https://api.example.com/finance/report
```

#### **Option B: Auth0**

```bash
# Vendor Selection
AGBAC_VENDOR=auth0

# Auth0 Configuration
AUTH0_TOKEN_URL=https://your-tenant.auth0.com/oauth/token
AGENT_CLIENT_ID=your-m2m-app-client-id
AGENT_CLIENT_SECRET=your-client-secret-from-auth0
API_AUDIENCE=https://api.example.com

# API Configuration
API_URL=https://api.example.com/finance/report
```

#### **Option C: Okta**

```bash
# Vendor Selection
AGBAC_VENDOR=okta

# Okta Configuration
OKTA_TOKEN_URL=https://dev-123.okta.com/oauth2/aus123abc/v1/token
AGENT_CLIENT_ID=your-service-app-client-id
AGENT_CLIENT_SECRET=your-client-secret-from-okta
API_AUDIENCE=https://api.example.com

# API Configuration
API_URL=https://api.example.com/finance/report
```

#### **Option D: EntraID**

```bash
# Vendor Selection
AGBAC_VENDOR=entraid

# EntraID Configuration
ENTRAID_TOKEN_URL=https://login.microsoftonline.com/your-tenant-id/oauth2/v2.0/token
ENTRAID_TENANT_ID=your-tenant-id
AGENT_CLIENT_ID=your-app-registration-id
AGENT_CLIENT_SECRET=your-client-secret-from-entraid
API_AUDIENCE=https://api.example.com/.default

# EntraID Hybrid Approach Keys
APP_PRIVATE_KEY_PEM="-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
...
-----END PRIVATE KEY-----"

APP_IDENTIFIER=agbac-application

# API Configuration
API_URL=https://api.example.com/finance/report
```

### 2.3 Load Environment Variables (Optional)

`agbac_config.py` is a **utility module** that helps developers load AGBAC-Min configuration from environment variables.


1. ✅ **agbac_config.py is a library module, not a script**
   - Import it in your application
   - Call `get_config()` to load configuration
   
2. ✅ **Environment variables must be set before running your app**
   - In shell: `export AGBAC_VENDOR=keycloak`
   - In Docker: Environment section
   - In Kubernetes: ConfigMap/Secret
   
3. ✅ **Use the returned config dictionary to create adapters**
   - `config = get_config()`
   - `adapter = KeycloakAdapter(config)`
   
4. ✅ **Handle ConfigurationError**
   - Catch it at application startup
   - Log the error
   - Exit gracefully


#### **Step 1: Set Environment Variables**

Before running your application, set the required environment variables:

```bash
# Choose vendor
export AGBAC_VENDOR=keycloak

# Common configuration (all vendors)
export AGENT_CLIENT_ID=finance-agent
export AGENT_CLIENT_SECRET=my-secret-123

# Vendor-specific configuration
export KEYCLOAK_TOKEN_URL=https://keycloak.example.com/realms/prod/protocol/openid-connect/token
```

#### **Step 2: Import and Use in Your Application**

In your Python application code:

```python
# your_app.py
from agbac_config import get_config, ConfigurationError
from adapters import KeycloakAdapter
from sender import HybridSender, UserSession
from phase1.in_session_token_request import InSessionTokenRequest
import sys

def main():
    # Load configuration from environment variables
    try:
        config = get_config()
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create adapter with config
    adapter = KeycloakAdapter(config)
    
    # Extract user identity
    session = UserSession(
        user_email="alice@corp.example.com",
        user_name="Alice Smith",
        user_id="f1234567-89ab-cdef-0123-456789abcdef"
    )
    
    sender = HybridSender()
    act = sender.extract_act_from_session(session)
    
    # Request token
    token_request = InSessionTokenRequest(adapter)
    token_response = token_request.request_token(
        agent_id=config['client_id'],
        act=act,
        scope=['finance.read']
    )
    
    # Use token to call API
    print(f"Got token! Expires in {token_response.expires_in} seconds")

if __name__ == '__main__':
    main()
```

#### **Step 3: Run Your Application**

```bash
python your_app.py
```

<br>

#### **Usage Pattern 1: Simple Usage (Recommended)**

```python
from agbac_config import get_config, ConfigurationError

# Auto-detects vendor from AGBAC_VENDOR env var
config = get_config()
```

#### **Usage Pattern 2: Explicit Vendor**

```python
from agbac_config import get_config

# Override vendor (ignores AGBAC_VENDOR env var)
config = get_config(vendor='auth0')
```

#### **Usage Pattern 3: With Error Handling (nice!)**

```python
from agbac_config import get_config, ConfigurationError
import logging
import sys

logger = logging.getLogger(__name__)

try:
    config = get_config()
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)
```

<br>

#### What Gets Returned

`get_config()` returns a **dictionary** containing all configuration needed by adapters:

#### **Keycloak:**
```python
{
    'token_url': 'https://keycloak.example.com/realms/prod/protocol/openid-connect/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'audience': None  # Auto-derived
}
```

#### **Auth0:**
```python
{
    'token_url': 'https://tenant.auth0.com/oauth/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'audience': 'https://api.example.com'
}
```

#### **Okta:**
```python
{
    'token_url': 'https://dev-123.okta.com/oauth2/aus123/v1/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'audience': 'https://api.example.com'
}
```

#### **EntraID:**
```python
{
    'token_url': 'https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token',
    'client_id': 'finance-agent',
    'client_secret': 'my-secret-123',
    'scope': 'https://api.example.com/.default',
    'app_private_key_path': '/keys/app_private_key.pem',
    'app_id': 'https://app.example.com',
    'act_audience': 'https://api.example.com'
}
```

⚠️ **Security Note:** For production use proper secrets management (AWS Secrets Manager, GCP Secrets Manager, Azure Key Vault, etc.)

<br>

## **Step 3: Implement Human Identity Extraction**

### 3.1 Understanding Human Identity Extraction

The **HybridSender** extracts human identity from your application's authenticated session and formats it for AGBAC-Min.

**What it does:**
1. Takes authenticated user data from your session
2. Formats it as an "act" claim
3. Prepares it for transmission to agents (in-memory or over network)

### 3.2 Create HybridSender Instance

```python
from sender import HybridSender

# For in-session scenarios (no keys needed)
sender = HybridSender()

# For out-of-session scenarios (requires signing keys)
sender = HybridSender(
    private_key_pem=os.environ['APP_PRIVATE_KEY_PEM'],
    app_identifier='agbac-application'
)
```

### 3.3 Extract Act from Your Session

**Example 1: From Flask Session**

```python
from flask import session
from sender import UserSession, HybridSender

# After user authenticates via OIDC/SAML/etc.
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    # Create UserSession from Flask session
    user_session = UserSession(
        user_email=session['user']['email'],
        user_name=session['user']['name'],
        user_id=session['user'].get('id')
    )
    
    # Extract act claim
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # act is now ready to pass to agent
    # {'sub': 'alice@corp.example.com', 'email': '...', 'name': '...'}
```

**Example 2: From Django Session**

```python
from django.contrib.auth.decorators import login_required
from sender import UserSession, HybridSender

@login_required
def dashboard(request):
    # Create UserSession from Django user
    user_session = UserSession(
        user_email=request.user.email,
        user_name=request.user.get_full_name(),
        user_id=str(request.user.id)
    )
    
    # Extract act claim
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
```



### 3.3.1 Best Practice: Extract from OIDC Token

The recommended approach is to extract user information directly from the OIDC ID token:

```python
from flask import session
from sender import UserSession, HybridSender
import jwt

@app.route('/dashboard')
def dashboard():
    if 'id_token' not in session:
        return redirect('/login')
    
    # Decode OIDC ID token (signature already verified during login)
    id_token = session['id_token']
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    
    # Extract IAM user identifier from token
    user_id = decoded['sub']  # IAM user ID (NOT email!)
    user_email = decoded.get('email', decoded.get('preferred_username'))
    user_name = decoded.get('name', '')
    
    # For EntraID, also extract object ID
    user_oid = decoded.get('oid')  # EntraID only
    
    # Create UserSession with IAM identifier
    user_session = UserSession(
        user_email=user_email,
        user_name=user_name,
        user_id=user_id  # This is the IAM user ID from OIDC token
    )
    
    # Extract act claim
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # act.sub will now contain the IAM user ID (pseudonymous)
    # Example for Keycloak: 'f1234567-89ab-cdef-0123-456789abcdef'
    # Example for Auth0: 'auth0|63f1234567890abcdef12345'
    # Example for Okta: '00u123abc456xyz'
```

**Why extract from OIDC token?**
- Token's `sub` claim contains the IAM user ID
- Verified by IAM provider during authentication
- Consistent across all sessions
- No manual mapping needed

**Vendor-Specific OIDC Token Claims:**

| Vendor | sub claim | Additional Claims | Notes |
|--------|-----------|-------------------|-------|
| Keycloak | User ID (UUID) | `preferred_username`, `email`, `name` | sub is always user ID |
| Auth0 | User ID | `email`, `name`, `nickname` | Includes provider prefix |
| Okta | User ID | `preferred_username`, `email`, `name` | Starts with `00u` |
| EntraID | User UPN | `oid` (Object ID), `email`, `name` | **Both sub and oid needed** |


**Example 3: Alternative - Using Helper Function for OIDC**

```python
from sender import create_act_from_oidc_token
import jwt

# After OIDC authentication
id_token = request.session.get('id_token')
decoded_token = jwt.decode(id_token, options={"verify_signature": False})

# Extract act from OIDC token
act = create_act_from_oidc_token(decoded_token)
```

**Example 4: From SAML Assertion**

```python
from sender import create_act_from_saml_assertion

# After SAML authentication
saml_attributes = {
    'email': ['alice@corp.example.com'],
    'displayName': ['Alice Smith'],
    'uid': ['alice123']
}

# Extract act from SAML
act = create_act_from_saml_assertion(saml_attributes)
```

### 3.4 Verify Act Format

The `act` should be a dictionary containing the human identity:

```python
{
    'sub': 'keycloak-user-id',           # Required: IAM user identifier (see note below)
    'email': 'alice@corp.example.com',   # Recommended: For display
    'name': 'Alice Smith',               # Recommended: For display
    'oid': 'entraid-object-id'          # Required for EntraID: Object ID
}
```

⚠️ **Security Note:** CRITICAL: act.sub Should Contain IAM User Identifier not PII

The `act.sub` field should contain the user's **IAM user identifier**, not their email address:

| IAM Provider | act.sub Value | Example | Where to Get It |
|--------------|---------------|---------|-----------------|
| **Keycloak** | User ID (UUID) | `f1234567-89ab-cdef-0123-456789abcdef` | OIDC token `sub` claim |
| **Auth0** | User ID | `auth0|63f1234567890abcdef12345` | OIDC token `sub` claim |
| **Okta** | User ID | `00u123abc456xyz` | OIDC token `sub` claim |
| **EntraID** | User UPN + Object ID | `sub`: UPN, `oid`: GUID | OIDC token `sub` and `oid` claims |

**Why IAM identifier instead of email?**
- **Privacy**: IAM user ID is pseudonymous (not PII)
- **Stability**: Doesn't change if user's email changes
- **Correlation**: Perfect correlation with IAM audit logs
- **GDPR/CCPA**: Reduces PII in logs

**How to extract IAM identifier:**

When your application authenticates users via OIDC, the ID token contains the IAM user identifier in the `sub` claim:

```python
# After OIDC authentication
id_token = request.session.get('id_token')
decoded = jwt.decode(id_token, options={"verify_signature": False})

# Extract IAM user identifier from OIDC token
user_id = decoded['sub']  # This is the IAM user ID (NOT email!)

# For EntraID, also get object ID
if vendor == 'entraid':
    user_oid = decoded['oid']  # EntraID Object ID
```

**Example act claims by vendor:**

**Keycloak:**
```python
act = {
    'sub': 'f1234567-89ab-cdef-0123-456789abcdef',  # Keycloak user ID
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}
```

**Auth0:**
```python
act = {
    'sub': 'auth0|63f1234567890abcdef12345',  # Auth0 user ID
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}
```

**Okta:**
```python
act = {
    'sub': '00u123abc456xyz',  # Okta user ID
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}
```

**EntraID (requires both sub and oid):**
```python
act = {
    'sub': 'alice@yourdomain.onmicrosoft.com',  # UPN for display
    'oid': 'a1b2c3d4-e5f6-7890-1234-567890abcdef',  # Object ID for logging
    'email': 'alice@corp.example.com',
    'name': 'Alice Smith'
}
```

❌ **Common Mistake - DON'T DO THIS:** ❌
```python
#
#act = {
#    'sub': 'alice@corp.example.com',  # This is what gets logged; PII!!
#    'email': 'alice@corp.example.com',
#    'name': 'Alice Smith'
#}
```

⚠️ **Security Note:** The IAM user identifier in `act.sub` will be logged (pseudonymous). Email and name are for display only and should not be logged.


<br>

## **Step 4: Implement In-Session Agent**

### 4.1 Understanding In-Session Agents

**In-session agents** run in the same process as your application. They:
- Receive human identity (act) in-memory
- Request tokens from IAM
- Make API calls
- No network transmission of act required

**Use case:** AI features integrated directly into your web application.

### 4.2 Configure IAM Adapter

```python
import os
from phase1.in_session_token_request import get_adapter

# Get vendor from environment
vendor = os.environ.get('AGBAC_VENDOR', 'keycloak')

# Configure adapter based on vendor
if vendor == 'keycloak':
    adapter_config = {
        'token_url': os.environ['KEYCLOAK_TOKEN_URL'],
        'client_id': os.environ['AGENT_CLIENT_ID'],
        'client_secret': os.environ['AGENT_CLIENT_SECRET']
    }
elif vendor == 'auth0':
    adapter_config = {
        'token_url': os.environ['AUTH0_TOKEN_URL'],
        'client_id': os.environ['AGENT_CLIENT_ID'],
        'client_secret': os.environ['AGENT_CLIENT_SECRET'],
        'audience': os.environ['API_AUDIENCE']
    }
elif vendor == 'okta':
    adapter_config = {
        'token_url': os.environ['OKTA_TOKEN_URL'],
        'client_id': os.environ['AGENT_CLIENT_ID'],
        'client_secret': os.environ['AGENT_CLIENT_SECRET'],
        'audience': os.environ['API_AUDIENCE']
    }
elif vendor == 'entraid':
    adapter_config = {
        'token_url': os.environ['ENTRAID_TOKEN_URL'],
        'client_id': os.environ['AGENT_CLIENT_ID'],
        'client_secret': os.environ['AGENT_CLIENT_SECRET'],
        'tenant_id': os.environ['ENTRAID_TENANT_ID'],
        'app_private_key_pem': os.environ['APP_PRIVATE_KEY_PEM'],
        'app_identifier': os.environ.get('APP_IDENTIFIER', 'agbac-app'),
        'api_audience': os.environ['API_AUDIENCE']
    }

# Create adapter
adapter = get_adapter(vendor, adapter_config)
```

### 4.3 Create In-Session Agent

```python
from phase1.in_session_token_request import InSessionAgent, AgentConfig

# Configure agent
agent_config = AgentConfig(
    agent_id=os.environ['AGENT_CLIENT_ID'],
    client_secret=os.environ['AGENT_CLIENT_SECRET'],
    scopes=['finance.read']  # Adjust scopes for your API
)

# Create agent
agent = InSessionAgent(adapter, agent_config)
```

### 4.4 Pass Act to Agent and Request Token

```python
# Step 1: Agent receives act (in-memory)
agent.receive_act(act)

# Step 2: Agent requests dual-subject token
try:
    token_response = agent.request_token()
    
    # Token received successfully
    print(f"Token expires in: {token_response.expires_in} seconds")
    
    # For standard vendors (Keycloak, Auth0, Okta)
    access_token = token_response.access_token
    
    # For EntraID (hybrid approach)
    access_token = token_response.access_token
    act_assertion = token_response.act_assertion  # Second component
    
except TokenRequestError as e:
    print(f"Token request failed: {e}")
    # Handle error appropriately
```

### 4.5 Complete In-Session Example

```python
from flask import Flask, session, redirect
from sender import UserSession, HybridSender
from phase1.in_session_token_request import get_adapter, InSessionAgent, AgentConfig
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

@app.route('/agent-task')
def agent_task():
    # 1. Verify user authenticated
    if 'user' not in session:
        return redirect('/login')
    
    # 2. Extract human identity
    user_session = UserSession(
        user_email=session['user']['email'],
        user_name=session['user']['name']
    )
    
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # 3. Configure adapter
    vendor = os.environ.get('AGBAC_VENDOR', 'keycloak')
    adapter_config = {
        'token_url': os.environ[f'{vendor.upper()}_TOKEN_URL'],
        'client_id': os.environ['AGENT_CLIENT_ID'],
        'client_secret': os.environ['AGENT_CLIENT_SECRET']
    }
    
    if vendor in ['auth0', 'okta']:
        adapter_config['audience'] = os.environ['API_AUDIENCE']
    
    adapter = get_adapter(vendor, adapter_config)
    
    # 4. Create agent and request token
    agent_config = AgentConfig(
        agent_id=os.environ['AGENT_CLIENT_ID'],
        client_secret=os.environ['AGENT_CLIENT_SECRET'],
        scopes=['finance.read']
    )
    
    agent = InSessionAgent(adapter, agent_config)
    agent.receive_act(act)
    
    try:
        token_response = agent.request_token()
        
        # 5. Use token for API calls (see Step 8)
        # ...
        
        return "Agent task completed successfully"
        
    except Exception as e:
        return f"Error: {e}", 500
```

<br>

## **Step 5: Test In-Session Flow**

### 5.1 Create Test Script

Create `test_in_session.py`:

```python
import os
import logging
from dotenv import load_dotenv
from sender import UserSession, HybridSender
from phase1.in_session_token_request import get_adapter, InSessionAgent, AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment
load_dotenv()

def test_in_session_flow():
    print("=" * 60)
    print("AGBAC-Min In-Session Flow Test")
    print("=" * 60)
    
    # 1. Simulate authenticated user
    print("\n1. Simulating authenticated user...")
    user_session = UserSession(
        user_email="alice@corp.example.com",
        user_name="Alice Smith",
        user_id="user_12345"
    )
    print("   ✓ User: alice@corp.example.com")
    
    # 2. Extract act
    print("\n2. Extracting human identity (act)...")
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    print(f"   ✓ Act extracted with fields: {list(act.keys())}")
    
    # 3. Configure adapter
    print("\n3. Configuring IAM adapter...")
    vendor = os.environ.get('AGBAC_VENDOR', 'keycloak')
    print(f"   Vendor: {vendor}")
    
    if vendor == 'keycloak':
        adapter_config = {
            'token_url': os.environ['KEYCLOAK_TOKEN_URL'],
            'client_id': os.environ['AGENT_CLIENT_ID'],
            'client_secret': os.environ['AGENT_CLIENT_SECRET']
        }
    elif vendor == 'auth0':
        adapter_config = {
            'token_url': os.environ['AUTH0_TOKEN_URL'],
            'client_id': os.environ['AGENT_CLIENT_ID'],
            'client_secret': os.environ['AGENT_CLIENT_SECRET'],
            'audience': os.environ['API_AUDIENCE']
        }
    elif vendor == 'okta':
        adapter_config = {
            'token_url': os.environ['OKTA_TOKEN_URL'],
            'client_id': os.environ['AGENT_CLIENT_ID'],
            'client_secret': os.environ['AGENT_CLIENT_SECRET'],
            'audience': os.environ['API_AUDIENCE']
        }
    elif vendor == 'entraid':
        adapter_config = {
            'token_url': os.environ['ENTRAID_TOKEN_URL'],
            'client_id': os.environ['AGENT_CLIENT_ID'],
            'client_secret': os.environ['AGENT_CLIENT_SECRET'],
            'tenant_id': os.environ['ENTRAID_TENANT_ID'],
            'app_private_key_pem': os.environ['APP_PRIVATE_KEY_PEM'],
            'app_identifier': os.environ.get('APP_IDENTIFIER', 'agbac-app'),
            'api_audience': os.environ['API_AUDIENCE']
        }
    
    adapter = get_adapter(vendor, adapter_config)
    print(f"   ✓ Adapter created: {adapter.__class__.__name__}")
    
    # 4. Create agent
    print("\n4. Creating in-session agent...")
    agent_config = AgentConfig(
        agent_id=os.environ['AGENT_CLIENT_ID'],
        client_secret=os.environ['AGENT_CLIENT_SECRET'],
        scopes=['finance.read']
    )
    
    agent = InSessionAgent(adapter, agent_config)
    print("   ✓ Agent created")
    
    # 5. Pass act to agent
    print("\n5. Passing act to agent (in-memory)...")
    agent.receive_act(act)
    print("   ✓ Act received by agent")
    
    # 6. Request token
    print("\n6. Requesting dual-subject token...")
    try:
        token_response = agent.request_token()
        print("   ✓ Token received successfully")
        print(f"   Token type: {token_response.token_type}")
        print(f"   Expires in: {token_response.expires_in} seconds")
        print(f"   Scope: {token_response.scope}")
        
        if token_response.act_assertion:
            print("   ✓ Act assertion included (EntraID hybrid)")
        
        print("\n" + "=" * 60)
        print("✓ IN-SESSION FLOW TEST PASSED")
        print("=" * 60)
        
        return token_response
        
    except Exception as e:
        print(f"   ✗ Token request failed: {e}")
        print("\n" + "=" * 60)
        print("✗ IN-SESSION FLOW TEST FAILED")
        print("=" * 60)
        raise

if __name__ == '__main__':
    test_in_session_flow()
```

### 5.2 Run Test

```bash
python test_in_session.py
```

### 5.3 Expected Output

```
============================================================
AGBAC-Min In-Session Flow Test
============================================================

1. Simulating authenticated user...
   ✓ User: alice@corp.example.com

2. Extracting human identity (act)...
   ✓ Act extracted with fields: ['sub', 'email', 'name']

3. Configuring IAM adapter...
   Vendor: keycloak
   ✓ Adapter created: KeycloakAdapter

4. Creating in-session agent...
   ✓ Agent created

5. Passing act to agent (in-memory)...
   ✓ Act received by agent

6. Requesting dual-subject token...
   ✓ Token received successfully
   Token type: Bearer
   Expires in: 300 seconds
   Scope: finance.read

============================================================
✓ IN-SESSION FLOW TEST PASSED
============================================================
```

### 5.4 Troubleshooting Test Failures

**HTTP 401 - Authentication Failed:**
```
Error: Authentication failed - check client credentials
```
**Solution:** Verify `AGENT_CLIENT_ID` and `AGENT_CLIENT_SECRET` are correct

**HTTP 400 - Bad Request:**
```
Error: Bad request to IAM - check client assertion
```
**Solution:** Verify token endpoint URL is correct

**Missing Act Claim (Keycloak/Auth0/Okta):**
```
Token received but missing 'act' claim
```
**Solution:** Verify IAM configuration (protocol mapper, action, or custom claim)

**Private Key Error (EntraID):**
```
Error: Invalid app_private_key_pem format
```
**Solution:** Verify `APP_PRIVATE_KEY_PEM` is valid PEM format with proper newlines

<br>

## **Step 6: Implement Out-of-Session Agent**

### 6.1 Understanding Out-of-Session Agents

**Out-of-session agents** run in a separate process (often on different servers). They:
- Receive human identity (act) as signed JWT over HTTPS
- Verify JWT signature
- Request tokens from IAM
- Make API calls

**Use case:** Standalone AI services, microservices, remote agents.

### 6.2 Generate Application RSA Keys

**For out-of-session scenarios, your application needs RSA keys to sign act JWTs.**

**Using OpenSSL:**

```bash
# Generate private key
openssl genrsa -out app-private-key.pem 2048

# Generate public key
openssl rsa -in app-private-key.pem -pubout -out app-public-key.pem

# Display keys
cat app-private-key.pem
cat app-public-key.pem
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
with open('app-private-key.pem', 'wb') as f:
    f.write(private_pem)

with open('app-public-key.pem', 'wb') as f:
    f.write(public_pem)

print("✓ Keys generated: app-private-key.pem, app-public-key.pem")
```

**Add keys to environment:**

```bash
# In .env file for non-prod and proper secrets management like AWS, GCP, Azure in prod
APP_PRIVATE_KEY_PEM="-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
...
-----END PRIVATE KEY-----"

APP_PUBLIC_KEY_PEM="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
...
-----END PUBLIC KEY-----"

APP_IDENTIFIER=agbac-application
AGENT_ENDPOINT=https://agent.example.com/invoke
```

### 6.3 Application: Create and Send Act JWT

**In your web application:**

```python
from sender import HybridSender, UserSession
import requests
import os

# After user authenticates
user_session = UserSession(
    user_email=session['user']['email'],
    user_name=session['user']['name']
)

# Create sender with private key
sender = HybridSender(
    private_key_pem=os.environ['APP_PRIVATE_KEY_PEM'],
    app_identifier=os.environ['APP_IDENTIFIER']
)

# Extract act
act = sender.extract_act_from_session(user_session)

# Create signed act JWT
agent_endpoint = os.environ['AGENT_ENDPOINT']
act_jwt = sender.prepare_out_of_session_act(
    act=act,
    agent_endpoint=agent_endpoint,
    ttl_seconds=60  # JWT valid for 60 seconds
)

# Send to agent over HTTPS
response = requests.post(
    agent_endpoint,
    json={'act_jwt': act_jwt},
    headers={'Content-Type': 'application/json'},
    verify=True,  # TLS certificate verification
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    print(f"Agent task completed: {result}")
else:
    print(f"Agent task failed: {response.status_code}")
```

### 6.4 Agent: Receive and Verify Act JWT

**In your agent service:**

```python
from flask import Flask, request, jsonify
from phase2.out_of_session_token_request import (
    OutOfSessionAgent,
    ActJWTConfig,
    AgentConfig
)
from phase1.in_session_token_request import get_adapter
import os

app = Flask(__name__)

@app.route('/invoke', methods=['POST'])
def invoke_agent():
    # 1. Get act JWT from request
    data = request.json
    act_jwt = data.get('act_jwt')
    
    if not act_jwt:
        return jsonify({'error': 'Missing act_jwt'}), 400
    
    # 2. Configure adapter
    vendor = os.environ.get('AGBAC_VENDOR', 'keycloak')
    
    if vendor == 'keycloak':
        adapter_config = {
            'token_url': os.environ['KEYCLOAK_TOKEN_URL'],
            'client_id': os.environ['AGENT_CLIENT_ID'],
            'client_secret': os.environ['AGENT_CLIENT_SECRET']
        }
    # ... other vendors
    
    adapter = get_adapter(vendor, adapter_config)
    
    # 3. Configure JWT verification
    jwt_config = ActJWTConfig(
        app_public_key_pem=os.environ['APP_PUBLIC_KEY_PEM'],
        expected_issuer=os.environ.get('APP_IDENTIFIER', 'agbac-app'),
        expected_audience=os.environ['AGENT_ENDPOINT'],
        max_age_seconds=120
    )
    
    # 4. Create agent
    agent_config = AgentConfig(
        agent_id=os.environ['AGENT_CLIENT_ID'],
        client_secret=os.environ['AGENT_CLIENT_SECRET'],
        scopes=['finance.read']
    )
    
    agent = OutOfSessionAgent(adapter, agent_config, jwt_config)
    
    # 5. Verify act JWT and request token
    try:
        agent.receive_act_jwt(act_jwt)
        token_response = agent.request_token()
        
        # 6. Perform agent task with token
        # (see Step 8 for API calls)
        
        return jsonify({
            'status': 'success',
            'message': 'Agent task completed'
        })
        
    except ValueError as e:
        return jsonify({'error': f'JWT verification failed: {e}'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
```

<br>

## **Step 7: Test Out-of-Session Flow**

### 7.1 Create Test Script

Create `test_out_of_session.py`:

```python
import os
import logging
from dotenv import load_dotenv
from sender import UserSession, HybridSender
from phase2.out_of_session_token_request import (
    OutOfSessionAgent,
    ActJWTConfig,
    AgentConfig
)
from phase1.in_session_token_request import get_adapter

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment
load_dotenv()

def test_out_of_session_flow():
    print("=" * 60)
    print("AGBAC-Min Out-of-Session Flow Test")
    print("=" * 60)
    
    # Part 1: Application creates act JWT
    print("\n[APPLICATION SIDE]")
    print("1. Simulating authenticated user...")
    user_session = UserSession(
        user_email="alice@corp.example.com",
        user_name="Alice Smith"
    )
    print("   ✓ User: alice@corp.example.com")
    
    print("\n2. Creating signed act JWT...")
    sender = HybridSender(
        private_key_pem=os.environ['APP_PRIVATE_KEY_PEM'],
        app_identifier=os.environ.get('APP_IDENTIFIER', 'agbac-app')
    )
    
    act = sender.extract_act_from_session(user_session)
    
    act_jwt = sender.prepare_out_of_session_act(
        act=act,
        agent_endpoint=os.environ['AGENT_ENDPOINT'],
        ttl_seconds=60
    )
    
    print(f"   ✓ Act JWT created (expires in 60 seconds)")
    
    # Part 2: Agent receives and verifies JWT
    print("\n[AGENT SIDE]")
    print("3. Configuring IAM adapter...")
    vendor = os.environ.get('AGBAC_VENDOR', 'keycloak')
    print(f"   Vendor: {vendor}")
    
    # ... (adapter configuration same as in-session)
    
    adapter = get_adapter(vendor, adapter_config)
    print(f"   ✓ Adapter created: {adapter.__class__.__name__}")
    
    print("\n4. Configuring JWT verification...")
    jwt_config = ActJWTConfig(
        app_public_key_pem=os.environ['APP_PUBLIC_KEY_PEM'],
        expected_issuer=os.environ.get('APP_IDENTIFIER', 'agbac-app'),
        expected_audience=os.environ['AGENT_ENDPOINT'],
        max_age_seconds=120
    )
    print("   ✓ JWT verification configured")
    
    print("\n5. Creating out-of-session agent...")
    agent_config = AgentConfig(
        agent_id=os.environ['AGENT_CLIENT_ID'],
        client_secret=os.environ['AGENT_CLIENT_SECRET'],
        scopes=['finance.read']
    )
    
    agent = OutOfSessionAgent(adapter, agent_config, jwt_config)
    print("   ✓ Agent created")
    
    print("\n6. Verifying act JWT...")
    try:
        agent.receive_act_jwt(act_jwt)
        print("   ✓ JWT signature verified")
        print("   ✓ JWT claims validated")
        print("   ✓ Act extracted from JWT")
    except ValueError as e:
        print(f"   ✗ JWT verification failed: {e}")
        raise
    
    print("\n7. Requesting dual-subject token...")
    try:
        token_response = agent.request_token()
        print("   ✓ Token received successfully")
        print(f"   Token type: {token_response.token_type}")
        print(f"   Expires in: {token_response.expires_in} seconds")
        
        print("\n" + "=" * 60)
        print("✓ OUT-OF-SESSION FLOW TEST PASSED")
        print("=" * 60)
        
        return token_response
        
    except Exception as e:
        print(f"   ✗ Token request failed: {e}")
        print("\n" + "=" * 60)
        print("✗ OUT-OF-SESSION FLOW TEST FAILED")
        print("=" * 60)
        raise

if __name__ == '__main__':
    test_out_of_session_flow()
```

### 7.2 Run Test

```bash
python test_out_of_session.py
```

### 7.3 Expected Output

```
============================================================
AGBAC-Min Out-of-Session Flow Test
============================================================

[APPLICATION SIDE]
1. Simulating authenticated user...
   ✓ User: alice@corp.example.com

2. Creating signed act JWT...
   ✓ Act JWT created (expires in 60 seconds)

[AGENT SIDE]
3. Configuring IAM adapter...
   Vendor: keycloak
   ✓ Adapter created: KeycloakAdapter

4. Configuring JWT verification...
   ✓ JWT verification configured

5. Creating out-of-session agent...
   ✓ Agent created

6. Verifying act JWT...
   ✓ JWT signature verified
   ✓ JWT claims validated
   ✓ Act extracted from JWT

7. Requesting dual-subject token...
   ✓ Token received successfully
   Token type: Bearer
   Expires in: 300 seconds

============================================================
✓ OUT-OF-SESSION FLOW TEST PASSED
============================================================
```

<br>

## **Step 8: Implement API Calls**

### 8.1 Understanding API Client

The **APIClient** handles authenticated API calls with dual-subject tokens.

**Key features:**
- Automatically formats headers for all vendors
- EntraID: Adds `X-Act-Assertion` header automatically
- HTTPS enforcement
- Retry logic for transient failures
- Proper error handling

### 8.2 Create API Client

```python
from phase1.in_session_api_call import APIClient
import os

# Create client for your vendor
vendor = os.environ.get('AGBAC_VENDOR', 'keycloak')
client = APIClient(vendor=vendor)
```

### 8.3 Make GET Request

```python
# After getting token from agent
token_response = agent.request_token()

# Make authenticated GET request
response = client.get(
    url='https://api.example.com/finance/report/Q4-2025',
    token_response=token_response,
    params={'detail': 'full'},
    timeout=30
)

# Handle response
if response.status_code == 200:
    data = response.json()
    print(f"Report data: {data}")
elif response.status_code == 403:
    print("Access denied - check authorization")
else:
    print(f"API error: {response.status_code}")
```

### 8.4 Make POST Request

```python
# Make authenticated POST request
response = client.post(
    url='https://api.example.com/finance/transactions',
    token_response=token_response,
    json_data={
        'amount': 1000.00,
        'description': 'Q4 budget allocation'
    },
    timeout=30
)

if response.status_code == 201:
    print("Transaction created")
else:
    print(f"Failed: {response.status_code}")
```

### 8.5 Complete API Call Example

```python
from phase1.in_session_token_request import get_adapter, InSessionAgent, AgentConfig
from phase1.in_session_api_call import APIClient
from sender import UserSession, HybridSender
import os

def perform_agent_task():
    # 1. Extract human identity
    user_session = UserSession(
        user_email="alice@corp.example.com",
        user_name="Alice Smith"
    )
    
    sender = HybridSender()
    act = sender.extract_act_from_session(user_session)
    
    # 2. Get token
    vendor = os.environ['AGBAC_VENDOR']
    adapter_config = {...}  # Configure for your vendor
    adapter = get_adapter(vendor, adapter_config)
    
    agent_config = AgentConfig(
        agent_id=os.environ['AGENT_CLIENT_ID'],
        client_secret=os.environ['AGENT_CLIENT_SECRET'],
        scopes=['finance.read', 'finance.write']
    )
    
    agent = InSessionAgent(adapter, agent_config)
    agent.receive_act(act)
    token_response = agent.request_token()
    
    # 3. Create API client
    client = APIClient(vendor=vendor)
    
    # 4. Make API calls
    # Get financial report
    report_response = client.get(
        url=os.environ['API_URL'],
        token_response=token_response,
        params={'quarter': 'Q4', 'year': '2025'}
    )
    
    if report_response.status_code == 200:
        report = report_response.json()
        
        # Process report and create summary
        summary = analyze_report(report)
        
        # Post summary
        summary_response = client.post(
            url='https://api.example.com/finance/summaries',
            token_response=token_response,
            json_data=summary
        )
        
        if summary_response.status_code == 201:
            return {'success': True, 'summary_id': summary_response.json()['id']}
    
    return {'success': False, 'error': 'API call failed'}

def analyze_report(report):
    """Analyze financial report and create summary."""
    # Agent AI logic here
    return {
        'total_revenue': report['revenue'],
        'total_expenses': report['expenses'],
        'net_income': report['revenue'] - report['expenses']
    }
```

### 8.6 EntraID-Specific Header Handling

**The API client automatically handles EntraID's two-header format:**

```python
# For Keycloak/Auth0/Okta
# Headers sent:
# Authorization: Bearer <token>

# For EntraID
# Headers sent:
# Authorization: Bearer <entraid-token>
# X-Act-Assertion: <app-signed-jwt>

# You don't need to do anything different!
client = APIClient(vendor='entraid')  # Automatically handles both headers
response = client.get(url, token_response)  # Works identically
```

<br>



## **Step 8.5: Logging Best Practices**

### Understanding What to Log

AGBAC-Min uses **IAM user identifiers** (not PII) for logging, ensuring privacy compliance while maintaining audit trails.

**✅ DO: Log IAM identifiers**
```python
import logging

logger = logging.getLogger(__name__)

# After extracting act
act = sender.extract_act_from_session(user_session)

# Log using IAM user identifier (pseudonymous)
logger.info(
    "API request initiated",
    extra={
        "agent_id": os.environ['AGENT_CLIENT_ID'],
        "human_id": act['sub'],  # IAM user ID (NOT email!)
        "action": "read",
        "resource": "/api/finance/reports"
    }
)
```

**❌ DON'T: Log PII**
```python
# BAD - Logs PII
logger.info(f"User {act['email']} accessed reports")  # ❌ Email is PII
logger.info(f"Name: {act['name']}")                   # ❌ Name is PII
```

### Why Log IAM Identifiers?

**Privacy:**
- IAM user IDs are pseudonymous (not PII)
- GDPR/CCPA compliant
- Can be used in analytics without privacy concerns

**Correlation:**
- Matches IAM audit logs perfectly
- Security investigations can correlate app logs ↔ IAM logs

**Stability:**
- User ID does not change if email changes
- Historical logs remain valid

### Correlation with IAM Audit Logs

| IAM Provider | Audit Log Field | Your App Log Field | Correlation |
|--------------|-----------------|-------------------|-------------|
| Keycloak | `userId` | `human_id` | Match UUIDs |
| Auth0 | `user_id` | `human_id` | Match user IDs |
| Okta | `actor.id` | `human_id` | Match user IDs |
| EntraID | `userId` | `human_id` (from oid) | Match Object IDs |


<br>

## **Step 9: Production Deployment**

### 9.1 Secrets Management

**❌ DO NOT** store secrets in `.env` files in production.

**✅ DO** use proper secrets management:

**AWS Secrets Manager:**

```python
import boto3
import json

def get_secrets():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='agbac/production')
    return json.loads(response['SecretString'])

secrets = get_secrets()

adapter_config = {
    'token_url': secrets['TOKEN_URL'],
    'client_id': secrets['CLIENT_ID'],
    'client_secret': secrets['CLIENT_SECRET']
}
```

**Azure Key Vault:**

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=credential
)

adapter_config = {
    'token_url': client.get_secret('token-url').value,
    'client_id': client.get_secret('client-id').value,
    'client_secret': client.get_secret('client-secret').value
}
```

**Google Secret Manager:**

```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
project_id = "your-project-id"

def get_secret(secret_id):
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

adapter_config = {
    'token_url': get_secret('token-url'),
    'client_id': get_secret('client-id'),
    'client_secret': get_secret('client-secret')
}
```

### 9.2 Logging Configuration

**Production logging with structured JSON:**

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_obj.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

# Configure root logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### 9.3 Error Monitoring

**Integrate with monitoring services:**

```python
import sentry_sdk

# Sentry
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

# Now errors are automatically reported
try:
    token_response = agent.request_token()
except Exception as e:
    # Automatically sent to Sentry
    raise
```

### 9.4 Deploying your App/Agent with AGBAC-Min via Docker

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY adapters/ ./adapters/
COPY sender/ ./sender/
COPY phase1/ ./phase1/
COPY phase2/ ./phase2/
COPY your_app.py .

# Run application
CMD ["python", "-u", "your_app.py"]
```

**Build and run:**

```bash
docker build -t agbac-agent .
docker run -e AGBAC_VENDOR=keycloak \
           -e AGENT_CLIENT_ID=... \
           -e AGENT_CLIENT_SECRET=... \
           agbac-agent
```

### 9.5 Deploying your App/Agent with AGBAC-Min via Kubernetes

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agbac-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agbac-agent
  template:
    metadata:
      labels:
        app: agbac-agent
    spec:
      containers:
      - name: agent
        image: your-registry/agbac-agent:latest
        env:
        - name: AGBAC_VENDOR
          valueFrom:
            configMapKeyRef:
              name: agbac-config
              key: vendor
        - name: AGENT_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: agbac-secrets
              key: client-id
        - name: AGENT_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: agbac-secrets
              key: client-secret
        ports:
        - containerPort: 5000
```

**secrets.yaml:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agbac-secrets
type: Opaque
stringData:
  client-id: your-client-id
  client-secret: your-client-secret
  token-url: https://your-iam/token
```

### 9.6 Health Checks

**Add health check endpoint:**

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    # Check IAM connectivity
    try:
        # Attempt to reach IAM provider
        response = requests.get(
            os.environ['KEYCLOAK_TOKEN_URL'].replace('/token', ''),
            timeout=5
        )
        iam_healthy = response.status_code < 500
    except:
        iam_healthy = False
    
    return jsonify({
        'status': 'healthy' if iam_healthy else 'degraded',
        'iam_reachable': iam_healthy
    }), 200 if iam_healthy else 503

@app.route('/ready')
def ready():
    # Check if secrets loaded
    required_env = ['AGBAC_VENDOR', 'AGENT_CLIENT_ID', 'AGENT_CLIENT_SECRET']
    ready = all(os.environ.get(var) for var in required_env)
    
    return jsonify({
        'ready': ready
    }), 200 if ready else 503
```

<br>

## **Troubleshooting**

### **Common Issues**

#### **Issue 1: Import Errors**

```
ImportError: No module named 'adapters'
```

**Solution:**
- Verify directory structure is correct
- Ensure `__init__.py` files exist in all package directories
- Check Python path: `export PYTHONPATH="${PYTHONPATH}:/path/to/your/project"`

#### **Issue 2: JWT Signature Verification Failed**

```
ValueError: Act JWT verification failed: InvalidSignatureError
```

**Solutions:**
- Verify `APP_PUBLIC_KEY_PEM` matches `APP_PRIVATE_KEY_PEM`
- Check key format (should be PEM with headers)
- Ensure newlines are preserved in environment variable

**Verify keys match:**

```python
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Load private key
with open('app-private-key.pem', 'rb') as f:
    private_key = serialization.load_pem_private_key(
        f.read(), password=None, backend=default_backend()
    )

# Extract public key from private key
public_from_private = private_key.public_key()

# Load public key file
with open('app-public-key.pem', 'rb') as f:
    public_from_file = serialization.load_pem_public_key(
        f.read(), backend=default_backend()
    )

# Compare
print("Keys match!" if public_from_private.public_numbers() == 
      public_from_file.public_numbers() else "Keys DON'T match!")
```

#### **Issue 3: Token Missing Act Claim**

**For Keycloak:**
```
Token received but missing 'act' claim
```

**Solution:**
1. Verify protocol mapper is configured (see Keycloak IAM Guide Step 4)
2. Check mapper is added to `finance-agent-dedicated` scope
3. Verify client assertion contains `act` claim
4. Check Keycloak logs: `/opt/keycloak/data/log/keycloak.log`

**For Auth0:**
```
Token missing 'act' claim
```

**Solution:**
1. Verify Credentials Exchange Action is deployed
2. Check Action is enabled
3. Review Action logs in Auth0 dashboard

**For Okta:**
```
Token missing 'act' claim
```

**Solution:**
1. Verify custom claim expression: `clientAssertion.claims.act`
2. Check claim is set to include in Access Token
3. Verify access policy allows client

#### **Issue 4: EntraID Two Headers**

```
API returns 401 even with valid token
```

**Solution for EntraID:**
- Verify API client is configured with `vendor='entraid'`
- Check resource server expects `X-Act-Assertion` header
- Verify `act_assertion` is not None in token_response

```python
# Correct
client = APIClient(vendor='entraid')  # Must specify vendor
response = client.get(url, token_response)

# Verify token_response has both components
print(f"Has access_token: {token_response.access_token is not None}")
print(f"Has act_assertion: {token_response.act_assertion is not None}")
```

#### **Issue 5: HTTPS Required Error**

```
ValueError: API URL must use HTTPS (https://)
```

**Solution:**
- Change `http://` to `https://` in all URLs
- Verify `TOKEN_URL`, `API_URL`, `AGENT_ENDPOINT` use HTTPS
- For local development: Use self-signed certificates or tunneling (ngrok)

#### **Issue 6: Rate Limiting**

```
TokenRequestError: Rate limit exceeded (HTTP 429)
```

**Solution:**
- Implement token caching (reuse tokens until expiration)
- Add backoff logic for retries
- Contact IAM provider to increase rate limits

**Token caching example:**

```python
from datetime import datetime, timedelta

class TokenCache:
    def __init__(self):
        self.token = None
        self.expires_at = None
    
    def get_token(self, agent):
        now = datetime.now()
        
        # Return cached token if valid
        if self.token and self.expires_at and now < self.expires_at:
            return self.token
        
        # Request new token
        token_response = agent.request_token()
        self.token = token_response
        self.expires_at = now + timedelta(seconds=token_response.expires_in - 60)
        
        return self.token

# Usage
cache = TokenCache()
token = cache.get_token(agent)  # Only requests when needed
```

<br>


### Problem: act.sub contains email instead of IAM user ID

**Symptoms:**
- Logs show email addresses in `human_id` field
- Cannot correlate with IAM audit logs
- Privacy concerns (logging PII)

**Cause:**
Application is using email as `user_id` when creating `UserSession`:

```python
# ❌ WRONG
user_session = UserSession(
    user_email=session['email'],
    user_name=session['name'],
    user_id=session['email']  # This is wrong! Should be IAM user ID
)
```

**Solution:**
Extract IAM user identifier from OIDC token's `sub` claim:

```python
# ✅ CORRECT
# After OIDC authentication
id_token = session['id_token']
decoded = jwt.decode(id_token, options={"verify_signature": False})

user_session = UserSession(
    user_email=decoded.get('email'),
    user_name=decoded.get('name'),
    user_id=decoded['sub']  # IAM user ID from OIDC token
)
```

**Verify the fix:**
```python
act = sender.extract_act_from_session(user_session)
print(f"act.sub = {act['sub']}")

# Should print IAM user ID, not email:
# Keycloak: f1234567-89ab-cdef-0123-456789abcdef
# Auth0: auth0|63f1234567890abcdef12345
# Okta: 00u123abc456xyz
# EntraID: alice@yourdomain.onmicrosoft.com (UPN is acceptable)
```

### Problem: Cannot find IAM user ID in application session

**Symptoms:**
- Application does not have IAM user ID
- Only have email and name in session
- OIDC token not stored in session

**Solutions:**

**Option 1: Store OIDC token in session (Recommended)**
```python
# During login/callback
@app.route('/callback')
def callback():
    # After OIDC authentication
    tokens = oauth.keycloak.authorize_access_token()
    id_token = tokens['id_token']
    
    # Store entire ID token in session
    session['id_token'] = id_token
    
    # Later, extract user info from stored token
    decoded = jwt.decode(session['id_token'], options={"verify_signature": False})
    user_id = decoded['sub']  # IAM user ID
```

**Option 2: Store user ID separately**
```python
# During login
@app.route('/callback')
def callback():
    tokens = oauth.keycloak.authorize_access_token()
    id_token = tokens['id_token']
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    
    # Store user ID in session
    session['user'] = {
        'id': decoded['sub'],  # Store IAM user ID
        'email': decoded.get('email'),
        'name': decoded.get('name')
    }
    
# Later use
user_session = UserSession(
    user_email=session['user']['email'],
    user_name=session['user']['name'],
    user_id=session['user']['id']  # IAM user ID
)
```

**Option 3: Fetch from IAM API (Not Recommended - adds latency)**
```python
# Query IAM API to get user ID from email
# This adds latency - better to store during login
```

### Problem: EntraID missing oid field

**Symptoms:**
- EntraID tokens work but oid field missing
- Cannot correlate with EntraID audit logs

**Cause:**
Not extracting `oid` claim from EntraID OIDC token.

**Solution:**
EntraID requires both `sub` and `oid` in act claim:

```python
# After EntraID OIDC authentication
id_token = session['id_token']
decoded = jwt.decode(id_token, options={"verify_signature": False})

# Extract both sub (UPN) and oid (Object ID)
user_upn = decoded['sub']        # UPN
user_oid = decoded['oid']        # Object ID

# Create act with both fields
act = {
    'sub': user_upn,              # For display
    'oid': user_oid,              # For logging (primary)
    'email': decoded.get('email'),
    'name': decoded.get('name')
}

# Or manually add to UserSession-generated act
user_session = UserSession(
    user_email=decoded.get('email'),
    user_name=decoded.get('name'),
    user_id=user_upn
)
act = sender.extract_act_from_session(user_session)
act['oid'] = user_oid  # Add oid for EntraID
```


<br>

## **Reference: Complete Examples**

### **Example 1: Flask Application with In-Session Agent**

```python
from flask import Flask, session, redirect, url_for, jsonify
from sender import UserSession, HybridSender
from phase1.in_session_token_request import get_adapter, InSessionAgent, AgentConfig
from phase1.in_session_api_call import APIClient
import os

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

def get_configured_adapter():
    """Get adapter configured for current vendor."""
    vendor = os.environ['AGBAC_VENDOR']
    
    if vendor == 'keycloak':
        config = {
            'token_url': os.environ['KEYCLOAK_TOKEN_URL'],
            'client_id': os.environ['AGENT_CLIENT_ID'],
            'client_secret': os.environ['AGENT_CLIENT_SECRET']
        }
    elif vendor == 'auth0':
        config = {
            'token_url': os.environ['AUTH0_TOKEN_URL'],
            'client_id': os.environ['AGENT_CLIENT_ID'],
            'client_secret': os.environ['AGENT_CLIENT_SECRET'],
            'audience': os.environ['API_AUDIENCE']
        }
    # ... other vendors
    
    return get_adapter(vendor, config)

@app.route('/api/agent/analyze-finances', methods=['POST'])
def analyze_finances():
    """Agent endpoint: Analyze user's finances."""
    
    # 1. Verify user authenticated
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # 2. Extract human identity
        user_session = UserSession(
            user_email=session['user']['email'],
            user_name=session['user']['name'],
            user_id=session['user']['id']
        )
        
        sender = HybridSender()
        act = sender.extract_act_from_session(user_session)
        
        # 3. Create agent
        adapter = get_configured_adapter()
        agent_config = AgentConfig(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            client_secret=os.environ['AGENT_CLIENT_SECRET'],
            scopes=['finance.read']
        )
        
        agent = InSessionAgent(adapter, agent_config)
        agent.receive_act(act)
        
        # 4. Get token
        token_response = agent.request_token()
        
        # 5. Make API calls
        vendor = os.environ['AGBAC_VENDOR']
        client = APIClient(vendor=vendor)
        
        # Get financial data
        response = client.get(
            url=os.environ['API_URL'],
            token_response=token_response,
            params={'user_id': session['user']['id']}
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'API call failed'}), response.status_code
        
        financial_data = response.json()
        
        # 6. Analyze with AI (agent logic)
        analysis = {
            'total_assets': sum(financial_data.get('assets', [])),
            'total_liabilities': sum(financial_data.get('liabilities', [])),
            'net_worth': sum(financial_data.get('assets', [])) - 
                         sum(financial_data.get('liabilities', []))
        }
        
        return jsonify(analysis), 200
        
    except Exception as e:
        app.logger.error(f"Agent task failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

### **Example 2: Standalone Agent Service (Out-of-Session)**

```python
from flask import Flask, request, jsonify
from phase2.out_of_session_token_request import (
    OutOfSessionAgent,
    ActJWTConfig,
    AgentConfig
)
from phase1.in_session_token_request import get_adapter
from phase1.in_session_api_call import APIClient
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_configured_adapter():
    """Get adapter for current vendor."""
    vendor = os.environ['AGBAC_VENDOR']
    # ... (same as Example 1)
    return get_adapter(vendor, config)

@app.route('/invoke', methods=['POST'])
def invoke_agent():
    """
    Receive act JWT from application and perform agent task.
    
    Expected request:
    {
        "act_jwt": "eyJ...",
        "task": "analyze_report",
        "parameters": {...}
    }
    """
    
    # 1. Validate request
    data = request.json
    act_jwt = data.get('act_jwt')
    task = data.get('task')
    parameters = data.get('parameters', {})
    
    if not act_jwt:
        return jsonify({'error': 'Missing act_jwt'}), 400
    
    if not task:
        return jsonify({'error': 'Missing task'}), 400
    
    try:
        # 2. Configure adapter
        adapter = get_configured_adapter()
        
        # 3. Configure JWT verification
        jwt_config = ActJWTConfig(
            app_public_key_pem=os.environ['APP_PUBLIC_KEY_PEM'],
            expected_issuer=os.environ.get('APP_IDENTIFIER', 'agbac-app'),
            expected_audience=os.environ['AGENT_ENDPOINT'],
            max_age_seconds=120
        )
        
        # 4. Create agent
        agent_config = AgentConfig(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            client_secret=os.environ['AGENT_CLIENT_SECRET'],
            scopes=['finance.read', 'finance.write']
        )
        
        agent = OutOfSessionAgent(adapter, agent_config, jwt_config)
        
        # 5. Verify JWT and get token
        agent.receive_act_jwt(act_jwt)
        token_response = agent.request_token()
        
        # 6. Perform task
        vendor = os.environ['AGBAC_VENDOR']
        client = APIClient(vendor=vendor)
        
        if task == 'analyze_report':
            result = analyze_report_task(client, token_response, parameters)
        elif task == 'generate_summary':
            result = generate_summary_task(client, token_response, parameters)
        else:
            return jsonify({'error': f'Unknown task: {task}'}), 400
        
        return jsonify({
            'status': 'success',
            'task': task,
            'result': result
        }), 200
        
    except ValueError as e:
        logger.error(f"JWT verification failed: {e}")
        return jsonify({'error': 'Invalid act_jwt'}), 401
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def analyze_report_task(client, token_response, parameters):
    """Analyze financial report."""
    report_id = parameters.get('report_id')
    
    # Get report data
    response = client.get(
        url=f"{os.environ['API_URL']}/reports/{report_id}",
        token_response=token_response
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get report: {response.status_code}")
    
    report = response.json()
    
    # AI analysis logic
    analysis = {
        'revenue_trend': 'increasing',
        'expense_ratio': 0.75,
        'recommendations': [
            'Reduce operational expenses',
            'Increase marketing budget'
        ]
    }
    
    return analysis

def generate_summary_task(client, token_response, parameters):
    """Generate financial summary."""
    # ... similar implementation
    pass

if __name__ == '__main__':
    # Production: Use gunicorn
    # gunicorn -w 4 -b 0.0.0.0:5000 agent_service:app
    app.run(debug=False, host='0.0.0.0', port=5000, ssl_context='adhoc')
```

### **Example 3: FastAPI Application**

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sender import UserSession, HybridSender
from phase1.in_session_token_request import get_adapter, InSessionAgent, AgentConfig
from phase1.in_session_api_call import APIClient
import os

app = FastAPI(title="AGBAC-Min Agent Service")
security = HTTPBearer()

class AgentRequest(BaseModel):
    user_email: str
    user_name: str
    task: str
    parameters: dict = {}

@app.post("/api/agent/task")
async def execute_agent_task(
    request: AgentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Execute agent task with dual-subject authorization.
    
    This endpoint expects the user to already be authenticated.
    The Bearer token in Authorization header is the user's session token.
    """
    
    try:
        # 1. Verify user session (your authentication logic)
        # user = verify_session_token(credentials.credentials)
        
        # 2. Extract act
        user_session = UserSession(
            user_email=request.user_email,
            user_name=request.user_name
        )
        
        sender = HybridSender()
        act = sender.extract_act_from_session(user_session)
        
        # 3. Create agent and get token
        vendor = os.environ['AGBAC_VENDOR']
        adapter = get_configured_adapter(vendor)
        
        agent_config = AgentConfig(
            agent_id=os.environ['AGENT_CLIENT_ID'],
            client_secret=os.environ['AGENT_CLIENT_SECRET'],
            scopes=['finance.read']
        )
        
        agent = InSessionAgent(adapter, agent_config)
        agent.receive_act(act)
        token_response = agent.request_token()
        
        # 4. Execute task
        client = APIClient(vendor=vendor)
        result = await execute_task(
            client,
            token_response,
            request.task,
            request.parameters
        )
        
        return {
            "status": "success",
            "task": request.task,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_task(client, token_response, task, parameters):
    """Execute specific task."""
    # ... task implementation
    pass

def get_configured_adapter(vendor):
    """Get configured adapter for vendor."""
    # ... (same as previous examples)
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

<br>

## **Next Steps**

After completing this guide, you should:

1. ✅ Have AGBAC-Min integrated into your application
2. ✅ Be able to request dual-subject tokens
3. ✅ Be able to make authorized API calls
4. ✅ Understand in-session and out-of-session flows
5. ✅ Be ready for production deployment

**Recommended Next Actions:**

1. **Review Security:** Audit logging, secrets management, error handling
2. **Performance Testing:** Load test token requests and API calls
3. **Monitoring:** Set up alerts for token failures, API errors
4. **Documentation:** Document your specific implementation
5. **Team Training:** Train team on AGBAC-Min concepts

<br>

## **Support Resources**

- **IAM Configuration Guides:** See individual guides for Keycloak, Auth0, Okta, EntraID
- **Code Documentation:** Review inline documentation in Python files
- **Changelog:** See `CHANGELOG.md` for update and change log details

<br>

