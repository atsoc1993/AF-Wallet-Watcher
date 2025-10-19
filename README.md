## Summary

The two files included, `tweet_on_activity.py` and `tweet_af_holdings_summary.py`, contain the logic necessary to, respectively:
- Send an X post when a transaction is detected from or to any of the officially labeled wallets owned by the Algorand Foundation
- Tweet an Algo balance summary (and the respective USDC value at that time) for all officially labeled Algorand Foundation wallets


The officially labeled wallets are contained in a map in both files:

```
foundation_market_wallets = {
    'KEU3FQHJ5CVO7DC5OJKHR74Z6M3X26O4IZYHHAIV6T7SLYHJJG32LCHICQ': 'Foundation: Treasury 1',
    '6OZQ3ENWXS4JFMIUKMKHPTQPWJVSN6VGBMSBR2E3BY3S5CPF2JPLGUXAJQ': 'Foundation: Treasury 3',
    '2ZHDNJEHQ7NIDKRML7IWSYJXGCN6WUURKT5LGTLF7I5ABFCM2KE4NL3XT4': 'Foundation: Treasury 4',
    'JB2EEILIBYWA3WACBIERYPG5TV6K6IHOWJKDFDHRGSCOEHTMEUUML7YXGE': 'Foundation: Treasury 5',
    'XUPBGF6OXIRVIGU2VHHYJFI4JEHLLIPNLMWNCSUZ7F44KYFRPV52ULIYNI': 'Foundation: Ecosystem Support 46',
    'VAOTJJLJP54QIKGCCFNJZVNHXXFZUZ3AAXCVGX5LRDQXQOUZRWBFBASUDQ': 'Foundation: Ecosystem Support 48',
     . . .
}
```

The officially labeled wallets were obtained from this link, under the "Account Address" toggle: https://algorand.co/algorand-foundation/transparency

<img width="1014" height="546" alt="image" src="https://github.com/user-attachments/assets/d500cf66-0926-4fd6-b88a-a1faf1fa2a19" />


*Note: I use my own Algorand node on my VPS for both scripts to not take advantage of Nodely's free API consistently, and avoid potential rate limiting.*


## `tweet_af_holdings_summary.py`: USDC Value Logic, Fetching Account balances, OAuth1 & API Keys, Tweet Content Compilation

To get the equivalent USDC value when tweeting a balance summary in `tweet_af_holdings_summary.py`, we compute the Logic Sig Account for the pool address for USDC/ALGO on Tinyman by inserting the tinyman router application ID, asset A & asset B id's into the program bytes of the logic sig template provided by Tinyman for all pool address'.

```
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
```

Once the pool address is determined, we extract the address from the LogicSigAccount object, and fetch the local states of the pool address against the Tinyman router. The only local states needed for price calculation are `asset_1_reserves` and `asset_2_reserves`.

We simply take the quotient of `asset_1_reserves` over `asset_2_reserves`:

```
logic_sig_account = get_pool_logicsig(TINYMAN_ROUTER, asset_a, asset_b)
pool_address = logic_sig_account.address()

local_states = algorand.app.get_local_state(address=pool_address, app_id=TINYMAN_ROUTER)
asset_1_reserves = local_states.get('asset_1_reserves').value
asset_2_reserves = local_states.get('asset_2_reserves').value

algorand_price = asset_1_reserves / asset_2_reserves
```

Once the current price of Algo is obtained taking decimals into account, we can now loop through all officially labeled foundation address' and fetch their balances, while simultaneously preparing a formatted tweet message:

```    
  algorand_price = getAlgoPrice()
  balances_text = ''
  total_algo = 0
  total_value = 0
  algorand = AlgorandClient.mainnet()
  decimals_scale = 10**6
  for key, value in foundation_market_wallets.items():
      algo_balance = algorand.client.algod.account_info(key)['amount'] / decimals_scale
      dollar_value = algo_balance * algorand_price
      balances_text += f'{value} \nValue: {algo_balance:,.2f}A | ${dollar_value:,.2f}\n\n'
      total_algo += algo_balance
      total_value += dollar_value
```

We also append a description header to the prepared tweet string:

```
total_value_text = f'Foundation Wallet Weekly Summary: \n\nTotal Remaining Foundation Funds: {total_algo:,.2f}A | ${total_value:,.2f}\n\n'
tweet_text = total_value_text + balances_text
tweet_text = tweet_text + '#Algofam #Algorand' + '\nCreated and Hosted by @atsoc93'
```

Now that the tweet content is prepared, I use API keys as parameters to create an `OAuth1Session` object from the `requests_oauthlib` library.

Instructions to obtain API keys for X can be found here: https://docs.x.com/fundamentals/authentication/oauth-1-0a/api-key-and-secret

We create a payload containing a single property, `text`, with our compiled tweet text as a value, and make a post request to the `"https://api.twitter.com/2/tweets"` endpoint.

```
payload = {"text": tweet_text}

oauth   = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)
resp = oauth.post("https://api.twitter.com/2/tweets", json=payload)
if resp.status_code != 201:
    raise RuntimeError(f"Twitter error {resp.status_code}: {resp.text}")

print("Tweeted:", tweet_text)
```

The script uses a while loop that uses a 7-day long sleep function to schedule balance summary tweets weekly, these go out on Sunday's.
```while True:
    balance_summary_tweet()
    time.sleep(604_800)
```
## `tweet_on_activity.py` 

The script begins with setting the previous round cursor to 0, where we then initiate a while loop (with try except clauses) that checks if the next round has passed (next block has been confirmed and a new mem pool is forming for the subsequent round).

If we now have a new, complete block to crawl, we trigger the if logic, which resets the AlgorandClient object to avoid any errors that may arise from a stale client or hanging network connection to the VPS where the node is hosted.

If the next round has not been confirmed yet, then we simply sleep for 1 second to avoid spamming the node with unnecessary requests, since we have 2.8~ seconds on average per round completion.

```
previous_round = 0

algorand = AlgorandClient(config=config)

while True:
    try:
        next_round = algorand.client.algod.status()['last-round']
        if next_round > previous_round:
            algorand = AlgorandClient(config=config)

        . . .

        time.sleep(1)
```

Once the `if` logic triggers, the code executes— we will get into the `tweet` functions' logic afterwards.

The following code block gets all transaction ID's from the recently proposed block and the block information, and zips these blobs of data to map each transaction ID to transaction information.

Initially, I was getting individual transaction info for each transaction ID, but noticed that transaction ID's & block info map 1:1, and the block info method was far more efficient.

Once the transaction ID's & block info are zipped, we now have an array of arrays, where the inner array items are a length of 2 and contain each transaction ID & individual transaction info.

We iterate through the array, and set a flag for `found_AF_tx` to False. We use this later to determine if we should prepare a tweet or not if a transaction is detected from or to an officially labeled Algorand Foundation account.

There are various ways to deconstruct transaction information and crawl them, and to each their own, but it's just important to note that different transaction types contain different keys.

For example a payment transaction may or may not have a `rcv` (receiver) field depending on the exact usage (rekey, lease to, & close to can be used instead), and an asset transfer will have an `arcv` field (asset receiver) instead of `rcv`. A payment transaction
will have an `xaid` field whereas a payment transaction will not, a payment transaction will have an `amt` (amount) field (if not 0) whereas an asset transfer transaction will have an `aamt` (asset amount) field if not 0, so on and so forth.

The main purpose is to check each transaction to see if we have an AF labeled wallet in the `snd`, `arcv`, or `rcv` field, the transaction's type, and ensure that whatever the scenario, we have the associated information with that transaction. Should we find
any transaction that involves an AF wallet, we set the `found_AF_tx` flag to True, and pass the information about the transaction to the `tweet` method.

If the transaction type is not a payment or asset transfer transaction, we perform further validation later in the `tweet` method.

After the `tweet` method runs, which we will discuss after the following code block, we set the `previous_round` value to `next_round`

```
if next_round > previous_round:
  algorand = AlgorandClient(config=config)

  block_txs = algorand.client.algod.get_block_txids(next_round)['blockTxids']
  block_info = algorand.client.algod.block_info(next_round)['block']['txns']
  tx_and_info = [[id, tx['txn']] for id, tx in zip(block_txs, block_info)]
  for tx_id, txn_info in tx_and_info:
      found_AF_tx = False
      sender = txn_info.get('snd', None)
      type = txn_info['type']

      if type == 'pay':
          receiver = txn_info.get('rcv', sender)
          asset = 0
          amount = txn_info.get('amt', 0)
          unknown_activity = False
          if (sender in foundation_market_wallets or receiver in foundation_market_wallets) \
              and amount > 1_000_000:                    
              found_AF_tx = True

      elif type == 'axfer':
          receiver = txn_info['arcv']
          asset = txn_info['xaid']
          amount = txn_info.get('aamt', 0)
          unknown_activity = False
          if sender in foundation_market_wallets or receiver in foundation_market_wallets:
              found_AF_tx = True

      else:
          unknown_activity = True
          receiver = ''
          asset = 0
          amount = 0
          if sender in foundation_market_wallets:
              found_AF_tx = True

      if found_AF_tx:
          tweet(tx_id=tx_id, sender=sender, receiver=receiver, asset=asset, amount=amount, unknown_activity=unknown_activity, tx_type=type)
  previous_round = next_round
  time.sleep(2)
```

The `tweet` method's only purpose is to prepare a legible, straightforward message about what has occured in the transaction involving an AF Acccount. 

We distinguish if they were the sender or receiver, or both, and get the appropriate label from the AF Account hashmap constant in the global scope:
```
foundation_market_wallets = {
    'KEU3FQHJ5CVO7DC5OJKHR74Z6M3X26O4IZYHHAIV6T7SLYHJJG32LCHICQ': 'Foundation: Treasury 1',
    '6OZQ3ENWXS4JFMIUKMKHPTQPWJVSN6VGBMSBR2E3BY3S5CPF2JPLGUXAJQ': 'Foundation: Treasury 3',
    '2ZHDNJEHQ7NIDKRML7IWSYJXGCN6WUURKT5LGTLF7I5ABFCM2KE4NL3XT4': 'Foundation: Treasury 4',
    'JB2EEILIBYWA3WACBIERYPG5TV6K6IHOWJKDFDHRGSCOEHTMEUUML7YXGE': 'Foundation: Treasury 5',
    'XUPBGF6OXIRVIGU2VHHYJFI4JEHLLIPNLMWNCSUZ7F44KYFRPV52ULIYNI': 'Foundation: Ecosystem Support 46',
    'VAOTJJLJP54QIKGCCFNJZVNHXXFZUZ3AAXCVGX5LRDQXQOUZRWBFBASUDQ': 'Foundation: Ecosystem Support 48',
     . . .
}

. . .

def tweet(tx_id: str, sender: str, receiver: str, asset: int, amount: int, tx_type: str, unknown_activity: bool):
    sender_label = foundation_market_wallets.get(sender)
    receiver_label = foundation_market_wallets.get(receiver)

    sender_is_af = sender_label is not None
    receiver_is_af = receiver_label is not None

```
We determine if the message needs to be catered for a Market Operations event to be careful with wording:
    . . .
    
    sender_is_mops = sender_is_af and "Market Operations" in sender_label
    receiver_is_mops = receiver_is_af and "Market Operations" in receiver_label
    elif sender_is_mops and not receiver_is_mops:
        recv_part = receiver_label or receiver
        tweet_text = f"{sender_label} (Structured-Selling Wallet) transferred {amt_fmt} {asset_name} through {recv_part}."

    . . .
```

We determine the asset name involved, if any, where 0 represents Algo, which uses 6 decimal points for units.
If not Algo, we get the asset's information to get it's name & decimal-conscious quantity.
One of the Treasury address' contains Defly tokens, so we don't tweet if it's an airdrop as these are somewhat arbitrary non-important announcements to make:

```
    if asset == 0:
        asset_name, decimals = "Algo", 6
    else:
        info = algorand.asset.get_by_id(asset)
        asset_name = info.asset_name
        decimals = info.decimals

    amt_fmt = f"{amount / 10**decimals:,.2f}"

    if asset == 470842789: #Ignore Defly airdrops
        return
```

We determine the appropriate wording for the tweet content, depending on the scenario.

If the transaction type is not a payment or asset transfer, than we can assume it was an application call or key registration transaction (marked as unknown).
These are not further validated aside from general information, but are inspected manually to confirm if there is anything interesting afoot.
For the most part, no application calls or key registration transactions have been interesting. So far, `unknown_activity` has always been a 'keyreg' type for participation key renewal upon further investigation.

If the sender & receiver are equal to each other, and the asset is not Algo, than they are surely opting into some asset.

If either the `sender_is_mops` or `receiver_is_mops` (mops is market operations) flags are True, then we should cater the message for market operations context. (Structured selling activity)

If not an application call or key registration transaction, an opt-in, or market ops activity, then the only remaining options are an internal transfer of some Algo or Asset, or a receipt of some amount of Algo or asset from a non AF account.

Similar to the asset summary logic, we prepare a formatted text payload, and tweet the contents from the @AFWalletWatcher account.

```
    if unknown_activity and type != 'keyreg':
        tweet_text = f"Foundation Wallet Activity:\n {sender_label or sender} ({sender}) performed an uncrawled application call or key registration transaction."
        
    elif tx_type == 'keyreg':
        algo_balance = algorand.client.algod.account_info(sender)['amount'] / 10**6
        tweet_text = f"{sender_label} renewed participation keys or removed {algo_balance:,.0f} Algorand from online stake!"

    elif sender == receiver and asset:
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

    tweet_text = tweet_text + f'\nPera Link:\nhttps://explorer.perawallet.app/tx/{tx_id}'
    tweet_text = tweet_text + '\n\n' '#Algofam #Algorand' + '\nCreated and Hosted by @atsoc93'
  ```
