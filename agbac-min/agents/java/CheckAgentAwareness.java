package com.agbac.helpers;

import com.agbac.adapters.BaseAdapter;
import com.agbac.sender.HybridSender;
import com.agbac.token.InSessionTokenRequest;
import com.agbac.token.OutOfSessionTokenRequest;

import java.util.Map;

/**
 * Helper script to verify if an agent is aware of the human user (act) identity.
 * Can be used for both in-session and out-of-session agents.
 */
public class CheckAgentAwareness {

    public static void main(String[] args) {
        Map<String, Object> sessionData = Map.of("user", Map.of("username", "alice@example.com"));
        String agentId = "agent-app";

        HybridSender sender = new HybridSender();
        BaseAdapter adapter = new BaseAdapter() {
            @Override
            public String requestToken(Map<String, Object> tokenPayload) {
                return tokenPayload.toString();
            }
        };

        // Check in-session agent
        InSessionTokenRequest inSession = new InSessionTokenRequest(sender, adapter);
        String inSessionToken = inSession.requestToken(sessionData, agentId);
        System.out.println("In-session token includes: " + inSessionToken);

        // Check out-of-session agent
        OutOfSessionTokenRequest outSession = new OutOfSessionTokenRequest(sender, adapter);
        String outSessionToken = outSession.requestToken(sessionData, agentId);
        System.out.println("Out-of-session token includes: " + outSessionToken);
    }
}
