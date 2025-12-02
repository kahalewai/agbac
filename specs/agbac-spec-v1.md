# **AGBAC Specification v1.0 (Draft)**

**AI-Agent-Based Access Control (AGBAC)**
**Open Security Specification — 2025**

---

# **Status of This Document**

This is a **draft** specification published for community review.
The goal of AGBAC is to define a universal, open, interoperable access control model that governs how **AI agents perform actions on behalf of human users** using **existing IAM technologies** (OAuth2, OIDC, JWT, RBAC, ABAC, PBAC, etc.).

This document defines:

* AGBAC terminology
* Identity model
* Token requirements
* Delegation model
* Policy requirements
* Enforcement requirements
* Audit and logging standards
* Security and threat considerations

This specification is open, royalty-free, and intended for public implementation.

---

# **1. Introduction**

## 1.1 Purpose

AGBAC defines an access control model for **autonomous or semi-autonomous AI agents** acting **on behalf of** human users.
Unlike traditional access control models (RBAC, PBAC, ABAC), where **the human user directly performs the action**, AGBAC governs scenarios where:

* **The human communicates instructions to an AI agent**, and
* **The AI agent executes actions in a system using its own identity**,
* **But only to the extent the human is also permitted to perform the action**.

Thus AGBAC requires **dual-subject authorization**:

**An action must be authorized for BOTH the human user AND the AI agent.**

AGBAC is designed to be implemented using **existing IAM systems** without requiring new infrastructure.

---

# **2. Terminology**

### **Agent Identity**

A digital identity representing an AI system, model, agent, or automation capable of making authenticated requests.

### **Human Principal**

A human user whose intent triggers AI agent actions.

### **Delegated Intent**

An explicit instruction from a human principal authorizing an AI agent to perform actions.

### **Dual-Subject Authorization**

An evaluation that requires:

1. **The agent is permitted to perform the requested action**, AND
2. **The human is permitted to instruct the agent to perform the requested action**.

### **Delegation Token**

A token containing both human and agent identity information.

### **PDP / PEP**

* *Policy Decision Point* (e.g., OPA, Cedar)
* *Policy Enforcement Point* (e.g., API gateway, service)

### **Resource Server**

A system receiving requests from an AI agent.

---

# **3. Identity Requirements**

## 3.1 Agent Identity

The agent identity must be authenticated using:

* OIDC (recommended)
* OAuth2 client credentials
* SPIFFE/SPIRE identity
* mTLS certificates
* Platform-provided workload identities

AGBAC does **not** define new identity types.

## 3.2 Human Identity

Human identity MUST use the enterprise’s existing IdP:

* Azure AD
* Okta
* Auth0
* Keycloak
* AWS IAM Identity Center
* SAML IdPs

---

# **4. Token Requirements**

AGBAC-compliant requests must carry a **Delegation Token** containing **both** human and agent subjects.

This MUST be expressible in existing JWT/OIDC token formats.

## 4.1 Required Claims

### **4.1.1 `sub` — Agent Subject (REQUIRED)**

Represents the AI agent identity.

```
"sub": "agent:example-ai-123"
```

### **4.1.2 `act` — Human Actor (REQUIRED)**

Uses the standard OAuth “Actor” claim.

```
"act": {
  "sub": "user:alice@example.com"
}
```

### **4.1.3 `delegation` — Delegated Intent (REQUIRED)**

Describes the nature, scope, and time of the delegation.

Example:

```
"delegation": {
  "granted_at": "2025-12-01T15:32Z",
  "method": "explicit",
  "intent_summary": "User requested AI agent to retrieve customer records"
}
```

### **4.1.4 `agbac_ver` — AGBAC Version**

```
"agbac_ver": "1.0"
```

### **4.1.5 `scp` / `permissions` — Agent Permissions**

The agent’s allowed actions.

### **4.1.6 `usr_scopes` — Human Permissions**

Optional if policies resolve this independently.

```
"usr_scopes": ["read:customer-records"]
```

### **4.1.7 `agent_confidence_level` (OPTIONAL)**

For organizations evaluating model reliability, safety or alignment.

---

# **5. Authorization Model**

## 5.1 Dual-Subject Authorization Rule (Core Requirement)

A policy engine MUST evaluate AGBAC requests according to the following model:

```
ALLOW(action, resource)
IFF
    AgentIdentity is permitted to perform action on resource
AND
    HumanIdentity is permitted to perform action on resource
AND
    DelegatedIntent is valid, non-expired, and appropriate for the action
```

This is **the defining behavior** of AGBAC.

## 5.2 No Permission Escalation

The AI agent MUST NOT gain any permissions through delegation.

The human MUST NOT gain new permissions through agent execution.

## 5.3 Delegation Scope

Policies should define:

* which humans may delegate actions to which agents
* which agents may act on behalf of which humans
* which actions require explicit delegation

---

# **6. Delegation Requirements**

## 6.1 Types of Delegation

### **6.1.1 Explicit Delegation (RECOMMENDED)**

Human intentionally instructs the AI agent to perform an action.

### **6.1.2 Implicit Delegation (NOT RECOMMENDED)**

Agent infers user desires through contextual interaction.
Must be explicitly permitted by policy.

### **6.1.3 System Delegation (PERMITTED)**

System workflows automatically assign tasks to AI agents.

---

# **7. Policy Requirements**

## 7.1 AGBAC Policy Must Support:

1. Agent permissions
2. Human permissions
3. Delegation relationship
4. Resource constraints
5. Contextual constraints

## 7.2 Implementation

Policies may be implemented in:

* OPA/Rego
* Cedar
* Zanzibar-like systems
* AWS IAM
* Azure Role Assignments
* Keycloak Authorization Services

AGBAC does **not** mandate a specific policy engine.

---

# **8. Enforcement Requirements**

## 8.1 PEP Requirements

A Policy Enforcement Point MUST:

1. Accept a Delegation Token from the AI agent
2. Verify the token’s signature and issuer
3. Extract both identities (`sub` and `act`)
4. Forward both identities to the PDP for evaluation
5. Deny access if either subject fails authorization
6. Generate an audit event (see Section 9)

## 8.2 Token Acquisition

AGBAC recommends OAuth **Token Exchange (RFC 8693)** for issuing delegation tokens.

---

# **9. Audit & Logging Requirements**

Every AGBAC-controlled action MUST generate a structured audit event containing:

### Required Fields:

* Timestamp
* Agent identity
* Human identity
* Action performed
* Resource affected
* Delegation type
* Delegation context
* Policy decision (allow/deny)
* Reason for decision
* Correlation ID

### Optional Fields:

* Agent reasoning summary
* Safety confidence score

Audit events MUST NOT contain raw prompts or confidential user content unless explicitly configured.

---

# **10. Security Considerations**

## 10.1 Supported Threats

AGBAC is designed to mitigate:

* AI privilege escalation
* Human permission overreach via AI
* Prompt-injection leading to unauthorized actions
* Misuse of autonomous agents
* Undocumented delegation
* Cross-user impersonation
* Agent impersonation
* Token replay
* Delegation tampering

## 10.2 Token Security

Delegation tokens MUST:

* be signed
* have short TTLs
* be bound to transport layer (e.g., mTLS, DPoP, token binding where possible)

## 10.3 Logging & Privacy

Audit logs must be sanitized of unnecessary personal data.

---

# **11. Interoperability Requirements**

AGBAC implementations **must use existing IAM standards**, including:

* OAuth 2.0
* OAuth 2.0 Token Exchange (RFC 8693)
* OIDC
* JWT
* XACML, OPA, or Cedar for policy
* Existing enterprise IdPs

No new token formats or cryptographic primitives are defined by AGBAC.

---

# **12. Reference Flows**

## 12.1 Human → AI Agent → Resource Server

```
Human → AI Agent: "Get customer record 553"
AI Agent → Token Service: Token Exchange (include Human identity)
Token Service → AI Agent: AGBAC Delegation Token
AI Agent → Resource Server: API Request + Token
Resource Server → PDP: Evaluate dual-subject
PDP → Resource Server: ALLOW or DENY
Resource Server: Return response
Audit System: Log AGBAC event
```

---

# **13. Conformance Requirements**

An implementation is AGBAC-conformant if:

### REQUIRED:

1. Uses dual-subject tokens including `sub` and `act` claims
2. Enforces dual-subject authorization
3. Logs all AGBAC decisions
4. Validates delegation scope
5. Uses a secure token format (JWT/OIDC)

### RECOMMENDED:

1. Implements OAuth Token Exchange
2. Supports OPA or Cedar policy templates
3. Supports explicit delegation workflows

---

# **14. Versioning**

AGBAC versions follow semantic versioning:

```
MAJOR.MINOR.PATCH
```

This spec is **v1.0.0-draft**.

---

# **15. Licensing**

This specification is published under the 

---

# **End of AGBAC v1.0 Specification (Draft)**
