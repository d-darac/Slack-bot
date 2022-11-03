import os
from dotenv import load_dotenv, find_dotenv
from slack_sdk import WebClient, signature, errors as slack_errors

load_dotenv(find_dotenv())

slack_client = WebClient(os.environ["BOT_USER_TOKEN"])
slack_signature_verifier = signature.SignatureVerifier(os.environ["SIGNING_SECRET"])
