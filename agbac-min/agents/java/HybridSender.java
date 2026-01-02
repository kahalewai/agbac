package com.agbac.sender;

import com.agbac.adapters.BaseAdapter;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.Base64;
import java.util.Map;

/**
 * HybridSender is responsible for securely providing human "act" data to agents.
 * 
 * Supports:
 *  - In-session agents: "act" data is passed directly within the application.
 *  - Out-of-session agents: "act" data is transmitted via signed JWT over TLS.
 * 
 * Responsibilities:
 *  1. Extract human user "act" from authenticated session.
 *  2. Provide act to in-session agents directly.
 *  3. Provide act to out-of-session agents via JWT + TLS.
 */
public class HybridSender {

    private final String jwtSecret; // Shared secret for signing JWTs
    private final BaseAdapter adapter;

    public HybridSender(String jwtSecret, BaseAdapter adapter) {
        this.jwtSecret = jwtSecret;
        this.adapter = adapter;
    }

    /**
     * Extract human "act" data from the application session.
     * 
     * @param sessionData Map representing the authenticated session
     * @return Map containing "act" data (e.g., user identifier)
     */
    public Map<String, Object> extractActFromSession(Map<String, Object> sessionData) {
        // Example: extract username and other claims from session
        String username = (String) sessionData.get("username");
        Map<String, Object> actData = Map.of("sub", username);

        log("Extracted act data from session: " + actData);
        return actData;
    }

    /**
     * Provide act data for an in-session agent.
     * Agent will receive act directly; no JWT/TLS needed.
     * 
     * @param sessionData Authenticated user session
     * @return act data map
     */
    public Map<String, Object> provideActForInSession(Map<String, Object> sessionData) {
        return extractActFromSession(sessionData);
    }

    /**
     * Provide act data for an out-of-session agent.
     * Act is packaged into a signed JWT for secure transmission.
     * 
     * @param sessionData Authenticated user session
     * @return signed JWT string containing act
     */
    public String provideActForOutOfSession(Map<String, Object> sessionData) {
        try {
            Map<String, Object> actData = extractActFromSession(sessionData);

            // Build JWT header
            String header = Base64.getUrlEncoder().withoutPadding()
                    .encodeToString("{\"alg\":\"HS256\",\"typ\":\"JWT\"}".getBytes());

            // Build JWT payload
            String payloadJson = "{\"act\":" + "{\"sub\":\"" + actData.get("sub") + "\"}" + "}";
            String payload = Base64.getUrlEncoder().withoutPadding()
                    .encodeToString(payloadJson.getBytes());

            // Create signature
            String message = header + "." + payload;
            Mac hmac = Mac.getInstance("HmacSHA256");
            hmac.init(new SecretKeySpec(jwtSecret.getBytes(), "HmacSHA256"));
            String signature = Base64.getUrlEncoder().withoutPadding()
                    .encodeToString(hmac.doFinal(message.getBytes()));

            String jwt = header + "." + payload + "." + signature;

            log("Generated signed JWT for out-of-session agent: " + jwt);
            return jwt;

        } catch (Exception e) {
            log("Failed to generate JWT for out-of-session agent: " + e.getMessage());
            throw new RuntimeException("Failed to generate JWT", e);
        }
    }

    /**
     * Utility logging method consistent with adapter logging
     */
    private void log(String message) {
        System.out.println("[HybridSender] " + message);
    }
}
