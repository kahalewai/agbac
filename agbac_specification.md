# **AGBAC — AI-Agent-Based Access Control**

## **Open Security Specification v1.0**

**Status:** Production-Ready for Public Adoption
**Year:** 2025
**License:** Apache License 2.0
**Audience:** Security architects, IAM engineers, AI platform builders, policy engine authors

---

## **Status of This Document**

This document is a public, production-ready specification released for industry and community adoption.

AGBAC defines an open, vendor-neutral, royalty-free access control model governing how AI agents perform actions on behalf of human principals using existing identity and access management (IAM) technologies (OAuth2, OIDC, JWT, RBAC, ABAC, PBAC, etc.).

This document defines:

* AGBAC terminology
* Identity model
* Token requirements
* Delegation model
* Policy requirements
* Enforcement requirements
* Audit and logging standards
* Security and threat considerations

---

## **1. Purpose and Scope**

AGBAC defines an access control model for dual-subject authorization of autonomous or semi-autonomous AI agents acting on behalf of human users.
Unlike traditional access control models (RBAC, PBAC, ABAC), where the human user directly performs the action, AGBAC governs scenarios where:

* A human principal communicates instructions to an AI agent (authorizes the intent), and
* The AI agent executes actions in a system using its own identity, and
* Both subjects must be independently authorized to perform the action.

Thus AGBAC requires dual-subject authorization:

* An action must be authorized for BOTH the human user AND the AI agent.

AGBAC is designed to be implemented using:
OAuth 2.0, OIDC, JWT, existing identity providers, and existing policy engines.

Thus, AGBAC is designed to be implemented using existing IAM systems without requiring new infrastructure. AGBAC does not replace existing authorization models. It defines how those models are safely composed in AI-driven systems. AGBAC addresses a structural limitation in existing authorization models, which assume the calling principal and authorizing principal are the same entity. AI agents violate this assumption. AGBAC formalizes this distinction.

---

## **1.1 Non-Goals**

AGBAC does not:

* Define a new identity provider
* Define a new authentication mechanism
* Define a new token format or cryptographic primitive
* Replace RBAC, ABAC, PBAC, or policy engines
* Mandate a specific AI model, architecture, or agent framework
* Require changes to OAuth 2.0, OIDC, or existing standards

AGBAC extends existing IAM systems by defining how they must be used together when AI agents act on behalf of humans.

---

## **2. Core Principles**

1. **Dual Authority**
   Both the AI agent and the human principal must be authorized.

2. **No Privilege Transfer**
   Delegation enables execution, not permission inheritance.

3. **Explicit Accountability**
   Every action is attributable to both subjects.

4. **Least Privilege by Construction**
   Constraints apply independently to agents and humans.

5. **Interoperability First**
   Existing standards are reused wherever possible.

---

## **3. Terminology**

**Agent**
A software entity capable of autonomous or semi-autonomous action.

**Agent Identity**
A first-class, non-human, digital identity representing an AI system, model, agent, or automation capable of making authenticated requests.

**Human Principal**
A human user whose intent triggers AI agent execution.

**Delegated Intent**
An explicit instruction from a human principal authorizing an AI agent to execute actions on behalf of a human within explicitly defined bounds.
Delegated intent represents authorization to execute intent, not inferred desire, unless policy explicitly permits it.

**Dual-Subject Authorization**
Authorization requiring approval of two independent subjects.

1. The agent is permitted to perform the requested action, AND
2. The human is permitted to perform the requested action, AND
3. The human is permitted to instruct the agent to perform the requested action.

**Delegation Token**
A token representing both agent and human identities.

**PEP / PDP**
Policy Enforcement Point / Policy Decision Point.

**Resource Server**
A system receiving AI agent requests.

---

## **4. Identity Requirements**

### **4.1 Agent Identity**

Agents must be represented as first-class, non-human identities.

The agent identity must be authenticated using:

* OAuth 2.0 clients
* OIDC workload identities
* mTLS certificates
* SPIFFE/SPIRE identities
* Platform-provided workload identities

AGBAC does not define new identity types.
Agents must not reuse human identities.

---

### **4.2 Human Identity**

Human principals must authenticate via existing enterprise identity providers.

Examples include (non-normative):

* Microsoft Entra ID (Azure AD)
* Okta
* Auth0
* Keycloak
* AWS IAM Identity Center
* Enterprise SAML identity providers

AGBAC does not define human authentication mechanisms.

---

## **5. Delegation Token Requirements**

### **5.1 Overview**

AGBAC-compliant requests must carry a Delegation Token containing both human and agent subjects.
This MUST be expressible in existing JWT/OIDC token formats.

---

### **5.2 Required Claims**

**`sub` — Agent Subject (REQUIRED)**
Represents the AI agent identity.

```
"sub": "agent:example-ai-123"
```

**`act` — Human Actor (REQUIRED)**
Uses the standard OAuth Actor Claim (RFC 8693).

```
"act": {
  "sub": "user:name@example.com"
}
```

> **Normative:**
> The presence of the `act` claim MUST NOT be interpreted as authorization.

**`delegation` — Delegated Intent Context (REQUIRED)**
Includes:

* Grant timestamp
* Delegation method (explicit, implicit, system)
* Intent summary

Describes the nature, scope, and time of the delegation.

Example:

```
"delegation": {
  "granted_at": "2025-12-01T15:32Z",
  "method": "explicit",
  "intent_summary": "User requested AI agent to retrieve customer records"
}
```

**`agbac_ver` — Specification Version (REQUIRED)**

```
"agbac_ver": "1.0"
```

---

### **5.3 Optional Claims**

**`scp` or `permissions` — Agent Permissions (OPTIONAL)**

The agent’s allowed actions.

**`usr_scopes` — Human Permissions (OPTIONAL)**

Optional if policies resolve this independently.

```
"usr_scopes": ["read:customer-records"]
```

**`agent_confidence_level` (OPTIONAL)**

For organizations evaluating model reliability, safety or alignment.

**`delegation_expiry` (OPTIONAL)**

---

## **6. Delegation Semantics**

### **6.1 Delegation Types**

* **Explicit** — Human intentionally authorizes the agent (RECOMMENDED)
* **Implicit** — Intent inferred only if explicitly permitted by policy
* **System-Initiated** — Workflow-driven delegation

---

### **6.2 Delegation Constraints (NORMATIVE)**

Delegation must be:

* Time-bounded
* Scope-bounded
* Revocable
* Independently auditable

---

## **7. Authorization Model**

### **7.1 Dual-Subject Rule**

An action must be allowed if and only if:

* Agent is authorized
  AND
* Human is authorized
  AND
* Delegated intent is valid

A policy engine must evaluate AGBAC requests according to the following model:

```
ALLOW(action, resource)
IFF
    AgentIdentity is permitted to perform action on resource
AND
    HumanIdentity is permitted to perform action on resource
AND
    DelegatedIntent is valid, non-expired, and appropriate for the action
```

This is a core requirement of AGBAC.

---

### **7.2 No Escalation Guarantees**

Delegation must not:

* Grant agents new permissions through delegation
* Grant humans indirect permissions through agent execution

---

### **7.3 Delegation Scope Rules**

Policies MUST define:

* Which humans may delegate actions to which agents
* Which agents may act on behalf of which humans
* Which actions require explicit delegation

---

# **8. Delegation Requirements**

## 8.1 Types of Delegation

### **8.1.1 Explicit Delegation (RECOMMENDED)**

Human intentionally instructs the AI agent to perform an action.

### **8.1.2 Implicit Delegation (NOT RECOMMENDED)**

Agent infers user desires through contextual interaction.
Must be explicitly permitted by policy.

### **8.1.3 System Delegation (PERMITTED)**

System workflows automatically assign tasks to AI agents.

---


## **9. Policy Requirements**

### **9.1 AGBAC Policy must support:**

1. Agent identity and permissions
2. Human identity and permissions
3. Delegation relationship
4. Delegated intent
5. Resource attributes
6. Resource constraints
7. Environmental context
8. Contextual constraints

### 9.2 Policy Implementation

Policies may be implemented in:

* OPA/Rego
* Cedar
* Zanzibar-like systems
* AWS IAM
* Azure Role Assignments
* Keycloak Authorization Services

AGBAC does not mandate a specific policy engine.

---

## **10. Enforcement Requirements**

### **10.1 Policy Enforcement Points**

A Policy Enforcement Point (PEP) MUST:

1. Accept a Delegation Token from the AI agent
2. Authenticate and validate the delegation token
3. Validate issuer and signature
4. Extract both `sub` and `act` identities
5. Submit both `sub` and `act` identities to the PDP
6. Evaluate authorization for both subjects independently
7. Infer authorization from both the `act` and `sub` claims
8. Deny access if either subject fails authorization
9. Emit an audit event

---

### **10.2 Token Issuance**

OAuth 2.0 Token Exchange (RFC 8693) is RECOMMENDED.

Alternative mechanisms are permitted only if they provide equivalent guarantees, including:

* Dual-subject integrity
* Non-forgery
* Replay resistance
* Bounded delegation

---

## **11. Audit and Logging Requirements**

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

### **Optional Audit Extensions (NON-NORMATIVE)**

* Agent reasoning summary
* Safety confidence score

Audit events MUST NOT contain raw prompts or confidential user content unless explicitly configured.
Raw prompts MUST NOT be logged by default.

---

## **12. Security Considerations**

### 12.1 Supported Threats

AGBAC is designed to mitigate:

* Privilege escalation via AI
* Human permission overreach via AI
* Prompt-injection leading to unauthorized actions
* Misuse of autonomous agents
* Undocumented delegation
* Cross-user agent misuse
* Cross-user impersonation
* Agent impersonation
* Token replay
* Delegation tampering

### 12.2 Token Security

Delegation tokens must:

* Be signed
* Be short-lived TTL
* Use transport binding where available (e.g., mTLS, DPoP, token binding where possible)

### 12.3 Logging and Privacy

Audit logs must be sanitized of unnecessary personal data (PII).

---

## **13. Interoperability**

AGBAC implementations must use existing IAM standards, including:

* OAuth 2.0
* OAuth 2.0 Token Exchange (RFC 8693)
* OIDC
* JWT
* XACML, OPA, or Cedar for policy
* Existing enterprise IdPs

No new token formats or cryptographic primitives are defined by AGBAC.

---

## **14. Reference Flow (Non-Normative)**

Human → AI Agent → Resource Server

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

## **15. Conformance**

### **REQUIRED**

1. Uses dual-subject tokens including `sub` and `act` claims
2. Enforces dual-subject authorization
3. Logs all AGBAC decisions
4. Validates delegation scope
5. Uses a secure token format (JWT/OIDC)
6. Audit logging

### **RECOMMENDED**

1. Implements OAuth Token Exchange
2. Supports OPA or Cedar policy templates
3. Supports explicit delegation workflows

---

## **16. Versioning**

AGBAC versions follow semantic versioning:

```
MAJOR.MINOR.PATCH
```

This spec is **v1.0.0**.

---

## **17. Licensing**

This specification is licensed under the **Apache License 2.0**.

---

## **End of AGBAC Specification v1.0**
