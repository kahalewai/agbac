# **AGBAC-Min-Keycloak**

## **Foundational AGBAC Profile for Keycloak**

**Profile ID:** AGBAC-Min-Keycloak
**AGBAC Version:** 1.0
**Scope:** System-level access only
**Identity Platform:** Keycloak (Workforce / Enterprise realms)
**Enforcement:** Keycloak native authorization and application assignments
**Code Required:** None (configuration only; optional built-in mappers)

---

## **1. Purpose**

AGBAC-Min-Keycloak is a **foundational implementation profile** of the **AI-Agent-Based Access Control (AGBAC)** specification. It demonstrates how **core AGBAC principles** can be realized today using:

* Keycloak realms
* Users and groups
* Service accounts (client credentials)
* OAuth 2.0 / OpenID Connect
* Client roles and group roles
* Protocol mappers for token claims

This profile enables organizations to allow **AI agents to access enterprise systems on behalf of users**, while enforcing the central AGBAC invariant:

> **An AI agent may access a system on behalf of a user only if BOTH the agent and the human user are independently authorized for that system.**

---

## **2. What This Profile Implements**

### **Implemented AGBAC Capabilities**

✅ AI agents as first-class identities
✅ Human identities managed in Keycloak
✅ Dual-subject access tokens (`sub` + `act`)
✅ Explicit delegation semantics
✅ System-level (client-level) authorization
✅ Dual-subject audit attribution

---

### **Out of Scope for This Profile**

❌ Object-level authorization
❌ Centralized external policy engines (OPA, Cedar)
❌ Multi-agent delegation chains
❌ AI reasoning or prompt validation
❌ Custom enforcement proxies or gateways

These capabilities are addressed in the **full AGBAC specification** and future AGBAC profiles.

---

## **3. Architecture Overview**

### **Actors**

| Actor         | Keycloak Representation                      |
| ------------- | -------------------------------------------- |
| Human user    | Keycloak user                                |
| AI agent      | Keycloak client with Service Account enabled |
| Authorization | Keycloak token issuance + role enforcement   |
| Target system | Keycloak-protected client/application        |

---

### **High-Level Flow**

```
1. Human authenticates to Keycloak
2. Human instructs AI agent
3. Agent authenticates using client credentials
4. Keycloak issues access token:
      - sub = agent (service account client)
      - act = human user
5. Agent accesses protected system
6. Keycloak enforces:
      - agent client role
      - human user role
7. Logs capture both identities
```

---

## **4. Identity Model**

### **4.1 Human Identity**

* Humans are represented as **Keycloak users**
* Groups or realm/client roles represent **system-level access**
* Users are assigned to groups or roles

**Example Roles / Groups**

| Role / Group       | Purpose                       |
| ------------------ | ----------------------------- |
| `finance-app-user` | Access to Finance application |
| `hr-app-user`      | Access to HR application      |

---

### **4.2 Agent Identity**

Each AI agent is represented as a **Keycloak client** with a **service account**.

**Requirements**

* One client per agent (recommended)
* Service Accounts enabled
* Client Credentials flow enabled
* Assigned only to approved client roles

**Example Agents**

| Agent            | Keycloak Client        |
| ---------------- | ---------------------- |
| Finance AI Agent | `finance-agent-client` |
| HR AI Agent      | `hr-agent-client`      |

---

## **5. System-Level Authorization Model**

AGBAC-Min-Keycloak enforces the following rule **by configuration**:

```
ALLOW system access
IFF
  agent client has required client role
AND
  human user has required role or group
```

This ensures **dual-subject authorization** at the system (client) boundary.

---

## **6. Keycloak Configuration — Step by Step**

---

### **6.1 Create a Realm**

1. Create or select a **Keycloak realm**
2. Configure standard security settings (TLS, token lifetimes)

This realm will host **users, agents, and applications**.

---

### **6.2 Create Clients (Target Systems)**

For each protected system:

1. Create a **Client**
2. Set:

   * Access Type: `confidential`
   * Standard Flow: enabled (for humans)
   * Service Accounts: enabled (for agents)
3. Configure redirect URIs as required

**Example Clients**

* `finance-app`
* `hr-app`

---

### **6.3 Configure Human Authorization**

#### **Option A — Realm Roles**

1. Create realm roles:

   * `finance-app-user`
   * `hr-app-user`
2. Assign roles to users

#### **Option B — Groups (Recommended)**

1. Create groups:

   * `FinanceAppUsers`
   * `HRAppUsers`
2. Map groups to roles if desired
3. Assign users to groups

Only users with the correct role/group may access the system.

---

### **6.4 Create Agent Clients**

For each AI agent:

1. Create a new **Client**
2. Enable **Service Accounts**
3. Disable standard user login
4. Generate client secret or configure mTLS

---

### **6.5 Assign Agent Roles**

1. Create **client roles** on the target system client:

   * Example: `agent-access`
2. Assign the role to the **agent service account**

If the agent does not have the role, it cannot access the system.

---

## **7. Token Configuration (Dual-Subject Claims)**

Keycloak **Protocol Mappers** are used to add AGBAC claims.

---

### **7.1 Agent Subject (`sub`)**

* Automatically populated
* Identifies the agent client (service account)

---

### **7.2 Human Actor (`act`) Claim**

Create a **Protocol Mapper** on the target client:

* **Mapper Type:** Script Mapper (or User Attribute Mapper)
* **Token Claim Name:** `act`
* **Claim JSON Type:** JSON
* **Script Example:**

```javascript
var user = userSession.getUser();
if (user !== null) {
  token.setOtherClaims("act", {
    sub: "user:" + user.getUsername()
  });
}
```

This embeds the **human principal** when a user context exists.

---

### **7.3 Delegation Metadata Claim**

Create a static mapper:

* **Token Claim Name:** `delegation`
* **Value:**

```json
{
  "method": "explicit",
  "profile": "AGBAC-Min-Keycloak"
}
```

---

### **7.4 AGBAC Version Claim**

```json
{
  "agbac_ver": "1.0"
}
```

---

## **8. Resulting Token (Example)**

```json
{
  "sub": "agent:finance-agent-client",
  "act": {
    "sub": "user:alice@corp.example"
  },
  "realm_access": {
    "roles": ["finance-app-user"]
  },
  "resource_access": {
    "finance-app": {
      "roles": ["agent-access"]
    }
  },
  "delegation": {
    "method": "explicit",
    "profile": "AGBAC-Min-Keycloak"
  },
  "agbac_ver": "1.0"
}
```

---

## **9. Enforcement Behavior**

### **Access Outcomes**

| Agent Role | Human Role | Result |
| ---------- | ---------- | ------ |
| ✅          | ✅          | ALLOW  |
| ❌          | ✅          | DENY   |
| ✅          | ❌          | DENY   |
| ❌          | ❌          | DENY   |

There is **no supported configuration** that allows access based on only one subject.

---

## **10. Audit & Logging**

Keycloak event logs capture:

* Client ID (agent)
* User ID (human)
* Client accessed
* Timestamp
* Success or failure

This provides **dual-subject accountability** using Keycloak-native logging.

---

## **11. Operational Guidance**

### **Revocation**

* Remove user from group / role → access revoked
* Remove agent client role → access revoked
* Disable agent client → access revoked

---

### **Least Privilege**

* Assign agents only required client roles
* Keep human roles narrowly scoped
* Prefer short-lived tokens
* Rotate client secrets or use mTLS

---

## **12. Security Guarantees Provided**

AGBAC-Min-Keycloak guarantees:

* No agent-only access
* No human-only proxying
* No privilege escalation via AI
* Clear accountability for actions
* Alignment with Zero Trust principles

---

## **13. Extensibility**

AGBAC-Min-Keycloak aligns with:

* AGBAC-Min-Okta
* AGBAC-Min-EntraID
* AGBAC-Min-Auth0

All profiles implement the **same security semantics**, differing only in platform configuration details.

---

## **14. Relationship to AGBAC-Full**

AGBAC-Min-Keycloak implements a **bounded subset** of the AGBAC specification.

Future AGBAC-Full implementations may introduce:

* Object-level authorization
* Policy engines (OPA / Cedar)
* Delegation chains
* Dedicated PEP components

This profile remains **forward-compatible** with those models.

---

## **15. Philosophy**

> AGBAC-Min-Keycloak demonstrates that **strong AI access control can be achieved today** using open-source IAM — while providing a clear, standards-aligned path toward richer AGBAC enforcement models in the future.

