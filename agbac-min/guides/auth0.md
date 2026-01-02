# Auth0 Configuration for AGBAC-Min (Dual-Subject Authorization)

## Target Outcome (What This Configuration Guarantees)

After completing these steps:

✅ Every **agent token** will include:

* `sub` → agent identity
* `act` → human identity (from hybrid sender)

✅ Works for:

* **Phase 1 – In-Session agents**
* **Phase 2 – Out-of-Session agents (TLS + JWT)**

✅ Auth0 enforces:

* Agent pre-approval (RBAC)
* Human pre-approval (RBAC)
* Token issuance only for approved agent + human pairs

<br>

# Architecture Alignment

Auth0 plays the same role as Okta did:

| Component                   | Responsibility          |
| --------------------------- | ----------------------- |
| Auth0 Authorization Server  | Issues OAuth tokens     |
| Auth0 Application (M2M)     | Represents agents       |
| Auth0 Application (SPA/Web) | Represents humans       |
| Auth0 Actions               | Inject `act` claim      |
| Your Code                   | Supplies `act` securely |

**Auth0 does NOT discover the human.**
Your **hybrid sender** provides it explicitly — this is correct and required.

<br>

# Step 0 – Prerequisites

You must have:

* Auth0 Tenant Admin access
* An API identifier (audience)
* Your hybrid sender already implemented
* Auth0 adapter using **client_credentials**

<br>

# Step 1 – Create the API (Authorization Server)

This represents the protected system.

### UI Steps

1. **Dashboard → Applications → APIs**
2. Click **Create API**
3. Configure:

   * **Name:** `AGBAC-Min API`
   * **Identifier:** `https://api.example.com/agbac-min`
   * **Signing Algorithm:** RS256
4. Save

<br>

### Resulting API JSON (Conceptual)

```json
{
  "name": "AGBAC-Min API",
  "identifier": "https://api.example.com/agbac-min",
  "signing_alg": "RS256",
  "token_lifetime": 3600
}
```

<br>

# Step 2 – Define Scopes

### UI Steps

1. Open **AGBAC-Min API**
2. Go to **Permissions**
3. Add:

   * **Scope:** `system.access`
   * **Description:** `Agent system access`

<br>

### Scope Artifact

```json
{
  "value": "system.access",
  "description": "Agent system access"
}
```

<br>

# Step 3 – Create Agent Applications (Machine-to-Machine)

Each agent gets **its own M2M application**.

### UI Steps

1. **Applications → Create Application**
2. Choose **Machine to Machine**
3. Name: `Finance Agent`
4. Select **AGBAC-Min API**
5. Grant scope: `system.access`
6. Save

<br>

### Agent Application JSON (Conceptual)

```json
{
  "name": "Finance Agent",
  "app_type": "non_interactive",
  "grant_types": ["client_credentials"],
  "allowed_audiences": ["https://api.example.com/agbac-min"]
}
```

<br>

# Step 4 – Enable RBAC for Agents

### UI Steps

1. Open **AGBAC-Min API**
2. Go to **RBAC Settings**
3. Enable:

   * ✅ Enable RBAC
   * ✅ Add Permissions in the Access Token

<br>

### RBAC Result

Auth0 will include permissions in tokens **only if assigned**.

<br>

# Step 5 – Define Roles (Human + Agent Approval)

We will enforce **dual pre-approval**.

### Create Human Role

1. **User Management → Roles**
2. Create role:

   * Name: `FinanceUser`
3. Assign permission:

   * `system.access`

### Create Agent Role

1. Create role:

   * Name: `FinanceAgent`
2. Assign permission:

   * `system.access`

<br>

### Role JSON (Conceptual)

```json
{
  "name": "FinanceUser",
  "permissions": ["system.access"]
}
```

```json
{
  "name": "FinanceAgent",
  "permissions": ["system.access"]
}
```

<br>

# Step 6 – Assign Roles

### Human Assignment

* Assign `FinanceUser` role to human users

### Agent Assignment

* Assign `FinanceAgent` role to agent applications

**This is the RBAC gate**
If either is missing → token issuance or API access fails.

<br>

# Step 7 – Inject `act` Claim Using Auth0 Actions

Auth0 **does not automatically include custom request fields** in tokens.

We must explicitly inject `act`.

<br>

## 7.1 Create an Auth0 Action

### UI Steps

1. **Actions → Flows → Login**
2. Click **Add Action**
3. Create **Custom Action**
4. Name: `Inject act claim`

<br>

## 7.2 Action Code (PRODUCTION-SAFE)

```js
/**
 * Auth0 Action: Inject human act claim
 *
 * This action injects the `act` claim into access tokens.
 * It supports both in-session and out-of-session agents.
 */

exports.onExecutePostLogin = async (event, api) => {
  // act may be passed via:
  // 1. custom claim in request
  // 2. client assertion JWT
  // 3. hybrid sender propagated context

  const act =
    event.request.body?.act ||
    event.client?.metadata?.act ||
    event.transaction?.metadata?.act;

  if (!act) {
    console.log("No act claim provided — token will not include act");
    return;
  }

  // Enforce RBAC: ensure user is authorized
  if (!event.authorization || !event.authorization.roles.includes("FinanceUser")) {
    throw new Error("Human not authorized for system");
  }

  api.accessToken.setCustomClaim("act", act);
};
```

<br>

### Resulting Token Example

```json
{
  "sub": "finance-agent@clients",
  "act": "alice@corp.example",
  "permissions": ["system.access"],
  "aud": "https://api.example.com/agbac-min"
}
```

<br>

# Step 8 – In-Session Flow (Phase 1)

### How It Works

1. Human authenticates via Auth0 (OIDC)
2. Application extracts human identity
3. Hybrid sender passes `act` **in memory**
4. In-session agent:

   * Requests token
   * Includes `act`
5. Auth0 Action injects `act`

✔ Token contains `sub + act`

<br>

# Step 9 – Out-of-Session Flow (Phase 2)

### How It Works

1. Human authenticates
2. Hybrid sender:

   * Extracts `act`
   * Signs JWT
3. JWT sent to out-of-session agent (TLS)
4. Agent:

   * Extracts `act`
   * Requests token
   * Includes `act`
5. Auth0 Action injects `act`

✔ Token contains `sub + act`

<br>

# Step 10 – API / Resource Validation

Your API must:

1. Validate JWT signature
2. Verify:

   * `permissions` includes `system.access`
   * `sub` is known agent
   * `act` exists and is valid
3. Log:

   * `sub`
   * `act`
   * request ID

<br>
