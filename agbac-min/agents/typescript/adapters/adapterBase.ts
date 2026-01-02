/**
 * adapterBase.ts
 * Base adapter interface and helper functions for all IAM vendor adapters.
 * Provides standard methods that each vendor-specific adapter must implement.
 */

import winston from 'winston';

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.printf(({ timestamp, level, message }) => `${timestamp} [${level}]: ${message}`)
  ),
  transports: [new winston.transports.Console()]
});

// Define standard interface for IAM adapters
export interface IAMAdapter {
    /**
     * Requests an OAuth token including sub (agent) and act (human) claims
     * @param act - human actor object { sub: string }
     * @param sub - agent subject string
     * @returns Promise resolving to token string
     */
    requestToken(act: { sub: string }, sub: string): Promise<string>;

    /**
     * Optional: retrieves metadata or configuration from the IAM vendor
     */
    getMetadata?(): Promise<any>;
}

// Base adapter class providing common helper methods
export abstract class AdapterBase implements IAMAdapter {
    abstract requestToken(act: { sub: string }, sub: string): Promise<string>;

    protected handleError(error: any, context: string) {
        logger.error(`Error in AdapterBase [${context}]: ${error.message || error}`);
        throw error;
    }

    protected logInfo(message: string) {
        logger.info(message);
    }
}
