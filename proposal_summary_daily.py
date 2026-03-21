from requests_oauthlib import OAuth1Session
from algokit_utils import AlgorandClient, AlgoClientConfigs, AlgoClientNetworkConfig
from base64 import b64encode, b64decode
from algosdk.logic import get_application_address
from algosdk.encoding import encode_address
from time import time, sleep
from typing import Any
from dotenv import load_dotenv
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

VOTE_OPENING_TIMESTAMP = b64encode(b'vote_opening_timestamp').decode()
VOTE_DURATION = b64encode(b'voting_duration').decode()
VOTE_TITLE = b64encode(b'title').decode()
VOTE_APPROVALS = b64encode(b'approvals').decode()
VOTE_REJECTIONS = b64encode(b'rejections').decode()
VOTE_NULLS = b64encode(b'nulls').decode()
VOTED_MEMBERS = b64encode(b'voted_members').decode()
ASSIGNED_MEMBERS = b64encode(b'assigned_members').decode()
WEIGHTED_QUROUM_THRESHOLD = b64encode(b'weighted_quorum_threshold').decode()
QUROUM_THRESHOLD = b64encode(b'quorum_threshold').decode()
PROPOSER = b64encode(b'proposer').decode()

def get_global_value(globals_: dict, key: str, value_type: 'str'):
    return next((item['value'][value_type] for item in globals_ if item['key'] == key), None)

def create_proposal_object(globals_: dict[str, Any]) -> dict:
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

def get_proposals_tweet_text(app_id: int, proposal: dict) -> str:
    proposal_text = ""
    current_time = time()

    if proposal['vote-opening-timestamp'] and proposal['vote-duration']:
        if current_time < proposal['vote-duration'] + proposal['vote-opening-timestamp']:
            remaining = proposal['vote-duration'] + proposal['vote-opening-timestamp'] - current_time
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            minutes = int((remaining % 3600) // 60)

            approvals = proposal['approvals']
            rejections = proposal['rejections']
            nulls = proposal['nulls']
            vote_quorum = proposal['weighted-quorum-threshold']
            voter_quorum = proposal['quorum-threshold']
            voted_members = proposal['voted-members']
            proposer = proposal['proposer']
            assigned_members = proposal['assigned-members']
            total_votes = approvals + rejections + nulls

            proposal_text += f"Proposal #{app_id}\n"
            proposal_text += f"{proposal['title']}\n"
            proposal_text += f"Ends In: {days}d {hours}h {minutes}m\n"
            proposal_text += f"Yes: {approvals:,.0f} | No: {rejections:,.0f} | Null: {nulls:,.0f}\n"
            proposal_text += f"Votes Cast: {total_votes:,.0f} / {vote_quorum:,.0f}\n"
            proposal_text += f"Vote Threshold: {((total_votes / vote_quorum) * 100):,.2f}%\n"
            proposal_text += f"Voter Threshold: {((voted_members / voter_quorum) * 100):,.2f}%\n"
            proposal_text += f"xGovs Voted: {voted_members} / {assigned_members}\n"
            proposal_text += f"Approval: {((approvals / total_votes) * 100):,.2f}% In Favor\n"
            proposal_text += f"Created by: {proposer}\n"
            proposal_text += f"https://xgov.algorand.co/proposal/{app_id}\n\n"

    return proposal_text

def create_tweet_content(algorand: AlgorandClient) -> str:
    created_applications: list[dict[Any, Any]] = algorand.account.get_information(XGOV_APP_ADDRESS).created_apps
    proposals: dict[Any, Any] = {}
    tweet_text = "ACTIVE PROPOSALS SUMMARY:\n\n"
    for app in created_applications: # All created applications are proposals
        app_id = app['id']
        globals_ = app['params']['global-state']
        proposals[app_id] = create_proposal_object(globals_)
            
    for proposal in proposals:
        tweet_text += get_proposals_tweet_text(proposal, proposals[proposal])


    return tweet_text

def test_tweet(tweet_text: str):
    payload = {"text": tweet_text}
    oauth   = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )
    resp = oauth.post("https://api.x.com/2/tweets", json=payload)
    if resp.status_code != 201:
        raise RuntimeError(f"Twitter error {resp.status_code}: {resp.text}")

    print("Tweeted:", tweet_text)

while True:
    try:
        try:
            algorand = AlgorandClient(config=CONFIG)
            algorand.client.algod.status()
        except:
            algorand = AlgorandClient.mainnet()
        tweet_text = create_tweet_content(algorand=algorand)

        test_tweet(tweet_text)  
    except Exception as e:
        print(e)
        
    sleep(86_400)