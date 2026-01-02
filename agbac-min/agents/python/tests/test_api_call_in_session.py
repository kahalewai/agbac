import unittest
from phase1.api_call_in_session import InSessionAPICaller
from adapters.okta_adapter import OktaAdapter

class TestInSessionAPICaller(unittest.TestCase):

    def setUp(self):
        self.adapter = OktaAdapter(
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://okta.example.com/oauth2/default/v1/token"
        )
        self.api_caller = InSessionAPICaller(adapter=self.adapter)
        self.access_token = "dummy-access-token"
        self.resource_url = "https://api.example.com/resource"

    def test_api_call_success(self):
        """Verify that API call returns JSON response"""
        response = self.api_caller.call_api(
            access_token=self.access_token,
            resource_url=self.resource_url
        )
        self.assertIsInstance(response, dict)

if __name__ == "__main__":
    unittest.main()
