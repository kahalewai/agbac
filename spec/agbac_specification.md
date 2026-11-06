# Agent-Based Access Control (AGBAC)

```
Network Working Group                                        S. K. Reilly
Internet-Draft                                                Independent
Intended status: Standards Track                           11 August 2026
Expires: 12 February 2027
```

## Abstract

Agent-Based Access Control (AGBAC) is an open, vendor-neutral, royalty-free access control model governing how artificial intelligence (AI) agents perform actions on behalf of human principals using existing identity and access management (IAM) technologies such as OAuth 2.0, OpenID Connect (OIDC), and JSON Web Token (JWT). AGBAC requires dual-subject authorization: an action must be authorized for both the human principal and the AI agent. This document defines AGBAC terminology, the identity model, token requirements, the delegation model, policy requirements, enforcement requirements, audit and logging standards, and security and threat considerations, and it specifies how existing IAM systems are safely composed in AI-driven systems without requiring new infrastructure.

## Status of This Memo

This document is an Internet-Draft. It is a working document and a work
in progress. It does not define an adopted, ratified, or published
standard and has no formal standing with any standards body.

This Internet-Draft may be updated, replaced, or obsoleted by other
documents at any time. It is inappropriate to use this Internet-Draft
as reference material or to cite it other than as "work in progress."

This Internet-Draft is valid for a maximum of six months from its date
of issue and expires on 12 February 2027. A revised version restarts this
period.

This document is published independently by its author and is formatted
in the style of an IETF Internet-Draft. It is not a product of the IETF,
the IETF Trust, the Internet Society, or any IETF working group, and its
use of Internet-Draft conventions does not imply IETF adoption,
endorsement, or review. Governance of this specification, including its
versioning, rests solely with its author.

The key normative conventions used in this document are described in
Section 3 (Conventions and Definitions).

## Copyright and License Notice

Copyright (c) 2025, 2026 Shawn Kahalewai Reilly. All rights reserved.

This document and the specification it describes are licensed under the
Apache License, Version 2.0 (the "License"); you may not use this file
except in compliance with the License. You may obtain a copy of the
License at https://www.apache.org/licenses/LICENSE-2.0. Unless required
by applicable law or agreed to in writing, this document is distributed
on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Core Principles](#2-core-principles)
3. [Conventions and Definitions](#3-conventions-and-definitions)
4. [Identity Requirements](#4-identity-requirements)
5. [Delegation Token Requirements](#5-delegation-token-requirements)
6. [Delegation Semantics](#6-delegation-semantics)
7. [Authorization Model](#7-authorization-model)
8. [Delegation Requirements](#8-delegation-requirements)
9. [Policy Requirements](#9-policy-requirements)
10. [Enforcement Requirements](#10-enforcement-requirements)
11. [Audit and Logging Requirements](#11-audit-and-logging-requirements)
12. [Security Considerations](#12-security-considerations)
13. [Interoperability](#13-interoperability)
14. [Reference Flow (Non-Normative)](#14-reference-flow-non-normative)
15. [Conformance](#15-conformance)
16. [Versioning](#16-versioning)
17. [Licensing](#17-licensing)
18. [IANA Considerations](#18-iana-considerations)
19. [References](#19-references)

- [Appendix A. Document History](#appendix-a-document-history)
- [Authors' Addresses](#authors-addresses)

<br>

## 1. Purpose and Scope

AGBAC defines an access control model for dual-subject authorization of autonomous or semi-autonomous AI agents acting on behalf of human users.
Unlike traditional access control models (RBAC, PBAC, ABAC), where the human user directly performs the action, AGBAC governs scenarios where:

* A human principal communicates instructions to an AI agent (authorizes the intent), and
* The AI agent executes actions in a system using its own identity, and
* Both subjects must be independently authorized to perform the action.

Thus, AGBAC requires dual-subject authorization:

* An action must be authorized for BOTH the human user AND the AI agent.

AGBAC is designed to be implemented using:
OAuth 2.0, OIDC, JWT, existing identity providers, and existing policy engines.

Thus, AGBAC is designed to be implemented using existing IAM systems without requiring new infrastructure. AGBAC does not replace existing authorization models. It defines how those models are safely composed in AI-driven systems. AGBAC addresses a structural limitation in existing authorization models, which assume the calling principal and authorizing principal are the same entity. AI agents violate this assumption. AGBAC formalizes this distinction.

This document is intended for security architects, IAM engineers, AI platform builders, and policy engine authors.



<br>

### 1.1 Out of Scope

AGBAC does not:

* Define a new identity provider
* Define a new authentication mechanism
* Define a new token format or cryptographic primitive
* Replace RBAC, ABAC, PBAC, or policy engines
* Mandate a specific AI model, architecture, or agent framework
* Require changes to OAuth 2.0, OIDC, or existing standards

AGBAC extends existing IAM systems by defining how they must be used together when AI agents act on behalf of humans.


<br>
<br>

## 2. Core Principles

1. **Dual Authority**
   Both the AI agent and the human principal must be authorized.

2. **No Privilege Transfer**
   Delegation enables execution, not permission inheritance.

3. **Explicit Accountability**
   Every action is attributable to both subjects.

4. **Least Privilege by Construction**
   Constraints apply independently to agents and humans.

5. **Interoperability First**
   Existing standards are reused wherever possible.


<br>
<br>

## 3. Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all
capitals, as shown here.

**Agent**
A software entity capable of autonomous or semi-autonomous action.

**Agent Identity**
A first-class, non-human, digital identity representing an AI system, model, agent, or automation capable of making authenticated requests.

**Human Principal**
A human user whose intent triggers AI agent execution.

**Delegated Intent**
An explicit instruction from a human principal authorizing an AI agent to execute actions on behalf of a human within explicitly defined bounds.
Delegated intent represents authorization to execute intent, not inferred desire, unless policy explicitly permits it.

**Dual-Subject Authorization**
Authorization requiring approval of two independent subjects.

1. The agent is permitted to perform the requested action, AND
2. The human is permitted to perform the requested action, AND
3. The human is permitted to instruct the agent to perform the requested action.

**Delegation Token**
A token representing both agent and human identities.

**PEP / PDP**
Policy Enforcement Point / Policy Decision Point.

**Resource Server**
A system receiving AI agent requests.


<br>
<br>

## 4. Identity Requirements

### 4.1 Agent Identity

Agents must be represented as first-class, non-human identities.

The agent identity must be authenticated using:

* OAuth 2.0 clients
* OIDC workload identities
* mTLS certificates
* SPIFFE/SPIRE identities
* Platform-provided workload identities

AGBAC does not define new identity types.
Agents must not reuse human identities.

<br>

### 4.2 Human Identity

Human principals must authenticate via existing enterprise identity providers.

Examples include (non-normative):

* Microsoft Entra ID (Azure AD)
* Okta
* Auth0
* Keycloak
* AWS IAM Identity Center
* Enterprise SAML identity providers

AGBAC does not define human authentication mechanisms.


<br>
<br>

## 5. Delegation Token Requirements

### 5.1 Overview

AGBAC-compliant requests must carry a Delegation Token containing both human and agent subjects.

This MUST be expressible in existing JWT/OIDC token formats.

<br>

### 5.2 Required Claims

<br>

**`sub` - Human Principal (REQUIRED)**
Represents the human principal identity.

Example:
```
"sub": "user:name@example.com"
```

<br>

**`act` - Agent Actor (REQUIRED)**
Represents the AI agent identity, the acting party to whom authority
has been delegated.
Uses the standard OAuth Actor Claim (RFC 8693).

Example:
```
"act": {
  "sub": "agent:example-ai-123"
}
```

<br>

> **Normative:**
> The presence of the `act` claim MUST NOT be interpreted as authorization.

<br>

**`delegation` - Delegated Intent Context (REQUIRED)**
Includes:

* Grant timestamp
* Delegation method (explicit, implicit, system)
* Intent summary

Describes the nature, scope, and time of the delegation.

Example:

```
"delegation": {
  "granted_at": "2025-12-01T15:32Z",
  "method": "explicit",
  "intent_summary": "User requested AI agent to retrieve customer records"
}
```

<br>

**`agbac_ver` - Specification Version (REQUIRED)**

Example:
```
"agbac_ver": "1.0"
```

<br>

### 5.3 Optional Claims

<br>

**`scp` or `permissions` - Agent Permissions (OPTIONAL)**

The agent’s allowed actions.

<br>

**`usr_scopes` - Human Permissions (OPTIONAL)**

Optional if policies resolve this independently.

Example:
```
"usr_scopes": ["read:customer-records"]
```

<br>

**`agent_confidence_level` (OPTIONAL)**

For organizations evaluating model reliability, safety or alignment.

<br>

**`delegation_expiry` (OPTIONAL)**


<br>
<br>

## 6. Delegation Semantics

### 6.1 Delegation Types

* **Explicit** - Human intentionally authorizes the agent (RECOMMENDED)
* **Implicit** - Intent inferred only if explicitly permitted by policy
* **System-Initiated** - Workflow-driven delegation

<br>

### 6.2 Delegation Constraints (NORMATIVE)

Delegation must be:

* Time-bounded
* Scope-bounded
* Revocable
* Independently auditable


<br>
<br>

## 7. Authorization Model

### 7.1 Dual-Subject Rule

An action must be allowed if and only if:

* Agent is authorized
  AND
* Human is authorized
  AND
* Delegated intent is valid

A policy engine must evaluate AGBAC requests according to the following model:

```
ALLOW(action, resource)
IFF
    AgentIdentity is permitted to perform action on resource
AND
    HumanIdentity is permitted to perform action on resource
AND
    DelegatedIntent is valid, non-expired, and appropriate for the action
```

This is a core requirement of AGBAC.

AGBAC profiles OAuth 2.0 Token Exchange (RFC 8693) by additionally
requiring dual-subject evaluation. RFC 8693 directs a token consumer to
consider only the token's top-level claims and the party identified as
the current actor by the `act` claim; AGBAC deliberately strengthens
this consumption rule. An implementation that authorizes only the
current actor, as a plain RFC 8693 consumer does, does not satisfy this
section.

<br>

### 7.2 No Escalation Guarantees

Delegation must not:

* Grant agents new permissions through delegation
* Grant humans indirect permissions through agent execution

<br>

### 7.3 Delegation Scope Rules

Policies MUST define:

* Which humans may delegate actions to which agents
* Which agents may act on behalf of which humans
* Which actions require explicit delegation


<br>
<br>

## 8. Delegation Requirements

### 8.1 Explicit Delegation (RECOMMENDED)

Human intentionally instructs the AI agent to perform an action.

<br>

### 8.2 Implicit Delegation (NOT RECOMMENDED)

Agent infers user desires through contextual interaction.
Must be explicitly permitted by policy.

<br>

### 8.3 System Delegation (PERMITTED)

System workflows automatically assign tasks to AI agents.


<br>
<br>

## 9. Policy Requirements

### 9.1 AGBAC Policy must support:

1. Agent identity and permissions
2. Human identity and permissions
3. Delegation relationship
4. Delegated intent
5. Resource attributes
6. Resource constraints
7. Environmental context
8. Contextual constraints

<br>

### 9.2 Policy Implementation

Policies may be implemented in:

* OPA/Rego
* Cedar
* Zanzibar-like systems
* AWS IAM
* Azure Role Assignments
* Keycloak Authorization Services

AGBAC does not mandate a specific policy engine.


<br>
<br>

## 10. Enforcement Requirements

### 10.1 Policy Enforcement Points

A Policy Enforcement Point (PEP) MUST:

1. Accept a Delegation Token from the AI agent
2. Authenticate and validate the delegation token
3. Validate issuer and signature
4. Extract both `sub` and `act` identities
5. Submit both `sub` and `act` identities to the PDP
6. Evaluate authorization for both subjects independently
7. Deny access if either subject fails authorization
8. Emit an audit event

A PEP MUST NOT infer authorization from the presence or contents of
the `sub` and `act` claims alone; authorization comes from PDP
evaluation.

<br>

### 10.2 Token Issuance

OAuth 2.0 Token Exchange (RFC 8693) is RECOMMENDED.

Alternative mechanisms are permitted only if they provide equivalent guarantees, including:

* Dual-subject integrity
* Non-forgery
* Replay resistance
* Bounded delegation


<br>
<br>

## 11. Audit and Logging Requirements

Every AGBAC-controlled action MUST generate a structured audit event containing:

### 11.1 Required Fields:

* Timestamp
* Agent identity
* Human identity
* Action performed
* Resource affected
* Delegation type
* Delegation context
* Policy decision (allow/deny)
* Reason for decision
* Correlation ID

### 11.2 Optional Audit Extensions (NON-NORMATIVE)

* Agent reasoning summary
* Safety confidence score

Audit events MUST NOT contain raw prompts or confidential user content unless explicitly configured.
Raw prompts MUST NOT be logged by default.


<br>
<br>

## 12. Security Considerations

### 12.1 Supported Threats

AGBAC is designed to mitigate:

* Privilege escalation via AI
* Human permission overreach via AI
* Prompt-injection leading to unauthorized actions
* Misuse of autonomous agents
* Undocumented delegation
* Cross-user agent misuse
* Cross-user impersonation
* Agent impersonation
* Token replay
* Delegation tampering

<br>

### 12.2 Token Security

Delegation tokens must:

* Be signed (see the JSON Web Token Best Current Practices [RFC8725])
* Be short-lived TTL
* Use transport binding where available (e.g., mTLS [RFC8705], DPoP [RFC9449], token binding where possible)

<br>

### 12.3 Logging and Privacy

Audit logs must be sanitized of unnecessary personal data (PII).


<br>
<br>

## 13. Interoperability

AGBAC implementations must use existing IAM standards, including:

* OAuth 2.0
* OAuth 2.0 Token Exchange (RFC 8693)
* OIDC
* JWT
* XACML, OPA, or Cedar for policy
* Existing enterprise IdPs

No new token formats or cryptographic primitives are defined by AGBAC.


<br>
<br>

## 14. Reference Flow (Non-Normative)

Human → AI Agent → Resource Server

```
Human → AI Agent: "Get customer record 553"
AI Agent → Token Service: Token Exchange (include Human identity)
Token Service → AI Agent: AGBAC Delegation Token
AI Agent → Resource Server: API Request + Token
Resource Server → PDP: Evaluate dual-subject
PDP → Resource Server: ALLOW or DENY
Resource Server: Return response
Audit System: Log AGBAC event
```


<br>
<br>

## 15. Conformance

An implementation is AGBAC-conformant if it satisfies all of
Section 15.1.

### 15.1 REQUIRED

1. Uses dual-subject tokens including `sub` and `act` claims
2. Enforces dual-subject authorization
3. Logs all AGBAC decisions
4. Validates delegation scope
5. Uses a secure token format (JWT/OIDC)
6. Audit logging

### 15.2 RECOMMENDED

1. Implements OAuth Token Exchange
2. Supports OPA or Cedar policy templates
3. Supports explicit delegation workflows

Implementations that omit any REQUIRED behavior MUST NOT claim AGBAC conformance.

<br>
<br>

## 16. Versioning

AGBAC versions follow semantic versioning:

```
MAJOR.MINOR.PATCH
```

This spec is **2.0.0**.


<br>
<br>

## 17. Licensing

This specification is licensed under the Apache License 2.0.

<br>

## 18. IANA Considerations

This document has no IANA actions.

## 19. References

### 19.1 Normative References

```
[OIDC]     Sakimura, N., Bradley, J., Jones, M., de Medeiros, B.,
           and C. Mortimore, "OpenID Connect Core 1.0", OpenID
           Foundation, November 2014,
           <https://openid.net/specs/openid-connect-core-1_0.html>.

[RFC2119]  Bradner, S., "Key words for use in RFCs to Indicate
           Requirement Levels", BCP 14, RFC 2119, March 1997,
           <https://www.rfc-editor.org/info/rfc2119>.

[RFC6749]  Hardt, D., Ed., "The OAuth 2.0 Authorization Framework",
           RFC 6749, October 2012,
           <https://www.rfc-editor.org/info/rfc6749>.

[RFC7519]  Jones, M., Bradley, J., and N. Sakimura, "JSON Web Token
           (JWT)", RFC 7519, May 2015,
           <https://www.rfc-editor.org/info/rfc7519>.

[RFC8174]  Leiba, B., "Ambiguity of Uppercase vs Lowercase in
           RFC 2119 Key Words", BCP 14, RFC 8174, May 2017,
           <https://www.rfc-editor.org/info/rfc8174>.

[RFC8693]  Jones, M., Nadalin, A., Campbell, B., Ed., Bradley, J.,
           and C. Mortimore, "OAuth 2.0 Token Exchange", RFC 8693,
           January 2020, <https://www.rfc-editor.org/info/rfc8693>.
```

### 19.2 Informative References

```
[CEDAR]    Amazon Web Services, "Cedar Policy Language",
           <https://www.cedarpolicy.com/>.

[OPA]      The Open Policy Agent Project, "Open Policy Agent",
           <https://www.openpolicyagent.org/>.

[RFC8705]  Campbell, B., Bradley, J., Sakimura, N., and
           T. Lodderstedt, "OAuth 2.0 Mutual-TLS Client
           Authentication and Certificate-Bound Access Tokens",
           RFC 8705, February 2020,
           <https://www.rfc-editor.org/info/rfc8705>.

[RFC8725]  Sheffer, Y., Hardt, D., and M. Jones, "JSON Web Token
           Best Current Practices", BCP 225, RFC 8725,
           February 2020, <https://www.rfc-editor.org/info/rfc8725>.

[RFC9449]  Fett, D., Campbell, B., Bradley, J., Lodderstedt, T.,
           Jones, M., and D. Waite, "OAuth 2.0 Demonstrating
           Proof of Possession (DPoP)", RFC 9449, September 2023,
           <https://www.rfc-editor.org/info/rfc9449>.

[SPIFFE]   Cloud Native Computing Foundation, "SPIFFE: Secure
           Production Identity Framework for Everyone",
           <https://spiffe.io/>.

[XACML]    OASIS, "eXtensible Access Control Markup Language (XACML)
           Version 3.0", OASIS Standard, January 2013,
           <https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html>.
```

## Appendix A. Document History

| Version | Date       | Status         | Summary                                                             |
|---------|------------|----------------|---------------------------------------------------------------------|
| 1.0.0   | 2025-12-20 | Internet-Draft | Initial publication.                                                |
| 1.0.1   | 2026-08-01 | Internet-Draft | Editorial: reformatted to IETF Internet-Draft conventions; terminology corrected; no normative changes. |
| 2.0.0   | 2026-08-11 | Internet-Draft | Breaking: `sub`/`act` claim semantics swapped to align with RFC 8693 (`sub` = human principal, `act` = agent actor); Section 7.1 clarifies AGBAC's dual-subject strengthening of RFC 8693; contradictory Section 10.1 item replaced by an explicit claim-inference prohibition; Section 15 lead-in completed; informative references added (RFC 8705, RFC 8725, RFC 9449); XACML URL normalized to https; author contact email added. |

## Authors' Addresses

   Shawn Kahalewai Reilly
   Independent

   Email: shawn.k.reilly@gmail.com
