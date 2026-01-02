<div align="center">

# AGBAC-Min Okta IAM Configuration Guide

Implementing dual-subject authorization for humans and agents at system / application layer

</div>


<br>

# **Step 0: Prerequisites**

Before starting, ensure:

1. You have **Okta Org Admin access**.
2. All agents and human users are created in Okta and can be assigned to applications.
3. You have the **Okta API token** ready for programmatic configuration (optional but recommended for automation).

We will configure:

* OAuth 2.0 Authorization Server
* Scopes
* Claims (`sub` and `act`)
* Client Application assignments (for agent and human)
* Policies to enforce pre-approval

<br>

# **Step 1: Create a Custom Authorization Server**

**Goal:** This server will issue tokens for agents, including `sub` (agent) and `act` (human) claims.

**Steps:**

1. Navigate to **Security → API → Authorization Servers**.
2. Click **Add Authorization Server**.
3. Enter:

   * **Name:** `AGBAC-Min-AS`
   * **Audience:** `https://api.example.com`
   * **Description:** `Authorization Server for dual-subject agent + human authorization`
4. Click **Save**.

**Example JSON artifact:**

```json
{
  "id": "AGBAC-Min-AS",
  "name": "AGBAC-Min-AS",
  "audiences": ["https://api.example.com"],
  "issuer": "https://dev-123456.okta.com/oauth2/AGBAC-Min-AS",
  "status": "ACTIVE",
  "description": "Authorization Server for dual-subject agent + human authorization"
}
```

<br>

# **Step 2: Define Scopes**

**Goal:** Define a scope for system access (used in both in-session and out-of-session flows).

**Steps:**

1. Inside the authorization server, go to **Scopes → Add Scope**.
2. Create a scope:

   * **Name:** `system.access`
   * **Display Name:** `System Access`
   * **Description:** `Allows agents to access protected system resources`
   * **Consent:** None (used internally for agents)
3. Save.

**Example JSON artifact:**

```json
{
  "id": "system.access",
  "name": "system.access",
  "description": "Allows agents to access protected system resources",
  "consent": "NONE"
}
```

<br>

# **Step 3: Add Custom Claims**

We need two claims in the JWT issued by Okta:

1. **sub** → The agent identity (already included by default for client_credentials).
2. **act** → Human identity acting via agent.

**Steps:**

1. Go to **Authorization Server → Claims → Add Claim**.
2. **For `act` claim:**

   * **Name:** `act`
   * **Include in token type:** `Access Token`
   * **Value type:** `Expression`
   * **Expression:** `app.profile.humanActId` *(or a user profile attribute representing the human identity)*
   * **Always include in token:** Yes
   * **Scopes:** `system.access`
3. Save.

**Example JSON artifact:**

```json
{
  "id": "claim_act",
  "name": "act",
  "status": "ACTIVE",
  "claimType": "RESOURCE",
  "valueType": "EXPRESSION",
  "value": "app.profile.humanActId",
  "alwaysIncludeInToken": true,
  "conditions": {
    "scopes": ["system.access"]
  }
}
```

> ⚠️ Note: For **out-of-session agents**, the `act` value must be provided in the token request. The code provided accomplishes this for you.

<br>

# **Step 4: Create OAuth 2.0 Client Applications**

**Goal:** Register agent clients in Okta with `client_credentials` grant.

**Steps:**

1. Navigate to **Applications → Applications → Create App Integration**.
2. Choose:

   * **OAuth 2.0 → Service (machine-to-machine)**.
3. Configure:

   * **App Name:** `Finance Agent`
   * **Grant Type:** `Client Credentials`
   * **Scopes:** `system.access`
   * **Sign-in redirect URIs:** Not required for client_credentials
4. Save.

**Example JSON artifact:**

```json
{
  "id": "finance-agent-client",
  "client_id": "abc123",
  "client_secret": "secret-value",
  "name": "Finance Agent",
  "application_type": "service",
  "grant_types": ["client_credentials"],
  "scopes": ["system.access"]
}
```

Repeat for each agent that will request tokens.

<br>

# **Step 5: Assign Human Users and Agents to Application**

**Goal:** Ensure that **both the human and agent** are explicitly assigned to the same application for dual-subject enforcement.

**Steps:**

1. Go to the application (e.g., `Finance Agent`).
2. Click **Assignments → Assign People**.
3. Select human users and assign them.
4. Click **Assignments → Assign Groups / Service Principals**.
5. Select agent service clients and assign them.

**Example JSON artifact for an assignment:**

```json
{
  "applicationId": "finance-agent-client",
  "assignedUserId": "alice@example.com",
  "assignedClientId": "abc123"
}
```

> ⚠️ Both **sub** (agent client) and **act** (human) must be pre-approved in Okta to allow token issuance.

<br>

# **Step 6: Configure Authorization Server Policies**

**Goal:** Restrict token issuance only to clients where both human (`act`) and agent (`sub`) are pre-approved.

**Steps:**

1. Go to **Authorization Server → Access Policies → Add Policy**.
2. Name: `AGBAC-Min-Policy`.
3. Set **Conditions**:

   * Grant Type: `Client Credentials`
   * Application assigned: Required
   * User (for act claim): Must be assigned to the app
4. Add Rule:

   * **Rule Name:** `Allow Pre-Approved Agent+Human`
   * **Grant Type:** `Client Credentials`
   * **Scopes:** `system.access`
   * **Conditions:** Only allow if both agent and human are assigned
5. Save.

**Example JSON artifact:**

```json
{
  "id": "policy_agbac_min",
  "name": "AGBAC-Min-Policy",
  "status": "ACTIVE",
  "conditions": {
    "grant_types": ["client_credentials"],
    "applications": ["finance-agent-client"],
    "users": ["alice@example.com"]
  },
  "rules": [
    {
      "name": "Allow Pre-Approved Agent+Human",
      "grant_types": ["client_credentials"],
      "scopes": ["system.access"],
      "actions": {
        "token": {
          "access_token_lifetime_minutes": 60,
          "refresh_token_lifetime_minutes": 0
        }
      }
    }
  ]
}
```

<br>

# **Step 7: Testing and Verification**

1. **In-Session Flow**

   * Application extracts human identity from the session.
   * Passes `act` to in-session agent.
   * Agent requests token using `client_credentials` and includes `act`.
   * Verify token contains:

     ```json
     {
       "sub": "finance-agent-client",
       "act": "alice@example.com",
       "scp": ["system.access"]
     }
     ```

2. **Out-of-Session Flow**

   * Application extracts human identity from the session.
   * Sends `act` via TLS + signed JWT to out-of-session agent.
   * Agent requests token including both `sub` and `act`.
   * Verify token contains the same claims as above.

3. **Check Logs / Auditing**

   * Okta logs should show **agent and human identities** in each request.


