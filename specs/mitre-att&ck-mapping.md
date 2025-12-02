# **MITRE ATT&CK Tactics & Techniques Relevant to AI Agents + AGBAC Mitigations**

This mapping identifies how AGBAC mitigates common MITRE ATT&CK techniques related to identity, credential abuse, and system manipulation by or through AI agents.

---

# **1. Initial Access**

| Technique                             | Description                                     | AGBAC Mitigation                                                               |
| ------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------ |
| **T1078 – Valid Accounts**            | Attacker uses stolen user or agent credentials. | Dual-subject auth prevents one stolen identity from granting access.           |
| **T1190 – Exploit Public-Facing App** | Compromise agent endpoints.                     | PEP verification of agent identity; cannot act without valid delegation token. |

---

# **2. Execution**

| Technique                                     | Description                                         | AGBAC Mitigation                                                                  |
| --------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------- |
| **T1059 – Command Execution**                 | Malicious prompt or input causes unsafe operations. | Authorization enforced outside the model; prompt cannot grant privileged actions. |
| **T1203 – Exploitation for Client Execution** | Agent manipulated to execute unauthorized calls.    | Dual-subject checks block policy violations.                                      |

---

# **3. Persistence**

| Technique                        | AGBAC Mitigation                                                                         |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| **T1098 – Account Manipulation** | Delegations have TTL; agents cannot create new privileges.                               |
| **T1053 – Scheduled Tasks**      | Agent autonomous tasks evaluated via same policies—cannot schedule unauthorized actions. |

---

# **4. Privilege Escalation**

| Technique                                         | AGBAC Mitigation                                                       |
| ------------------------------------------------- | ---------------------------------------------------------------------- |
| **T1068 – Exploitation for Privilege Escalation** | Agent cannot exceed permissions of human or agent identity.            |
| **T1078 – Valid Accounts Misuse**                 | Dual-subject requirement mitigates misuse of one compromised identity. |

---

# **5. Defense Evasion**

| Technique                                  | AGBAC Mitigation                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------- |
| **T1562 – Impair Defenses**                | Authorization enforced through external PDP; agents cannot bypass PEP. |
| **T1497 – Virtualization/Sandbox Evasion** | AGBAC enforces identity checks regardless of agent behavior.           |

---

# **6. Credential Access**

| Technique                         | AGBAC Mitigation                                                                 |
| --------------------------------- | -------------------------------------------------------------------------------- |
| **T1552 – Unsecured Credentials** | Token Exchange generates short-lived tokens; reduces blast radius.               |
| **T1555 – Token Theft**           | Token binding/mTLS recommended; dual-subject reduces usefulness of stolen token. |

---

# **7. Discovery**

| Technique                                | AGBAC Mitigation                                                       |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| **T1087 – Account Discovery**            | Even if agents discover accounts, policies prevent unauthorized use.   |
| **T1082 – System Information Discovery** | Agents may discover systems but cannot access without dual permission. |

---

# **8. Lateral Movement**

| Technique                   | AGBAC Mitigation                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------ |
| **T1021 – Remote Services** | Dual-subject authorization enforced across all services prevents lateral escalation. |

---

# **9. Collection**

| Technique                               | AGBAC Mitigation                                                                |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| **T1213 – Data from Info Repositories** | Both user and agent require access rights; prevents agent-driven data scraping. |

---

# **10. Command & Control**

| Technique                  | AGBAC Mitigation                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------- |
| **T1102 – Web Service C2** | Delegation tokens short-lived; identity binding prevents long-lived C2 operations. |

---

# **11. Exfiltration**

| Technique                                     | AGBAC Mitigation                                                    |
| --------------------------------------------- | ------------------------------------------------------------------- |
| **T1041 – C2 Exfiltration Over Web Protocol** | Agent cannot exfiltrate data without both identities having access. |

---

# **12. Impact**

| Technique                                | AGBAC Mitigation                                                              |
| ---------------------------------------- | ----------------------------------------------------------------------------- |
| **T1485 – Data Destruction**             | Both identities must have delete permission; limits destructive operations.   |
| **T1490 – Data Encryption (Ransomware)** | Dual-subject check prevents agent misuse even under coercion or manipulation. |
