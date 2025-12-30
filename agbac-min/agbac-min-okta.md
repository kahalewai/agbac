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

* Agent identities as first-class principals
* Human identities from AD → Okta
* Dual-subject tokens (`sub` + `act`)
* Explicit delegation semantics
* System-level access control
* Dual-subject audit attribution

### **Does Not Implement**

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

### **6.1 Create Okta Applications (Target Systems)**

For each protected system:

1. Create an **OIDC or SAML Application** in Okta
2. Enable access via Okta authentication
3. Do NOT allow public access

**Example Applications**

* `FinanceApp`
* `HRApp`

<br>

### **6.2 Configure Human Access (AD → Okta)**

1. Sync AD groups to Okta
2. Assign groups to applications

**Example**

| Application | Assigned Group      |
| ----------- | ------------------- |
| FinanceApp  | `FINANCE_APP_USERS` |
| HRApp       | `HR_APP_USERS`      |

<br>

### **6.3 Create Agent OAuth Applications**

For each AI agent:

1. Create a **Service Application**
2. Enable **Client Credentials**
3. Disable user login
4. Assign the agent to allowed applications

**Example**

| Agent App         | Assigned Application |
| ----------------- | -------------------- |
| finance-agent-app | FinanceApp           |
| hr-agent-app      | HRApp                |

<br>

### **6.4 Authorization Server Configuration**

Use a **Custom Authorization Server**.

#### **Required Scopes**

| Scope           | Purpose               |
| --------------- | --------------------- |
| `system.access` | Generic system access |

<br>

### **6.5 Custom Claims (Dual-Subject Token)**

#### **Claim: `sub` (Agent)**

* Default OAuth subject
* Automatically set to agent client ID or name

<br>

#### **Claim: `act` (Human)**

Create a **custom claim**:

* **Name:** `act`
* **Type:** JSON
* **Value Expression:**

```text
{
  "sub": "user." + user.login
}
```

* **Include in:** Access Token
* **Condition:** Token issued in user context

This ensures the human principal is embedded in the token.

<br>

### **6.6 Delegation Metadata Claim**

Create a minimal delegation claim:

* **Name:** `delegation`
* **Type:** JSON
* **Value:**

```json
{
  "method": "explicit",
  "profile": "AGBAC-Min-Okta"
}
```

<br>

## **7. Resulting Token (Example)**

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

## **9. Audit & Logging**

Okta System Logs will record:

* Agent OAuth client
* Human user
* Application accessed
* Time of access
* Success / failure

This enables **dual-subject audit trails** without additional tooling.

<br>

## **10. Operational Guidance**

### **Revocation**

* Remove human from AD group → access revoked
* Remove agent assignment → access revoked
* Disable agent OAuth app → all access revoked

<br>

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

