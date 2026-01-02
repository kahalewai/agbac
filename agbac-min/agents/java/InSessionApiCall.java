package com.agbac.api;

import com.agbac.token.InSessionTokenRequest;

import java.util.Map;

/**
 * Represents an API/resource call from an in-session agent.
 * Requires a valid OAuth token obtained from InSessionTokenRequest.
 */
public class InSessionApiCall {

    private final InSessionTokenRequest tokenRequest;

    public InSessionApiCall(InSessionTokenRequest tokenRequest) {
        this.tokenRequest = tokenRequest;
    }

    /**
     * Calls a protected resource with the agent's token and human act info.
     *
     * @param sessionData Authenticated user session
     * @param agentClientId Agent client ID
     * @param resourceUrl URL of the API/resource
     * @return response body string
     */
    public String callResource(Map<String, Object> sessionData, String agentClientId, String resourceUrl) {
        try {
            String accessToken = tokenRequest.requestToken(sessionData, agentClientId);

            // Example: call API using HTTP client (pseudo-code)
            // HttpRequest req = HttpRequest.newBuilder()
            //     .uri(URI.create(resourceUrl))
            //     .header("Authorization", "Bearer " + accessToken)
            //     .GET()
            //     .build();
            // HttpResponse<String> resp = HttpClient.newHttpClient().send(req, BodyHandlers.ofString());

            String response = "Simulated API response for resource: " + resourceUrl;
            log("API called successfully with access token: " + accessToken);
            return response;

        } catch (Exception e) {
            log("Failed API/resource call: " + e.getMessage());
            throw new RuntimeException("In-session API/resource call failed", e);
        }
    }

    private void log(String message) {
        System.out.println("[InSessionApiCall] " + message);
    }
}
