/**
 * outOfSessionTokenRequest.ts
 * Handles OAuth token request for out-of-session agents.
 * Receives human `act` data securely via TLS + JWT from the HybridSender.
 * Works with any adapter (Okta, EntraID, Auth0, Keycloak).
 */

import axios from 'axios';
import winston from 'winston';
import { HybridSender, HumanActor } from './hybridSender';
import { BaseAdapter } from './adapters/baseAdapter';

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message }) => `${timestamp} [${level}]: ${message}`)
    ),
    transports: [new winston.transports.Console()]
});

export class OutOfSessionTokenRequest {
    private hybridSender: HybridSender;
    private adapter: BaseAdapter;

    constructor(hybridSender: HybridSender, adapter: BaseAdapter) {
        this.hybridSender = hybridSender;
        this.adapter = adapter;
    }

    /**
     * Request an OAuth token for an out-of-session agent including human `act` data
     */
    async requestToken(): Promise<string> {
        try {
            // Get securely transmitted ACT data via TLS + JWT from sender
            const actData: HumanActor = await this.hybridSender.getOutOfSessionAct();
            logger.info(`Preparing out-of-session token request including human ACT: ${actData.sub}`);

            // Build token request payload with `sub` and `act`
            const payload = this.adapter.buildTokenRequestPayload(actData);

            // Execute token request
            const tokenResponse = await axios.post(this.adapter.tokenUrl, payload, {
                headers: this.adapter.getTokenRequestHeaders()
            });

            const accessToken = tokenResponse.data.access_token;
            logger.info(`Token request successful for out-of-session agent`);
            return accessToken;

        } catch (error) {
            logger.error(`Out-of-session token request failed: ${error.message || error}`);
            throw error;
        }
    }
}
