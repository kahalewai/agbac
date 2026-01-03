# Mapping of AGBAC to the AOSI Model

<br>

AGBAC is a **security and authorization model** designed for AI agents acting on behalf of humans. It is primarily concerned with **identity, delegation, authorization, policy enforcement, and auditing**.

<br>


The AOSI model ([link](https://github.com/kahalewai/aosi)) is a **technical stack for AI systems**, from infrastructure up to application delivery. Security is a **cross-cutting concern**, so AGBAC touches multiple layers indirectly, but some layers are more relevant than others.

<br>


### **AOSI Model Layer Analysis**

| AOSI Layer                   | Relation to AGBAC | Details                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------------   | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Infrastructure**   | Indirect          | AGBAC relies on the infrastructure to securely execute agents and store credentials/tokens. Infrastructure isolation, containerization, and runtime security help prevent agent impersonation or privilege escalation. However, AGBAC does not define infrastructure.                                                                                    |
| **Model**            | Minimal           | AGBAC does not directly govern model architecture, weights, or predictions. It treats the model as a black box: the AI agent is authorized based on identity and delegation, not model internals. Security here is indirect (ensuring that the model cannot be used outside the authorized scope).                                                       |
| **Data**             | Indirect          | While AGBAC does not handle data validation or preprocessing, it governs access to resources that may include data. Delegation constraints and authorization decisions can restrict access to sensitive datasets.                                                                                                                                        |
| **Orchestration**    | Strong            | This layer is **highly relevant**. Orchestration handles execution and coordination of agents. AGBAC’s dual-subject authorization, delegation semantics, and execution constraints map directly here. The PEP/PDP enforcement and delegation context enforcement are applied at this layer to ensure agents act safely.                                  |
| **Communication**    | Moderate          | Communication layer provides the transport and protocols for agents to request actions. AGBAC relies on this layer for token transport (OAuth/JWT) and auditing events. Enforcement of delegation and binding tokens to transport is critical to prevent replay or tampering.                                                                            |
| **Interface**        | Strong            | Interface layer is relevant because it mediates **human-agent interaction**. AGBAC requires that human intent triggers agent actions. Authentication of the human principal, delegation approval, and logging all occur at the interface boundary. Dual-subject authorization ensures that users cannot bypass the system by invoking agents indirectly. |
| **Application**      | Moderate          | Applications consume agent services. AGBAC enforces authorization and auditing here to ensure that only authorized actions affect end-user services. The enforcement of least privilege, delegation context, and audit logging supports secure application-level behavior.                                                                               |

<br>

### Cross-Cutting Security Mapping

AGBAC operates as a **security overlay** across the AOSI stack:

* **Identity & Delegation** → Layers 4, 6
* **Authorization Enforcement (PEP/PDP)** → Layer 4, 6
* **Audit Logging & Compliance** → Layers 5, 6, 7
* **Token Transport & Replay Protection** → Layer 5
* **Least Privilege Enforcement** → Layers 4, 6, 7

This shows that while AGBAC does not require changes to model training or data pipelines, it **secures the operational and human-facing layers** where AI agents act autonomously or semi-autonomously.

<br>

### Conclusion

**AGBAC is primarily focused on Layers 4 and 6 of the AOSI stack**:

* **Layer 4 - Orchestration:** Enforces safe, delegated agent actions.
* **Layer 6 - Interface:** Ensures human intent, approval, and accountability.

It also interacts moderately with:

* **Layer 5 - Communication:** Secure transport, token validation, and auditing.
* **Layer 7 - Application:** Ensures safe effects on end-user systems and services.

It has **supporting but indirect relationships** with:

* **Layer 1 - Infrastructure:** Runtime isolation, execution security.
* **Layer 2 - Model:** Agents are black boxes; model-level security is out of scope.
* **Layer 3 - Data:** Access to sensitive data is controlled, but preprocessing/validation is outside AGBAC.

