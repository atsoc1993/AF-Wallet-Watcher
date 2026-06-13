from constants import (
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET,
    ACTIVITY_POLL_INTERVAL_SECONDS,
    ALGO_ASSET_ID,
    ALGO_DECIMALS,
    ALPHA_ARCADE_FEE_FAUCET_LABEL,
    ALPHA_ARCADE_ADDRESS,
    ALGORAND_CONFIG,
    ASSET_TRANSFER_TRANSACTION_TYPE,
    CONSUMER_KEY,
    CONSUMER_SECRET,
    DEFLY_DROPS_ASSET_ID,
    DECIMAL_BASE,
    FOUNDATION_MARKET_WALLETS,
    HTTP_CREATED,
    KEY_REGISTRATION_TRANSACTION_TYPE,
    MARKET_OPERATIONS_LABEL_FRAGMENT,
    MICROALGOS_PER_ALGO,
    MIN_TRACKED_PAYMENT_MICROALGOS,
    PAYMENT_TRANSACTION_TYPE,
    PERA_TRANSACTION_URL,
    SOCIAL_POST_FOOTER,
    TWITTER_API_URL,
)
from requests_oauthlib import OAuth1Session
from algokit_utils import AlgorandClient
from typing import cast, Any
from yourplace_messages.bot import send_yourplace_post
from time import sleep


def tweet(
    tx_id: str, sender: str,
    receiver: str, asset: int,
    amount: int, tx_type: str,
    unknown_activity: bool, algorand: AlgorandClient
):

    sender_label = FOUNDATION_MARKET_WALLETS.get(sender)
    receiver_label = FOUNDATION_MARKET_WALLETS.get(receiver)

    sender_is_af = sender_label is not None
    receiver_is_af = (
        receiver_label is not None
        and receiver_label != ALPHA_ARCADE_FEE_FAUCET_LABEL
    )

    sender_is_mops = (
        sender_is_af
        and sender_label
        and MARKET_OPERATIONS_LABEL_FRAGMENT in sender_label
    )
    receiver_is_mops = (
        receiver_is_af
        and receiver_label
        and MARKET_OPERATIONS_LABEL_FRAGMENT in receiver_label
    )

    if asset == ALGO_ASSET_ID:
        asset_name, decimals = "Algo", ALGO_DECIMALS
    else:
        info = algorand.asset.get_by_id(asset)
        asset_name = info.asset_name if info.asset_name != None else ''
        decimals = info.decimals

    amt_fmt = f"{amount / DECIMAL_BASE**decimals:,.2f}"

    if asset == DEFLY_DROPS_ASSET_ID: #ignore defly related drops
        return

    if sender == ALPHA_ARCADE_ADDRESS and not receiver_is_af: # If Alpha Arcade & not a foundation wallet
        return # Not essential to be processing these sadly, sorry Alpha Arcade <3

    if unknown_activity: # Not crawling app calls, too ambiguous
        tweet_text = (
            "Foundation Wallet Activity:\n"
            f"{sender_label or sender} ({sender}) performed an uncrawled application call or key registration transaction."
        )

    elif tx_type == KEY_REGISTRATION_TRANSACTION_TYPE:
        algo_balance = cast(dict[str, Any], algorand.client.algod.account_info(sender)).get('amount', 0) / MICROALGOS_PER_ALGO
        tweet_text = f"{sender_label} removed {algo_balance:,.0f} Algorand from online stake! =)"

    elif sender == receiver and asset != ALGO_ASSET_ID:
        tweet_text = f'{sender_label} opted into {asset_name}'

    elif sender_is_mops and not receiver_is_mops:
        recv_part = receiver_label or receiver
        tweet_text = f"{sender_label} (Structured-Selling Wallet) transferred {amt_fmt} {asset_name} through {recv_part}."

    elif sender_is_af and receiver_is_af:
        tweet_text = f"{sender_label} transferred {amt_fmt} {asset_name} to {receiver_label}."

    elif (not sender_is_af) and receiver_is_af:
        tweet_text = f"Unknown address {sender} sent {amt_fmt} {asset_name} to {receiver_label}."

    else:
        return

    tweet_text = (
        f"{tweet_text}\nPera Link:\n"
        f"{PERA_TRANSACTION_URL.format(tx_id=tx_id)}"
    )
    tweet_text = f"{tweet_text}\n\n{SOCIAL_POST_FOOTER}"

    payload = {"text": tweet_text}

    oauth   = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )
    resp = oauth.post(TWITTER_API_URL, json=payload)
    if resp.status_code != HTTP_CREATED:
        raise RuntimeError(f"Twitter error {resp.status_code}: {resp.text}")

    print("Tweeted:", tweet_text)
    send_yourplace_post(tweet_text)
    sleep(ACTIVITY_POLL_INTERVAL_SECONDS)

previous_round = 0

while True:
    try:
        algorand = AlgorandClient(config=ALGORAND_CONFIG)
        algorand.client.algod.status()
    except:
        algorand = AlgorandClient.mainnet()
    try:
        next_round = cast(dict[str, Any], algorand.client.algod.status())['last-round']
        if next_round > previous_round:

            block_txs = cast(dict[str, Any], algorand.client.algod.get_block_txids(next_round))['blockTxids']
            block_info = cast(dict[str, Any], algorand.client.algod.block_info(next_round))['block']['txns']
            tx_and_info: list[tuple[str, dict[str, Any]]] = [(id, tx['txn']) for id, tx in zip(block_txs, block_info)] # type: ignore
            
            for tx_id, txn_info in tx_and_info:
                found_AF_tx = False
                sender = txn_info.get('snd', None)
                type = txn_info['type']
                receiver = None
                asset = ALGO_ASSET_ID
                amount = None
                unknown_activity = False

                if type == PAYMENT_TRANSACTION_TYPE:
                    receiver = txn_info.get('rcv', sender)
                    amount = txn_info.get('amt', 0)
                    unknown_activity = False
                    if (sender in FOUNDATION_MARKET_WALLETS or receiver in FOUNDATION_MARKET_WALLETS) \
                        and amount > MIN_TRACKED_PAYMENT_MICROALGOS:
                        found_AF_tx = True

                elif type == ASSET_TRANSFER_TRANSACTION_TYPE:
                    receiver = txn_info['arcv']
                    asset = txn_info['xaid']
                    amount = txn_info.get('aamt', 0)
                    unknown_activity = False
                    if (sender in FOUNDATION_MARKET_WALLETS or receiver in FOUNDATION_MARKET_WALLETS) and sender != ALPHA_ARCADE_ADDRESS:
                        found_AF_tx = True

                else:
                    unknown_activity = True
                    receiver = ''
                    amount = 0
                    if sender in FOUNDATION_MARKET_WALLETS and sender != ALPHA_ARCADE_ADDRESS:
                        found_AF_tx = True

                if found_AF_tx:
                    tweet(
                        tx_id=tx_id,
                        sender=sender,
                        receiver=receiver,
                        asset=asset,
                        amount=amount,
                        unknown_activity=unknown_activity,
                        tx_type=type,
                        algorand=algorand
                    )

            previous_round = next_round

    except Exception as e:
        algorand = AlgorandClient(config=ALGORAND_CONFIG)
        print(e)

    sleep(ACTIVITY_POLL_INTERVAL_SECONDS)
