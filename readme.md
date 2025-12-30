<div align="center">

# AGBAC Agent Based Access Control

Welcome to the AGBAC Open Security Specification & Reference Landing


<img width="237" height="314" alt="agbac-final" src="https://github.com/user-attachments/assets/118e76e3-dab4-45e7-8147-07e0cd48c7fb" />



</div>

<br>

## Intro


AGBAC (Agent-Based Access Control) is an open, vendor-neutral security specification that defines how AI agents securely perform actions on behalf of human users.  AGBAC was designed to use existing Standards and Technology, extending existing IAM infrastructure (OAuth2, OIDC, RBAC, ABAC, PBAC). AGBAC introduces no new token formats, cryptographic systems, or identity providers, making AGBAC compatible with existing IAM Solutions. AGBAC addresses a rapidly emerging security challenge in enterprise systems:

<br>

> AI agents now initiate actions, but existing access control models assume a human is always the caller.

<br>

AGBAC introduces a dual-subject authorization model that ensures both the human user and the AI agent are independently authorized for every action. The AGBAC specification is publicly released and may be used, implemented, and extended by organizations, vendors, and the open-source community. AGBAC is an evolution of Access Control Models (RBAC, ABAC, PBAC, now AGBAC)

<br>

## Why another Access Control Model?

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

<br>

## How does AGBAC work?


**Step 1 - Human instructs AI agent**

```
Human → Agent: “Retrieve customer record 55239”
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

## How do I use AGBAC?

**Option 1 - Use the Specification to Build/Create**

Use the Specification to build your own Implementation (for Vendors, Product Owners, IAM Providers, etc)

• The AGBAC specification v1.0.0 is released (link)

• The specification is open, royalty-free, and vendor-neutral

• The spec defines the authoritative security model for AGBAC

• Organizations are encouraged to adopt, reference, and build upon it

The specification describes the complete AGBAC model, including identity, delegation, policy, enforcement, audit, and security considerations.

<br>

**Option 2 - Use AGBAC Minimal today with existing IAM Solutions**

Implement a sub-set of AGBAC (aka AGBAC-Min) for system-level access right now (Let's GOOOOO!!!)

• AGBAC-Min is a bounded sub-set of the full AGBAC specification (link)

• Works with your existing Enterprise IAM Solutions right now; No patch or update required (custom config)

• Provides system-level access control, native IAM configuration/scope only (remember, this is Minimal)

• Enforce dual-subject authorization at the system boundary; Supports both Agent and Human access and authorization out-of-the-box

• Are you using Okta? Go directly to AGBAC-Min-Okta now! (link)

• Are you using EntraID? Go directly to AGBAC-Min-EntraID now! (link)

• Are you using Auth0? Go directly to AGBAC-Min-Auth0 now! (link)

• Are you using Keycloak? Go directly to AGBAC-Min-Keycloak now! (link)

<br>

**Option 3 - Use AGBAC Full when development is complete/released**

Implement a fully functional AGBAC Solution (aka AGBAC-Full) for object/resource-level access when development is complete

• AGBAC-Full is a vendor-neutral full implementation of the AGBAC specification

• Development of AGBAC-Full will begin Jan 2026, and espected to be complete Feb 2026

• Will work with your existing Enterprise IAM Solutions; Vendor-neutral PEP will be provided

• Provides object/resource-level access control, enhanced scope for agent-aware IAM Solutions

• Will support delegation chains and multi-agent workflows

• Will provide standardized AI-aware audit semantics

• Implements defense in depth patterns and positions your organization for Zero Trust compliance at the Agent Layer

<br>
<br>






## Project Status

### AGBAC Specification



---

### AGBAC-Full Implementation

AGBAC-Full represents the **complete realization of the specification**, including:

• Fine-grained and object-level authorization
• Dedicated policy decision and enforcement points
• Delegation chains and multi-agent workflows
• Standardized AI-aware audit semantics
• Defense-in-depth enforcement patterns

Work toward AGBAC-Full reference implementations is **ongoing**.

---

## AGBAC-Min: Foundational Implementations Available Today

While AGBAC-Full is under active development, the project has released **AGBAC-Min** profiles to demonstrate that **core AGBAC security guarantees can be implemented today** using existing enterprise IAM platforms.

AGBAC-Min profiles:
• Implement a bounded subset of the AGBAC spec
• Use native IAM configuration only
• Require no application code changes
• Enforce dual-subject authorization at the system boundary

AGBAC-Min is designed to:
• Enable immediate adoption
• Build confidence in the AGBAC model
• Provide consistent semantics across vendors
• Create a smooth path to AGBAC-Full

---

## Available AGBAC-Min Profiles

The following foundational profiles are available today:

• **AGBAC-Min-Okta**
• **AGBAC-Min-EntraID**
• **AGBAC-Min-Auth0**
• **AGBAC-Min-Keycloak**

Each profile is vendor-specific, self-contained, and can be implemented independently.

AGBAC-Min profiles should be viewed as **foundational layers**, not the final form of AGBAC.

---

## Core Security Principle

The defining invariant of AGBAC is:

An AI agent may perform an action on behalf of a human user **only when both the agent and the human are independently authorized for that action**.

This invariant applies consistently across:
• AGBAC-Min
• AGBAC-Full
• All future extensions of the model

---

## What the AGBAC Specification Defines

The AGBAC specification defines:

• AI agent identities as first-class principals
• Human principals as the source of authority
• Explicit delegation semantics
• Dual-subject authorization requirements
• Policy evaluation rules
• Enforcement responsibilities
• Audit and compliance requirements
• Security and threat mitigations
• Interoperability with existing IAM standards

The specification does **not** introduce new token formats, cryptographic primitives, or identity providers.

---

## Design Goals

AGBAC is designed to:

• Strengthen security without breaking existing IAM systems
• Work with OAuth 2.0, OIDC, JWT, and enterprise IdPs
• Preserve least-privilege principles
• Improve auditability and accountability
• Scale across vendors and environments
• Support incremental adoption

---

## Relationship Between AGBAC-Min and AGBAC-Full

AGBAC-Min and AGBAC-Full are complementary:

• AGBAC-Min demonstrates what is possible today
• AGBAC-Full defines where the industry is going
• Both share the same core security semantics
• AGBAC-Min implementations are forward-compatible

Organizations can adopt AGBAC-Min now and evolve naturally toward AGBAC-Full as capabilities mature.

---

## Intended Audience

AGBAC is designed for:

• Security architects
• IAM engineers
• Platform teams
• AI infrastructure teams
• Identity vendors
• Open-source maintainers
• Compliance and risk leaders

---

## Community and Collaboration

AGBAC is an open initiative.

The project welcomes:
• Feedback on the specification
• Additional AGBAC-Min vendor profiles
• Reference implementations
• Policy models and tooling
• Threat analysis and security review

The goal is to **advance AI security collaboratively**, without vendor blame or disruption.

---

## Licensing

The AGBAC specification and all reference materials are released under the **Apache License 2.0**.

---

## Closing Note

AI agents are becoming part of the enterprise control plane.

AGBAC exists to ensure that **security, accountability, and least privilege evolve alongside them**.

AGBAC-Min shows what can be done today.
AGBAC-Full defines what comes next.

