# YourPlace Messages

Posts AF Wallet Watcher transaction alerts on-chain to YourPlace via the Algorand blockchain.

## Setup

### 1. Get an Algorand Private Key

You need an Algorand account with a small ALGO balance to cover transaction fees (~0.001 ALGO per transaction).

**Option A — Use an existing wallet:**
Export your private key (mnemonic) from Pera Wallet, Defly, or any Algorand wallet. Convert the 25-word mnemonic to a private key:

```python
from algosdk import mnemonic
private_key = mnemonic.to_private_key("your 25 word mnemonic here")
print(private_key)
```

**Option B — Generate a new account:**

```python
from algosdk import account, mnemonic
private_key, address = account.generate_account()
print(f"Address: {address}")
print(f"Private Key: {private_key}")
print(f"Mnemonic: {mnemonic.from_private_key(private_key)}")
```

Fund the address with a small amount of ALGO (1-2 ALGO is plenty for thousands of transactions).

### 2. Set the Environment Variable

Add to your `.env` file (alongside the existing `ALGOD_TOKEN` and `PORT` used by the watcher):

```
YOURPLACE_ALGO_PRIVATE_KEY=<your-base64-private-key>
```

Both `metadata.py` and `bot.py` use the same local Algod node configured via `ALGOD_TOKEN` and `PORT` in `.env`.

### 3. Set Profile Metadata (One-Time)

Edit the hardcoded values at the bottom of `metadata.py` to set the bot's YourPlace profile (name, description, avatar, etc.). Uncomment any lines you want to set, then run:

```bash
python -m yourplace_messages.metadata
```

Each function call submits a separate on-chain transaction. Only run the ones you need — comment out the rest. To update a single field later, comment out everything except that one call and re-run.

### 4. Automatic Posting

`bot.py` is imported and called automatically by `tweet_on_activity.py` (real-time alerts) and `tweet_af_holdings_summary.py` (weekly balance summary). No manual setup needed beyond the env variable. Each alert is posted on-chain as a YourPlace post.

## Files

- **metadata.py** — Functions to set profile metadata on-chain. Run manually.
- **bot.py** — `send_yourplace_post(message)` called by the main watcher to post alerts on-chain.

Errors from both files are logged to `yourplace_errors.log` in the project root.

## Transaction Format

All YourPlace transactions are zero-amount self-pay Algorand transactions with a UTF-8 note field:

```
yp/1/<action_code>:<json_payload>
```

Posts: `yp/1/p:{"p":"message text"}`
Metadata: `yp/1/mn:{"n":"name"}`, `yp/1/md:{"d":"description"}`, etc.

## Cost

Each transaction costs the Algorand minimum fee (~0.001 ALGO). At current rates, 1 ALGO covers ~1000 transactions.
