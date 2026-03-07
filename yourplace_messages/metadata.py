from algosdk.v2client import algod
from algosdk import account, transaction
from dotenv import load_dotenv
import json
import os
import traceback

load_dotenv()

ERROR_LOG = "yourplace_errors.log"

node_token = os.getenv("ALGOD_TOKEN")
node_port = os.getenv("PORT")
private_key = os.getenv("YOURPLACE_ALGO_PRIVATE_KEY")
assert private_key is not None, "YOURPLACE_ALGO_PRIVATE_KEY not set in .env"
address = account.address_from_private_key(private_key)
algod_client = algod.AlgodClient(node_token, f"http://localhost:{node_port}")

def create_and_submit_txn(note: str):
    try:
        sp = algod_client.suggested_params()
        txn = transaction.PaymentTxn(
            sender=address,
            sp=sp,
            receiver=address,
            amt=0,
            note=note.encode("utf-8")
        )
        signed = txn.sign(private_key)
        tx_id = algod_client.send_transaction(signed)
        print(f"YourPlace txn submitted: {tx_id}")
        return tx_id
    except Exception as e:
        print(f"YourPlace txn failed: {e}")
        with open(ERROR_LOG, "a") as f:
            f.write(f"{traceback.format_exc()}\n")
        return None

def set_avatar(url: str):
    create_and_submit_txn(f'yp/1/ma:{json.dumps({"a": url})}')
def set_banner(url: str):
    create_and_submit_txn(f'yp/1/mb:{json.dumps({"b": url})}')
def set_description(description: str):
    create_and_submit_txn(f'yp/1/md:{json.dumps({"d": description})}')
def set_name(name: str):
    create_and_submit_txn(f'yp/1/mn:{json.dumps({"n": name})}')
def set_vertical(vertical: str):
    create_and_submit_txn(f'yp/1/mv:{json.dumps({"v": vertical})}')
def set_website(url: str):
    create_and_submit_txn(f'yp/1/mw:{json.dumps({"w": url})}')

if __name__ == "__main__":
    set_name("AF Wallet Watcher")
    set_description("Monitoring Algorand Foundation wallet activity in real-time.")
    set_vertical("News")
    set_website("https://x.com/AFWalletWatcher")
    # set_avatar("https://example.com/avatar.png")
    # set_banner("https://example.com/banner.png")
