<div align="center">

# AGBAC Minimal

Implementing dual-subject authorization for humans and agents at system / application layer

</div>

<br>

## Intro

AGBAC Minimal (AGBAC-Min) is a system / application layer scoped implementation of the Agent-Based Access Control (AGBAC) specification. The goal of AGBAC-Min is to demonstrate that a sub-set of AGBAC security capabilities can be implemented today using existing enterprise IAM platforms without external policy engines or new IAM infrastructure. Each IAM Configuration Guide shows how a bounded subset of the AGBAC specification can be implemented using native configuration features of a specific identity provider. Applications and Agents are updated to become dual-subject aware (human AND agent identities)

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
* Agents can become aware of the associated human user
* Authorization is enforced before system access
* Audit records reflect both subjects

<br>
<br>

**Key Characteristics**

| Aspect              | Scope                               |
| ------------------  | ----------------------------------- |
| Access granularity  | System / application level          |
| Identity types      | Human + agent                       |
| Authorization       | Role-based intersection             |
| Delegation          | Explicit                            |
| Enforcement         | Existing IAM mechanisms             |
| IAM Code required   | None or minimal configuration logic |
| Agent Code required | Minimal to moderate updates to code |

<br>
<br>

**Conceptual Flow**

```
Human → AI Agent → Identity Platform → Target System
   |         |            |
   |         |            +-- Issues dual-subject token
   |         |
   |         +-- Receives human identity; requests token
   |
   +-- Authenticates to application; initiates agentic workflow
```

Access is permitted only when both subjects are authorized.

<br>
<br>

## Available IAM Configuration Guides

IAM Configuration Guides explain how to configure a specific IAM vendor to support AGBAC-Min

* Okta: [https://github.com/kahalewai/agbac/agbac-min/guides/okta](https://github.com/kahalewai/agbac/blob/main/agbac-min/guides/okta.md)
* EntraID: [https://github.com/kahalewai/agbac/agbac-min/guides/entraid](https://github.com/kahalewai/agbac/blob/main/agbac-min/guides/entraid.md)
* Auth0: [https://github.com/kahalewai/agbac/agbac-min/guides/auth0](https://github.com/kahalewai/agbac/blob/main/agbac-min/guides/auth0.md)
* Keycloak: [https://github.com/kahalewai/agbac/agbac-min/guides/keycloak](https://github.com/kahalewai/agbac/blob/main/agbac-min/guides/keycloak.md)

<br>

IAM Guides and their resulting implementations are independent, and do not depend on each-other. If your organization uses multiple IAM platforms, AGBAC-Min profiles can be implemented in parallel while preserving consistent security semantics.


<br>
<br>

## Available Application/Agent Code

Application/Agent Code enhances your Applications and Agents to become dual-subject aware and support out-of-session agents

* Python: [https://github.com/kahalewai/agbac/agbac-min/code/python](https://github.com/kahalewai/agbac/blob/main/agbac-min/code/python/readme.md)
* Typescript: (Coming Soon)
* Java: (Coming Soon)

<br>

Application and Agent implementations are independent, and do not depend on each-other. If your organization uses multiple languages, AGBAC-Min will maintain object/artifact formatting across languages.


<br>
<br>


## Wait, so it works with my existing enterprise IAM Solution?

That's right, AGBAC-Min was designed to work with your existing enterprise IAM solution:
* Follow best-practices; implement into non-prod first to test and validate
* You will need to configure your IAM solution to support AGBAC-Min (follow the guides)
* You will need to create or use existing organizational authorization approval workflows
* You will configure your IAM solution system / application access policies once approved
* Your existing IAM solution will now process/log requests for humans and agents (dual-subject)
* You will then update your application and agent code to become dual-subject aware (follow the guides)
* Works with single or multi-agent systems for most providers; agents can use default OAuth clients
* You will be able to enforce authorization requirements for both humans and agents

<br>


| Agent Authorized | Human Authorized | Result |
| -------------- | -------------- | ------ |
| ✅              | ✅              | ALLOW  |
| ❌              | ✅              | DENY   |
| ✅              | ❌              | DENY   |
| ❌              | ❌              | DENY   |

<br>

* This will not interfere with or impact existing authorizations for humans only (different tokens)
* You will now be able to log agent requests on behalf of human users (security attribution)
* Dual-subject authorizations are maintained the same way as traditional human only authorizations
* You just majorly upgraded your IAM capabilities without needing an entire new solution



<br>
<br>

## What about Multi-Agent or Advanced Scenario's?

AGBAC-Min can support multi-agent workfows, out-of-session agents, and async execution with certain providers, after updating the application and agent code. The AGBAC-Min Agent Guides provide the necessary code for applications and agents, which passes the human subject identity `act` to the agent for IAM token request. In out-of-session scenarios, the solution uses TLS and JWT to make remote agents aware of their human counterpart. Without this update, AGBAC-Min may natively support in-session agents only (agents that are initiatived within the same authentication session as the application). We recommend updating applications and code to become agent AND human aware!

* Application and agent instructions and code are provided with AGBAC-Min Agent Guides
* Implement the instructions in order, starting with the adapters, then the sender, then the requests
* It is intended that the code is integrated into existing applications and agents
* Unit tests and helper scripts are provided to verify the code is working properly and agents are aware
* Be advised that adding these updates will add an `act` claim to the agent OAuth requests (dual-subject)
* AGBAC-Min does not implement RFC 8693 token exchange, nor delegations (app is trust authority)
* EntraID does not support out-of-session agents due to EntraID design. AGBAC-Full will resolve this limitation.

In AGBAC-Min, the agent does not determine or request a human identity from the IAM solution; the human is authenticated and authorized for the application session. The human identity data is passed to the in-session or out-of-session agent for token request. The IAM solution enforces that both the agent and the human are independently authorized to access the target system or application.

<br>
<br>

## Out of Scope for AGBAC-Min

AGBAC-Min guides do not:
* Provide full AGBAC spec implementations
* Provide object-level authorization
* Introduce centralized policy engines
* Perform RFC 8693 token exchange
* Support dynamic delegation
* Provide automated implementations

<br>
<br>

## When will AGBAC-Full be available?

AGBAC-Full details:
* AGBAC-Full will provide a full AGBAC spec implementation
* AGBAC-Full will work with your existing IAM solution(s)
* AGBAC-Full will support object-level authorization policies
* AGBAC-Full will allow EntraID users to support out-of-session agentic workflows
* AGBAC-Full development starting Jan '26 (expected completion Feb '26)



<br>
<br>
<br>
<br>
<br>
<p align="center">
▁ ▂ ▂ ▃ ▃ ▄ ▄ ▅ ▅ ▆ ▆ Created with Aloha by Kahalewai - 2025 ▆ ▆ ▅ ▅ ▄ ▄ ▃ ▃ ▂ ▂ ▁

</p>

