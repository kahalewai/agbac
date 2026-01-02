/**
 * auth0Adapter.ts
 * Implements AdapterBase for Auth0.
 */

import { AdapterBase } from './adapterBase';
import axios from 'axios';

export class Auth0Adapter extends AdapterBase {
    private tokenUrl: string;
    private clientId: string;
    private clientSecret: string;

    constructor(tokenUrl: string, clientId: string, clientSecret: string) {
        super();
        this.tokenUrl = tokenUrl;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
    }

    async requestToken(act: { sub: string }, sub: string): Promise<string> {
        try {
            this.logInfo('Requesting token from Auth0 with sub and act claims');

            const response = await axios.post(this.tokenUrl, {
                grant_type: 'client_credentials',
                client_id: this.clientId,
                client_secret: this.clientSecret,
                audience: 'https://api.example.com',
                sub: sub,
                act: act
            }, {
                headers: { 'Content-Type': 'application/json' }
            });

            return response.data.access_token;
        } catch (error) {
            this.handleError(error, 'Auth0Adapter.requestToken');
        }
    }
}
