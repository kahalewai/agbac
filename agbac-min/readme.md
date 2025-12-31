<div align="center">

# AGBAC Minimal

AGBAC-Min Implementation Guides

</div>

<br>

## Intro

AGBAC Minimal (AGBAC-Min) is a collection of foundational, vendor-specific implementation guides for the Agent-Based Access Control (AGBAC) specification. The goal of AGBAC-Min is to demonstrate that a sub-set of AGBAC security capabilities can be implemented today using existing enterprise IAM platforms without custom code, external policy engines, or new infrastructure. Each AGBAC-Min guide shows how a bounded subset of the AGBAC specification can be implemented using native configuration features of a specific identity provider.

AGBAC-Min is intended to:
* Make AGBAC concepts tangible and adoptable
* Enforce dual-subject authorization (human + agent)
* Apply at the system / application boundary
* Provide clear, auditable attribution
* Build confidence in the AGBAC model
* Show compatibility with existing IAM investments
* Provide a starting point for future (full) AGBAC implementations
* Encourage experimentation and feedback

<br>

## How AGBAC-Min works

Implement AGBAC-Min by following the AGBAC-Min guides below. Each guide enforces the same core requirement:

<br>

> An AI agent may access a system on behalf of a human user only if both agent and human are independently authorized.

<br>

The concept of AGBAC-Min focuses on system-level access control, showing that:

* AI agents can be represented as first-class identities
* Human principals remain the source of authority
* Tokens can carry dual-subject identity
* Access decisions can require independent authorization
* Delegation is explicit, not implicit
* Authorization is enforced before system access
* Audit records reflect both subjects

<br>

**Key Characteristics**

| Aspect             | Scope                               |
| ------------------ | ----------------------------------- |
| Access granularity | System / application level          |
| Identity types     | Human + agent                       |
| Authorization      | Role-based intersection             |
| Delegation         | Explicit                            |
| Enforcement        | Existing IAM mechanisms             |
| Code required      | None or minimal configuration logic |

<br>

**Conceptual Flow**

```
Human → AI Agent → Identity Platform → Target System
   |         |            |
   |         |            +-- Issues dual-subject token
   |         |
   |         +-- Authenticates as agent
   |
   +-- Delegates intent
```

Access is permitted only when both subjects are authorized.

<br>

## Available AGBAC-Min Guides

**AGBAC-Min-Okta**
* Foundational AGBAC profile using Okta Workforce Identity, Active Directory, OAuth 2.0, and native application assignments.
* GitHub: [https://github.com/kahalewai/agbac/agbac-min/agbac-min-okta](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-okta.md)

**AGBAC-Min-EntraID**
* Foundational AGBAC profile using Microsoft Entra ID (Azure AD), Enterprise Applications, App Registrations, and native token claims.
* GitHub: [https://github.com/kahalewai/agbac/agbac-min/agbac-min-entraid](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-entraid.md)

**AGBAC-Min-Auth0**
* Foundational AGBAC profile using Auth0 Workforce or B2B Identity, Machine-to-Machine applications, RBAC, and token customization.
* GitHub: [https://github.com/kahalewai/agbac/agbac-min/agbac-min-auth0](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-auth0.md)

**AGBAC-Min-Keycloak**
* Foundational AGBAC profile using Keycloak realms, service accounts, client roles, and protocol mappers.
* GitHub: [https://github.com/kahalewai/agbac/agbac-min/agbac-min-keycloak](https://github.com/kahalewai/agbac/blob/main/agbac-min/agbac-min-keycloak.md)

<br>

Guides and their resulting implementations are independent, and do not depend on each-other. If your organization uses multiple IAM platforms, AGBAC-Min profiles can be implemented in parallel while preserving consistent security semantics.


<br>

## Wait, so it works with my existing enterprise IAM Solution?

That's right, AGBAC-Min was designed to work with your existing enterprise IAM solution:
* You will need to configure your IAM solution to support AGBAC-Min (follow the guides)
* You will need to create or use existing organizational authorization approval workflows
* You will configure your IAM solution system / application access policies once approved
* Your existing IAM solution will now process/log requests for humans and agents (dual-subject)
* You will be able to enforce authorization requirements for both humans and agents


<br>

## Out of Scope

AGBAC-Min guides do not:
* Provide full AGBAC spec implementations
* Provide object-level authorization
* Introduce centralized policy engines
* Validate AI reasoning or prompts
* Require custom enforcement components

<br>
<br>
<br>
<br>
<br>
<p align="center">
▁ ▂ ▂ ▃ ▃ ▄ ▄ ▅ ▅ ▆ ▆ Created with Aloha by Kahalewai - 2025 ▆ ▆ ▅ ▅ ▄ ▄ ▃ ▃ ▂ ▂ ▁

</p>

