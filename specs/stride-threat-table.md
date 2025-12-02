# **STRIDE Threat Table for AGBAC**

AGBAC incorporates a two-principal identity model (Human + Agent), which introduces specific threats addressed in this STRIDE analysis.

---

# **S — Spoofing**

| Threat                  | Description                 | AGBAC Control                                                |
| ----------------------- | --------------------------- | ------------------------------------------------------------ |
| Agent identity spoofing | Attacker impersonates agent | Strong agent authentication; `sub` verification; mTLS/SPIFFE |
| User identity spoofing  | Attacker impersonates human | MFA via IdP; separate human/agent identity validation        |
| Delegation spoofing     | Fake delegation to agent    | Delegation tokens signed & time-bound                        |

---

# **T — Tampering**

| Threat              | Description                         | AGBAC Control                           |
| ------------------- | ----------------------------------- | --------------------------------------- |
| Token tampering     | Modify `act` or `delegation` fields | Signed JWTs; issuer verification        |
| Policy tampering    | Modify authorization rules          | External PDP, policy integrity controls |
| Audit log tampering | Alter records of agent actions      | Immutable / append-only audit logs      |

---

# **R — Repudiation**

| Threat                        | Description                        | AGBAC Control                   |
| ----------------------------- | ---------------------------------- | ------------------------------- |
| User denies instructing agent | “I didn’t tell the AI to do that.” | Delegation metadata + timestamp |
| Agent denies making a call    | “I didn’t perform that action.”    | Dual-identity audit log entries |
| Lack of attribution           | No trace of who triggered what     | Required AGBAC audit schemas    |

---

# **I — Information Disclosure**

| Threat                                | Description                            | AGBAC Control             |
| ------------------------------------- | -------------------------------------- | ------------------------- |
| Unauthorized data retrieval           | Agent accesses data without permission | Dual-subject checks       |
| Prompt-embedded sensitive info leaked | Agents log sensitive prompt text       | Prompt-safe audit logging |

---

# **D — Denial of Service (DoS)**

| Threat                                    | Description                       | AGBAC Control                                      |
| ----------------------------------------- | --------------------------------- | -------------------------------------------------- |
| Agent floods system with authorized calls | Overload from misconfigured agent | Rate limiting; delegation TTL; behavioral controls |
| Malicious user induces overuse            | User abuses agent automation      | Delegation limits + policy constraints             |

---

# **E — Elevation of Privilege**

| Threat                               | Description                                  | AGBAC Control                              |
| ------------------------------------ | -------------------------------------------- | ------------------------------------------ |
| Human escalates privileges via agent | "Do this admin task for me"                  | Agent cannot exceed user permissions       |
| Agent escalates privileges via user  | Inferred intent gives agent too much power   | Explicit delegation required               |
| Model exploit (prompt injection)     | AI tricked into performing privileged action | Authorization enforced outside agent logic |

