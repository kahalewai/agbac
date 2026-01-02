# **Java Implementation Workflow for AGBAC-Min with Hybrid Sender**

### **Step 0: Project Setup**

1. Create a new Java project using your preferred build tool (Maven or Gradle).
2. Ensure the following dependencies are included:

   * `JUnit 5` for unit testing.
   * `SLF4J` or `java.util.logging` for logging.
   * Any HTTP client library (like `HttpClient` or `OkHttp`) if performing real API/resource calls.
3. Define the package structure:

```
com.agbac.adapters
com.agbac.sender
com.agbac.token
com.agbac.api
com.agbac.tests
com.agbac.helpers
```

<br>

### **Step 1: Implement the Adapter Base and Vendor Adapters**

1. **BaseAdapter.java** – Vendor-agnostic adapter for token requests.
2. **OktaAdapter.java**, **EntraIDAdapter.java**, **Auth0Adapter.java**, **KeycloakAdapter.java** – Extend `BaseAdapter` for specific vendor logic.
3. Logging and error handling should be implemented in each adapter’s `requestToken()` method.

**Purpose:** Standardizes token request logic across vendors while supporting `sub` (agent) and `act` (human) claims.

<br>

### **Step 2: Implement Hybrid Sender**

1. **HybridSender.java** – Centralized sender that:

   * Extracts the human `act` data from the application session.
   * Shares `act` data internally for in-session agents.
   * Creates a TLS + JWT package for out-of-session agents.
2. **Modes:**

   * **In-session only:** Shares `act` within code directly.
   * **Out-of-session only:** Encapsulates `act` in signed JWT sent to agent.
   * **Hybrid:** Supports both in-session and out-of-session simultaneously.
3. Ensure proper logging when `act` is extracted, sent, or signed.

<br>

### **Step 3: Implement Token Request Logic**

1. **InSessionTokenRequest.java**

   * Uses `HybridSender` to receive `act` data from the session.
   * Sends token request to IAM vendor including `sub` (agent) and `act` (human) claims.
2. **OutOfSessionTokenRequest.java**

   * Uses `HybridSender` to receive `act` data via TLS + JWT.
   * Sends token request including `sub` and `act` claims.
   * JWT ensures secure transmission of human identity out-of-session.
3. Logging should indicate both agent and human data included in request.

<br>

### **Step 4: Implement API or Resource Call Classes**

1. **InSessionApiCall.java**

   * Accepts session data and in-session token.
   * Makes API/resource calls using the token.
   * Logs success or failure.
2. **OutOfSessionApiCall.java**

   * Accepts session data and out-of-session token.
   * Makes API/resource calls using token from out-of-session agent.
   * Logs success or failure.

<br>

### **Step 5: Unit Tests**

1. Place all unit tests in `com.agbac.tests` package.
2. Test classes:

   * `InSessionTokenRequestTest.java` – verifies in-session token includes `sub` and `act`.
   * `InSessionApiCallTest.java` – verifies API call succeeds using in-session token.
   * `OutOfSessionTokenRequestTest.java` – verifies out-of-session token includes `sub` and `act` via JWT.
   * `OutOfSessionApiCallTest.java` – verifies API call succeeds with out-of-session token.
3. Ensure tests **fail if sub or act is missing**.
4. Logging should show token payloads (without exposing secrets).

<br>

### **Step 6: Helper Script**

1. **CheckAgentAwareness.java**

   * Verifies if a specific agent is aware of the human `act` data.
   * Runs both in-session and out-of-session checks.
   * Prints token payload for visual verification.
2. Useful for IAM engineers and developers to confirm dual-subject awareness.

<br>

### **Step 7: Wiring the Application**

1. **Initialize the Hybrid Sender** in your main application:

   ```java
   HybridSender sender = new HybridSender();
   BaseAdapter adapter = new OktaAdapter(); // Or any vendor
   ```
2. **For In-Session Agent:**

   ```java
   InSessionTokenRequest inSessionTokenRequest = new InSessionTokenRequest(sender, adapter);
   InSessionApiCall apiCall = new InSessionApiCall(inSessionTokenRequest);
   apiCall.callResource(sessionData, agentId, resourceUrl);
   ```
3. **For Out-of-Session Agent:**

   ```java
   OutOfSessionTokenRequest outSessionTokenRequest = new OutOfSessionTokenRequest(sender, adapter);
   OutOfSessionApiCall apiCall = new OutOfSessionApiCall(outSessionTokenRequest);
   apiCall.callResource(sessionData, agentId, resourceUrl);
   ```
4. **Unit Tests:** Run `com.agbac.tests.*` to verify functionality.
5. **Helper Script:** Run `CheckAgentAwareness` to confirm agent awareness of human identity.

<br>

### **Step 8: Logging and Error Handling**

* All classes log **success and failure events**.
* All token requests validate that `sub` and `act` are present.
* Exceptions are caught and logged with **clear messages** to aid debugging.

<br>

### **Summary**

By following this workflow:

* **In-session agents** receive `act` directly from the application session.
* **Out-of-session agents** receive `act` securely via TLS + JWT.
* Both agents request tokens that include **dual-subject authorization (`sub` + `act`)**.
* Unit tests and helper scripts validate the flow.
* Adapter base supports **Okta, EntraID, Auth0, Keycloak**, aligning with all instructions we created previously.
* Logging, comments, and error handling are consistent with Python and TypeScript implementations.

<br>
