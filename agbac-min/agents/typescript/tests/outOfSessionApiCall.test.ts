import { OutOfSessionApiCall } from './outOfSessionApiCall';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('OutOfSessionApiCall', () => {
    it('should successfully call API using out-of-session token', async () => {
        const apiCall = new OutOfSessionApiCall('https://example.com/api');
        const mockData = { success: true };

        mockedAxios.get.mockResolvedValue({ status: 200, data: mockData });

        const result = await apiCall.callApi('dummy-token');
        expect(result).toEqual(mockData);
        expect(mockedAxios.get).toHaveBeenCalledWith('https://example.com/api', expect.any(Object));
    });
});
