package com.agbac.adapters;

import java.util.HashMap;
import java.util.Map;

/**
 * EntraIDAdapter implements BaseAdapter for Microsoft Entra ID.
 * Supports in-session dual-subject token requests (agent + human) only.
 */
public class EntraIDAdapter extends BaseAdapter {

    private final String tenantId;
    private final String clientId;
    private final String clientSecret;

    public EntraIDAdapter(String tenantId, String clientId, String clientSecret) {
        this.tenantId = tenantId;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
    }

    @Override
    public Map<String, Object> requestToken(String agentId, Map<String, Object> actData) throws AdapterException {
        log("Requesting token for agent: " + agentId + " with act data: " + actData);

        try {
            // Build OAuth request payload with sub + act claims for in-session agent
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("client_id", clientId);
            requestBody.put("client_secret", clientSecret);
            requestBody.put("grant_type", "client_credentials");
            requestBody.put("scope", "system.access");
            requestBody.put("agent_id", agentId);
            requestBody.put("act", actData); // Dual-subject claim

            // TODO: Implement HTTP request to EntraID /token endpoint

            Map<String, Object> tokenResponse = new HashMap<>();
            tokenResponse.put("access_token", "mock_entraid_token");
            tokenResponse.put("token_type", "Bearer");
            tokenResponse.put("expires_in", 3600);

            log("Token request successful for agent: " + agentId);
            return tokenResponse;
        } catch (Exception e) {
            throw new AdapterException("Failed to request token from EntraID", e);
        }
    }

    @Override
    public Map<String, Object> callApi(String token, String apiEndpoint, Map<String, Object> payload) throws AdapterException {
        log("Calling API endpoint: " + apiEndpoint + " with token");

        try {
            // TODO: Implement HTTP request to API with Authorization: Bearer {token}
            Map<String, Object> apiResponse = new HashMap<>();
            apiResponse.put("status", "success");
            apiResponse.put("data", "mock_api_response");

            log("API call successful: " + apiEndpoint);
            return apiResponse;
        } catch (Exception e) {
            throw new AdapterException("API call failed: " + apiEndpoint, e);
        }
    }
}
