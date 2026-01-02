package com.agbac.api;

import com.agbac.token.OutOfSessionTokenRequest;

/**
 * Represents an API/resource call from an out-of-session agent.
 * Requires a valid OAuth token obtained from OutOfSessionTokenRequest.
 */
public class OutOfSessionApiCall {

    private final OutOfSessionTokenRequest tokenRequest;

    public OutOfSessionApiCall(OutOfSessionTokenRequest tokenRequest) {
        this.tokenRequest = tokenRequest;
    }

    /**
     * Calls a protected resource with the out-of-session agent token.
     *
     * @param sessionData Authenticated user session (sender extracts act)
     * @param agentClientId Agent client ID
     * @param resourceUrl URL of the API/resource
     * @return response body string
     */
    public String callResource(Map<String, Object> sessionData, String agentClientId, String resourceUrl) {
        try {
            String accessToken = tokenRequest.requestToken(sessionData, agentClientId);

            // Example: call API using HTTP client (pseudo-code)
            String response = "Simulated API response for out-of-session resource: " + resourceUrl;
            log("API called successfully with access token: " + accessToken);
            return response;

        } catch (Exception e) {
            log("Failed API/resource call: " + e.getMessage());
            throw new RuntimeException("Out-of-session API/resource call failed", e);
        }
    }

    private void log(String message) {
        System.out.println("[OutOfSessionApiCall] " + message);
    }
}
