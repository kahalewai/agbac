Agent Home Readme File

Agent Logic

### **Phase 1 – In-Session Agents**

1. **Human logs in:**

   * Human authenticates to the application (OIDC/SAML).
   * The application now has the human identity (user ID, email, roles) in the session.

2. **Application extracts `act`:**

   * A **sender module in the application** reads the human’s identity from the session.
   * Example data:

     ```json
     {
       "user_id": "alice-123",
       "email": "alice@corp.example",
       "roles": ["finance_viewer"]
     }
     ```

3. **Pass `act` to the in-session agent:**

   * The **same application** has a component that invokes the in-session agent.
   * The `act` data is **passed directly within the application process** to the agent’s token request code.

4. **Agent requests OAuth token:**

   * The agent requests a token using **client_credentials**, but now includes the `act` data in the request (e.g., via custom claims or request parameters).
   * This ensures the token carries both:

     * `sub` → agent identity
     * `act` → human identity

5. **API / Resource call:**

   * The agent calls the resource with the token containing both `sub` and `act`.
   * Enforcement is still dual-subject:

     * Okta confirms agent is allowed.
     * Application ensures human is allowed (via session).

**Key:** Everything happens **within the same application process**, so there is **no need for TLS/JWT**.

---

### **Phase 2 – Out-of-Session Agents**

1. **Human logs in:**

   * Same as Phase 1, human is authenticated to the application.

2. **Application extracts `act`:**

   * Same sender module extracts the human identity from session.

3. **Securely send `act` to the out-of-session agent:**

   * Since the agent is **outside the session**, the application **wraps the `act` in a signed JWT** and must use TLS for transport:

     * JWT is signed by the application’s key.
     * TLS ensures transport confidentiality.
   * The agent receives the JWT **when invoked** and extracts the human `act` from it.

4. **Agent requests OAuth token:**

   * The agent uses its client credentials, but now **includes `act` data extracted from JWT** when requesting a token.
   * Token contains:

     * `sub` → agent identity
     * `act` → human identity

5. **API / Resource call:**

   * The agent calls the resource with the token including both `sub` and `act`.
   * Enforcement: same as in-session, dual-subject.

**Key:** No receiver code is needed on the agent beyond JWT validation. All security happens **via JWT and TLS**.

---

### **Hybrid / Shared Sender**

* The sender module can handle both scenarios:

  1. **In-session agent:** pass `act` directly in code.
  2. **Out-of-session agent:** sign `act` as JWT and send over TLS.

* This ensures a single implementation can handle both in-session and out-of-session agents without changing the agent logic.
