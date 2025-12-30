# AGBAC-Min

Foundational Implementation Profiles for AI-Agent-Based Access Control

---

## Overview

**AGBAC-Min** is a collection of **foundational, vendor-specific implementation profiles** for the **AI-Agent-Based Access Control (AGBAC)** specification.

The goal of AGBAC-Min is to demonstrate that **core AGBAC security guarantees can be implemented today** using existing enterprise IAM platforms — **without custom code, external policy engines, or new infrastructure**.

Each AGBAC-Min-<vendor> profile shows how a **bounded subset of the AGBAC specification** can be realized using **native configuration features** of a specific identity provider.

AGBAC-Min is intended to:
• Enable immediate adoption
• Build confidence in the AGBAC model
• Provide a consistent security story across vendors
• Create a clean path toward future, more advanced AGBAC implementations

---

## What AGBAC-Min Is (and Is Not)

### What AGBAC-Min Is

AGBAC-Min profiles:
• Are production-realistic today
• Use only native IAM configuration
• Introduce AI agents as first-class identities
• Enforce dual-subject authorization (human + agent)
• Apply at the system / application boundary
• Provide clear, auditable attribution

Each profile enforces the same core invariant:

An AI agent may access a system on behalf of a human user **only if both the agent and the human are independently authorized for that system**.

---

### What AGBAC-Min Is Not

AGBAC-Min profiles do not:
• Replace full AGBAC implementations
• Provide object-level authorization
• Introduce centralized policy engines
• Validate AI reasoning or prompts
• Require custom enforcement components

Those capabilities are addressed in **AGBAC-Full** implementations.

---

## Why AGBAC-Min Exists

Enterprises are adopting AI agents faster than IAM platforms are evolving.

AGBAC-Min exists to show that:
• Stronger AI access control does not require waiting
• Existing IAM systems already provide key building blocks
• AGBAC concepts can be layered safely and incrementally
• Vendors and customers can move forward together

AGBAC-Min is intentionally **non-disruptive**, **vendor-respectful**, and **forward-looking**.

---

## Core AGBAC Concepts Implemented in AGBAC-Min

All AGBAC-Min profiles implement the following shared concepts:

• AI agents are first-class identities
• Humans remain the source of authority
• Access decisions consider both identities
• Delegation is explicit, not implicit
• Authorization is enforced before system access
• Audit records reflect both subjects

These concepts are expressed using different platform mechanisms, but the **security semantics remain identical** across vendors.

---

## Available AGBAC-Min Profiles

Each profile is a **self-contained README** that can be implemented independently.

### AGBAC-Min-Okta

Foundational AGBAC profile using Okta Workforce Identity, Active Directory, OAuth 2.0, and native application assignments.

GitHub: [https://github.com/your-org/agbac-min-okta](https://github.com/your-org/agbac-min-okta)

---

### AGBAC-Min-EntraID

Foundational AGBAC profile using Microsoft Entra ID (Azure AD), Enterprise Applications, App Registrations, and native token claims.

GitHub: [https://github.com/your-org/agbac-min-entra-id](https://github.com/your-org/agbac-min-entra-id)

---

### AGBAC-Min-Auth0

Foundational AGBAC profile using Auth0 Workforce or B2B Identity, Machine-to-Machine applications, RBAC, and token customization.

GitHub: [https://github.com/your-org/agbac-min-auth0](https://github.com/your-org/agbac-min-auth0)

---

### AGBAC-Min-Keycloak

Foundational AGBAC profile using Keycloak realms, service accounts, client roles, and protocol mappers.

GitHub: [https://github.com/your-org/agbac-min-keycloak](https://github.com/your-org/agbac-min-keycloak)

---

## Choosing the Right Profile

Select the profile that matches your existing IAM platform.

You do not need to read or implement other profiles to use one successfully.

If your organization uses multiple IAM platforms, AGBAC-Min profiles can be implemented **in parallel** while preserving consistent security semantics.

---

## Security Guarantees Provided by All AGBAC-Min Profiles

All AGBAC-Min profiles guarantee:

• No agent-only access
• No human-only proxy access
• No implicit privilege escalation through AI
• Explicit delegation semantics
• Clear dual-subject auditability
• Compatibility with Zero Trust models

---

## Operational Characteristics

AGBAC-Min profiles:
• Require no application code changes
• Use existing IAM operational processes
• Support immediate revocation
• Align with least-privilege principles
• Scale across teams and environments

---

## Relationship to the AGBAC Specification

AGBAC-Min implements a **bounded subset** of the AGBAC specification.

It is intentionally designed to:
• Be backward-compatible with existing IAM practices
• Be forward-compatible with future AGBAC-Full implementations

AGBAC-Min profiles should be viewed as:
**Foundational enforcement layers**, not the final form of AGBAC.

---

## Path Forward: AGBAC-Full

Future AGBAC-Full implementations may include:
• Object-level access control
• Policy decision and enforcement points
• Delegation chains and reasoning
• AI-aware authorization semantics

AGBAC-Min provides the **starting point** for that evolution.

---

## Community and Contributions

AGBAC-Min is intended to:
• Encourage collaboration across vendors
• Support security researchers and practitioners
• Enable consistent industry discussions
• Avoid blame or negative framing

Contributions are welcome in the form of:
• Additional vendor profiles
• Validation feedback
• Operational guidance
• Threat modeling and analysis
