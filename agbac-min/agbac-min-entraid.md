# **AGBAC-Min-EntraID**

## **Foundational AGBAC Profile for Microsoft Entra ID**

**Profile ID:** AGBAC-Min-EntraID
**AGBAC Version:** 1.0
**Scope:** System-level access only
**Identity Platform:** Microsoft Entra ID (Azure AD)
**Enforcement:** Entra ID native authorization
**Code Required:** None (configuration only)

---

## **1. Purpose**

AGBAC-Min-EntraID is a **foundational implementation profile** of the **AI-Agent-Based Access Control (AGBAC)** specification, demonstrating how **core AGBAC principles** can be implemented today using:

* Microsoft Entra ID (Azure AD)
* Azure AD Enterprise Applications
* App registrations (service principals)
* OAuth 2.0 / OpenID Connect
* App roles and group assignments
* Token claims configuration

This profile enables organizations to safely allow **AI agents to access enterprise systems on behalf of users**, while enforcing the following invariant:

> **An AI agent may access a system on behalf of a user only if BOTH the agent and the human user are independently authorized for that system.**

---

## **2. What This Profile Implements**

### **Implemented AGBAC Capabilities**

✅ AI agents as first-class identities
✅ Human identities managed in Entra ID
✅ Dual-subject access tokens (`sub` + `act`)
✅ Explicit delegation semantics
✅ System-level (application-level) access control
✅ Dual-subject audit attribution

---

### **Out of Scope for This Profile**

❌ Object-level authorization
❌ Centralized policy engines (OPA, Cedar)
❌ Multi-agent delegation chains
❌ AI reasoning or prompt validation
❌ Custom enforcement services

These capabilities are addressed by the **full AGBAC specification** and future AGBAC profiles.

---

## **3. Architecture Overview**

### **Actors**

| Actor         | Entra ID Representation                  |
| ------------- | ---------------------------------------- |
| Human user    | Entra ID user                            |
| AI agent      | App Registration (service principal)     |
| Authorization | Entra ID token issuance + app assignment |
| Target system | Entra ID–protected application           |

---

### **High-Level Flow**

```
1. Human authenticates to Entra ID
2. Human instructs AI agent
3. Agent requests OAuth token
4. Entra ID issues access token:
      - sub = agent (service principal)
      - act = human user
5. Agent accesses protected system
6. Entra ID enforces:
      - agent app assignment
      - human app assignment
7. Audit logs record both identities
```

---

## **4. Identity Model**

### **4.1 Human Identity**

* Humans are managed as **Entra ID users**
* Group membership represents **system-level authorization**
* Groups are assigned to applications

**Example Groups**

| Group Name         | Purpose                       |
| ------------------ | ----------------------------- |
| `FinanceApp-Users` | Access to Finance application |
| `HRApp-Users`      | Access to HR application      |

---

### **4.2 Agent Identity**

Each AI agent is represented as a **dedicated App Registration**.

**Requirements**

* One App Registration per agent (recommended)
* Client Credentials flow enabled
* No interactive login
* Assigned only to approved applications

**Example Agents**

| Agent            | App Registration    |
| ---------------- | ------------------- |
| Finance AI Agent | `finance-agent-app` |
| HR AI Agent      | `hr-agent-app`      |

---

## **5. System-Level Authorization Model**

AGBAC-Min-EntraID enforces the following rule **by configuration**:

```
ALLOW system access
IFF
  agent service principal is assigned to the application
AND
  human user is assigned to the application
```

This achieves **dual-subject authorization** at the system boundary using native Entra ID controls.

---

## **6. Entra ID Configuration — Step by Step**

---

### **6.1 Create Enterprise Applications (Target Systems)**

For each protected system:

1. Create an **Enterprise Application**

   * OIDC or SAML
2. Require Entra ID authentication
3. Disable anonymous access

**Example Applications**

* `FinanceApp`
* `HRApp`

---

### **6.2 Configure Human Access**

1. Create Entra ID security groups
2. Assign groups to Enterprise Applications

**Example**

| Application | Assigned Group     |
| ----------- | ------------------ |
| FinanceApp  | `FinanceApp-Users` |
| HRApp       | `HRApp-Users`      |

Only users in these groups may access the system.

---

### **6.3 Create Agent App Registrations**

For each AI agent:

1. Create a new **App Registration**
2. Enable **Client Credentials** (application permissions)
3. Generate client secret or certificate
4. Disable user sign-in
5. Assign the agent to allowed applications

**Assignment is critical** — unassigned agents cannot access the system.

---

### **6.4 Assign Agents to Applications**

1. Open the target Enterprise Application
2. Assign the **agent service principal** as a user
3. (Optional) Assign an app role such as `AgentAccess`

This ensures the agent must be explicitly trusted for the system.

---

## **7. Token Configuration (Dual-Subject Claims)**

### **7.1 Agent Subject (`sub`)**

* Automatically set by Entra ID
* Identifies the **service principal (agent)**

---

### **7.2 Human Actor (`act`)**

Add a **custom token claim**:

* **Name:** `act`
* **Type:** JSON
* **Source:** User attributes
* **Value:**

```json
{
  "sub": "user.userprincipalname"
}
```

* Included in **access tokens**
* Emitted when a user context is present

This represents the **human principal** whose intent triggered the agent action.

---

### **7.3 Delegation Metadata Claim**

Add a static delegation marker:

* **Name:** `delegation`
* **Value:**

```json
{
  "method": "explicit",
  "profile": "AGBAC-Min-EntraID"
}
```

This indicates AGBAC delegation semantics without requiring custom code.

---

## **8. Resulting Token (Example)**

```json
{
  "sub": "spn:finance-agent-app",
  "act": {
    "sub": "user:alice@corp.example"
  },
  "scp": ["system.access"],
  "delegation": {
    "method": "explicit",
    "profile": "AGBAC-Min-EntraID"
  },
  "agbac_ver": "1.0"
}
```

---

## **9. Enforcement Behavior**

### **Access Outcomes**

| Agent Assigned | Human Assigned | Result |
| -------------- | -------------- | ------ |
| ✅              | ✅              | ALLOW  |
| ❌              | ✅              | DENY   |
| ✅              | ❌              | DENY   |
| ❌              | ❌              | DENY   |

There is **no configuration path** that allows agent-only or human-only access.

---

## **10. Audit & Logging**

Entra ID audit and sign-in logs capture:

* Service principal (agent)
* User principal
* Application accessed
* Time of access
* Success or failure

This provides **dual-subject accountability** using native Microsoft logging.

---

## **11. Operational Guidance**

### **Revocation**

* Remove user from group → access revoked
* Remove agent assignment → access revoked
* Disable agent app → access revoked

---

### **Least Privilege**

* Assign agents only to required systems
* Keep human group membership narrowly scoped
* Prefer certificates over secrets for agents

---

## **12. Security Guarantees Provided**

AGBAC-Min-EntraID guarantees:

* No agent-only access
* No human-only proxying
* No permission escalation through AI
* Explicit accountability
* Compatibility with Zero Trust principles

---

## **13. Extensibility**

This profile is designed to align with other AGBAC-Min profiles:

* AGBAC-Min-Okta
* AGBAC-Min-Auth0
* AGBAC-Min-Keycloak

All share the **same security semantics**, differing only in platform configuration.

---

## **14. Relationship to AGBAC-Full**

AGBAC-Min-EntraID implements a **bounded subset** of the AGBAC specification.

Future AGBAC-Full implementations may introduce:

* Object-level enforcement
* Policy decision points
* Delegation chains
* Dedicated PEPs

All future profiles remain **conceptually compatible** with this foundation.

---

## **15. Philosophy**

> AGBAC-Min-EntraID demonstrates that **strong AI access control is achievable today** using Microsoft Entra ID — while providing a clear path toward richer enforcement models as enterprise IAM evolves.

