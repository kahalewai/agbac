import logging
import sys
from adapters.okta_adapter import OktaAdapter
from sender.hybrid_sender import HybridSender
from phase1.token_request_in_session import InSessionTokenRequester
from phase2.token_request_out_of_session import OutOfSessionTokenRequester

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def check_agent_act(agent_type, adapter, hybrid_sender=None):
    """
    Checks if the agent token includes the human 'act' data.

    Parameters:
        agent_type (str): 'in_session' or 'out_of_session'
        adapter (BaseAdapter): IAM adapter (Okta, Auth0, Keycloak, EntraID)
        hybrid_sender (HybridSender, optional): Required for out-of-session

    Returns:
        bool: True if 'act' is present in token, False otherwise
    """
    try:
        # Sample identities for testing
        agent_identity = "test-agent-app"
        human_identity = {"sub": "user:alice@example.com"}

        if agent_type == "in_session":
            logging.info("Testing in-session agent token for human 'act' data...")
            requester = InSessionTokenRequester(adapter=adapter)
            token = requester.request_token(agent_identity, human_identity)

        elif agent_type == "out_of_session":
            if hybrid_sender is None:
                logging.error("Hybrid sender required for out-of-session test.")
                return False
            logging.info("Testing out-of-session agent token for human 'act' data...")
            requester = OutOfSessionTokenRequester(adapter=adapter, sender=hybrid_sender)
            token = requester.request_token(agent_identity, human_identity)

        else:
            logging.error("Invalid agent type. Must be 'in_session' or 'out_of_session'.")
            return False

        # Check for 'act' field in token
        if "act" in token and token["act"] == human_identity:
            logging.info("SUCCESS: Human 'act' data detected in token!")
            return True
        else:
            logging.warning("FAILURE: Human 'act' data NOT present in token.")
            return False

    except Exception as e:
        logging.exception(f"Error checking agent token: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    agent_type = sys.argv[1] if len(sys.argv) > 1 else "in_session"
    adapter = OktaAdapter(
        client_id="test-client-id",
        client_secret="test-client-secret",
        token_url="https://okta.example.com/oauth2/default/v1/token"
    )
    hybrid_sender = HybridSender(private_key_path="path/to/private_key.pem")

    result = check_agent_act(agent_type, adapter, hybrid_sender if agent_type == "out_of_session" else None)
    if result:
        logging.info(f"{agent_type} agent correctly includes human 'act' data in token.")
    else:
        logging.error(f"{agent_type} agent does NOT include human 'act' data in token.")
