from constants import (
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET,
    ALGORAND_CONFIG,
    APPROVAL_PERCENT_THRESHOLD,
    COMMITTEE_MEMBERS,
    CONSUMER_KEY,
    CONSUMER_SECRET,
    DISCUSSION_DURATION,
    DISCUSSION_STALE_DAYS,
    FACEPALM_EMOJI,
    FINALIZED,
    FINALIZED_VALUE,
    HTTP_CREATED,
    MICROALGOS_PER_ALGO,
    MISSING_FORUM_LINK,
    OPEN_TIMESTAMP,
    PERCENT_MULTIPLIER,
    PROPOSAL_METADATA_BOX_NAME,
    PROPOSAL_SUMMARY_INTERVAL_SECONDS,
    PROPOSER,
    QUORUM_PERCENT_THRESHOLD,
    QUROUM_THRESHOLD,
    REQUESTED_AMOUNT,
    SECONDS_PER_DAY,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    SOCIAL_POST_FOOTER,
    THRESHOLD_MET_EMOJI,
    THRESHOLD_NOT_MET_EMOJI,
    TIMER_EMOJI,
    VOTE_APPROVALS,
    VOTE_DURATION,
    VOTE_NULLS,
    VOTE_OPENING_TIMESTAMP,
    VOTE_REJECTIONS,
    VOTE_TITLE,
    VOTE_TIMER_WARNING_DAYS,
    VOTED_MEMBERS,
    WEIGHTED_QUROUM_THRESHOLD,
    X_API_URL,
    XGOV_APP_ADDRESS,
    XGOV_PROPOSAL_URL,
)
from requests_oauthlib import OAuth1Session
from requests import get
from algokit_utils import AlgorandClient
from base64 import b64decode
from algosdk.encoding import encode_address
from time import time, sleep
from typing import Any
from yourplace_messages.bot import send_yourplace_post
import json

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
    return THRESHOLD_MET_EMOJI if percent >= threshold else THRESHOLD_NOT_MET_EMOJI

def get_proposals_tweet_text(app_id: int, proposal: dict) -> str:
    proposal_text = ""
    current_time = time()

    vote_end_time = proposal['vote-opening-timestamp'] + proposal['vote-duration']
    discussion_end_time = proposal['open-timestamp'] + proposal['discussion-duration']
    if current_time < vote_end_time or proposal['vote-opening-timestamp'] == 0:
        if proposal['finalized'] != FINALIZED_VALUE:
            
            vote_time_remaining = vote_end_time - current_time
            voting_days = int(vote_time_remaining // SECONDS_PER_DAY)
            voting_hours = int((vote_time_remaining % SECONDS_PER_DAY) // SECONDS_PER_HOUR)
            voting_minutes = int((vote_time_remaining % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE)

            discussion_time_remaining = discussion_end_time - current_time
            discussion_days = int(discussion_time_remaining // SECONDS_PER_DAY)
            discussion_hours = int((discussion_time_remaining % SECONDS_PER_DAY) // SECONDS_PER_HOUR)
            discussion_minutes = int((discussion_time_remaining % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE)

            if proposal['vote-opening-timestamp'] == 0 and discussion_days < -DISCUSSION_STALE_DAYS:
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

            voter_threshold_percent = (voted_members / voter_quorum) * PERCENT_MULTIPLIER if voter_quorum else 0
            vote_threshold_percent = (total_votes / vote_quorum) * PERCENT_MULTIPLIER if vote_quorum else 0
            approval_percent = (approvals / (approvals + rejections)) * PERCENT_MULTIPLIER if total_votes else 0

            voter_threshold_emoji = threshold_emoji(voter_threshold_percent, QUORUM_PERCENT_THRESHOLD)
            vote_threshold_emoji = threshold_emoji(vote_threshold_percent, QUORUM_PERCENT_THRESHOLD)
            approval_emoji = threshold_emoji(approval_percent, APPROVAL_PERCENT_THRESHOLD)
            timer_emoji = (
                TIMER_EMOJI
                if vote_time_remaining < VOTE_TIMER_WARNING_DAYS * SECONDS_PER_DAY
                else ""
            )
            proposer_nfd = proposal.get('nfd', None)
            facepalm = FACEPALM_EMOJI

            proposal_text += f"Proposal #{app_id}\n"
            proposal_text += f"{proposal['title']}\n"
            proposal_text += f"Requesting {(requested_amount / MICROALGOS_PER_ALGO):,.0f} Algo\n"
            if current_time < vote_end_time and proposal['vote-opening-timestamp'] != 0:
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
            forum_link = MISSING_FORUM_LINK
            if len(proposal_app_boxes) > 0:
                proposal_box_info = algorand.app.get_box_value(
                    app_id,
                    box_name=PROPOSAL_METADATA_BOX_NAME,
                )
                json_proposal_box_info = json.loads(proposal_box_info)
                if 'forumLink' in json_proposal_box_info:
                    forum_link = json_proposal_box_info['forumLink']
            proposal_text += f"Created by: {proposer_nfd if proposer_nfd else proposer}\n"
            proposal_text += f"Forum Link: {forum_link}\n"
            proposal_text += f"Voting Link: {XGOV_PROPOSAL_URL.format(app_id=app_id)}\n\n"

    return proposal_text


def create_tweet_content(algorand: AlgorandClient) -> str:
    created_applications: list[dict[Any, Any]] = algorand.account.get_information(XGOV_APP_ADDRESS).created_apps
    proposals: dict[int, dict[Any, Any]] = {}
    tweet_text = "ACTIVE PROPOSALS SUMMARY (Every Other Day):\n\n"

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
    tweet_text = f"{tweet_text}{SOCIAL_POST_FOOTER}"
    send_yourplace_post(tweet_text)
    payload = {"text": tweet_text}
    oauth   = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )
    resp = oauth.post(X_API_URL, json=payload)
    if resp.status_code != HTTP_CREATED:
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
            algorand = AlgorandClient(config=ALGORAND_CONFIG)
            algorand.client.algod.status()
        except:
            algorand = AlgorandClient.mainnet()
        tweet_text = create_tweet_content(algorand=algorand)

        test_tweet(tweet_text)  
    except Exception as e:
        print(e)

    sleep(PROPOSAL_SUMMARY_INTERVAL_SECONDS)
