# Keycloak Configuration for AGBAC-Min (Dual-Subject Authorization)

## Target Outcome

After completing these steps:

✅ Every issued access token contains:

* `sub` → agent identity (service account / client)
* `act` → human identity (from hybrid sender)

✅ Works for:

* **Phase 1 – In-session agents**
* **Phase 2 – Out-of-session agents (TLS + signed JWT)**

✅ Keycloak enforces:

* Agent pre-approval (RBAC)
* Human pre-approval (RBAC)
* No delegation, no impersonation, no human discovery by agents

<br>

# Architectural Mapping

| Concept              | Keycloak                                           |
| -------------------- | -------------------------------------------------- |
| Authorization Server | Realm                                              |
| API                  | Resource Server (client with audience)             |
| Agent                | Confidential Client (service account enabled)      |
| Human                | User                                               |
| RBAC                 | Realm / Client Roles                               |
| `act` claim          | Protocol Mapper (from client assertion or request) |

Keycloak **does not infer the human**.
Your **hybrid sender provides `act` explicitly**, which is correct.

<br>

# Step 0 – Prerequisites

You must have:

* Admin access to Keycloak
* TLS enabled for token endpoints
* Realm admin privileges
* Hybrid sender already implemented

<br>

# Step 1 – Create a Realm

### UI Steps

1. Open **Keycloak Admin Console**
2. Click **Create Realm**
3. Enter:

   * **Realm Name:** `agbac-min`
4. Create

<br>

### Realm JSON (Conceptual)

```json
{
  "realm": "agbac-min",
  "enabled": true
}
```

<br>

# Step 2 – Create the API (Resource Server)

### UI Steps

1. **Clients → Create client**
2. Client ID: `agbac-min-api`
3. Client type: **Confidential**
4. Save
5. Enable:

   * **Authorization Enabled**
   * **Service Accounts Enabled**

<br>

### API Client JSON

```json
{
  "clientId": "agbac-min-api",
  "enabled": true,
  "protocol": "openid-connect",
  "publicClient": false,
  "serviceAccountsEnabled": true
}
```

<br>

# Step 3 – Define Scopes

### UI Steps

1. Open `agbac-min-api`
2. **Authorization → Resources**
3. Create resource:

   * Name: `System`
   * URI: `/`
4. **Authorization → Scopes**
5. Create:

   * Name: `system.access`

<br>

### Scope JSON

```json
{
  "name": "system.access"
}
```

<br>

# Step 4 – Create Agent Clients (Service Accounts)

Each agent is a **confidential client**.

### UI Steps

1. **Clients → Create client**
2. Client ID: `finance-agent`
3. Client type: **Confidential**
4. Enable:

   * **Service Accounts**
   * **Client authentication**
5. Save

<br>

### Agent Client JSON

```json
{
  "clientId": "finance-agent",
  "enabled": true,
  "serviceAccountsEnabled": true,
  "protocol": "openid-connect"
}
```

<br>

# Step 5 – Create Roles (RBAC)

## 5.1 Human Role

### UI Steps

1. **Realm Roles → Create role**
2. Name: `FinanceUser`

<br>

## 5.2 Agent Role

1. Create role:

   * Name: `FinanceAgent`

<br>

### Roles JSON

```json
{
  "name": "FinanceUser"
}
```

```json
{
  "name": "FinanceAgent"
}
```

<br>

# Step 6 – Assign Roles

## Human Assignment

1. **Users → Select User**
2. **Role Mapping**
3. Assign:

   * `FinanceUser`

## Agent Assignment

1. **Clients → finance-agent**
2. **Service Account Roles**
3. Assign:

   * `FinanceAgent`

**Both assignments are mandatory**

<br>

# Step 7 – Configure Protocol Mapper for `act`

This is the critical step.

Keycloak allows **custom protocol mappers** to inject claims from:

* Client assertion JWT
* Request parameters
* Client attributes

<br>

## 7.1 Create Protocol Mapper

### UI Steps

1. **Clients → agbac-min-api**
2. **Client Scopes → Create**
3. Name: `act-scope`
4. Assign scope to API

<br>

## 7.2 Add Mapper

1. Inside `act-scope`
2. **Protocol Mappers → Create**
3. Mapper type: **OIDC Claim to Token Mapper**
4. Configure:

| Field               | Value                  |
| ------------------- | ---------------------- |
| Name                | `act-claim-mapper`     |
| Token Claim Name    | `act`                  |
| Claim JSON Type     | `String`               |
| Add to access token | ✅                      |
| Add to ID token     | ❌                      |
| Add to userinfo     | ❌                      |
| Claim value         | `client_assertion.act` |

<br>

### Mapper JSON

```json
{
  "name": "act-claim-mapper",
  "protocol": "openid-connect",
  "protocolMapper": "oidc-hardcoded-claim-mapper",
  "config": {
    "claim.name": "act",
    "jsonType.label": "String",
    "access.token.claim": "true",
    "claim.value": "${client_assertion.act}"
  }
}
```

> ✔ This allows Keycloak to extract `act` from the **signed JWT assertion** provided by your hybrid sender.

<br>

# Step 8 – In-Session Flow (Phase 1)

### Flow

1. Human logs in (OIDC)
2. Application extracts human identity
3. Hybrid sender passes `act` in memory
4. In-session agent:

   * Requests token
   * Includes `act`
5. Keycloak injects `act` via mapper

<br>

### Token Example

```json
{
  "sub": "finance-agent",
  "act": "alice@corp.example",
  "scope": "system.access"
}
```

<br>

# Step 9 – Out-of-Session Flow (Phase 2)

### Flow

1. Human logs in
2. Hybrid sender:

   * Extracts `act`
   * Signs JWT
3. JWT sent over TLS to agent
4. Agent:

   * Uses JWT as client assertion
   * Requests token
5. Mapper injects `act`

   * No session required
   * No impersonation
   * Full attribution

<br>

# Step 10 – Authorization Policies

### UI Steps

1. **agbac-min-api → Authorization → Policies**
2. Create **Role Policy**
3. Require:

   * `FinanceAgent`
   * `FinanceUser`

<br>

### Policy JSON

```json
{
  "name": "DualSubjectPolicy",
  "type": "role",
  "logic": "POSITIVE",
  "roles": [
    "FinanceAgent",
    "FinanceUser"
  ]
}
```

<br>

# Step 11 – API Enforcement

Your API must:

1. Validate token signature
2. Verify:

   * `sub` is trusted agent
   * `act` exists
   * `scope` includes `system.access`
3. Log:

   * agent (`sub`)
   * human (`act`)
   * request ID

<br>

