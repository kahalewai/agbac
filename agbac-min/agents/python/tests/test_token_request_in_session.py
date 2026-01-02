import unittest
from phase1.token_request_in_session import InSessionTokenRequester
from adapters.okta_adapter import OktaAdapter

class TestInSessionTokenRequester(unittest.TestCase):

    def setUp(self):
        # Use Okta adapter for testing; could also mock
        self.adapter = OktaAdapter(
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://okta.example.com/oauth2/default/v1/token"
        )
        self.token_requester = InSessionTokenRequester(adapter=self.adapter)

        self.agent_identity = "agent-app"
        self.human_identity = {"sub": "user:alice@example.com"}

    def test_token_request_success(self):
        """Verify that token request includes both agent and human (sub + act)"""
        token_response = self.token_requester.request_token(
            agent_identity=self.agent_identity,
            human_identity=self.human_identity
        )
        self.assertIn("access_token", token_response)
        self.assertEqual(token_response.get("act"), self.human_identity)

if __name__ == "__main__":
    unittest.main()
