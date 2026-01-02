package com.agbac.tests;

import com.agbac.adapters.BaseAdapter;
import com.agbac.token.OutOfSessionTokenRequest;
import com.agbac.sender.HybridSender;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for OutOfSessionTokenRequest.
 * Validates token requests include act JWT and sub (agent).
 */
public class OutOfSessionTokenRequestTest {

    private OutOfSessionTokenRequest tokenRequest;

    @BeforeEach
    public void setup() {
        HybridSender sender = new HybridSender();
        BaseAdapter adapter = new BaseAdapter() {
            @Override
            public String requestToken(Map<String, Object> tokenPayload) {
                return "token:" + tokenPayload.get("client_id") + ":" + tokenPayload.get("act_jwt");
            }
        };
        tokenRequest = new OutOfSessionTokenRequest(sender, adapter);
    }

    @Test
    public void testOutOfSessionTokenIncludesActJwt() {
        Map<String, Object> sessionData = Map.of("user", Map.of("username", "alice@example.com"));
        String agentId = "agent-app";

        String token = tokenRequest.requestToken(sessionData, agentId);

        assertTrue(token.contains(agentId));
        assertTrue(token.contains("alice@example.com"), "Token must include act data via JWT");
    }
}
