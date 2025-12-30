# **AGBAC-Min-Auth0**

## **Foundational AGBAC Profile for Auth0**

**Profile ID:** AGBAC-Min-Auth0
**AGBAC Version:** 1.0
**Scope:** System-level access only
**Identity Platform:** Auth0 (Workforce or B2B)
**Enforcement:** Auth0 native authorization
**Code Required:** None (configuration only)

---

## **1. Purpose**

AGBAC-Min-Auth0 is a **foundational implementation profile** of the **AI-Agent-Based Access Control (AGBAC)** specification. It demonstrates how **core AGBAC principles** can be implemented today using:

* Auth0 Workforce or B2B Identity
* OAuth 2.0 / OpenID Connect
* Machine-to-Machine (M2M) applications
* Roles and permissions
* Custom token claims (Actions)
* Application-level access control

This profile enables organizations to allow **AI agents to access enterprise systems on behalf of users**, while enforcing the following invariant:

> **An AI agent may access a system on behalf of a user only if BOTH the agent and the human user are independently authorized for that system.**

---

## **2. What This Profile Implements**

### **Implemented AGBAC Capabilities**

✅ AI agents as first-class identities
✅ Human identities managed by Auth0
✅ Dual-subject access tokens (`sub` + `act`)
✅ Explicit delegation semantics
✅ System-level (application-level) authorization
✅ Dual-subject audit attribution

---

### **Out of Scope for This Profile**

❌ Object-level authorization
❌ External policy engines (OPA, Cedar)
❌ Multi-agent delegation chains
❌ AI reasoning or prompt validation
❌ Custom enforcement proxies

These capabilities are addressed by the **full AGBAC specification** and future AGBAC profiles.

---

## **3. Architecture Overview**

### **Actors**

| Actor         | Auth0 Representation               |
| ------------- | ---------------------------------- |
| Human user    | Auth0 user                         |
| AI agent      | Auth0 Machine-to-Machine (M2M) app |
| Authorization | Auth0 Authorization Server         |
| Target system | Auth0-protected application / API  |

---

### **High-Level Flow**

```
1. Human authenticates to Auth0
2. Human instructs AI agent
3. Agent requests OAuth token
4. Auth0 issues access token:
      - sub = agent (M2M client)
      - act = human user
5. Agent calls protected system
6. Auth0 enforces:
      - agent permissions
      - human role membership
7. Logs capture both identities
```

---

## **4. Identity Model**

### **4.1 Human Identity**

* Humans are represented as **Auth0 users**
* Roles represent **system-level authorization**
* Users are assigned roles directly or via groups

**Example Roles**

| Role             | Purpose                  |
| ---------------- | ------------------------ |
| `FinanceAppUser` | Access to Finance system |
| `HRAppUser`      | Access to HR system      |

---

### **4.2 Agent Identity**

Each AI agent is represented as a **Machine-to-Machine (M2M) Application** in Auth0.

**Requirements**

* One M2M application per agent (recommended)
* Client Credentials flow enabled
* No interactive login
* Explicitly granted permissions

**Example Agents**

| Agent            | Auth0 Application   |
| ---------------- | ------------------- |
| Finance AI Agent | `finance-agent-m2m` |
| HR AI Agent      | `hr-agent-m2m`      |

---

## **5. System-Level Authorization Model**

AGBAC-Min-Auth0 enforces the following rule **by configuration and conventions**:

```
ALLOW system access
IFF
  agent has required API permissions
AND
  human user has required role
```

This ensures **dual-subject authorization** at the system boundary.

---

## **6. Auth0 Configuration — Step by Step**

---

### **6.1 Create APIs (Protected Systems)**

For each protected system:

1. Create an **API** in Auth0
2. Define an Identifier (audience)
3. Enable RBAC
4. Enable “Add Permissions in the Access Token”

**Example APIs**

* `FinanceAPI`
* `HRAPI`

---

### **6.2 Configure Human Authorization**

1. Create roles in Auth0
2. Assign permissions to roles
3. Assign users to roles

**Example**

| API        | Required Role    |
| ---------- | ---------------- |
| FinanceAPI | `FinanceAppUser` |
| HRAPI      | `HRAppUser`      |

---

### **6.3 Create Agent M2M Applications**

For each AI agent:

1. Create an **M2M Application**
2. Authorize it for the target API
3. Grant only required permissions

**Example Permissions**

| API        | Permission      |
| ---------- | --------------- |
| FinanceAPI | `system:access` |
| HRAPI      | `system:access` |

---

### **6.4 Enforce Agent Authorization**

* Agents **must** have API permissions
* Unauthorized M2M apps cannot obtain valid tokens
* This ensures agent authorization is mandatory

---

## **7. Token Customization (Dual-Subject Claims)**

Auth0 **Actions** are used to add dual-subject semantics.

---

### **7.1 Agent Subject (`sub`)**

* Automatically populated by Auth0
* Identifies the M2M client (agent)

---

### **7.2 Human Actor (`act`) Claim**

Create a **Post-Login Action**:

**Action Type:** Login / Token issuance
**Purpose:** Embed human principal identity

**Claim Added**

```json
{
  "act": {
    "sub": "user.email"
  }
}
```

This claim represents the **human principal** on whose behalf the agent is acting.

---

### **7.3 Delegation Metadata Claim**

Add a static delegation claim:

```json
{
  "delegation": {
    "method": "explicit",
    "profile": "AGBAC-Min-Auth0"
  }
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
  "sub": "agent:finance-agent-m2m",
  "act": {
    "sub": "user:alice@corp.example"
  },
  "permissions": ["system:access"],
  "delegation": {
    "method": "explicit",
    "profile": "AGBAC-Min-Auth0"
  },
  "agbac_ver": "1.0"
}
```

---

## **9. Enforcement Behavior**

### **Access Outcomes**

| Agent Authorized | Human Authorized | Result |
| ---------------- | ---------------- | ------ |
| ✅                | ✅                | ALLOW  |
| ❌                | ✅                | DENY   |
| ✅                | ❌                | DENY   |
| ❌                | ❌                | DENY   |

There is **no supported configuration** where only one subject grants access.

---

## **10. Audit & Logging**

Auth0 logs capture:

* M2M client ID (agent)
* User identity
* API accessed
* Timestamp
* Grant type and decision

This enables **dual-subject auditability** using native Auth0 logs.

---

## **11. Operational Guidance**

### **Revocation**

* Remove user role → access revoked
* Remove agent API permission → access revoked
* Disable M2M app → access revoked

---

### **Least Privilege**

* Grant agents only required API permissions
* Keep human roles narrowly scoped
* Rotate client secrets regularly

---

## **12. Security Guarantees Provided**

AGBAC-Min-Auth0 guarantees:

* No agent-only access
* No human-only proxying
* No permission escalation via AI
* Clear attribution for every access
* Compatibility with Zero Trust models

---

## **13. Extensibility**

This profile aligns with:

* AGBAC-Min-Okta
* AGBAC-Min-EntraID
* Future AGBAC-Min profiles

All share the **same authorization semantics**, differing only in platform mechanics.

---

## **14. Relationship to AGBAC-Full**

AGBAC-Min-Auth0 implements a **bounded subset** of the AGBAC specification.

Future AGBAC-Full implementations may add:

* Object-level enforcement
* Policy engines
* Delegation chains
* Dedicated enforcement points

This profile remains **forward-compatible** with those models.

---

## **15. Philosophy**

> AGBAC-Min-Auth0 shows that **meaningful AI access control improvements are possible today** using Auth0 — while creating a clean path toward richer AGBAC enforcement as IAM platforms evolve.

