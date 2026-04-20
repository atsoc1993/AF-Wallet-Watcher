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

def send_yourplace_post(message: str):
    try:
        message = message.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
        sp = algod_client.suggested_params()
        txn = transaction.PaymentTxn(
            sender=address,
            sp=sp,
            receiver=address,
            amt=0,
            note=f'yp/1/p:{json.dumps({"p": message})}'.encode("utf-8")
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
