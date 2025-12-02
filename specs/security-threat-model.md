# **1. Introduction**

This document defines the **security threat model** for AGBAC (AI-Agent-Based Access Control).
Its purpose is to help organizations understand risks introduced when AI agents execute actions on behalf of human users, and how AGBAC mitigates them.

AGBAC augments existing IAM (Identity & Access Management) systems, adding:

* Dual-subject authorization
* Delegated intent
* Explicit human–agent identity binding
* Authorization context metadata
* Auditing requirements

This threat model is applicable to:

* AI assistants
* Autonomous agents
* Retrieval-augmented agents
* API-driven AI services
* AI copilots for operational systems
* Embedded AI in enterprise software

---

# **2. Threat Modeling Framework**

This document uses a hybrid model incorporating:

* **STRIDE** categories
* **Zero Trust principles** (NIST 800-207)
* **Identity threats** (NIST 800-63-3)
* **MITRE ATT&CK mappings** for relevant threat vectors
* **OWASP Top 10 LLM risks**
* **AI-specific vectors (autonomy, misalignment, indirect prompt risks)**

Mitigations provided by AGBAC are explicitly noted.

---

# **3. System Overview**

AI agents can:

* Authenticate independently
* Carry permissions
* Invoke APIs
* Modify data
* Interact with systems on behalf of human users

**Risk:**
AI agents become first-class actors in enterprise security, but typical IAM systems assume that **human users** drive all actions.

**AGBAC fills this gap** by ensuring:

> No AI agent can exceed the permissions of either the human or the agent itself.

---

# **4. Assets**

The following system assets require protection:

### **4.1 Identity Assets**

* Human identity
* Agent identity
* Delegation metadata
* Tokens (JWT, OIDC)
* Credentials (API keys, certificates, workload identities)

### **4.2 Authorization Assets**

* Permission assignments
* Delegation scopes
* Policy definitions
* Policy decision inputs

### **4.3 Data Assets**

* Protected resource data
* Audit logs
* Model-reasoning summaries
* User prompts and instructions

---

# **5. Adversaries**

AGBAC assumes the following adversaries may be present:

### **5.1 External Attackers**

* Attempt credential theft
* Try to impersonate agents or users
* Manipulate tokens

### **5.2 Malicious Insider**

* Authorized user misusing AI agents to circumvent controls
* Agent developer inserting backdoors

### **5.3 Compromised AI Agent**

* Agent manipulated through prompt attacks
* Model misalignment
* Supply-chain tampering

### **5.4 Compromised User**

* Phishing
* Social engineering
* Intent misrepresentation

### **5.5 Supply Chain & Cloud Threats**

* Malicious or compromised LLM providers
* Model poisoning
* Credential mismanagement

---

# **6. Threat Vectors and Mitigations**

Below are the primary threats addressed by AGBAC.

---

## **6.1 Identity Threats**

### **6.1.1 AI Agent Impersonation**

**Threat:** An attacker impersonates an AI agent to perform actions.
**Vectors:**

* Stolen credentials
* Replay attacks
* Token leakage

**AGBAC Mitigations:**

* Agent identity must be authenticated via existing IAM
* Short-lived delegation tokens
* Strict verification of `sub` claim
* Token binding/mTLS/SPIFFE recommended

---

### **6.1.2 Human Identity Impersonation**

**Threat:** An attacker pretends to be a human user controlling an agent.
**Vectors:**

* Compromised login
* Phishing
* OAuth token theft

**AGBAC Mitigations:**

* Separate authentication for human and agent
* Standard enterprise MFA for human identity
* Inclusion of `act.sub` claim
* Delegation metadata requiring explicit consent

---

## **6.2 Authorization Threats**

### **6.2.1 Permission Overreach by AI Agents**

**Threat:** AI agent uses *its own* permissions to perform actions the user cannot perform.
**AGBAC Mitigation:**

* Dual-subject authorization denies overreach
* Agents get *least privilege* by default
* Policies require BOTH agent and human to be authorized

---

### **6.2.2 Human Permission Overreach via AI**

**Threat:** A human user uses an AI agent to escalate privileges or bypass constraints.
**Examples:**

* User with restricted rights asks an agent with broader rights to perform privileged tasks

**AGBAC Mitigation:**

* Dual-subject authorization prevents user-hijacking agent permissions
* `delegation` metadata prevents covert delegations
* Audit logs detect anomalies

---

### **6.2.3 Undocumented or Implicit Delegation**

**Threat:** Agents act autonomously without clear human intent.

**Vectors:**

* Prompt inference
* Contextual hallucinations
* Autonomy without verification

**AGBAC Mitigation:**

* Delegation metadata required
* Policies may restrict implicit delegation
* Delegation TTLs enforce short-lived authority

---

## **6.3 Prompt & Model Manipulation Threats**

### **6.3.1 Prompt Injection Leading to Unauthorized Actions**

**Threat:**
Adversary injects malicious instructions that cause the agent to perform unauthorized tasks.

**AGBAC Mitigation:**

* Authorization enforced outside the model
* Model cannot override IAM roles
* Dual-subject restrictions prevent unauthorized tasks regardless of prompt

---

### **6.3.2 Output Manipulation / Hallucination-Induced Actions**

**Threat:**
Agent acts wrongly due to hallucinated intent or misinterpretation.

**AGBAC Mitigation:**

* Delegation must explicitly match the action
* Policies can require human confirmation
* Audit trails for reasoning verification

---

### **6.3.3 Adversarial Attack on Agent Model**

**Threat:**
Inputs designed to induce harmful or unauthorized actions.

**AGBAC Mitigations:**

* Authorization always enforced at PEP
* Agent identity cannot override policy
* Risk limited to what both identities can do

---

## **6.4 Token & Credential Threats**

### **6.4.1 Token Replay**

**Threat:**
Captured token reused by attacker.

**AGBAC Mitigation:**

* Short TTLs
* Token binding / mTLS
* Nonce-based replay protection recommended

---

### **6.4.2 Delegation Token Tampering**

**Threat:**
Attacker modifies token delegation metadata.

**AGBAC Mitigation:**

* Signed JWT tokens
* Verification of issuer and claims

---

### **6.4.3 Credential Theft of AI Agents**

**Threat:**
Attackers steal agent secrets, API keys, or certificates.

**AGBAC Mitigations:**

* Support for ephemeral workload identities (SPIFFE, AWS IAM roles)
* Agent credential rotation
* Zero Trust identity posture

---

## **6.5 Logging & Observability Threats**

### **6.5.1 Audit Log Tampering**

**Threat:**
Attacker modifies logs to hide unauthorized agent actions.

**AGBAC Mitigation:**

* Standardized immutable audit formats
* Write-once or append-only logging systems
* External SIEM integration

---

### **6.5.2 Sensitive Data Exposure in Logs**

**Threat:**
Raw prompts or user input leak into logs.

**AGBAC Mitigation:**

* Log minimization requirements
* Standard “safe audit fields”
* Optional reasoning redaction

---

# **7. Threats Not Directly Mitigated by AGBAC**

AGBAC does not attempt to solve:

### **7.1 Data Leakage via AI Responses**

Handled by data governance, not access control.

### **7.2 Model Misalignment Safety**

AGBAC restricts capabilities, but does not align models.

### **7.3 Unauthorized Fine-Tuned Model Behavior**

AGBAC limits impact but cannot fix model quality.

---

# **8. Recommended Security Controls**

## **8.1 Mandatory**

* MFA for all human identities
* Short-lived delegation tokens
* Signed tokens with verified issuer
* Dual-subject authorization
* Delegation context and TTL
* Immutable audit trails
* Regular agent credential rotation

## **8.2 Strongly Recommended**

* Token binding (DPoP, mTLS, platform identity)
* Behavioral anomaly detection for agents
* Safety filters around agent autonomy
* Explicit user confirmation for sensitive actions
* OPA/Cedar for policy enforcement

## **8.3 Optional**

* Agent trust scores
* Reasoning-trace logging
* Rate limits on autonomous agent actions

---

# **9. Residual Risk**

Even with AGBAC applied:

* Agents may still misunderstand human intent
* Policies may be misconfigured
* Model manipulation may occur
* Supply-chain risks remain
* Human users may mis-delegate authority

Residual risks must be addressed by:

* Human-in-the-loop approvals
* Defense-in-depth controls
* Runtime security checks
* Model alignment and validation

---

# **10. Conclusion**

AI systems introduce **new identity and authorization risks** that traditional IAM models are not designed to handle.
AGBAC mitigates these by ensuring:

### ✔ every action is tied to both an AI agent AND a human

### ✔ delegation is explicit and verifiable

### ✔ policies enforce least privilege for both parties

### ✔ audit trails capture who *actually* caused a change

AGBAC does not replace IAM—it extends it with the controls required for secure AI adoption.

