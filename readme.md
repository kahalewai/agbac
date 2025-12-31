<div align="center">

# AGBAC Agent Based Access Control

Welcome to the AGBAC Open Security Specification & Reference Landing



![agbac11-small](https://github.com/user-attachments/assets/22c4208d-dc6e-4524-8f2a-41376649b1ad)



</div>

<br>

## Intro


AGBAC (Agent-Based Access Control) is an open, vendor-neutral security specification that defines how AI agents securely perform actions on behalf of human users.  AGBAC was designed to use existing Standards and Technology, extending existing IAM infrastructure (OAuth2, OIDC, RBAC, ABAC, PBAC). AGBAC introduces no new token formats, cryptographic systems, or identity providers, making AGBAC compatible with existing IAM Solutions. 

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
Human → Agent: “Retrieve customer record xyz123”
```

**Step 2 - Agent obtains a Delegation Token**

Using OAuth2 Token Exchange (RFC 8693):

* `sub` = AI agent
* `act` = human
* `delegation` = metadata
* `scp` = agent scopes
* `usr_scopes` = user scopes (optional)

**Step 3 - Agent makes the API request with the token**

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
* The AGBAC specification v1.0.0 is released ([link](https://github.com/kahalewai/agbac/blob/main/agbac_specification.md))
* The specification is open, royalty-free, and vendor-neutral
* The spec defines the authoritative security model for AGBAC
* Organizations are encouraged to adopt, reference, and build upon it

The specification describes the complete AGBAC model, including identity, delegation, policy, enforcement, audit, and security considerations.

<br>

**Option 2 - Use AGBAC Minimal today with existing IAM Solutions**

Implement a sub-set of AGBAC (aka AGBAC-Min) for system-level access right now (**Let's GOOOOO!!!**)
* AGBAC-Min is a bounded sub-set of the full AGBAC specification ([link](https://github.com/kahalewai/agbac/tree/main/agbac-min))
* Works with your existing Enterprise IAM Solutions right now; No patch or update required (custom config)
* Provides system-level access control, native IAM configuration/scope only (remember, this is Minimal)
* Enforce dual-subject authorization at system boundary; Supports both Agent and Human access and authorization
* Are you using Okta? Go directly to AGBAC-Min-Okta now! ([link](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-okta.md))
* Are you using EntraID? Go directly to AGBAC-Min-EntraID now! ([link](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-entraid.md))
* Are you using Auth0? Go directly to AGBAC-Min-Auth0 now! ([link](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-auth0.md))
* Are you using Keycloak? Go directly to AGBAC-Min-Keycloak now! ([link](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-keycloak.md))

<br>

**Option 3 - Use AGBAC Full when development is complete/released**

Implement a fully functional AGBAC Solution (aka AGBAC-Full) for object/resource-level access (coming soon)
* AGBAC-Full is a vendor-neutral full implementation of the AGBAC specification
* Development of AGBAC-Full will begin Jan 2026, and espected to be complete Feb 2026
* Will work with your existing Enterprise IAM Solutions; Vendor-neutral PEP will be provided
* Provides object/resource-level access control, enhanced scope for agent-aware IAM Solutions
* Will support delegation chains and multi-agent workflows, supporting advanced configurations
* Will provide standardized AI-aware audit semantics, allowing your organization to fully audit agent interactions
* Implements defense in depth patterns and positions your organization for Zero Trust compliance at the Agent Layer

<br>
<br>

## What makes AGBAC effective out-of-the-box?

The defining core requirement of AGBAC is:

> An AI agent may perform an action on behalf of a human user **only when both the agent and the human are independently authorized for that action**.

All implementations of AGBAC accomplish this (even AGBAC-Min) but the secret sauce is how AGBAC was built. Instead of building something completely new, I did the due dilligence research to determine how existing standards and technology can be used to accomplish this. AGBAC does **not** introduce new token formats, cryptographic primitives, or identity providers.

AGBAC is designed to:

* Strengthen security without breaking existing IAM systems
* Work with OAuth 2.0, OIDC, JWT, and enterprise IdPs
* Preserve least-privilege principles
* Improve auditability and accountability
* Scale across vendors and environments
* Support incremental adoption

This means you can use AGBAC today (right now!) with your existing IAM solution, without needing to update or patch the solution. You just need to implement the vendor-specific configuration to begin your AGBAC journey (Option 2 above). And eventually, when AGBAC-Full is complete, or if/when your preferred vendor adopts this specification, you will be positioned to achieve Zero Trust (ZT) compliance at the AI Agent Layer. Boom!

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

* A mapping of AGBAC to the AOSI Model can be found here ([link](https://github.com/kahalewai/agbac/blob/main/aosi_mapping.md))
* A mapping of AGBAC to the OWASP Top 10 LLM Risks can be found here ([link](https://github.com/kahalewai/agbac/blob/main/owasp_mapping.md))
* A mapping of AGBAC to NIST 800-207 Zero Trust can be found here ([link](https://github.com/kahalewai/temp/blob/main/agbac/zero-trust-mapping.md))
* A Threat Model for AGBAC can be viewed here ([link](https://github.com/kahalewai/agbac/blob/main/threat_model.md))


<br>
<br>

## Licensing

The AGBAC specification and all reference materials are released under the Apache License 2.0.



<br>
<br>

## Community and Collaboration

AGBAC is an open initiative. The project welcomes (via Fork/PR):
* Feedback on the specification 
* Additional AGBAC-Min vendor profile requests
* Reference implementations
* Policy models and tooling
* Threat analysis and security reviews

The goal is to **advance AI security collaboratively** and **forward innovation in the IAM space for AI scenarios**.

<br>
<br>
<br>
<p align="center">
▁ ▂ ▄ ▅ ▆ ▇ █   Created with Aloha by Kahalewai - 2025  █ ▇ ▆ ▅ ▄ ▂ ▁
</p>

