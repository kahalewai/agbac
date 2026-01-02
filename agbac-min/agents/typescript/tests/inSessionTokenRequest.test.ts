import { InSessionTokenRequest } from './inSessionTokenRequest';
import { HybridSender, HumanActor } from './hybridSender';
import { BaseAdapter } from './adapters/baseAdapter';

describe('InSessionTokenRequest', () => {
    it('should build token request with sub and act for in-session agent', async () => {
        const sender = new HybridSender();
        const adapter = new BaseAdapter();
        const tokenRequest = new InSessionTokenRequest(sender, adapter);

        // Mock getInSessionAct
        jest.spyOn(sender, 'getInSessionAct').mockResolvedValue({ sub: 'user:alice@example.com' });

        const payload = await tokenRequest.buildPayload();
        expect(payload).toHaveProperty('sub');
        expect(payload).toHaveProperty('act');
        expect(payload.act.sub).toBe('user:alice@example.com');
    });
});
