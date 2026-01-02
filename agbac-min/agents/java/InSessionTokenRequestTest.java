package com.agbac.tests;

import com.agbac.adapters.BaseAdapter;
import com.agbac.token.InSessionTokenRequest;
import com.agbac.sender.HybridSender;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for InSessionTokenRequest.
 * Validates token requests include both sub (agent) and act (human).
 */
public class InSessionTokenRequestTest {

    private HybridSender sender;
    private BaseAdapter adapter;
    private InSessionTokenRequest tokenRequest;

    @BeforeEach
    public void setup() {
        sender = new HybridSender();
        adapter = new BaseAdapter() {
            @Override
            public String requestToken(Map<String, Object> tokenPayload) {
                // Simulated token response containing payload
                return "token:" + tokenPayload.get("client_id") + ":" + tokenPayload.get("act");
            }
        };
        tokenRequest = new InSessionTokenRequest(sender, adapter);
    }

    @Test
    public void testInSessionTokenIncludesAct() {
        Map<String, Object> sessionData = Map.of("user", Map.of("username", "alice@example.com"));
        String agentId = "agent-app";

        String token = tokenRequest.requestToken(sessionData, agentId);

        assertTrue(token.contains(agentId), "Token must contain agent client_id");
        assertTrue(token.contains("alice@example.com"), "Token must contain human act data");
    }
}
