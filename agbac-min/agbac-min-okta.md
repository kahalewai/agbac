# **AGBAC-Min-Okta**

## **Foundational AGBAC Guide for Okta + Active Directory**

**Guide ID:** AGBAC-Min-Okta

**AGBAC Version:** 1.0.0

**Scope:** System-level access only

**Enforcement:** Okta native authorization

**Code Required:** None (configuration only)

<br>

## **1. Purpose**

AGBAC-Min-Okta is a foundational implementation guide of the AGBAC specification that demonstrates how core AGBAC principles can be realized today using:

* Okta Workforce Identity
* Active Directory (for human identity)
* OAuth 2.0 / OIDC
* JWT custom claims
* Okta RBAC and application assignments

This profile allows organizations to safely enable AI agents to access enterprise systems on behalf of users, while ensuring that:

> **Both the AI agent and the human user must be independently authorized for every system access.**

<br>

## **2. What This Guide Implements (and What It Does Not)**

### **Implements**

* A sub-set of AGBAC capabilities
* Agent identities as first-class principals
* Human identities from AD → Okta
* Dual-subject tokens (`sub` + `act`)
* Explicit delegation semantics
* System-level access control
* Dual-subject audit attribution

### **Does Not Implement**

* The full AGBAC Specification
* Object-level authorization
* Policy engines (OPA/Cedar)
* Multi-agent delegation chains
* AI reasoning validation
* Custom enforcement services

These capabilities are defined in the **full AGBAC specification** and may be implemented via future AGBAC-Full profiles.

<br>

## **3. Architecture Overview**

### **Actors**

| Actor         | Representation             |
| ------------- | -------------------------- |
| Human user    | AD user → Okta user        |
| AI agent      | Okta OAuth service app     |
| Authorization | Okta Authorization Server  |
| Target system | Okta-protected application |

<br>

### **High-Level Flow**

```
1. Human authenticates to Okta (via AD)
2. Human instructs AI agent
3. Agent requests OAuth token
4. Okta issues dual-subject token:
      - sub  = agent
      - act  = human
5. Agent accesses system
6. Okta enforces:
      - agent must be assigned
      - human must be assigned
7. Audit logs record both identities
```

<br>

## **4. Identity Model**

### **4.1 Human Identity (Active Directory)**

* Humans are managed in **Active Directory**
* AD groups represent **system-level access**
* AD groups are synced to Okta
* Okta assigns users to applications based on group membership

**Example AD Groups**

| AD Group            | Meaning                      |
| ------------------- | ---------------------------- |
| `FINANCE_APP_USERS` | Allowed to access FinanceApp |
| `HR_APP_USERS`      | Allowed to access HRApp      |

<br>

### **4.2 Agent Identity (Okta)**

Each AI agent is represented as a **distinct Okta OAuth service application**.

**Requirements**

* One OAuth client per agent (recommended)
* Client Credentials grant enabled
* Assigned only to systems the agent may access

**Example Agents**

| Agent            | Okta App            |
| ---------------- | ------------------- |
| Finance AI Agent | `finance-agent-app` |
| HR AI Agent      | `hr-agent-app`      |

<br>

## **5. System-Level Authorization Model**

AGBAC-Min-Okta enforces the following rule **by configuration**:

```
ALLOW system access
IFF
  agent is assigned to the application
AND
  human is assigned to the application
```

This achieves **dual-subject authorization** at the system boundary.

<br>

## **6. Okta Configuration — Step by Step**

> **Assumptions:**
>
> * You have **Okta Org Admin** access.
> * Okta **API Access Management** is enabled.
> * Okta AD Agent is installed and syncing.
> * You already have **Active Directory groups** for human access.
> * This applies to **system‑layer only**, no token exchange, no dynamic delegation.
> * You are logged into **Okta Admin Console** (e.g., `https://<your‑org>.okta.com/admin`)

### **6.1 Create Okta Applications (Target Systems)**

For each protected system:

* Create an **OIDC or SAML Application** in Okta
* Enable access via Okta authentication
* Do NOT allow public access

**Example Applications**

* `FinanceApp`
* `HRApp`

1. Go to **Applications ➜ Applications**.
2. Click **Create App Integration**.
3. Select **OIDC – OpenID Connect** (or **SAML 2.0** if appropriate).
4. Click **Next**.

#### If OIDC:

5. Select **Web Application**.
6. Click **Next**.
7. Fill in:

   * **App integration name:** e.g., `FinanceApp`
   * **Sign‑on redirect URIs:** URI for your app
8. Click **Save**.

#### If SAML:

5. Complete the SAML config with appropriate ACS URL, etc.
6. Click **Next**, then **Finish**.

> Repeat for each system.

<br>

### **6.2 Configure Human Access (AD → Okta)**

* Sync AD groups to Okta
* Assign groups to applications

**Example**

| Application | Assigned Group      |
| ----------- | ------------------- |
| FinanceApp  | `FINANCE_APP_USERS` |
| HRApp       | `HR_APP_USERS`      |


1. Go to **Directory ➜ Directory Integrations**
1. Ensure **Okta AD Agent** is listed and status shows **Up**.
2. If not installed, install the AD Agent according to Okta documentation
3. Navigate to **Directory ➜ Groups**.
4. Confirm your AD groups are present:
   * Example: `FINANCE_APP_USERS`, `HR_APP_USERS`

5. If not present:
   * Click **Add Group**
   * Choose **Import Group from AD**
   * Select the AD group

> These groups will represent humans authorized for each system.

6. Go to **Applications ➜ Applications**.
7. Click your app (`FinanceApp`).
8. Go to **Assignments ➜ Assign**.
9. Select **Assign to Groups**.
10. Choose the AD group (e.g., `FINANCE_APP_USERS`).
11. Click **Done**.

> This ensures humans in AD groups can access the system.

<br>

### **6.3 Create Agent OAuth Applications**

For each AI agent:

* Create a **Service Application**
* Enable **Client Credentials**
* Disable user login
* Assign the agent to allowed applications

**Example**

| Agent App         | Assigned Application |
| ----------------- | -------------------- |
| finance-agent-app | FinanceApp           |
| hr-agent-app      | HRApp                |

1. Go to **Applications ➜ Applications**.
2. Click **Create App Integration**.
3. Choose **Service (Machine‑to‑Machine)**.
4. Click **Next**.
5. Fill:
   * **App integration name:** e.g., `finance‑agent‑app`
   * **Client authentication:** Enabled (defaults)
   * **Grant type:** **Client Credentials**
6. Click **Save**.

7. After creation, Okta will show:
   * **Client ID**
   * **Client Secret**
8. Copy them securely — needed for the agent.

9. In the agent app configuration screen, go to **Assignments**.
10. Click **Assign ➜ Assign to Applications**.
11. Choose the same system app (e.g., `FinanceApp`).
12. Click **Done**.

<br>

### **6.4 Authorization Server Configuration**

Use a **Custom Authorization Server**.

#### **Required Scopes**

| Scope           | Purpose               |
| --------------- | --------------------- |
| `system.access` | Generic system access |

1. Go to **Security ➜ API**.
2. Select the **Authorization Servers** tab.

1. Click **Add Authorization Server**.
2. Fill:

   * **Name:** `AGBAC‑Min‑AS`
   * **Audience:** `api://default`
3. Click **Save**.

1. Within the `AGBAC‑Min‑AS` configuration, go to **Scopes**.
2. Click **Add Scope**.
3. Fill:

   * **Name:** `system.access`
   * **Display name:** `System Level Access`
   * **Description:** “Access token scope for system‑level operations”
4. Click **Save**.

1. Go to **Access Policies** under `AGBAC‑Min‑AS`.
2. Click **Add Policy**.
3. Fill:

   * **Name:** `AGBAC‑Min Token Policy`
   * **Description:** `Allow client_credentials for AGBAC‑Min`
   * **Policy Type:** **Access Token**
4. Click **Create Policy**.

1. Under the new policy, click **Add Rule**.
2. Fill:

   * **Rule name:** `Allow Client Credentials`
   * **Grant type:** Select **Client Credentials**
   * **Scopes:** Check **system.access**
3. Click **Create Rule**.

<br>

Example Auth Server Configuration

## `okta/auth-server/agbac-min-auth-server.json`

```json
{
  "name": "AGBAC-Min-AS",
  "description": "Custom Authorization server for AGBAC-Min dual-subject access control",
  "issuerMode": "ORG_URL",
  "audiences": ["api://default"],
  "accessTokenLifetimeMinutes": 10,
  "refreshTokenLifetimeMinutes": 0,
  "issuerMode": "ORG_URL",
  "scopes": [
    {
      "name": "system.access",
      "description": "System-level access for AGBAC-Min agents",
      "consent": "IMPLICIT"
    }
  ],
  "policies": [
    {
      "name": "AGBAC-Min-Policy",
      "conditions": {
        "clients": {
          "include": ["ALL_CLIENTS"]
        }
      },
      "rules": [
        {
          "name": "Allow AGBAC-Min Token Issuance",
          "conditions": {
            "grantTypes": {
              "include": ["client_credentials"]
            },
            "scopes": {
              "include": ["system.access"]
            }
          },
          "actions": {
            "token": {
              "accessTokenLifetimeMinutes": 10
            }
          }
        }
      ]
    }
  ]
}
```

---

















### **6.5 Custom Claims (Dual-Subject Token)**

> In AGBAC‑Min, . 

#### **Claim: `sub` (Agent)**

* Default OAuth subject
* The `sub` claim is automatically set to the agent’s client ID by Okta.


<br>

#### **Claim: `act` (Human)**

* The agent token does **not** dynamically carry the human identity at issue time
* The upstream app binds the human at invocation.
* No action needed.

<br>

### **6.6 Delegation Metadata Claim**

Create a minimal delegation claim:

1. In **Claims**, click **Add Claim**.
2. Fill:

   * **Name:** `delegation`
   * **Include in:** *Access Token*
   * **Value type:** *JSON*
   * **Value:**

     ```json
     {
       "method": "explicit",
       "profile": "AGBAC-Min-Okta"
     }
     ```
   * **Scopes:** select **system.access**
3. Click **Create**.

<br>

Example Delegation Claim

## `okta/claims/delegation-claim.json`

```json
{
  "name": "delegation",
  "claimType": "RESOURCE",
  "valueType": "JSON",
  "value": {
    "method": "explicit",
    "profile": "AGBAC-Min-Okta"
  },
  "conditions": {
    "scopes": ["system.access"]
  },
  "includeInTokens": {
    "accessToken": true,
    "idToken": false
  }
}
```

<br>







1. In **Claims**, click **Add Claim**.
2. Fill:

   * **Name:** `agbac_ver`
   * **Include in:** *Access Token*
   * **Value type:** *String*
   * **Value:** `1.0`
   * **Scopes:** select **system.access**
3. Click **Create**.

<br>

Example Ver Claim

## `okta/claims/agbac-ver-claim.json`

```json
{
  "name": "agbac_ver",
  "claimType": "RESOURCE",
  "valueType": "STRING",
  "value": "1.0",
  "conditions": {
    "scopes": ["system.access"]
  },
  "includeInTokens": {
    "accessToken": true,
    "idToken": false
  }
}
```

---



<br>

## 6. Application / Orchestrator: Bind Human Context to Agent Invocation

This step is **not in Okta** — it is done in your application code to ensure the agent invocation carries the human identity.

### Why

In a client credentials flow, Okta cannot infer the human identity. So you must propagate the human from the application to the agent.

### What to Do (High‑Level)

* When a human user interacts with your application (they are authenticated via Okta), and an LLM/agent is invoked:

  1. Extract the human’s Okta identity (e.g., email).
  2. Pass that identity to the agent as internal context (HTTP headers or payload).
  3. The agent uses that context when acting.

> This ensures human identity is tied to the action.

(No explicit Okta UI steps — this is code in your app.)










```md
This agent implementation demonstrates:

• Proper OAuth2 client_credentials usage
• Correct AGBAC-Min token handling
• No token modification
• No privilege inference
• Production-safe request patterns
```

---

Example agent token request

## `agent/token_request.py`

```python
import requests
import os

OKTA_DOMAIN = os.getenv("OKTA_DOMAIN")
CLIENT_ID = os.getenv("OKTA_CLIENT_ID")
CLIENT_SECRET = os.getenv("OKTA_CLIENT_SECRET")
AUTH_SERVER_ID = "AGBAC-Min-AS"

TOKEN_URL = f"https://{OKTA_DOMAIN}/oauth2/{AUTH_SERVER_ID}/v1/token"

def request_agbac_token():
    response = requests.post(
        TOKEN_URL,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "scope": "system.access"
        },
        timeout=10
    )

    response.raise_for_status()
    return response.json()["access_token"]

if __name__ == "__main__":
    token = request_agbac_token()
    print("AGBAC-Min Token acquired")
```

---

Example agent call

## `agent/api_call.py`

```python
import requests
from token_request import request_agbac_token

API_URL = "https://finance.example.com/api/v1/reports"

def call_protected_api():
    token = request_agbac_token()

    response = requests.get(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        },
        timeout=10
    )

    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    result = call_protected_api()
    print("API call successful:", result)
```

---

Production Rules the Agent MUST Follow

✔ One OAuth client per agent
✔ Never reuse human tokens
✔ Never modify JWT claims
✔ Always pass token verbatim
✔ Respect token TTL
✔ Log correlation IDs



























---

## 7. Agent OAuth Token Request

Your agent (e.g., Node, Python) will request an Okta token:

### Token URL

```
POST https://<your‑org>.okta.com/oauth2/AGBAC‑Min‑AS/v1/token
```

### Request

* **Auth:** `Basic` with `client_id:client_secret`
* **Body (x‑www‑form‑urlencoded):**

  ```
  grant_type=client_credentials
  scope=system.access
  ```

Okta returns an access token with the agent’s identity.

> This token authenticates the agent.


Example Token: 

```json
{
  "sub": "agent:finance-agent-app",
  "act": {
    "sub": "user:alice@corp.example"
  },
  "scp": ["system.access"],
  "delegation": {
    "method": "explicit",
    "profile": "AGBAC-Min-Okta"
  },
  "agbac_ver": "1.0"
}
```

<br>

Example Token

## `tokens/example-agbac-min-access-token.json`

```json
{
  "iss": "https://corp.okta.com/oauth2/AGBAC-Min-AS",
  "aud": "api://default",
  "exp": 1767039000,
  "iat": 1767038400,
  "sub": "agent:finance-agent-app",
  "scp": ["system.access"],
  "act": {
    "sub": "user:alice@corp.example"
  },
  "delegation": {
    "method": "explicit",
    "profile": "AGBAC-Min-Okta"
  },
  "agbac_ver": "1.0"
}
```

---

<br>








## **8. Enforcement Behavior**

### **Allowed**

| Agent Assigned | Human Assigned | Result |
| -------------- | -------------- | ------ |
| ✅              | ✅              | ALLOW  |

### **Denied**

| Agent Assigned | Human Assigned | Result |
| -------------- | -------------- | ------ |
| ❌              | ✅              | DENY   |
| ✅              | ❌              | DENY   |
| ❌              | ❌              | DENY   |

No access path exists where **only one subject** is authorized.

<br>


At the system’s API:

1. Validate the access token against Okta (issuer, signature, expiry).
2. Confirm the agent identity is allowed (assignment).
3. Confirm the human identity (received via application context headers/payload) is allowed.
4. Enforce both — agent AND human.

---





## **9. Audit & Logging**

Okta System Logs will record:

* Agent OAuth client
* Human user
* Application accessed
* Time of access
* Success / failure

This enables **dual-subject audit trails** without additional tooling.

<br>


Capture structured events on each action:

* Agent ID (from token `sub`)
* Human ID (from context)
* System / App name
* Timestamp
* Correlation ID
* Decision (Allow / Deny)

This provides complete accountability.

<br>

Example Audit event

## `audit/agbac-min-audit-event.json`

```json
{
  "timestamp": "2025-12-29T12:01:03Z",
  "agent": "agent:finance-agent-app",
  "human": "user:alice@corp.example",
  "action": "system_access",
  "system": "FinanceApp",
  "decision": "ALLOW",
  "correlation_id": "7c4a8d09-ca45-4e9c-bc99-acde48001122"
}
```

---

<br>


## **10. Operational Guidance**

### **Revocation**

* Remove human from AD group → access revoked
* Remove agent assignment → access revoked
* Disable agent OAuth app → all access revoked

<br>


### Revoke Human

1. Remove user from relevant AD group in AD.
2. Sync group to Okta.
3. Human access revoked immediately.

### Revoke Agent

1. In Okta Admin:

   * Go to **Applications ➜ Applications ➜ finance‑agent‑app**.
   * Click **Deactivate** or **Delete**.

### Rotate Secrets

1. Go to **Applications ➜ Applications**.
2. Select the agent app.
3. Go to **General**.
4. Click **Edit Credentials**.

---













### **Least Privilege**

* Agents should be assigned to **only the systems they require**
* Humans should retain **normal RBAC discipline**

<br>

## **11. Security Guarantees Provided**

AGBAC-Min-Okta guarantees:

* No agent-only access
* No human-only proxying
* No permission escalation
* Clear accountability
* Compatibility with Zero Trust models

<br>

## **12. Relationship to AGBAC-Full**

AGBAC-Min-Okta implements a **bounded subset** of the AGBAC specification.

Future profiles may add:

* Object-level enforcement
* Policy engines
* Delegation chains
* Dedicated PEPs

All future profiles remain **backward-compatible** with this foundational model.

---

## **13. Philosophy**

> AGBAC-Min-Okta exists to show that **stronger AI security is achievable today** using the IAM systems enterprises already trust — while providing a clear path toward more advanced enforcement models over time.

