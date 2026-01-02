/**
 * inSessionTokenRequest.ts
 * Handles OAuth token request for in-session agents, including the human `act` claim.
 * Works with HybridSender to include `act` data in token request.
 */

import axios from 'axios';
import winston from 'winston';
import { HybridSender, HumanActor } from './hybridSender';
import { BaseAdapter } from './adapters/baseAdapter';

// Configure logging
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message }) => `${timestamp} [${level}]: ${message}`)
    ),
    transports: [new winston.transports.Console()]
});

export class InSessionTokenRequest {
    private hybridSender: HybridSender;
    private adapter: BaseAdapter;

    constructor(hybridSender: HybridSender, adapter: BaseAdapter) {
        this.hybridSender = hybridSender;
        this.adapter = adapter;
    }

    /**
     * Request an OAuth token for an in-session agent including the human `act` claim
     */
    async requestToken(): Promise<string> {
        try {
            const actData: HumanActor = this.hybridSender.getInSessionAct();
            logger.info(`Preparing token request including human ACT: ${actData.sub}`);

            // Build token request payload according to adapter
            const payload = this.adapter.buildTokenRequestPayload(actData);

            // Execute token request
            const tokenResponse = await axios.post(this.adapter.tokenUrl, payload, {
                headers: this.adapter.getTokenRequestHeaders()
            });

            const accessToken = tokenResponse.data.access_token;
            logger.info(`Token request successful for in-session agent`);
            return accessToken;

        } catch (error) {
            logger.error(`In-session token request failed: ${error.message || error}`);
            throw error;
        }
    }
}
