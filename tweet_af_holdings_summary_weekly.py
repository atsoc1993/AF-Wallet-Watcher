from constants import (
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET,
    ALGO_ASSET_ID,
    ALGORAND_CONFIG,
    CONSUMER_KEY,
    CONSUMER_SECRET,
    FEE_SINK_ADDRESS,
    FOUNDATION_MARKET_WALLETS,
    HTTP_CREATED,
    INDEXER_PAGE_LIMIT,
    MICROALGOS_PER_ALGO,
    MIN_WEEKLY_WALLET_BALANCE_ALGO,
    POOL_ASSET_1_ID_SLICE,
    POOL_ASSET_2_ID_SLICE,
    POOL_LOGICSIG_TEMPLATE,
    POOL_VALIDATOR_APP_ID_SLICE,
    SOCIAL_POST_FOOTER,
    TINYMAN_ROUTER_APP_ID,
    TWITTER_API_URL,
    UINT64_BYTE_LENGTH,
    USDC_ASSET_ID,
    WEEKLY_ROUND_TIME_WINDOW,
    WEEKLY_SUMMARY_INTERVAL_SECONDS,
)
from requests_oauthlib import OAuth1Session
from algokit_utils import AlgorandClient
from algosdk.transaction import LogicSigAccount
from base64 import b64decode
from yourplace_messages.bot import send_yourplace_post
import time




def getAlgoPrice(algorand: AlgorandClient):
    def get_pool_logicsig(
        validator_app_id: int, asset_a_id: int, asset_b_id: int
    ) -> LogicSigAccount:
        
        assets = [asset_a_id, asset_b_id]
        asset_1_id = max(assets)
        asset_2_id = min(assets)

        program = bytearray(b64decode(POOL_LOGICSIG_TEMPLATE))
        program[POOL_VALIDATOR_APP_ID_SLICE] = validator_app_id.to_bytes(
            UINT64_BYTE_LENGTH,
            "big",
        )
        program[POOL_ASSET_1_ID_SLICE] = asset_1_id.to_bytes(
            UINT64_BYTE_LENGTH,
            "big",
        )
        program[POOL_ASSET_2_ID_SLICE] = asset_2_id.to_bytes(
            UINT64_BYTE_LENGTH,
            "big",
        )
        
        return LogicSigAccount(program)


    logic_sig_account = get_pool_logicsig(
        TINYMAN_ROUTER_APP_ID,
        USDC_ASSET_ID,
        ALGO_ASSET_ID,
    )
    pool_address = logic_sig_account.address()

    local_states = algorand.app.get_local_state(
        address=pool_address,
        app_id=TINYMAN_ROUTER_APP_ID,
    )
    asset_1_reserves = local_states.get('asset_1_reserves').value
    asset_2_reserves = local_states.get('asset_2_reserves').value

    algorand_price = asset_1_reserves / asset_2_reserves

    return algorand_price

def balance_summary_tweet(algorand: AlgorandClient):
    algorand_price = getAlgoPrice(algorand=algorand)
    balances_text = ''
    total_value = 0
    decimals_scale = MICROALGOS_PER_ALGO
    balances = []
    total_algo = 0.0
    total_value = 0

    for addr, label in FOUNDATION_MARKET_WALLETS.items():
        info = algorand.account.get_information(addr)
        algo_balance = info.amount.micro_algo / decimals_scale
        dollar_value = algo_balance * algorand_price
        online = True if info.participation else False
        incentives = True if info.incentive_eligible else False
        balances.append((algo_balance, dollar_value, label, online, incentives))
        total_algo += algo_balance
        total_value += dollar_value

    balances.sort(key=lambda x: x[0], reverse=True)

    current_round = algorand.client.algod.status()['last-round']
    indexer = AlgorandClient.mainnet().client.indexer
    wallets_not_included_due_to_low_balance = 0
    balances_text = ""
    for algo_balance, dollar_value, label, online, incentives in balances:

        incentives_string = ''
        online_string = ''

        rewards_earned = 0
        if incentives:
            next_page = None
            next_page_available = True

            for address in FOUNDATION_MARKET_WALLETS.keys():
                if FOUNDATION_MARKET_WALLETS[address] == label:
                    account = address

            while next_page_available:
                payout_txs = indexer.search_transactions_by_address(
                    address=account,
                    txn_type='pay',
                    min_round=current_round - WEEKLY_ROUND_TIME_WINDOW,
                    max_round=current_round,
                    next_page=next_page,
                    limit=INDEXER_PAGE_LIMIT
                )

                for tx in payout_txs.get('transactions', []):
                    pay_tx = tx.get('payment-transaction', {})
                    sender = tx.get('sender', '')
                    receiver = pay_tx.get('receiver', '')
                    amount = pay_tx.get('amount')
                    if sender == FEE_SINK_ADDRESS and receiver == account:
                        rewards_earned += amount 


                next_page = payout_txs.get('next-token', None)
                if not next_page:
                    next_page_available=False

            incentives_string = f'\nOpted Into Incentives: Yes\nRewards Earned (last 7 days): {(rewards_earned / decimals_scale):,.2f}A | ${((rewards_earned / decimals_scale)* algorand_price):,.2f}'
        if online:
            online_string = f'Online: Yes'

        # Let's not affect any global value changes in total Algo or other metrics for accuracy, but not include arbitrary info in the tweet
        if algo_balance < MIN_WEEKLY_WALLET_BALANCE_ALGO:
            wallets_not_included_due_to_low_balance += 1
            continue
        else:
            balances_text += f"{label} \nValue: {algo_balance:,.2f}A | ${dollar_value:,.2f}\n{online_string}{incentives_string}\n\n"

    total_value_text = (
        f"Foundation Wallet Weekly Summary: \n\n"
        f"Total Remaining Foundation Funds: {total_algo:,.2f}A | ${total_value:,.2f}\n\n"
        f"{wallets_not_included_due_to_low_balance} were not included due to less than "
        f"{MIN_WEEKLY_WALLET_BALANCE_ALGO} Algo balance\n\n"
    )
    tweet_text = total_value_text + balances_text
    tweet_text = f"{tweet_text}{SOCIAL_POST_FOOTER}"
    send_yourplace_post(tweet_text)
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


while True:
    try:
        try:
            algorand = AlgorandClient(config=ALGORAND_CONFIG)
            algorand.client.algod.status()
        except:
            algorand = AlgorandClient.mainnet()

        balance_summary_tweet(algorand=algorand)
    except Exception as e:
        print(e)
    time.sleep(WEEKLY_SUMMARY_INTERVAL_SECONDS)
