<div align="center">

# AGBAC-Min TypeScript Application/Agent Configuration Guide

Implementing dual-subject authorization for humans and agents at system / application layer

</div>

<br>

This workflow assumes a developer has a TypeScript environment set up (`Node.js` + `tsc` or `ts-node`) and wants to implement dual-subject authorization with hybrid sender support.

<br>

## **Step 0: Project Setup**

1. Create a project directory, e.g., `agbac-ts`.
2. Initialize Node.js and TypeScript:

```bash
npm init -y
npm install typescript ts-node @types/node axios jsonwebtoken
npx tsc --init
```

3. Create a folder structure:

```
agbac-ts/
├─ adapters/
│  ├─ baseAdapter.ts
│  ├─ oktaAdapter.ts
│  ├─ entraIDAdapter.ts
│  ├─ auth0Adapter.ts
│  └─ keycloakAdapter.ts
├─ sender/
│  └─ hybridSender.ts
├─ tokenRequests/
│  ├─ inSessionTokenRequest.ts
│  └─ outOfSessionTokenRequest.ts
├─ apiCalls/
│  ├─ inSessionApiCall.ts
│  └─ outOfSessionApiCall.ts
├─ tests/
│  ├─ testInSession.ts
│  └─ testOutOfSession.ts
└─ helpers/
   └─ checkAgentAct.ts
```

<br>

## **Step 1: Implement Vendor-Agnostic Base Adapter**

* **File:** `adapters/baseAdapter.ts`
* **Purpose:** Abstract interface for all IAM vendors, ensures consistent methods like `requestToken`, `validateToken`, etc.
* **Workflow:** Any vendor adapter extends this base.

<br>

## **Step 2: Implement Vendor-Specific Adapters**

* **Files:**

  * `adapters/oktaAdapter.ts`
  * `adapters/entraIDAdapter.ts` (in-session only)
  * `adapters/auth0Adapter.ts`
  * `adapters/keycloakAdapter.ts`

* **Purpose:** Each adapter implements the BaseAdapter interface to communicate with its IAM vendor.

* **Logic:** Handles OAuth endpoints, token parsing, logging, and error handling.

* **Notes:**

  * Ensure dual-subject tokens include both `sub` (agent) and `act` (human).
  * Use the same dual-subject token format across all vendors.

<br>

## **Step 3: Implement Hybrid Sender**

* **File:** `sender/hybridSender.ts`

* **Purpose:** Extracts human `act` data from the application session and makes it available for:

  1. In-session agents (shared in code)
  2. Out-of-session agents (TLS + JWT)

* **Logic:**

  * Retrieves human `act` data securely.
  * Creates JWT signed by application if out-of-session agent is called.
  * Ensures correct timing/directionality: in-session is direct; out-of-session is secure transport.

<br>

## **Step 4: Implement Token Requests**

### **In-Session Token Request**

* **File:** `tokenRequests/inSessionTokenRequest.ts`
* **Purpose:** Build and send token request including both `sub` and `act` claims for in-session agents.
* **Workflow:**

  1. Import `HybridSender`.
  2. Build payload from in-session `act` data.
  3. Send request via vendor adapter.
  4. Return token.

### **Out-of-Session Token Request**

* **File:** `tokenRequests/outOfSessionTokenRequest.ts`
* **Purpose:** Token request for out-of-session agents, including `act` sent via TLS + JWT.
* **Workflow:**

  1. Import `HybridSender`.
  2. Generate signed JWT with human `act`.
  3. Include JWT in token request to IAM.
  4. Return token.

<br>

## **Step 5: Implement API / Resource Calls**

### **In-Session API Call**

* **File:** `apiCalls/inSessionApiCall.ts`
* **Purpose:** Makes API calls using the token obtained from `inSessionTokenRequest`.
* **Workflow:**

  1. Retrieve token.
  2. Add token to request headers.
  3. Make call to resource.
  4. Handle errors, log responses.

### **Out-of-Session API Call**

* **File:** `apiCalls/outOfSessionApiCall.ts`
* **Purpose:** Similar to in-session but uses token from `outOfSessionTokenRequest`.
* **Logic:** Same logging/error handling standards.

<br>

## **Step 6: Implement Unit Tests**

* **Files:**

  * `tests/testInSession.ts` → tests `inSessionTokenRequest` + `inSessionApiCall`.
  * `tests/testOutOfSession.ts` → tests `outOfSessionTokenRequest` + `outOfSessionApiCall`.

* **Purpose:** Verify token request payloads include both `sub` and `act`, and API calls succeed.

* **Workflow:**

  1. Mock the vendor adapter responses.
  2. Assert payload correctness (`sub` and `act`).
  3. Assert token parsing succeeds.
  4. Assert API calls return expected outputs.

<br>

## **Step 7: Implement Helper Script**

* **File:** `helpers/checkAgentAct.ts`
* **Purpose:** Verify whether an agent (in-session or out-of-session) is aware of human identity.
* **Workflow:**

  1. Calls `InSessionTokenRequest` and inspects payload.
  2. Calls `OutOfSessionTokenRequest`, decodes JWT, inspects payload.
  3. Logs results with clear success/warning messages.

<br>

## **Step 8: Using the Code**

1. **In-Session Flow:**

   * Application calls `HybridSender` → provides `act` to `InSessionTokenRequest` → call API via `inSessionApiCall`.

2. **Out-of-Session Flow:**

   * Application calls `HybridSender` → generates TLS + JWT → `OutOfSessionTokenRequest` → call API via `outOfSessionApiCall`.

3. **Verification:**

   * Run `checkAgentAct.ts` to ensure dual-subject awareness.

<br>

## **Step 9: Logging & Error Handling**

* All files follow **production-grade logging**:

  * Errors → `console.error()`
  * Warnings → `console.warn()`
  * Info → `console.log()`

* All network calls handle retries, exceptions, and invalid token formats.

<br>

##  **Summary**

| Component                    | File                                      | Purpose                                                        |
| ---------------------------- | ----------------------------------------- | -------------------------------------------------------------- |
| Adapter Base                 | `baseAdapter.ts`                          | Abstract interface for IAM vendor adapters                     |
| Okta Adapter                 | `oktaAdapter.ts`                          | Okta-specific token handling                                   |
| EntraID Adapter              | `entraIDAdapter.ts`                       | EntraID (in-session only)                                      |
| Auth0 Adapter                | `auth0Adapter.ts`                         | Auth0-specific token handling                                  |
| Keycloak Adapter             | `keycloakAdapter.ts`                      | Keycloak-specific token handling                               |
| Hybrid Sender                | `hybridSender.ts`                         | Provides human `act` to in-session and out-of-session agents   |
| In-Session Token Request     | `inSessionTokenRequest.ts`                | Builds token request for in-session agents                     |
| Out-of-Session Token Request | `outOfSessionTokenRequest.ts`             | Builds token request for out-of-session agents using TLS + JWT |
| In-Session API Call          | `inSessionApiCall.ts`                     | Makes API/resource calls for in-session agents                 |
| Out-of-Session API Call      | `outOfSessionApiCall.ts`                  | Makes API/resource calls for out-of-session agents             |
| Unit Tests                   | `testInSession.ts`, `testOutOfSession.ts` | Verify token requests and API calls work as expected           |
| Helper Script                | `checkAgentAct.ts`                        | Verify agent awareness of human `act` data                     |

<br>
