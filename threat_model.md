# Threat Model for AGBAC

## 3.1 Assets Protected

* Enterprise systems
* Sensitive data
* Authorization boundaries
* Audit integrity
* Human accountability

<br>

## 3.2 Threat Actors

* Malicious users
* Compromised AI agents
* Over-permissioned agents
* Insider threats
* External attackers using prompt injection

<br>

## 3.3 Threats and Mitigations

### Threat: AI Privilege Escalation

**Description**
Agent performs actions beyond its intended authority.

**Mitigation**
* Agent identity is independent
* Agent permissions are bounded
* Dual-subject authorization enforced

Residual Risk: Low

<br>

### Threat: Privilege Laundering via AI

**Description**
Human uses AI to bypass access restrictions.

**Mitigation**
* Human authorization required
* No permission transfer
* Explicit delegation required

Residual Risk: Low

<br>

### Threat: Cross-User Impersonation

**Description**
Agent acts on behalf of another user.

**Mitigation**
* `act` claim required
* Delegation validated
* Audit attribution enforced

Residual Risk: Low

<br>

### Threat: Agent Impersonation

**Description**
Malicious actor impersonates an AI agent.

**Mitigation**
* Strong agent authentication
* Token signing
* Revocation support

Residual Risk: Medium (depends on IAM hygiene)

<br>

### Threat: Prompt Injection → Unauthorized Action

**Description**
Injected prompt causes agent to execute forbidden actions.

**Mitigation**
* Authorization enforced independently of prompt
* Delegation scope validated

Residual Risk: Medium (prompt correctness still matters)

<br>

### Threat: Undocumented Delegation

**Description**
Agent acts without human awareness.

**Mitigation**
* Delegation metadata required
* Audit logging enforced

Residual Risk: Low

<br>

### Threat: Replay or Token Abuse

**Description**
Stolen tokens reused.

**Mitigation**
* Short TTLs
* Token binding
* Transport security

Residual Risk: Medium (standard OAuth risk)

<br>

## 3.4 Out of Scope

AGBAC does not prevent:
* Malicious authorized users
* Incorrect human instructions
* Model hallucinations
* Business logic flaws
