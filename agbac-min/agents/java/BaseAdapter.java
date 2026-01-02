package com.agbac.adapters;

import java.util.Map;

/**
 * BaseAdapter provides the abstract methods for all vendor-specific adapters.
 * Any vendor adapter (Okta, EntraID, Auth0, Keycloak) should extend this class.
 * 
 * Responsibilities:
 *  - Request OAuth tokens with dual-subject claims (sub + act)
 *  - Make API or resource calls
 *  - Standardized logging and error handling
 */
public abstract class BaseAdapter {

    /**
     * Request an OAuth token for the given agent and human actor.
     * 
     * @param agentId Identifier for the agent/service principal
     * @param actData Human user "act" data
     * @return Map containing token data (access_token, token_type, expires_in, etc.)
     * @throws AdapterException if the request fails or the response is invalid
     */
    public abstract Map<String, Object> requestToken(String agentId, Map<String, Object> actData) throws AdapterException;

    /**
     * Call a protected API or resource using the provided token.
     * 
     * @param token Access token to use for the API call
     * @param apiEndpoint URL of the API/resource
     * @param payload Optional payload for POST/PUT requests
     * @return Map containing API response
     * @throws AdapterException if API call fails or response is invalid
     */
    public abstract Map<String, Object> callApi(String token, String apiEndpoint, Map<String, Object> payload) throws AdapterException;

    /**
     * Utility method for logging messages in a consistent format.
     * Could be replaced with a logging framework such as Log4j or SLF4J.
     * 
     * @param message Message to log
     */
    protected void log(String message) {
        System.out.println("[BaseAdapter] " + message);
    }

    /**
     * Custom exception for adapter-related errors.
     */
    public static class AdapterException extends Exception {
        public AdapterException(String message) {
            super(message);
        }

        public AdapterException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
