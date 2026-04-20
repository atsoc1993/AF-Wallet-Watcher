from requests_oauthlib import OAuth1Session
from algokit_utils import AlgorandClient, AlgoClientConfigs, AlgoClientNetworkConfig
from base64 import b64encode, b64decode
from algosdk.logic import get_application_address
from time import sleep
from typing import Any
from dotenv import load_dotenv
from algosdk.encoding import encode_address
from yourplace_messages.bot import send_yourplace_post
import os

load_dotenv()

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_SECRET")

NODE_TOKEN = os.getenv('ALGOD_TOKEN')
NODE_PORT = os.getenv('PORT')

CONFIG = AlgoClientConfigs(
    algod_config=AlgoClientNetworkConfig(server='http://localhost', port=NODE_PORT, token=NODE_TOKEN),
    indexer_config=None,
    kmd_config=None,
)

XGOV_REGISTRY_APP_ID: int = 3147789458
XGOV_APP_ADDRESS = get_application_address(XGOV_REGISTRY_APP_ID)

VOTE_OPENING_TIMESTAMP = b64encode(b"vote_opening_timestamp").decode()
VOTE_DURATION = b64encode(b"voting_duration").decode()
VOTE_TITLE = b64encode(b"title").decode()
VOTE_APPROVALS = b64encode(b"approvals").decode()
VOTE_REJECTIONS = b64encode(b"rejections").decode()
VOTE_NULLS = b64encode(b"nulls").decode()
VOTED_MEMBERS = b64encode(b"voted_members").decode()
ASSIGNED_MEMBERS = b64encode(b"assigned_members").decode()
WEIGHTED_QUROUM_THRESHOLD = b64encode(b"weighted_quorum_threshold").decode()
QUROUM_THRESHOLD = b64encode(b"quorum_threshold").decode()
PROPOSER = b64encode(b'proposer').decode()

def get_global_value(globals_: list[dict[str, Any]], key: str, value_type: str):
    return next((item["value"][value_type] for item in globals_ if item["key"] == key), None)

def create_proposal_object(globals_: list[dict[str, Any]]) -> dict[str, Any]:

    return {
        'vote-opening-timestamp': get_global_value(globals_, VOTE_OPENING_TIMESTAMP, 'uint'),
        'vote-duration': get_global_value(globals_, VOTE_DURATION, 'uint'),
        'title': b64decode(get_global_value(globals_, VOTE_TITLE, 'bytes')).decode(),
        "approvals": get_global_value(globals_, VOTE_APPROVALS, "uint"),
        "rejections": get_global_value(globals_, VOTE_REJECTIONS, "uint"),
        "nulls": get_global_value(globals_, VOTE_NULLS, "uint"),
        "weighted-quorum-threshold": get_global_value(globals_, WEIGHTED_QUROUM_THRESHOLD, "uint"),
        "quorum-threshold": get_global_value(globals_, QUROUM_THRESHOLD, "uint"),
        "voted-members": get_global_value(globals_, VOTED_MEMBERS, "uint"),
        "assigned-members": get_global_value(globals_, ASSIGNED_MEMBERS, "uint"),
        'proposer': encode_address(b64decode(get_global_value(globals_, PROPOSER, 'bytes')))
    }


def get_proposals_tweet_text(app_id: int, proposal: dict[str, Any]) -> str:
    proposal_text = ""
    proposal_text += "====NEW PROPOSAL====\n\n"
    proposal_text += f"Proposal #{app_id}\n"
    proposal_text += f"{proposal['title']}\n"
    proposal_text += f"Created by {proposal['proposer']}\n"

    proposal_text += f"https://xgov.algorand.co/proposal/{app_id}\n"

    return proposal_text


def create_tweet_content(app: dict[str, Any]) -> str:
    app_id = app["id"]
    globals_ = app["params"]["global-state"]
    proposal_object = create_proposal_object(globals_)
    return get_proposals_tweet_text(app_id, proposal_object)


def tweet_new_proposal(tweet_text: str):
    yourplace_text = tweet_text
    tweet_text = tweet_text + '#Algofam #Algorand' + '\nCreated and Hosted by @atsoc93'
    send_yourplace_post(yourplace_text)
    payload = {"text": tweet_text}
    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )
    resp = oauth.post("https://api.x.com/2/tweets", json=payload)
    if resp.status_code != 201:
        raise RuntimeError(f"Twitter error {resp.status_code}: {resp.text}")

    print("Tweeted:", tweet_text)


seen_app_ids: set[int] = set()
initial_run = True

while True:
    try:
        try:
            algorand = AlgorandClient(config=CONFIG)
            algorand.client.algod.status()
        except:
            algorand = AlgorandClient.mainnet()

        created_applications: list[dict[str, Any]] = algorand.account.get_information(XGOV_APP_ADDRESS).created_apps
        current_ids = {app["id"] for app in created_applications if "id" in app}

        if initial_run:
            seen_app_ids = current_ids
            initial_run = False
        else:
            new_apps = [app for app in created_applications if app["id"] not in seen_app_ids]

            if new_apps:
                print("New Proposal Detected")
                for app in new_apps:
                    tweet_text = create_tweet_content(app)

                    if tweet_text:
                        tweet_new_proposal(tweet_text)

                seen_app_ids = current_ids
    except Exception as e:
        print(e)

    sleep(180)
