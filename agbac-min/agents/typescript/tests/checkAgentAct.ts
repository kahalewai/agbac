/**
 * checkAgentAct.ts
 * 
 * Helper script to verify whether a specific agent is aware of the human `act` data.
 * Works with both in-session and out-of-session agents.
 * Logs the result for the developer or IAM engineer.
 */

import { HybridSender, HumanActor } from './hybridSender';
import { InSessionTokenRequest } from './inSessionTokenRequest';
import { OutOfSessionTokenRequest } from './outOfSessionTokenRequest';

/**
 * Function to check if an in-session agent sees the human identity
 */
async function checkInSessionAgentAct() {
    const sender = new HybridSender();
    const tokenRequest = new InSessionTokenRequest(sender);

    try {
        const payload = await tokenRequest.buildPayload();
        console.log('--- In-Session Agent ---');
        console.log('Token Request Payload:', JSON.stringify(payload, null, 2));

        if (payload.act && payload.act.sub) {
            console.log(`✅ In-session agent is aware of human identity: ${payload.act.sub}`);
        } else {
            console.warn('⚠️ In-session agent does NOT include human `act` data.');
        }
    } catch (err) {
        console.error('Error checking in-session agent `act` data:', err);
    }
}

/**
 * Function to check if an out-of-session agent sees the human identity
 */
async function checkOutOfSessionAgentAct() {
    const sender = new HybridSender();
    const tokenRequest = new OutOfSessionTokenRequest(sender);

    try {
        const token = await tokenRequest.requestToken();
        console.log('--- Out-of-Session Agent ---');
        console.log('Received token:', token);

        // Decode token (assuming JWT) to inspect payload
        const parts = token.split('.');
        if (parts.length === 3) {
            const payloadBase64 = parts[1];
            const payloadJson = JSON.parse(Buffer.from(payloadBase64, 'base64').toString('utf-8'));
            console.log('Token Payload:', JSON.stringify(payloadJson, null, 2));

            if (payloadJson.act && payloadJson.act.sub) {
                console.log(`✅ Out-of-session agent is aware of human identity: ${payloadJson.act.sub}`);
            } else {
                console.warn('⚠️ Out-of-session agent does NOT include human `act` data.');
            }
        } else {
            console.warn('⚠️ Token format invalid, cannot inspect `act` data.');
        }
    } catch (err) {
        console.error('Error checking out-of-session agent `act` data:', err);
    }
}

/**
 * Main function to run both checks
 */
async function main() {
    console.log('Starting Agent `act` verification...');
    await checkInSessionAgentAct();
    await checkOutOfSessionAgentAct();
    console.log('Agent `act` verification completed.');
}

// Run the script
main().catch(err => {
    console.error('Unexpected error in helper script:', err);
});
