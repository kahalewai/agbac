# ✅ 1. **AGBAC Zero Trust Mapping**

**File:** `/specs/zero-trust-mapping.md`

# **AGBAC Zero Trust Architecture Mapping (NIST 800-207)**

AGBAC (AI-Agent-Based Access Control) integrates cleanly with Zero Trust Architecture (ZTA) by adding explicit authorization controls for **AI agents acting on behalf of human users**.
This document maps AGBAC elements to NIST 800-207 Zero Trust Architecture components and principles.

---

# **1. Zero Trust Goals Addressed by AGBAC**

| Zero Trust Goal                  | How AGBAC Satisfies                                                                                 |
| -------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Never trust, always verify**   | Both *agent* and *user* are independently verified at every action.                                 |
| **Continuous verification**      | Delegations have TTLs; tokens short-lived; authorization evaluated per request.                     |
| **Least privilege**              | Requires both subjects to have explicit permission; prevents privilege inflation.                   |
| **Assume breach**                | Compromise of agent or user does not grant unauthorized access unless both identities match policy. |
| **Strong identity for entities** | Agents have workload identities; users have standard enterprise identities.                         |
| **Policy-based access**          | AGBAC mandates policy evaluation via engines (OPA, Cedar, IAM) per request.                         |

---

# **2. Mapping to Zero Trust Components (NIST 800-207)**

## **2.1 Policy Decision Point (PDP)**

AGBAC-compliant PDP evaluates:

* Agent identity (`sub`)
* Human identity (`act`)
* Delegation metadata
* Resource/action match
* Policy constraints

AGBAC extends ZTA by requiring **dual-subject authorization**.

---

## **2.2 Policy Enforcement Point (PEP)**

PEPs MUST:

* Accept AGBAC delegation tokens
* Extract both identities
* Enforce dual-subject checks
* Deny if either subject fails policy

This aligns with ZTA’s requirement that enforcement is external to client systems.

---

## **2.3 Identity Provider (IdP)**

AGBAC uses:

* Standard OIDC/OAuth IdPs
* No new identity types
* Token Exchange (RFC 8693)

IdPs provide:

* User authentication
* Agent workload identity
* Delegation tokens

---

## **2.4 Continuous Diagnostics and Monitoring (CDM)**

AGBAC contributes:

* Standardized structured audit logs
* Dual-subject action telemetry
* Delegation tracing
* Explicit origin-of-intent visibility

This enhances Zero Trust observability.

---

## **2.5 Policy Engine**

AGBAC policies enforce:

* Dual authorization
* Delegation rules
* Human-to-agent mapping
* Delegation scope

Compatible with:

* OPA
* Cedar
* Zanzibar
* AWS IAM
* Azure RBAC

---

## **2.6 Threat Intelligence**

AGBAC audit logs enhance ZTA threat monitoring by:

* Capturing anomalous agent behavior
* Detecting user permission overreach
* Highlighting compromised identities

---

# **3. Mapping to Zero Trust Tenets**

| Zero Trust Tenet                          | AGBAC Mapping                                                     |
| ----------------------------------------- | ----------------------------------------------------------------- |
| **Identity as the new perimeter**         | AGBAC defines two identities per request—both verified.           |
| **Explicit verification of all entities** | Token Exchange ensures identity binding; AI agents authenticated. |
| **Access is per transaction**             | AGBAC enforces authorization on every request.                    |
| **Adaptive, context-aware access**        | Delegation includes context (intent, timestamp, method).          |
| **Access is dynamic and policy-driven**   | AGBAC policies account for agent, user, and context.              |
| **Automated threat detection**            | Logs provide fine-grained attribution for detecting anomalies.    |

---

# **4. Zero Trust Benefits of AGBAC**

1. Prevents AI-driven unauthorized actions
2. Eliminates human privilege escalation via agents
3. Eliminates agent privilege escalation via humans
4. Improves accountability and auditability
5. Reduces attack impact of agent compromise
6. Supports microservice architectures and workload identities


