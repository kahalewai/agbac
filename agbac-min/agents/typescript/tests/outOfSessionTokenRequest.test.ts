import { OutOfSessionTokenRequest } from './outOfSessionTokenRequest';
import { HybridSender } from './hybridSender';
import { BaseAdapter } from './adapters/baseAdapter';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('OutOfSessionTokenRequest', () => {
    it('should request token including act and sub for out-of-session agent', async () => {
        const sender = new HybridSender();
        const adapter = new BaseAdapter();
        const tokenRequest = new OutOfSessionTokenRequest(sender, adapter);

        // Mock getOutOfSessionAct and axios.post
        jest.spyOn(sender, 'getOutOfSessionAct').mockResolvedValue({ sub: 'user:bob@example.com' });
        mockedAxios.post.mockResolvedValue({ data: { access_token: 'dummy-token' } });

        const token = await tokenRequest.requestToken();
        expect(token).toBe('dummy-token');
        expect(mockedAxios.post).toHaveBeenCalled();
    });
});
