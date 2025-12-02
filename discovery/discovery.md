For the topic of IAM and Access Control, we have RBAC and PBAC, which apply to the identities of human users. I want to explore the idea of a new Access Control called AGBAC. AGBAC is intended for AI Agents, and would define the access authorizations that an identity associated with an AI Agent. The big differentiating factor between existing Access Controls like RBAC and PBAC, and the new AGBAC concept, is that for RBAC and PBAC, the human user themselves makes the access request, and for AGBAC, the AI Agent is making the request on the human users behalf. So the new AGBAC concept would need to understand that not only does the AI Agent identity need to be authorized for access, but the human user Identity asking the AI Agent to do something also need to be authorized for access. So this essentially becomes a two-step authentication for both AI Agent and human user. I want to explore how this could be developed as an open source solution that could be adopted by the industry. We dont want to build new infrastructure or tooling, we want existing infrastructure and tooling to support AGBAC. What would be the best way to approach this?

Below is a structured approach to developing **AGBAC (AI-Agent-Based Access Control)** as an open-source, industry-adopted model **without requiring new infrastructure**, only extensions to existing IAM concepts, APIs, and enforcement points.

---

# ✅ **1. Clarify the AGBAC Trust Model**

Your core idea:
**Every authorization request has two principals:**

1. **Human principal** – the “root intent” behind the request
2. **AI Agent principal** – the autonomous actor executing the request

Thus, an AGBAC decision requires:

```
ALLOW IF:
    AgentIdentity IS AUTHORIZED to perform Action
AND
    UserIdentity IS AUTHORIZED to have Agent perform Action
```

This effectively adds a **delegated intent + agent trust** layer on top of RBAC/PBAC.

This should *not* replace RBAC/PBAC, but extend them.

---

# ✅ **2. Your goal: Reuse existing IAM, do not introduce new infrastructure**

So any AGBAC design must work with:

* **OAuth2 / OIDC**
* **JWT / STS-issued tokens**
* **SAML (older enterprises)**
* **Policy engines (OPA, Cedar, Zanzibar-like models, AWS IAM)**
* **Identity providers (Azure AD, Okta, Auth0, Keycloak)**

Thus the solution should be:

* **token-based** (AI agent carries dual identity)
* **policy-based** (implemented in existing PDPs)
* **standard-framework compatible**

---

# ✅ **3. Recommended foundational approach: “Dual-Subject Tokens”**

You can support AGBAC today *without* new infrastructure by representing both identities inside a single existing token format (JWT/OIDC/OAuth).

Example AGBAC token structure using JWT:

```json
{
  "sub": "agent-12345",        // AI agent identity
  "act": "user-9876",          // Actor performing the action (human user)
  "scp": ["read:records"],     // Agent’s allowed scopes
  "user_scopes": ["read:records"], // User allowed scopes
  "delegation": "explicit",    // Human delegated this task
  "pol_ver": "agbac_v1"
}
```

This leverages:

* OAuth2 `act` claim (already exists for delegated authorization)
* Multiple-scope patterns (common in existing IAM)
* Custom claims (allowed by all providers)

💡 **This strategy requires *no new IAM tech*—just token conventions and policy evaluation logic.**

---

# ✅ **4. Use existing policy engines to evaluate AGBAC**

You can implement AGBAC in RBAC, PBAC, or ABAC policy languages by using the dual-identity claims.
Examples:

### **OPA/Rego**

```rego
allow {
    input.token.sub == "agent-12345"
    input.token.act == "user-9876"
    agent_allowed[input.action]
    user_allowed[input.action]
}
```

### **Cedar (AWS / open-source)**

```cedar
permit (
    agent, action, resource
) when {
    agent.isType("Agent") &&
    agent.delegatedBy == user &&
    user.can(action, resource) &&
    agent.can(action, resource)
};
```

Again—no new infrastructure. Just policy logic.

---

# ✅ **5. Define AGBAC as an open standard, not a tool**

Industry adoption comes from **a specification**, not a proprietary implementation.

You would create:

### 📘 **AGBAC Specification v1**

Defining:

* required claims (`sub`, `act`, `delegation`, `agent_confidence_level`, etc.)
* required behaviors (dual principal evaluation)
* minimal policy expressions
* example implementations for:

  * Keycloak
  * AWS IAM / Cedar
  * Open Policy Agent
  * OAuth2 authorization servers

This can be similar to:

* SCIM
* OIDC
* OAuth2 Token Exchange spec (RFC 8693)
* CNCF standards (SPIFFE/SPIRE for workload identity)

---

# ✅ **6. Leverage existing RFCs to avoid inventing anything new**

To integrate smoothly with industry standards, base AGBAC on two existing RFCs:

### **📌 RFC 8693 – OAuth2 Token Exchange**

Allows the AI agent to request a token “on behalf of” the human user.

Useful because you can describe AGBAC as:

> “An AI agent always uses a token obtained via Token Exchange, embedding the human principal.”

### **📌 The OAuth “act” claim**

Already represents a delegated actor. Perfect fit for AGBAC.

Thus AGBAC = **formalization + constraints on usage of existing delegated claims**.

---

# ✅ **7. Publish AGBAC as:**

### ✔ Open source reference implementation

A small set of:

* token transformation middleware
* sample policies for OPA, Cedar, Zanzibar
* example Keycloak plugin

### ✔ A GitHub organization (e.g., “AGBAC Working Group”)

Including:

* Spec document
* SDKs for Go/Python/Node
* Community discussions

### ✔ A standards-track draft (IETF/OWASP/CNCF)

Position AGBAC under one of these communities:

* **IETF OAuth Working Group** (best fit)
* **CNCF Security SIG**
* **OWASP (for threat model guidance)**

---

# ✅ **8. Encourage adoption by aligning with vendor incentives**

Vendors won’t adopt something that requires rewriting IAM.

AGBAC must give them:

### **What IdPs (Okta, AWS, Azure AD) get:**

* A standard way to describe “AI agent identity”
* A way to safely delegate actions to AI without massive risk

### **What enterprises get:**

* AI agent controls without new toolchains
* Policy reusability (same engines)
* Simple audit logs:

  * *“Alice asked Agent-7 to delete Record-544”*

### **What app developers get:**

* Easy libraries for checking AGBAC-compliant tokens

This ensures rapid adoption.

---

# ✅ **9. Suggested roadmap**

### **Phase 1 – Research + Spec Draft**

1. Draft AGBAC v0.1 spec (Markdown + examples)
2. Define required token claims
3. Define evaluation rules compatible with RBAC/PBAC/ABAC
4. Publish threat model (prevents prompt injection, privilege escalation)

### **Phase 2 – Reference Implementation**

Build:

* Reference OPA policies
* Reference Cedar policies
* Keycloak token hook that issues AGBAC tokens
* A small demo app showing agent + user delegation

### **Phase 3 – Industry Working Group**

Invite:

* CNCF SIG-Security
* OAuth Working Group
* Vendors (Okta, Auth0, Keycloak, AWS, Microsoft)

### **Phase 4 – 1.0 Release**

* Publish spec v1.0
* Submit to IETF as a Draft/Informational RFC
* Encourage vendor integration

---

# 🔥 Final Recommendation

**The best path is to define AGBAC as a standards-based extension of OAuth2 delegated authorization, using dual-subject JWT claims and evaluated via existing policy engines.**

No new IAM system.
No new enforcement points.
No new infrastructure.

Just a **specification + patterns** that every enterprise IAM can already support.






