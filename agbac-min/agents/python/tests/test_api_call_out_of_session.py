import unittest
from phase2.api_call_out_of_session import OutOfSessionAPICaller
from adapters.okta_adapter import OktaAdapter

class TestOutOfSessionAPICaller(unittest.TestCase):

    def setUp(self):
        self.adapter = OktaAdapter(
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://okta.example.com/oauth2/default/v1/token"
        )
        self.api_caller = OutOfSessionAPICaller(adapter=self.adapter)
        self.access_token = "dummy-access-token"
        self.resource_url = "https://api.example.com/resource"

    def test_api_call_success(self):
        """Verify out-of-session API call returns JSON response"""
        response = self.api_caller.call_api(
            access_token=self.access_token,
            resource_url=self.resource_url
        )
        self.assertIsInstance(response, dict)

if __name__ == "__main__":
    unittest.main()
