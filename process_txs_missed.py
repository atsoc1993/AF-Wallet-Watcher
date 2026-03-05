from get_txs_missed import foundation_market_wallets
from typing import cast, Any
from algokit_utils import AlgorandClient
from datetime import datetime
from algosdk.transaction import LogicSigAccount
from base64 import b64decode
import os
import json

def getAlgoPrice():

    algorand = AlgorandClient.mainnet()

    POOL_LOGICSIG_TEMPLATE = (
        "BoAYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgQBbNQA0ADEYEkQxGYEBEkSBAUM="
    )

    def get_pool_logicsig(
        validator_app_id: int, asset_a_id: int, asset_b_id: int
    ) -> LogicSigAccount:
        
        assets = [asset_a_id, asset_b_id]
        asset_1_id = max(assets)
        asset_2_id = min(assets)

        program = bytearray(b64decode(POOL_LOGICSIG_TEMPLATE))
        program[3:11] = validator_app_id.to_bytes(8, "big")
        program[11:19] = asset_1_id.to_bytes(8, "big")
        program[19:27] = asset_2_id.to_bytes(8, "big")
        
        return LogicSigAccount(program)


    #TINYMAN_ROUTER = 148607000 # Testnet router
    TINYMAN_ROUTER = 1002541853 # Mainnet router

    #asset_a = 10458941 # Testnet USDC
    asset_a = 31566704 # Mainnet USDC

    asset_b = 0 # Algo

    logic_sig_account = get_pool_logicsig(TINYMAN_ROUTER, asset_a, asset_b)
    pool_address = logic_sig_account.address()

    local_states = algorand.app.get_local_state(address=pool_address, app_id=TINYMAN_ROUTER)
    asset_1_reserves = local_states.get('asset_1_reserves').value
    asset_2_reserves = local_states.get('asset_2_reserves').value

    algorand_price = asset_1_reserves / asset_2_reserves

    return algorand_price


def write_tweets_to_json(tweet_text: str) -> None:
    with open(f'txs_missed/compiled_tweets.jsonl', 'a') as f:
        f.write(f'{tweet_text}\n\n')

def timestamp_to_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

def write_tweets_to_json_chronologically(timestamps_and_tweets: list[tuple[int, str]]) -> None:
    timestamps_and_tweets.sort(key=lambda x: x[0])
    for timestamp_and_tweet in timestamps_and_tweets:
        tweet = timestamp_and_tweet[1]
        with open(f'txs_missed/chronologically_compiled_tweets.jsonl', 'a') as f:
            f.write(f'{tweet}\n\n')


def add_tweet_text_to_jsonl(tx_id: str, sender: str, receiver: str, asset: int, amount: int, tx_type: str, unknown_activity: bool, timestamp: int):

    global all_tweets_and_timestamps

    global market_ops_algo_out
    global internal_algo_transfer_total
    
    date = timestamp_to_date(timestamp)

    sender_label = foundation_market_wallets.get(sender)
    receiver_label = foundation_market_wallets.get(receiver)

    sender_is_af = sender_label is not None
    receiver_is_af = receiver_label is not None and receiver_label != 'Alpha Arcade USDC Fee Faucet'

    sender_is_mops = sender_is_af and sender_label and "Market Operations" in sender_label 
    receiver_is_mops = receiver_is_af and receiver_label and "Market Operations" in receiver_label 

    if asset == 0:
        asset_name, decimals = "Algo", 6
    else:
        algorand = AlgorandClient.mainnet()
        info = algorand.asset.get_by_id(asset)
        asset_name = info.asset_name if info.asset_name != None else ''
        decimals = info.decimals

    amt_fmt = f"{amount / 10**decimals:,.2f}"

    if asset == 470842789: # ignore defly related drops
        return

    if sender == 'XUIBTKHE7ISNMCLJWXUOOK6X3OCP3GVV3Z4J33PHMYX6XXK3XWN' and not receiver_is_af: # If Alpha Arcade & not a foundation wallet
        return # Not essential to be processing these sadly, sorry Alpha Arcade <3

    tweet_text = date + '\n'
    if unknown_activity: # Not crawling app calls, too ambiguous
        tweet_text += (
            "Foundation Wallet Activity:\n"
            f"{sender_label or sender} ({sender}) performed an uncrawled application call or key registration transaction."
        )

    elif tx_type == 'keyreg':
        algo_balance = cast(dict[str, Any], algorand.client.algod.account_info(sender)).get('amount', 0) / 10**6
        tweet_text += f"{sender_label} removed {algo_balance:,.0f} Algorand from online stake! =)"

    elif sender == receiver:
        tweet_text += f'{sender_label} opted into {asset_name}'

    elif sender_is_mops and not receiver_is_mops:
        recv_part = receiver_label or receiver
        tweet_text += f"{sender_label} (Structured-Selling Wallet) transferred {amt_fmt} {asset_name} through {recv_part}."
        market_ops_algo_out += amount

    elif sender_is_af and receiver_is_af:
        tweet_text += f"{sender_label} transferred {amt_fmt} {asset_name} to {receiver_label}."
        internal_algo_transfer_total += amount

    elif (not sender_is_af) and receiver_is_af:
        tweet_text += f"Unknown address {sender} sent {amt_fmt} {asset_name} to {receiver_label}."

    else:
        return

    tweet_text += f'\nPera Link:\nhttps://explorer.perawallet.app/tx/{tx_id}'
    tweet_text += '\n\n' '#Algofam #Algorand' + '\nCreated and Hosted by @atsoc93'

    all_tweets_and_timestamps.append((timestamp, tweet_text)) # will sort by timestamp later to organize compiled tweet jsonl

    write_tweets_to_json(tweet_text)


def process_transactions_missed():

    global market_ops_algo_out
    global internal_algo_transfer_total
    global block_rewards_earned
    global fee_address
    global alpha_arcade_address

    files_in_txs_missed_dir = os.listdir('txs_missed')

    for file in files_in_txs_missed_dir:
        if file == 'compiled_tweet.jsonl':
            continue
        filepath = 'txs_missed/' + file
        with open(filepath, 'r') as f:
            for line in f:
                txn_info = json.loads(line)
                print(txn_info)
                tx_id = txn_info['id']
                found_AF_tx = False
                sender = txn_info.get('sender', None)
                type = txn_info.get('tx-type')
                receiver = None
                asset = 0
                amount = None
                unknown_activity = False
                timestamp = txn_info.get('round-time')
                if sender == alpha_arcade_address:
                    continue

                if type == 'pay':
                    pay_tx_info = txn_info.get('payment-transaction')
                    receiver = pay_tx_info.get('receiver')
                    amount = pay_tx_info.get('amount', 0)
                    unknown_activity = False
                    if (sender in foundation_market_wallets or receiver in foundation_market_wallets):
                        if amount > 15*10**6 and sender != fee_address:
                            found_AF_tx = True
                        else:
                            block_rewards_earned += amount
                        
                elif type == 'axfer':
                    axfer_tx_info = txn_info.get('asset-transfer-transaction')
                    receiver = axfer_tx_info.get('receiver')
                    amount = axfer_tx_info.get('amount', 0)
                    asset = axfer_tx_info.get('asset-id')
                    unknown_activity = False
                    if (sender in foundation_market_wallets or receiver in foundation_market_wallets):
                        found_AF_tx = True

                else:
                    unknown_activity = True
                    receiver = ''
                    amount = 0
                    if sender in foundation_market_wallets:
                        found_AF_tx = True

                if found_AF_tx:
                    add_tweet_text_to_jsonl(
                        tx_id=tx_id,
                        sender=sender,
                        receiver=receiver,
                        asset=asset,
                        amount=amount,
                        unknown_activity=unknown_activity,
                        tx_type=type,
                        timestamp=timestamp
                    )

fee_address = 'Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA'
alpha_arcade_address = 'XUIBTKHE7ISNMCLJWXUOOK6X3OCP3GVV3Z4J33PHMYX6XXK3XWN3KDMMNI'

market_ops_algo_out = 0
internal_algo_transfer_total = 0
block_rewards_earned = 0
all_tweets_and_timestamps: list[tuple[int, str]] = []

process_transactions_missed()

market_ops_algo_out_scaled_down = market_ops_algo_out / 10**6
internal_algo_transfer_total_scaled_down = internal_algo_transfer_total / 10**6
block_rewards_earned_scaled_down = block_rewards_earned / 10**6

market_ops_algo_out_usdc_amount = market_ops_algo_out_scaled_down * getAlgoPrice()
internal_algo_transfer_total_usdc_amount = internal_algo_transfer_total_scaled_down * getAlgoPrice()
block_rewards_earned_usdc_amount = block_rewards_earned_scaled_down * getAlgoPrice()

print(f'Market Operations Algo Out: {market_ops_algo_out_scaled_down:,.0f} Algo (${market_ops_algo_out_usdc_amount:,.2f})')
print(f'Internal Transfers Algo Amount: {internal_algo_transfer_total_scaled_down:,.0f} Algo (${internal_algo_transfer_total_usdc_amount:,.2f})')
print(f'Block Rewards Earned by Foundation Wallets: {block_rewards_earned_scaled_down:,.0f} Algo (${block_rewards_earned_usdc_amount:,.2f})')

write_tweets_to_json_chronologically(all_tweets_and_timestamps)

'''
Output after processing:

Market Operations Algo Out: 27,000,000 Algo ($2,388,718.93)
Internal Transfers Algo Amount: 387,930,249 Algo ($34,320,604.77)
Block Rewards Earned by Foundation Wallets: 577,759 Algo ($51,114.98)
'''