# **AGBAC — AI-Agent-Based Access Control**

## **Open Security Specification v1.0**

**Status:** Draft for Public Review
**Year:** 2025
**License:** Apache 2.0
**Audience:** Security architects, IAM engineers, cloud providers, AI platform builders, policy engine authors

---

## **1. Purpose and Scope**

### **1.1 Purpose**

AI-Agent-Based Access Control (AGBAC) defines a **vendor-neutral access control model** for scenarios in which **AI agents perform actions on behalf of human principals** using existing identity and access management (IAM) systems.

AGBAC addresses a structural gap in traditional authorization models:

> Existing IAM systems assume the caller and the authorizing principal are the same entity.
> AI agents break this assumption.

AGBAC introduces a **dual-subject authorization model** that ensures:

* AI agents never act beyond their own authority
* Humans never exercise permissions indirectly that they do not possess
* All actions are attributable, auditable, and policy-governed

---

### **1.2 Non-Goals**

AGBAC does **not**:

* Define a new identity provider
* Define a new token format or cryptographic primitive
* Replace RBAC, ABAC, PBAC, or policy engines
* Mandate a specific AI architecture or model
* Require changes to existing OAuth or OIDC standards

AGBAC **extends** existing IAM and authorization systems by defining **how they must be used together** when AI agents are involved.

---

## **2. Core Principles**

AGBAC is built on the following principles:

1. **Dual Authority**
   Every action must be authorized for *both* the AI agent and the human principal.

2. **No Privilege Transfer**
   Delegation does not transfer permissions between subjects.

3. **Explicit Accountability**
   All actions must be attributable to both subjects.

4. **Least Privilege by Construction**
   Agents and humans are constrained independently.

5. **Interoperability First**
   Existing standards are reused wherever possible.

---

## **3. Terminology**

| Term                           | Definition                                                         |
| ------------------------------ | ------------------------------------------------------------------ |
| **Agent**                      | A software entity capable of autonomous or semi-autonomous actions |
| **Agent Identity**             | A non-human identity representing an AI agent                      |
| **Human Principal**            | A human user whose intent triggers agent activity                  |
| **Delegation**                 | Authorization for an agent to act within bounded scope             |
| **Dual-Subject Authorization** | Authorization requiring approval of two independent subjects       |
| **Delegation Token**           | A token containing both agent and human identity information       |
| **PEP**                        | Policy Enforcement Point                                           |
| **PDP**                        | Policy Decision Point                                              |
| **Resource Server**            | System receiving the agent’s request                               |

---

## **4. Identity Model**

### **4.1 Agent Identity**

Agents MUST be represented as **first-class identities**.

Valid representations include:

* OAuth2 clients
* OIDC workload identities
* mTLS certificates
* SPIFFE identities
* Cloud provider workload identities

Agents MUST NOT reuse human identities.

---

### **4.2 Human Identity**

Human principals MUST be authenticated through existing enterprise identity providers, such as:

* Workforce IdPs
* Federated SAML providers
* Enterprise OIDC providers

AGBAC does not define human authentication mechanisms.

---

## **5. Delegation Token Model**

### **5.1 Overview**

AGBAC-controlled actions MUST be authenticated using a token that represents **both subjects**.

The token:

* Represents **who is acting** (agent)
* Represents **on whose behalf** the action is performed (human)
* Conveys **delegation context**

---

### **5.2 Required Claims**

#### **5.2.1 `sub` — Agent Subject (REQUIRED)**

Identifies the AI agent.

```json
"sub": "agent:example-agent-001"
```

---

#### **5.2.2 `act` — Human Actor (REQUIRED)**

Uses the OAuth Actor Claim (RFC 8693).

```json
"act": {
  "sub": "user:alice@example.com"
}
```

The presence of `act` **does not imply authorization**.

---

#### **5.2.3 `delegation` (REQUIRED)**

Describes the delegation context.

```json
"delegation": {
  "granted_at": "2025-12-01T15:32Z",
  "method": "explicit",
  "context": "User requested customer lookup"
}
```

---

#### **5.2.4 `agbac_ver` (REQUIRED)**

```json
"agbac_ver": "1.0"
```

---

### **5.3 Optional Claims**

| Claim                    | Purpose                        |
| ------------------------ | ------------------------------ |
| `scp`                    | Agent permissions              |
| `usr_scopes`             | Human permissions              |
| `agent_confidence_level` | Trust or assurance indicator   |
| `delegation_expiry`      | Explicit delegation expiration |

---

## **6. Delegation Semantics**

### **6.1 Delegation Types**

| Type                 | Description                              |
| -------------------- | ---------------------------------------- |
| **Explicit**         | Human intentionally authorizes the agent |
| **Implicit**         | Agent infers intent (policy-restricted)  |
| **System-Initiated** | Workflow-driven delegation               |

Policies MUST explicitly permit non-explicit delegation.

---

### **6.2 Delegation Constraints**

Delegation MUST be:

* Time-bounded
* Scope-bounded
* Revocable
* Independently auditable

---

## **7. Authorization Model**

### **7.1 Dual-Subject Rule (Normative)**

An action MUST be allowed **if and only if**:

```
Agent is authorized
AND
Human is authorized
AND
Delegation is valid
```

This is the **defining requirement** of AGBAC.

---

### **7.2 No Escalation Guarantees**

* Agents MUST NOT gain permissions from humans
* Humans MUST NOT gain permissions from agents

Delegation only permits **execution**, not **privilege transfer**.

---

## **8. Policy Requirements**

Policies MUST be able to reason about:

1. Agent identity and permissions
2. Human identity and permissions
3. Delegation context
4. Resource attributes
5. Environmental context

Policy engines MAY include:

* OPA / Rego
* Cedar
* Zanzibar-style systems
* Cloud IAM policy languages

AGBAC is policy-engine-agnostic.

---

## **9. Enforcement Requirements**

### **9.1 Policy Enforcement Points**

A PEP MUST:

1. Authenticate the delegation token
2. Extract both subjects
3. Submit both subjects to the PDP
4. Enforce the PDP decision
5. Generate an audit event

---

### **9.2 Token Issuance**

OAuth 2.0 Token Exchange (RFC 8693) is RECOMMENDED.

Other issuance mechanisms are permitted if equivalent guarantees are met.

---

## **10. Audit and Logging**

### **10.1 Required Audit Fields**

Every AGBAC decision MUST generate an audit record containing:

* Timestamp
* Agent identity
* Human identity
* Action
* Resource
* Delegation type
* Decision
* Reason
* Correlation ID

---

### **10.2 Privacy Considerations**

Audit records MUST:

* Avoid raw prompts by default
* Minimize personal data
* Support regulatory requirements

---

## **11. Security Considerations**

AGBAC addresses the following threats:

* Privilege escalation via AI
* Cross-user agent misuse
* Agent impersonation
* Prompt injection leading to unauthorized actions
* Undocumented delegation
* Token replay and tampering

Recommended mitigations include:

* Short-lived tokens
* Binding tokens to transport
* Defense-in-depth policy evaluation
* Continuous monitoring

---

## **12. Interoperability**

AGBAC implementations MUST use existing standards:

* OAuth 2.0
* OIDC
* JWT
* RFC 8693
* Standard policy engines

No new cryptographic primitives are defined.

---

## **13. Conformance**

An implementation is AGBAC-conformant if it:

1. Uses dual-subject tokens
2. Enforces dual-subject authorization
3. Validates delegation context
4. Produces compliant audit logs

---

## **14. Versioning**

AGBAC uses semantic versioning.

This document is **v1.0.0-draft**.

---

## **End of AGBAC Specification v1.0**
