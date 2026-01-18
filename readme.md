<div align="center">

# AGBAC AGent Based Access Control

Welcome to the AGBAC Open Security Specification & Reference Landing

<br>

![agbac-standard](https://github.com/user-attachments/assets/1d629957-5fd9-414f-a55b-27941fbf381b)


</div>

<br>

## Intro


AGBAC (AGent-Based Access Control) is an open, vendor-neutral security specification that defines how AI agents securely perform actions on behalf of human users.  AGBAC was designed to use existing Standards and Technology, extending existing IAM infrastructure (OAuth2, OIDC, RBAC, ABAC, PBAC). AGBAC introduces no new token formats, cryptographic systems, or identity providers, making AGBAC compatible with existing IAM Solutions. 

<br>

AGBAC addresses a rapidly emerging security challenge in enterprise systems:
> AI agents now initiate actions, but existing access control models assume a human is always the caller.

<br>

AGBAC introduces a dual-subject authorization model that ensures both the human user and the AI agent are independently authorized for every action. The AGBAC specification is publicly released and may be used, implemented, and extended by organizations, vendors, and the open-source community. AGBAC is an evolution of Access Control Models (RBAC, ABAC, PBAC, now AGBAC)

<br>

## Why another Access Control Model?

Existing access control models assume:

* *The human is initiating the action directly.*
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

<br>
<br>

## How does AGBAC work?

**Step 1 - Human instructs AI agent**

```
Human → LLM → Agent: “Access resource xyz123”
```

**Step 2 - Agent obtains a Delegation Token**

Using OAuth2 Token Exchange (RFC 8693):

* `sub` = AI agent
* `act` = human
* `delegation` = metadata
* `scp` = agent scopes
* `usr_scopes` = user scopes (optional)

**Step 3 - Agent makes the access request with the Token**

**Step 4 - PEP enforces dual-subject authorization**

```
ALLOW IFF agent AND human are authorized.
```

**Step 5 - Action is executed and audit event is generated**

<br>
<br>

## How do I use AGBAC?

**Option 1 - Use the Specification to Build/Create**

Use the Specification to build your own custom implementation (for Vendors, Product Owners, IAM Providers, etc)
* The AGBAC specification v1.0.0 is released ([link](https://github.com/kahalewai/agbac/blob/main/spec/agbac_specification.md))
* The specification is open, royalty-free, and vendor-neutral
* Organizations are encouraged to adopt, reference, and build upon it

<br>

**Option 2 - Use the Dual Auth Library today with existing IAM Solutions**

Implement a sub-set of AGBAC (Dual Auth) for system-level access right now (**Let's GOOOOO!!!** 🔥 🔥 🔥)
* Start here --> GitHub: [https://github.com/kahalewai/dual-auth](https://github.com/kahalewai/dual-auth)
* Works with your existing Enterprise IAM Solutions right now; Okta, EntraID, Auth0, Keycloak
* Easy first step towards Zero Trust alignment and enforcement of agentic workflows and access

<br>

## What makes AGBAC effective out-of-the-box?

The defining core requirement of AGBAC is:

> An AI agent may perform an action on behalf of a human user **only when both the agent and the human are independently authorized for that action**.

All implementations of AGBAC accomplish this (even Dual Auth) but the secret sauce is how AGBAC was built. Instead of building something completely new, performed the due diligence research to determine how existing standards and technology can be used to accomplish this. AGBAC does **not** introduce new token formats, cryptographic primitives, or identity providers. This means it works with all existing IAM solutions that use common standards!

AGBAC is designed to:

* Strengthen security without breaking existing IAM systems
* Work with OAuth 2.0, OIDC, JWT, and enterprise IdPs
* Preserve least-privilege principles
* Improve auditability and accountability
* Scale across vendors and environments
* Support incremental adoption

This means you can use AGBAC today (right now!) with your existing IAM solution, without needing to update or patch the solution. An easy first step is to implement the vendor-specific configuration guide for Dual Auth to begin your AGBAC journey (Option 2 above). You will be better positioned to achieve Zero Trust (ZT) compliance at the AI Agent Layer. Boom! 💥 💥 💥

<br>
<br>

## What the AGBAC Specification Defines

The AGBAC specification defines:

* AI agent identities as first-class principals
* Human principals as the source of authority
* Explicit delegation semantics
* Dual-subject authorization requirements
* Policy evaluation rules
* Enforcement responsibilities
* Audit and compliance requirements
* Security and threat mitigations
* Interoperability with existing IAM standards

<br>
<br>

## Security and Mapping of AGBAC

* A mapping of AGBAC to the OWASP Top 10 LLM Risks can be found here ([link](https://github.com/kahalewai/agbac/blob/main/security/owasp_mapping.md))
* A mapping of AGBAC to NIST 800-207 Zero Trust can be found here ([link](https://github.com/kahalewai/agbac/blob/main/security/zt_mapping.md))
* A mapping of AGBAC to the AOSI Model can be found here ([link](https://github.com/kahalewai/agbac/blob/main/security/aosi_mapping.md))
* A Threat Model for AGBAC can be viewed here ([link](https://github.com/kahalewai/agbac/blob/main/security/threat_model.md))


<br>
<br>

## Licensing

The AGBAC specification and all reference materials are released under the Apache License 2.0.



<br>
<br>

## Community and Collaboration

AGBAC is an open initiative. If the specification can be ehnanced and strengthened, we support this. The project welcomes:
* Feedback on the specification (enhance, reiterate)
* Additional Dual Auth vendor profile requests (just ask)
* Reference implementations (please share)
* Policy models and tooling (let's collaborate)
* Threat analysis and security reviews (please share)

The goal is to **advance AI security collaboratively** and **forward innovation in the IAM space for AI scenarios**.

<br>


