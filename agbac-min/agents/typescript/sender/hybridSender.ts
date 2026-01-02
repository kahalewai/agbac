/**
 * hybridSender.ts
 * Hybrid sender for both in-session and out-of-session agents.
 * 
 * Responsibilities:
 * 1. Extract human `act` data from in-session user session.
 * 2. Provide `act` to in-session agents directly.
 * 3. Securely send `act` to out-of-session agents using TLS + JWT.
 * 4. Include timing and directionality logic for out-of-session transmission.
 */

import fs from 'fs';
import jwt from 'jsonwebtoken';
import https from 'https';
import winston from 'winston';

// Configure logging (match Python style)
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message }) => `${timestamp} [${level}]: ${message}`)
    ),
    transports: [new winston.transports.Console()]
});

// Type for human actor
export interface HumanActor {
    sub: string; // e.g., 'user:alice@example.com'
}

// Type for out-of-session transmission
export interface OutOfSessionTarget {
    url: string;           // Agent endpoint
    tlsCertPath: string;   // Path to TLS certificate for secure communication
    privateKeyPath: string; // Private key to sign JWT
    tokenExpirySec?: number; // Optional JWT expiration
}

export class HybridSender {
    private humanActor: HumanActor;

    constructor(humanActor: HumanActor) {
        this.humanActor = humanActor;
        logger.info(`HybridSender initialized for human actor: ${humanActor.sub}`);
    }

    /**
     * Get human actor data for in-session agents.
     * The in-session agent can directly include this `act` in the token request.
     */
    getInSessionAct(): HumanActor {
        logger.info(`Providing in-session ACT data for: ${this.humanActor.sub}`);
        return this.humanActor;
    }

    /**
     * Send human actor `act` data securely to an out-of-session agent.
     * Uses TLS + signed JWT for authenticity.
     * 
     * @param target - target agent endpoint and TLS/JWT info
     */
    async sendOutOfSessionAct(target: OutOfSessionTarget): Promise<void> {
        logger.info(`Preparing to send out-of-session ACT data for: ${this.humanActor.sub} to ${target.url}`);

        try {
            // Load private key for signing JWT
            const privateKey = fs.readFileSync(target.privateKeyPath, 'utf-8');

            const payload = {
                act: this.humanActor,
                iat: Math.floor(Date.now() / 1000),
                exp: Math.floor(Date.now() / 1000) + (target.tokenExpirySec || 60)
            };

            // Sign JWT
            const token = jwt.sign(payload, privateKey, { algorithm: 'RS256' });

            logger.info(`JWT created for out-of-session transmission`);

            // Load TLS cert for HTTPS request
            const tlsCert = fs.readFileSync(target.tlsCertPath);

            // Send POST request to out-of-session agent securely
            await new Promise<void>((resolve, reject) => {
                const req = https.request(target.url, {
                    method: 'POST',
                    cert: tlsCert,
                    headers: {
                        'Content-Type': 'application/jwt',
                        'Authorization': `Bearer ${token}`
                    }
                }, res => {
                    if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                        logger.info(`Out-of-session ACT delivered successfully`);
                        resolve();
                    } else {
                        reject(new Error(`Failed to deliver out-of-session ACT: ${res.statusCode}`));
                    }
                });

                req.on('error', (err) => reject(err));
                req.end();
            });
        } catch (error) {
            logger.error(`Error sending out-of-session ACT: ${error.message || error}`);
            throw error;
        }
    }
}
