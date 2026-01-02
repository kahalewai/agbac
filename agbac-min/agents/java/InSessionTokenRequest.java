package com.agbac.token;

import com.agbac.sender.HybridSender;
import com.agbac.adapters.BaseAdapter;

import java.util.Map;

/**
 * Handles OAuth token requests for in-session agents.
 * Ensures that the token includes both:
 *  - sub: the agent identity
 *  - act: the human identity (from session via HybridSender)
 */
public class InSessionTokenRequest {

    private final HybridSender sender;
    private final BaseAdapter adapter;

    public InSessionTokenRequest(HybridSender sender, BaseAdapter adapter) {
        this.sender = sender;
        this.adapter = adapter;
    }

    /**
     * Request an OAuth token for an in-session agent.
     *
     * @param sessionData Authenticated user session containing human info
     * @param agentClientId Agent client ID (sub)
     * @return access token string
     */
    public String requestToken(Map<String, Object> sessionData, String agentClientId) {
        try {
            Map<String, Object> actData = sender.provideActForInSession(sessionData);

            // Prepare token request payload
            Map<String, Object> tokenPayload = Map.of(
                    "client_id", agentClientId,
                    "grant_type", "client_credentials",
                    "act", actData
            );

            // Call adapter to request token from IAM
            String token = adapter.requestToken(tokenPayload);

            log("In-session token obtained for agent " + agentClientId + " with act " + actData);
            return token;

        } catch (Exception e) {
            log("Failed to request in-session token: " + e.getMessage());
            throw new RuntimeException("In-session token request failed", e);
        }
    }

    private void log(String message) {
        System.out.println("[InSessionTokenRequest] " + message);
    }
}
