import unittest
from phase2.token_request_out_of_session import OutOfSessionTokenRequester
from adapters.okta_adapter import OktaAdapter
from sender.hybrid_sender import HybridSender

class TestOutOfSessionTokenRequester(unittest.TestCase):

    def setUp(self):
        self.adapter = OktaAdapter(
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://okta.example.com/oauth2/default/v1/token"
        )
        self.sender = HybridSender(private_key_path="path/to/key.pem")
        self.token_requester = OutOfSessionTokenRequester(adapter=self.adapter, sender=self.sender)

        self.agent_identity = "agent-app"
        self.human_identity = {"sub": "user:alice@example.com"}

    def test_out_of_session_token_success(self):
        """Verify that out-of-session token request includes both sub and act"""
        token_response = self.token_requester.request_token(
            agent_identity=self.agent_identity,
            human_identity=self.human_identity
        )
        self.assertIn("access_token", token_response)
        self.assertIn("act", token_response)
        self.assertEqual(token_response["act"], self.human_identity)

if __name__ == "__main__":
    unittest.main()
