package com.agbac.tests;

import com.agbac.api.InSessionApiCall;
import com.agbac.token.InSessionTokenRequest;
import com.agbac.adapters.BaseAdapter;
import com.agbac.sender.HybridSender;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for InSessionApiCall.
 * Verifies API call succeeds with in-session token.
 */
public class InSessionApiCallTest {

    private InSessionApiCall apiCall;

    @BeforeEach
    public void setup() {
        HybridSender sender = new HybridSender();
        BaseAdapter adapter = new BaseAdapter() {
            @Override
            public String requestToken(Map<String, Object> tokenPayload) {
                return "token:" + tokenPayload.get("client_id") + ":" + tokenPayload.get("act");
            }
        };
        InSessionTokenRequest tokenRequest = new InSessionTokenRequest(sender, adapter);
        apiCall = new InSessionApiCall(tokenRequest);
    }

    @Test
    public void testApiCallReturnsResponse() {
        Map<String, Object> sessionData = Map.of("user", Map.of("username", "alice@example.com"));
        String agentId = "agent-app";
        String resourceUrl = "https://example.com/resource";

        String response = apiCall.callResource(sessionData, agentId, resourceUrl);
        assertTrue(response.contains(resourceUrl));
    }
}
