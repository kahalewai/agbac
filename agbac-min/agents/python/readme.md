## **Step-by-Step Implementation Workflow: Python**

---

### **Step 0: Prepare Environment**

1. Install Python 3.10+.
2. Create a virtual environment:

   ```bash
   python -m venv agbac_env
   source agbac_env/bin/activate  # Linux/macOS
   agbac_env\Scripts\activate     # Windows
   ```
3. Install required packages:

   ```bash
   pip install requests pyjwt cryptography pytest
   ```
4. Create a project folder with subfolders for:

   ```
   /adapters
   /sender
   /phase1
   /phase2
   /tests
   /helper
   ```

---

### **Step 1: Implement Adapters**

#### **Files**

* `adapters/base_adapter.py`
* `adapters/okta_adapter.py`
* `adapters/entra_adapter.py`
* `adapters/auth0_adapter.py`
* `adapters/keycloak_adapter.py`

#### **Purpose**

* Standardized interface (`BaseAdapter`) for IAM providers.
* Specific adapters implement token requests, credential storage, and endpoint URLs for each IAM vendor.

#### **Instructions**

1. Implement `BaseAdapter` with methods for `request_token()`.
2. Implement vendor-specific adapters inheriting from `BaseAdapter`.
3. Ensure logging and error handling are implemented in all adapters.
4. Use these adapters in token request files for both in-session and out-of-session.

---

### **Step 2: Implement Hybrid Sender**

#### **File**

* `sender/hybrid_sender.py`

#### **Purpose**

* Extracts human `act` data from the authenticated session.
* Provides it to:

  * **In-session agents:** directly shared in code.
  * **Out-of-session agents:** securely transmitted using TLS + JWT.
* Handles timing and directionality for sending `act` data.

#### **Instructions**

1. Implement extraction of `act` from session object.
2. Implement method to generate JWT for out-of-session agent.
3. Provide helper methods to share `act` securely.

---

### **Step 3: Implement Phase 1 – In-Session**

#### **Files**

* `phase1/token_request_in_session.py`
* `phase1/api_call_in_session.py`

#### **Purpose**

* Token request includes **both agent (`sub`) and human (`act`)** claims.
* API/resource call uses token to perform operations as dual-subject.

#### **Instructions**

1. Import hybrid sender and in-session adapter.
2. Call `request_token()` with both `sub` and `act`.
3. Use token in API/resource calls.
4. Include error handling and logging.

---

### **Step 4: Implement Phase 2 – Out-of-Session**

#### **Files**

* `phase2/token_request_out_of_session.py`
* `phase2/api_call_out_of_session.py`

#### **Purpose**

* Token request includes **both agent (`sub`) and human (`act`)** claims.
* `act` data is received via hybrid sender JWT (TLS + JWT).
* API/resource call uses token to perform operations as dual-subject.

#### **Instructions**

1. Import hybrid sender and out-of-session adapter.
2. Receive `act` securely via JWT.
3. Call `request_token()` including both `sub` and `act`.
4. Use token in API/resource calls.
5. Include logging and error handling.

---

### **Step 5: Unit Tests**

#### **Files**

* `tests/test_in_session_token.py`
* `tests/test_in_session_api.py`
* `tests/test_out_of_session_token.py`
* `tests/test_out_of_session_api.py`

#### **Purpose**

* Validate token requests include both `sub` and `act`.
* Validate API/resource calls succeed using generated token.
* Validate adapters handle errors and logging correctly.

#### **Instructions**

1. Use `pytest` to run tests:

   ```bash
   pytest tests/
   ```
2. Verify that tokens include `act`.
3. Verify API calls succeed and logs are generated correctly.

---

### **Step 6: Helper Script – Verify Agent Awareness**

#### **File**

* `helper/helper_check_act.py`

#### **Purpose**

* Test if an agent (in-session or out-of-session) token includes human `act` data.
* Can be run manually by IAM engineers or developers.

#### **Instructions**

1. Configure the adapter for your vendor (Okta, Auth0, Keycloak, EntraID).
2. For out-of-session, provide hybrid sender private key path.
3. Run script:

   ```bash
   python tests/helper_check_act.py in_session
   python tests/helper_check_act.py out_of_session
   ```
4. Verify success messages indicate `act` data present.

---

### **Step 7: Full Workflow Example**

1. **Developer sets up IAM adapter** (Okta, Auth0, Keycloak, EntraID).
2. **Hybrid sender extracts human `act`** from session.
3. **In-session agent**:

   * Requests token including `sub` + `act` (phase1).
   * Makes API/resource call using token.
4. **Out-of-session agent**:

   * Receives `act` via JWT from hybrid sender (phase2).
   * Requests token including `sub` + `act`.
   * Makes API/resource call using token.
5. **Run unit tests** to validate.
6. **Run helper script** to confirm agent awareness of human `act`.

---

### **Step 8: Logging and Error Handling**

* Every file logs:

  * Token requests and responses (excluding secrets)
  * API/resource calls
  * Errors and exceptions
* Ensure logging is standardized across adapters, token requests, and API calls.

---
