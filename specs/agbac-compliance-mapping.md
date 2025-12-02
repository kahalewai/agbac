# **AGBAC Compliance Mapping**

### **SOC 2 • ISO 27001 • NIST 800-53 / 800-207 Zero Trust Alignment**

AGBAC (AI-Agent-Based Access Control) introduces security controls designed to ensure that actions taken by **AI agents** are strictly authorized by both the **agent identity** and the **human identity** that directed it.
This dual-subject model supports compliance across major security frameworks.

This document maps AGBAC features to relevant controls in:

* **SOC 2** (Security, Availability, Confidentiality)
* **ISO/IEC 27001:2022**
* **NIST SP 800-53 Rev. 5**
* **NIST 800-207 Zero Trust Architecture**

---

# 🔐 **1. Summary: How AGBAC Helps Compliance**

AGBAC supports compliance by enabling:

| Requirement                 | AGBAC Contribution                                      |
| --------------------------- | ------------------------------------------------------- |
| **Identity governance**     | Ensures both agent and human identities are validated.  |
| **Access control**          | Dual-subject authorization prevents privilege misuse.   |
| **Audit & accountability**  | Full audit chain linking agent actions to the user.     |
| **Least privilege**         | Agents cannot exceed the permissions of the human user. |
| **Delegation transparency** | Explicit intent and TTL ensure controlled usage.        |
| **Zero Trust enforcement**  | Every request evaluated against strict policies.        |
| **Risk reduction**          | Reduces blast radius of compromised agents or users.    |

---

# 🧩 **2. SOC 2 Trust Services Criteria Mapping**

## **SOC 2 CC Series (Common Criteria)**

### **CC6 – Logical and Physical Access Controls**

| SOC 2 Control                                 | AGBAC Alignment                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------- |
| **CC6.1 – Identification and Authentication** | AGBAC requires independent authentication for human and agent identities. |
| **CC6.2 – Authentication Mechanisms**         | Uses existing IAM systems (OIDC, MFA, workload identities).               |
| **CC6.3 – Role-Based Access**                 | Dual-subject enforcement extends RBAC/PBAC.                               |
| **CC6.6 – Restrict Logical Access**           | Agents cannot exceed privilege of human; delegation required.             |

---

### **CC7 – System Operations**

| Control                                  | AGBAC Alignment                                       |
| ---------------------------------------- | ----------------------------------------------------- |
| **CC7.2 – Change and Anomaly Detection** | Dual-subject logs reveal anomalous agent behavior.    |
| **CC7.3 – Incident Management**          | Delegation traceability improves root-cause analysis. |
| **CC7.4 – Logging and Monitoring**       | AGBAC provides standardized audit schemas.            |

---

### **CC8 – Change Management**

| Control                                  | AGBAC Alignment                                  |
| ---------------------------------------- | ------------------------------------------------ |
| **CC8.1 – Authorized Changes Only**      | AI agents cannot execute unauthorized actions.   |
| **CC8.2 – Prevent Unauthorized Changes** | Enforcement at PEP prevents rogue agent actions. |

---

### **CC9 – Risk Mitigation**

| Control                                               | AGBAC Alignment                                                  |
| ----------------------------------------------------- | ---------------------------------------------------------------- |
| **CC9.1 – Identify and Assess Risks**                 | Delegation metadata supports risk assessments for agent actions. |
| **CC9.2 – Mitigate Risks from Vendors/Third Parties** | Applies to external AI providers using AGBAC tokens.             |

---

# 🌍 **3. ISO/IEC 27001:2022 Mapping**

AGBAC aligns strongly with **Annex A** controls.

## **A.5 Organizational Controls**

| ISO Control                           | AGBAC Alignment                                                   |
| ------------------------------------- | ----------------------------------------------------------------- |
| **A.5.15 Access Control Policy**      | AGBAC defines structured, enforceable access controls for agents. |
| **A.5.17 Authentication Information** | Uses IdP authentication for agents + humans.                      |
| **A.5.19 Secure Log-On Procedures**   | Dual-subject identity model reinforces log-on security.           |

---

## **A.8 Technological Controls**

### **A.8.1 User Endpoint Devices**

| ISO Control                                | AGBAC Alignment                                           |
| ------------------------------------------ | --------------------------------------------------------- |
| **A.8.1.2 Privilege Management**           | Enforces least privilege across human + agent identities. |
| **A.8.1.3 Information Access Restriction** | Ensures agents cannot bypass user privileges.             |

---

### **A.8.2 Identity and Access Management**

| ISO Control                                         | AGBAC Alignment                                                            |
| --------------------------------------------------- | -------------------------------------------------------------------------- |
| **A.8.2.1 Identity Management**                     | Introduces managed agent identities.                                       |
| **A.8.2.2 Access Control**                          | Dual-subject authorization fully aligns with ISO AC requirements.          |
| **A.8.2.3 Responsibilities for Access**             | Clear responsibility attribution via audit logs.                           |
| **A.8.2.4 Access to Source Code & Admin Functions** | Ensures agents cannot perform admin actions without valid user delegation. |

---

### **A.8.12 Event Logging**

| ISO Control                     | AGBAC Alignment                                           |
| ------------------------------- | --------------------------------------------------------- |
| **A.8.12.1 Event Logging**      | AGBAC creates detailed audit logs: user ↔ agent ↔ action. |
| **A.8.12.2 Protection of Logs** | Logs can be stored in immutable stores.                   |
| **A.8.12.3 Clock Sync**         | Delegation timestamps require clock consistency.          |

---

### **A.8.16 Monitoring Activities**

| ISO Control                           | AGBAC Alignment                              |
| ------------------------------------- | -------------------------------------------- |
| **A.8.16.1 Monitoring of System Use** | Fine-grained audit of agent-driven activity. |

---

# 🇺🇸 **4. NIST SP 800-53 Rev. 5 Mapping**

## **4.1 Access Control (AC)**

| NIST Control                          | AGBAC Mapping                                     |
| ------------------------------------- | ------------------------------------------------- |
| **AC-2 Account Management**           | Agents treated as managed identities.             |
| **AC-3 Access Enforcement**           | Dual-subject enforcement matches AC-3 principles. |
| **AC-4 Information Flow Enforcement** | Prevents agent bypass of human permissions.       |
| **AC-5 Separation of Duties**         | Splits responsibilities between human + agent.    |
| **AC-6 Least Privilege**              | Central principle of AGBAC.                       |

---

## **4.2 Identification and Authentication (IA)**

| NIST Control                             | AGBAC Mapping                                   |
| ---------------------------------------- | ----------------------------------------------- |
| **IA-2 Identification & Authentication** | Independent authentication for human and agent. |
| **IA-4 Identifier Management**           | Structured naming for agent identities.         |
| **IA-5 Authenticator Management**        | Supports workload identity secret rotation.     |

---

## **4.3 Audit & Accountability (AU)**

| NIST Control                      | AGBAC Mapping                                          |
| --------------------------------- | ------------------------------------------------------ |
| **AU-2 Event Logging**            | AGBAC audit schemas include human + agent attribution. |
| **AU-3 Content of Audit Records** | Delegated intent + identity binding included.          |
| **AU-6 Audit Review & Analysis**  | Enables trace-back to the triggering human.            |
| **AU-12 Audit Generation**        | Standard for all AGBAC-compliant systems.              |

---

## **4.4 System & Information Integrity (SI)**

| NIST Control                           | AGBAC Mapping                            |
| -------------------------------------- | ---------------------------------------- |
| **SI-4 System Monitoring**             | Detect anomalous agent behavior.         |
| **SI-7 Software / Firmware Integrity** | Applies to agent code or model versions. |

---

# 🛡 **5. NIST 800-207 Zero Trust Architecture Mapping**

AGBAC aligns strongly with ZTA by:

| ZTA Requirement                   | AGBAC Mapping                                                            |
| --------------------------------- | ------------------------------------------------------------------------ |
| **Identity-centric security**     | Human + agent identities required for each request.                      |
| **Dynamic, context-aware policy** | Delegation context and TTL.                                              |
| **Externalized authorization**    | PDP evaluates all actions.                                               |
| **Per-request decision-making**   | Every call independently authorized.                                     |
| **Assume breach**                 | Compromised identities prevented from escalating via dual-subject rules. |
| **Continuous monitoring**         | Full audit visibility into agent behavior.                               |

---

# 🧾 **6. Governance, Risk, and Compliance (GRC) Benefits**

AGBAC improves GRC posture by delivering:

### ✔ Verifiable chain-of-intent

Every agent action is linked to a human and the delegated intent.

### ✔ Accountability

Clear attribution of AI-driven system changes.

### ✔ Mitigation of new AI identity risks

AGBAC closes structural IAM weaknesses exposed by AI agents.

### ✔ Better auditability

SOC2/ISO/NIST aligned logs produced automatically.

### ✔ Reduced fraud & unauthorized access

Dual-subject policy eliminates many overreach scenarios.

---

# 🧩 **7. Auditor-Ready Control Summary**

| Framework        | AGBAC Adds Value By…                                           |
| ---------------- | -------------------------------------------------------------- |
| **SOC 2**        | Strengthening identity, access control, monitoring, and audit. |
| **ISO 27001**    | Implementing modern IAM controls for AI systems.               |
| **NIST 800-53**  | Supporting access control, audit, and integrity families.      |
| **NIST 800-207** | Implementing ZTA-compliant dual-identity verification.         |

