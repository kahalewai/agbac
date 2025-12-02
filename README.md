# **AGBAC — AI-Agent-Based Access Control**

**Open Security Specification & Reference Implementations**

AGBAC is an **open, vendor-neutral access control model** designed to securely govern **AI agents acting on behalf of human users**. It extends existing IAM infrastructure (OAuth2, OIDC, RBAC, ABAC, PBAC) and introduces no new token formats, cryptographic systems, or identity providers.

AGBAC solves a rapidly emerging security challenge:

> **AI agents are performing actions in systems, but existing access control models assume a human is always the caller.**

AGBAC ensures that **both the AI agent AND the human user are authorized** for every action.

---

# 🚀 **Why AGBAC Exists**

Existing access control models assume:

* *The human calls the API directly.*
* *The system knows exactly who triggered the action.*

With AI, those assumptions break.

AI agents can:

* Execute actions asynchronously
* Perform tasks autonomously
* Operate with long-lived sessions
* Make calls outside the human’s direct control

This creates gaps in:

* Authorization
* Audit
* Intent verification
* Least privilege
* Regulatory compliance

**AGBAC closes those gaps** using a **dual-subject authorization model** that works with *existing IAM tooling*.

---

# 🔐 **What AGBAC Provides**

### ✔ Dual-Subject Identity

Every authorized action includes:

* The **agent identity** (`sub`)
* The **human principal** (`act`)

### ✔ Delegation Metadata

Tokens include the **delegated intent**, timestamp, and context.

### ✔ Policy Templates

Reference OPA, Cedar, and Zanzibar-style rules that enforce:

```
ALLOW IFF
  agent is authorized
AND
  human is authorized
AND
  delegation is valid
```

### ✔ Audit and Compliance

Standardized audit events for:

* Zero Trust
* SOC 2
* ISO 27001
* NIST 800-53
* Financial and regulated environments

### ✔ Security & Threat Modeling

Mitigations for:

* AI privilege escalation
* Human-overreach through AI
* Prompt injection
* Agent impersonation
* Cross-user misuse

---

# 📘 **AGBAC Components**

This repository contains:

```
/
├── specs/
│   ├── agbac-spec-v1.md            # Core specification
│   ├── token-format.md             # Token structure & claims
│   ├── policy-model.md             # Authorization model
│   └── security-threat-model.md    # Threat modeling
│
├── architecture/
│   ├── diagrams/                   # Sequence & architecture diagrams
│   └── reference-architecture.md
│
├── ref-impl/
│   ├── keycloak/                   # Keycloak token mapper
│   ├── auth0/                      # Auth0 rule for dual-subject tokens
│   ├── okta/                       # Okta/Workforce Identity example
│   ├── cognito/                    # AWS Cognito Lambda for delegation
│   └── agent-gateway/              # Example AI gateway (optional)
│
├── policy-templates/
│   ├── opa/                        # OPA/Rego dual-subject policies
│   ├── cedar/                      # Cedar policy examples
│   └── zanzibar/                   # Tuple schema + example relationships
│
├── sdks/
│   ├── python/
│   ├── go/
│   └── node/
│
├── tests/
│   ├── conformance/                # Ensures compliance with the spec
│   └── policy-tests/
│
└── README.md
```

---

# 🛠 **How AGBAC Works (High-Level)**

### **Step 1 — Human instructs AI agent**

```
Human → Agent: “Retrieve customer record 55239”
```

### **Step 2 — Agent obtains a Delegation Token**

Using OAuth2 Token Exchange (RFC 8693):

* `sub` = AI agent
* `act` = human
* `delegation` = metadata
* `scp` = agent scopes
* `usr_scopes` = user scopes (optional)

### **Step 3 — Agent makes the API request with the token**

### **Step 4 — PEP enforces dual-subject authorization**

```
ALLOW IFF agent AND human are authorized.
```

### **Step 5 — Action is executed and audit event is generated**

---

# ⚙️ **Compatibility With Existing IAM Systems**

AGBAC works natively with:

* **OAuth2 / OIDC**
* **JWT**
* **RFC 8693 Token Exchange**
* **RBAC / PBAC / ABAC**
* **OPA**
* **Cedar**
* **Zanzibar**
* **Keycloak**
* **Okta / Auth0 / Azure AD**
* **AWS IAM & Cognito**
* **mTLS / SPIFFE identities**

There are **no new token formats** and **no new cryptographic systems**.

---

# 🧩 **Example Delegation Token (JWT)**

```json
{
  "sub": "agent:analysis-assistant-001",
  "act": { "sub": "user:alice@example.com" },
  "delegation": {
    "granted_at": "2025-12-01T15:32Z",
    "method": "explicit",
    "intent_summary": "Retrieve customer record 55239"
  },
  "scp": ["read:customers"],
  "usr_scopes": ["read:customers"],
  "agbac_ver": "1.0"
}
```

---

# 📜 **Specification**

Full specification:
👉 `./specs/agbac-spec-v1.md`

This document defines the authoritative behavior for:

* Identity
* Delegation
* Policy
* Enforcement
* Security
* Interoperability
* Compliance
* Conformance tests

---

# 🧪 **Testing & Conformance**

AGBAC includes:

* JSON schemas for token validation
* Policy behavior tests
* Interop test suite
* PEP testing examples

These ensure consistent behavior across vendors and implementations.

---

# 🔰 **Security & Threat Model**

See:
👉 `./specs/security-threat-model.md`

The model covers:

* Prompt injection risk
* Agent/human impersonation
* Cross-user token misuse
* Delegation tampering
* Replay attacks
* Model misalignment
* Least privilege boundaries
* Defense-in-depth requirements

---

# 🤝 **Contributing**

AGBAC welcomes contributions from:

* Security engineers
* IAM architects
* AI safety researchers
* Policy engine maintainers
* Cloud providers
* Open-source communities

Please read:
👉 `CONTRIBUTING.md`
👉 `CODE_OF_CONDUCT.md`

---

# 🧭 **Roadmap**

### **v1.0**

* Core specification
* Reference implementations for major IdPs
* OPA/Cedar policy templates
* Initial conformance suite

### **v1.1**

* AI observation & reasoning audit fields
* More language SDKs
* Agent classification & trust levels

### **v2.0**

* Interop with autonomous agent networks
* Signed delegation artifacts
* Multi-agent delegation chains

---

# 📄 **License**

All AGBAC documentation, code, and specs are released under:
**Apache License 2.0**

---

# ⭐ **Support the Project**

If you believe AGBAC strengthens AI security, please consider:

* Starring the repo ⭐
* Sharing with your security/IAM teams
* Submitting issues
* Contributing implementations for other identity systems

