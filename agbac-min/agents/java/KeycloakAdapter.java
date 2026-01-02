package com.agbac.adapters;

import java.util.HashMap;
import java.util.Map;

/**
 * KeycloakAdapter implements BaseAdapter for Keycloak.
 */
public class KeycloakAdapter extends BaseAdapter {

    private final String realmUrl;
    private final String clientId;
    private final String clientSecret;

    public KeycloakAdapter(String realmUrl, String clientId, String clientSecret) {
        this.realmUrl = realmUrl;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
    }

    @Override
    public Map<String, Object> requestToken(String agentId, Map<String, Object> actData) throws AdapterException {
        log("Requesting token for agent: " + agentId + " with act data: " + actData);

        try {
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("client_id", clientId);
            requestBody.put("client_secret", clientSecret);
            requestBody.put("grant_type", "client_credentials");
            requestBody.put("scope", "system.access");
            requestBody.put("agent_id", agentId);
            requestBody.put("act", actData);

            // TODO: Implement HTTP request to Keycloak /protocol/openid-connect/token endpoint

            Map<String, Object> tokenResponse = new HashMap<>();
            tokenResponse.put("access_token", "mock_keycloak_token");
            tokenResponse.put("token_type", "Bearer");
            tokenResponse.put("expires_in", 3600);

            log("Token request successful for agent: " + agentId);
            return tokenResponse;
        } catch (Exception e) {
            throw new AdapterException("Failed to request token from Keycloak", e);
        }
    }

    @Override
    public Map<String, Object> callApi(String token, String apiEndpoint, Map<String, Object> payload) throws AdapterException {
        log("Calling API endpoint: " + apiEndpoint + " with token");

        try {
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
