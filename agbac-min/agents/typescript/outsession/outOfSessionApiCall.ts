/**
 * outOfSessionApiCall.ts
 * Performs API or resource call for out-of-session agent using token obtained via TLS + JWT hybrid sender.
 */

import axios from 'axios';
import winston from 'winston';

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message }) => `${timestamp} [${level}]: ${message}`)
    ),
    transports: [new winston.transports.Console()]
});

export class OutOfSessionApiCall {
    private apiUrl: string;

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }

    /**
     * Call the API or resource using the provided token
     * @param token OAuth access token including human `act` claim
     */
    async callApi(token: string): Promise<any> {
        try {
            const response = await axios.get(this.apiUrl, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            logger.info(`Out-of-session API call successful. Status: ${response.status}`);
            return response.data;

        } catch (error) {
            logger.error(`Out-of-session API call failed: ${error.message || error}`);
            throw error;
        }
    }
}
