from requests_oauthlib import OAuth1Session
from requests import get
from algokit_utils import AlgorandClient, AlgoClientConfigs, AlgoClientNetworkConfig
from base64 import b64encode, b64decode
from algosdk.logic import get_application_address
from algosdk.encoding import encode_address
from time import time, sleep
from typing import Any
from yourplace_messages.bot import send_yourplace_post
import json
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
COMMITTEE_MEMBERS = b64encode(b'committee_members').decode()
WEIGHTED_QUROUM_THRESHOLD = b64encode(b'weighted_quorum_threshold').decode()
QUROUM_THRESHOLD = b64encode(b'quorum_threshold').decode()
PROPOSER = b64encode(b'proposer').decode()
REQUESTED_AMOUNT = b64encode(b'requested_amount').decode()
OPEN_TIMESTAMP = b64encode(b'open_timestamp').decode()
DISCUSSION_DURATION = b64encode(b'discussion_duration').decode()
FINALIZED = b64encode(b'finalized').decode()

def get_global_value(globals_: dict, key: str, value_type: str):
    return next((item['value'][value_type] for item in globals_ if item['key'] == key), 0)

def create_proposal_object(globals_: dict[str, Any]) -> dict:
    
    return {
        'vote-opening-timestamp': get_global_value(globals_, VOTE_OPENING_TIMESTAMP, 'uint'),
        'vote-duration': get_global_value(globals_, VOTE_DURATION, 'uint'),
        'title': b64decode(get_global_value(globals_, VOTE_TITLE, 'bytes')).decode(),
        
        "requested-amount": get_global_value(globals_, REQUESTED_AMOUNT, "uint"),
        "approvals": get_global_value(globals_, VOTE_APPROVALS, "uint"),
        "rejections": get_global_value(globals_, VOTE_REJECTIONS, "uint"),
        "nulls": get_global_value(globals_, VOTE_NULLS, "uint"),
        "weighted-quorum-threshold": get_global_value(globals_, WEIGHTED_QUROUM_THRESHOLD, "uint"),
        "quorum-threshold": get_global_value(globals_, QUROUM_THRESHOLD, "uint"),
        "voted-members":  get_global_value(globals_, VOTED_MEMBERS, "uint"),
        "committee-members": get_global_value(globals_, COMMITTEE_MEMBERS, "uint"),
        'proposer': encode_address(b64decode(get_global_value(globals_, PROPOSER, 'bytes'))),

        'open-timestamp': get_global_value(globals_, OPEN_TIMESTAMP, 'uint'),
        'discussion-duration': get_global_value(globals_, DISCUSSION_DURATION, 'uint'),
        'finalized': get_global_value(globals_, FINALIZED, 'uint')
    }

def threshold_emoji(percent: float, threshold: float) -> str:
    return "✅" if percent > threshold else "❌"

def get_proposals_tweet_text(app_id: int, proposal: dict) -> str:
    proposal_text = ""
    current_time = time()

    vote_end_time = proposal['vote-opening-timestamp'] + proposal['vote-duration']
    discussion_end_time = proposal['open-timestamp'] + proposal['discussion-duration']
    if current_time < vote_end_time or proposal['vote-opening-timestamp'] == 0:
        if proposal['finalized'] != 1:
            
            vote_time_remaining = vote_end_time - current_time
            voting_days = int(vote_time_remaining // 86400)
            voting_hours = int((vote_time_remaining % 86400) // 3600)
            voting_minutes = int((vote_time_remaining % 3600) // 60)

            discussion_time_remaining = discussion_end_time - current_time
            discussion_days = int(discussion_time_remaining // 86400)
            discussion_hours = int((discussion_time_remaining % 86400) // 3600)
            discussion_minutes = int((discussion_time_remaining % 3600) // 60)

            if proposal['vote-opening-timestamp'] == 0 and discussion_days < -30:
                return ""

            requested_amount = proposal['requested-amount']
            approvals = proposal['approvals']
            rejections = proposal['rejections']
            nulls = proposal['nulls']
            vote_quorum = proposal['weighted-quorum-threshold']
            voter_quorum = proposal['quorum-threshold']
            voted_members = proposal['voted-members']
            proposer = proposal['proposer']
            total_members = proposal['committee-members']
            total_votes = approvals + rejections + nulls

            voter_threshold_percent = (voted_members / voter_quorum) * 100 if voter_quorum else 0
            vote_threshold_percent = (total_votes / vote_quorum) * 100 if vote_quorum else 0
            approval_percent = (approvals / total_votes) * 100 if total_votes else 0

            voter_threshold_emoji = threshold_emoji(voter_threshold_percent, 100)
            vote_threshold_emoji = threshold_emoji(vote_threshold_percent, 100)
            approval_emoji = threshold_emoji(approval_percent, 50)
            timer_emoji = "⏳ " if vote_time_remaining < 2 * 86400 else ""
            proposer_nfd = proposal.get('nfd', None)
            facepalm = "🤦"

            proposal_text += f"Proposal #{app_id}\n"
            proposal_text += f"{proposal['title']}\n"
            proposal_text += f"Requesting {(requested_amount / 1_000_000):,.0f} Algo\n"
            if current_time < vote_time_remaining and proposal['vote-opening-timestamp'] != 0:
                proposal_text += f"{timer_emoji}Voting Ends In: {voting_days}d {voting_hours}h {voting_minutes}m\n"
                proposal_text += f"{total_members - voted_members} xGovs have not voted {facepalm}\n"
                proposal_text += f"Voter Threshold: {voter_threshold_percent:,.2f}% {voter_threshold_emoji}\n"
                proposal_text += f"Vote Threshold: {vote_threshold_percent:,.2f}% {vote_threshold_emoji}\n"
                proposal_text += f"Approval: {approval_percent:,.2f}% In Favor {approval_emoji}\n"
                proposal_text += f"xGovs Voted: {voted_members} / {voter_quorum}\n"
                proposal_text += f"Yes: {approvals:,.0f} | No: {rejections:,.0f} | Null: {nulls:,.0f}\n"
                proposal_text += f"Votes Cast: {total_votes:,.0f} / {vote_quorum:,.0f}\n"
            else:
                if proposal['vote-opening-timestamp'] == 0 and current_time >= discussion_end_time:
                    proposal_text += "Discussion has ended, but voting has not started yet\n"
                else:
                    proposal_text += f"{timer_emoji}Discussion Ends In: {discussion_days}d {discussion_hours}h {discussion_minutes}m\n"
            proposal_app_boxes = algorand.app.get_box_names(app_id)
            forum_link = 'Forum Link Not Provided in Proposal'
            if len(proposal_app_boxes) > 0:
                proposal_box_info = algorand.app.get_box_value(app_id, box_name=b'M')
                json_proposal_box_info = json.loads(proposal_box_info)
                if 'forumLink' in json_proposal_box_info:
                    forum_link = json_proposal_box_info['forumLink']
            proposal_text += f"Created by: {proposer_nfd if proposer_nfd else proposer}\n"
            proposal_text += f"Forum Link: {forum_link}\n"
            proposal_text += f"Voting Link: https://xgov.algorand.co/proposal/{app_id}\n\n"

    return proposal_text


def create_tweet_content(algorand: AlgorandClient) -> str:
    created_applications: list[dict[Any, Any]] = algorand.account.get_information(XGOV_APP_ADDRESS).created_apps
    proposals: dict[int, dict[Any, Any]] = {}
    tweet_text = "ACTIVE PROPOSALS DAILY SUMMARY:\n\n"

    for app in created_applications:
        app_id = app['id']
        globals_ = app['params']['global-state']
        proposals[app_id] = create_proposal_object(globals_)


    current_time = time()

    ordered_proposals = sorted(
        proposals.items(),
        key=lambda item: (
            float("inf")
            if item[1]['vote-opening-timestamp'] == 0
            and current_time >= (item[1]['open-timestamp'] + item[1]['discussion-duration'])
            else (
                (item[1]['vote-opening-timestamp'] + item[1]['vote-duration']) - current_time
                if item[1]['vote-opening-timestamp'] != 0
                else (item[1]['open-timestamp'] + item[1]['discussion-duration']) - current_time
            )
        )
    )

    # addresses = [prop['proposer'] for prop in ordered_proposals]
    # nfds = get_nfds(addresses)
    for app_id, proposal in ordered_proposals:
        tweet_text += get_proposals_tweet_text(app_id, proposal)

    return tweet_text

def test_tweet(tweet_text: str):
    tweet_text = tweet_text + '#Algofam #Algorand' + '\nCreated and Hosted by @atsoc93'
    send_yourplace_post(tweet_text)
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

# def get_nfds(addresses: list[str]) -> list[str]:
#     base_nfd_v2_address_url = 'https://api.nf.domains/nfd/v2/address'
#     for address in addresses:
#         base_nfd_v2_address_url += f'?address={address}&'
#     base_nfd_v2_address_url += '&limit=1'

#     response = get(url=base_nfd_v2_address_url)
#     print(response)

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
