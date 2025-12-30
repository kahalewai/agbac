<div align="center">

# AGBAC Agent Based Access Control

Welcome to the AGBAC Open Security Specification & Reference Landing

![agbac6-small](https://github.com/user-attachments/assets/27872815-da23-4ef2-82f6-a2ffd8af1941)



</div>

<br>

## Intro


**AGBAC (Agent-Based Access Control)** is an open, vendor-neutral security specification that defines how AI agents securely perform actions on behalf of human users.  It extends existing IAM infrastructure (OAuth2, OIDC, RBAC, ABAC, PBAC) and introduces no new token formats, cryptographic systems, or identity providers.

AGBAC addresses a rapidly emerging security challenge in enterprise systems:

> AI agents now initiate actions, but existing access control models assume a human is always the caller.

AGBAC introduces a **dual-subject authorization model** that ensures **both the human user and the AI agent are independently authorized for every action**.

The AGBAC specification is publicly released and may be used, implemented, and extended by organizations, vendors, and the open-source community.

---

## Project Status

### AGBAC Specification

• The **AGBAC specification is released**
• The specification is **open, royalty-free, and vendor-neutral**
• The spec defines the **authoritative security model** for AGBAC
• Organizations are encouraged to adopt, reference, and build upon it

The specification describes the **complete AGBAC model**, including identity, delegation, policy, enforcement, audit, and security considerations.

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

