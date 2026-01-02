package com.agbac.token;

import com.agbac.sender.HybridSender;
import com.agbac.adapters.BaseAdapter;

/**
 * Handles OAuth token requests for out-of-session agents.
 * Expects act data to be provided via JWT from HybridSender.
 */
public class OutOfSessionTokenRequest {

    private final HybridSender sender;
    private final BaseAdapter adapter;

    public OutOfSessionTokenRequest(HybridSender sender, BaseAdapter adapter) {
        this.sender = sender;
        this.adapter = adapter;
    }

    /**
     * Request an OAuth token for an out-of-session agent.
     *
     * @param sessionData Authenticated user session (sender extracts act)
     * @param agentClientId Agent client ID (sub)
     * @return access token string
     */
    public String requestToken(Map<String, Object> sessionData, String agentClientId) {
        try {
            // Generate signed JWT containing act data for out-of-session agent
            String actJwt = sender.provideActForOutOfSession(sessionData);

            // Prepare token request payload
            Map<String, Object> tokenPayload = Map.of(
                    "client_id", agentClientId,
                    "grant_type", "client_credentials",
                    "act_jwt", actJwt
            );

            String token = adapter.requestToken(tokenPayload);

            log("Out-of-session token obtained for agent " + agentClientId + " with act JWT");
            return token;

        } catch (Exception e) {
            log("Failed to request out-of-session token: " + e.getMessage());
            throw new RuntimeException("Out-of-session token request failed", e);
        }
    }

    private void log(String message) {
        System.out.println("[OutOfSessionTokenRequest] " + message);
    }
}
