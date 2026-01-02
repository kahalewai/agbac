import { HybridSender, HumanActor } from './hybridSender';

describe('HybridSender', () => {
    it('should return human act data for in-session agents', async () => {
        const sender = new HybridSender();
        const actData: HumanActor = await sender.getInSessionAct();

        expect(actData).toHaveProperty('sub');
        expect(actData.sub).toBeDefined();
        expect(typeof actData.sub).toBe('string');
    });

    it('should return human act data securely for out-of-session agents', async () => {
        const sender = new HybridSender();
        const actData: HumanActor = await sender.getOutOfSessionAct();

        expect(actData).toHaveProperty('sub');
        expect(actData.sub).toBeDefined();
        expect(typeof actData.sub).toBe('string');
    });
});
