# **EntraID Configuration for In-Session Agents (AGBAC-Min)**

**Goal:** Configure EntraID so that in-session agents can request tokens that include **both the agent (`sub`) and human (`act`) identities**, supporting dual-subject authorization.

<br>

## **1. Create an Application Registration for the Agent**

**Purpose:** This represents the agent (service principal) that will request tokens from EntraID.

**Steps:**

1. Go to **Azure Active Directory → App registrations → New registration**.
2. Name: `finance-agent-app` (or your agent name).
3. Supported account types: Single tenant (or multi-tenant if needed).
4. Redirect URI: leave blank (not needed for client credentials).
5. Click **Register**.

**JSON artifact for reference:**

```json
{
  "appId": "00000000-0000-0000-0000-000000000001",
  "displayName": "finance-agent-app",
  "signInAudience": "AzureADMyOrg",
  "identifierUris": ["api://finance-agent-app"]
}
```

<br>

## **2. Create a Client Secret for the Agent**

**Purpose:** Allows the agent to authenticate with EntraID when requesting a token.

**Steps:**

1. Go to **Certificates & secrets → New client secret**.
2. Description: `Agent client secret`.
3. Expiration: 1 year / 2 years (based on policy).
4. Copy the **Value** (this will be used in the **EntraID adapter**).

**JSON artifact reference:**

```json
{
  "clientId": "00000000-0000-0000-0000-000000000001",
  "clientSecret": "super-secret-value",
  "secretExpiresOn": "2027-01-01T00:00:00Z"
}
```

<br>

## **3. Define API / Resource Access for the Agent**

**Purpose:** Configure scopes that represent system access (used in AGBAC-Min).

**Steps:**

1. Go to **Expose an API → Add a scope**.
2. Scope name: `system.access`
3. Who can consent: Admin only
4. Admin consent display name: `System Access`
5. Description: `Access to finance system API`
6. State: **Enabled**
7. Click **Add scope**.

**JSON artifact example:**

```json
{
  "id": "00000000-0000-0000-0000-000000000010",
  "value": "system.access",
  "adminConsentDisplayName": "System Access",
  "adminConsentDescription": "Access to finance system API",
  "enabled": true
}
```

<br>

## **4. Configure Custom `act` Claim**

**Purpose:** Include the human user identity in the access token (`act`) for dual-subject enforcement.

**Steps:**

1. Go to **Token configuration → Add optional claim → Token type: Access**.
2. Name: `act`
3. Source: `User` attributes → choose `userPrincipalName`
4. Additional options:

   * Format: JSON
   * Always include in token: Enabled
5. Save.

**JSON artifact example:**

```json
{
  "name": "act",
  "source": "user",
  "sourceAttribute": "userPrincipalName",
  "additionalProperties": {},
  "format": "JSON",
  "alwaysIncludeInToken": true
}
```

**Result:** Each access token will include the human user’s identity under `act`:

```json
{
  "sub": "spn:finance-agent-app",
  "act": {
    "sub": "user:alice@corp.example"
  },
  "scp": ["system.access"]
}
```

<br>

## **5. Assign Human Users and Agent to the Application**

**Purpose:** Ensure both human users and the agent are pre-approved for dual-subject authorization.

**Steps:**

1. Go to **Enterprise applications → finance-agent-app → Users and groups → Add user/group**.
2. Assign:

   * Users: All human users allowed to trigger the agent.
   * Service principal (agent): Already included by app registration.
3. Verify both are assigned correctly.

**JSON artifact example:**

```json
{
  "appId": "00000000-0000-0000-0000-000000000001",
  "users": [
    {
      "userId": "11111111-1111-1111-1111-111111111111",
      "userPrincipalName": "alice@corp.example",
      "role": "user"
    }
  ],
  "servicePrincipal": {
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "finance-agent-app"
  }
}
```

<br>

## **6. Configure Token Lifetime & Validation**

**Purpose:** Align token TTL and enforcement for security.

**Steps:**

1. Go to **Token configuration → Access token lifetime**.
2. Recommended: 1 hour.
3. Optional: Enable refresh tokens if needed (for continuous LLM sessions).

**JSON artifact example:**

```json
{
  "accessTokenLifetime": 3600,
  "refreshTokenLifetime": 7200
}
```

<br>

## **7. Verify Token Output**

**Purpose:** Ensure dual-subject (`sub` + `act`) tokens are issued correctly.

**Steps:**

1. Use the **EntraID adapter** in Python.
2. Request a token for an **in-session agent** via client credentials using the hybrid sender.
3. Inspect the token claims:

```json
{
  "sub": "spn:finance-agent-app",
  "act": {
    "sub": "user:alice@corp.example"
  },
  "scp": ["system.access"]
}
```

* `sub` → agent identity
* `act` → human identity
* `scp` → system access scopes

<br>
