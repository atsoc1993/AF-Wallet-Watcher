from constants import (
    ALGORAND_CONFIG,
    ASSIGNED_MEMBERS,
    PROPOSAL_WATCH_INTERVAL_SECONDS,
    PROPOSER,
    QUROUM_THRESHOLD,
    VOTE_APPROVALS,
    VOTE_DURATION,
    VOTE_NULLS,
    VOTE_OPENING_TIMESTAMP,
    VOTE_REJECTIONS,
    VOTE_TITLE,
    VOTED_MEMBERS,
    WEIGHTED_QUROUM_THRESHOLD,
    X_API_URL,
    XGOV_APP_ADDRESS,
    XGOV_PROPOSAL_URL,
)
from algokit_utils import AlgorandClient
from base64 import b64decode
from time import sleep
from typing import Any
from algosdk.encoding import encode_address
from tweet_helper import publish_tweet

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

    proposal_text += f"{XGOV_PROPOSAL_URL.format(app_id=app_id)}\n"

    return proposal_text


def create_tweet_content(app: dict[str, Any]) -> str:
    app_id = app["id"]
    globals_ = app["params"]["global-state"]
    proposal_object = create_proposal_object(globals_)
    return get_proposals_tweet_text(app_id, proposal_object)


seen_app_ids: set[int] = set()
initial_run = True

while True:
    try:
        try:
            algorand = AlgorandClient(config=ALGORAND_CONFIG)
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
                        publish_tweet(tweet_text, X_API_URL)

                seen_app_ids = current_ids
                
    except Exception as e:
        print(e)

    sleep(PROPOSAL_WATCH_INTERVAL_SECONDS)
