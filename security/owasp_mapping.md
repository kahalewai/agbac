# Mapping AGBAC to OWASP Top 10 for LLM Applications

Below is a correlation between AGBAC controls and the OWASP LLM Top 10 risks (2023–2024).

<br>

## LLM01: Prompt Injection

**Risk**
Attacker manipulates prompts to cause unauthorized actions.

**AGBAC Mitigation**
Partial

AGBAC:
* Prevents injected prompts from executing actions outside authorization
* Ensures the agent cannot exceed agent + human permissions

AGBAC does **not**:
* Detect prompt manipulation
* Validate semantic correctness of prompts

Result:
Prompt injection becomes **contained**, not eliminated.

<br>

## LLM02: Insecure Output Handling

**Risk**
Model output is executed blindly by downstream systems.

**AGBAC Mitigation**
Strong

AGBAC:
* Requires authorization before execution
* Treats execution as a privileged action
* Prevents agent-only execution paths

Result:
Unauthorized outputs cannot cross trust boundaries.

<br>

## LLM03: Training Data Poisoning

**Risk**
Model behavior influenced by malicious data.

**AGBAC Mitigation**
Out of scope

AGBAC correctly does not attempt to address this.

<br>

## LLM04: Model Denial of Service

**Risk**
Resource exhaustion via agent actions.

**AGBAC Mitigation**
Indirect

AGBAC:
* Enables per-agent and per-user rate limits
* Improves attribution for abuse detection

AGBAC does not:
* Enforce quotas directly

<br>

## LLM05: Supply Chain Vulnerabilities

**Risk**
Compromised models, plugins, or agents.

**AGBAC Mitigation**
Partial

AGBAC:
* Requires agent identities
* Enables revocation of compromised agents
* Prevents agent impersonation

Does not:
* Validate model integrity

<br>

## LLM06: Sensitive Information Disclosure

**Risk**
Unauthorized access to sensitive data.

**AGBAC Mitigation**
Strong

AGBAC:
* Requires both human and agent authorization
* Prevents privilege laundering
* Improves auditability

This is one of AGBAC’s strongest areas.

<br>

## LLM07: Insecure Plugin Design

**Risk**
Plugins execute actions with excessive privileges.

**AGBAC Mitigation**
Strong

AGBAC:
* Treats plugins/agents as identities
* Requires explicit permission assignment
* Prevents “god-mode” plugins

<br>

## LLM08: Excessive Agency

**Risk**
Agents act beyond intended scope.

**AGBAC Mitigation**
Very strong

This is **the primary problem AGBAC solves**.

Controls:
* Dual authorization
* Explicit delegation
* Time-bounded execution
* Revocation

<br>

## LLM09: Overreliance on LLMs

**Risk**
Blind trust in model outputs.

**AGBAC Mitigation**
Indirect

AGBAC:
* Forces human authority checks
* Ensures accountability

Does not:
* Validate correctness

<br>

## LLM10: Improper Authorization

**Risk**
Access control failures in AI systems.

**AGBAC Mitigation**
Primary mitigation

AGBAC directly addresses this risk category.

<br>

### OWASP Summary Table

| OWASP LLM Risk            | AGBAC Coverage |
| ------------------------- | -------------- |
| Prompt Injection          | Partial        |
| Insecure Output Handling  | Strong         |
| Data Poisoning            | Out of Scope   |
| DoS                       | Partial        |
| Supply Chain              | Partial        |
| Sensitive Data Disclosure | Strong         |
| Insecure Plugins          | Strong         |
| Excessive Agency          | Very Strong    |
| Overreliance              | Indirect       |
| Improper Authorization    | Primary        |

