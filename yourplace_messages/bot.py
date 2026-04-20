from algokit_utils import AlgoAmount, AlgoClientNetworkConfig, AlgorandClient, PaymentParams, SigningAccount
from dotenv import load_dotenv
import json
import os
import traceback

load_dotenv()

ERROR_LOG = "yourplace_errors.log"

private_key = os.getenv("YOURPLACE_ALGO_PRIVATE_KEY")
assert private_key is not None, "YOURPLACE_ALGO_PRIVATE_KEY not set in .env"


def get_algorand_client() -> AlgorandClient:
    node_port = os.getenv("PORT")
    node_token = os.getenv("ALGOD_TOKEN")

    if node_port:
        try:
            algorand = AlgorandClient.from_config(
                algod_config=AlgoClientNetworkConfig(
                    server="http://localhost",
                    port=node_port,
                    token=node_token,
                )
            )
            algorand.client.algod.status()
            return algorand
        except Exception:
            pass

    return AlgorandClient.mainnet()


def submit_note_transaction(note: str):
    algorand = get_algorand_client()
    account = SigningAccount(private_key)
    algorand.set_signer_from_account(account)
    result = algorand.send.payment(
        PaymentParams(
            sender=account.address,
            receiver=account.address,
            amount=AlgoAmount.from_micro_algo(0),
            note=note.encode("utf-8"),
        )
    )
    return result.tx_id or result.tx_ids[0]

def send_yourplace_post(message: str):
    try:
        message = message.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
        tx_id = submit_note_transaction(f'yp/1/p:{json.dumps({"p": message})}')
        print(f"YourPlace txn submitted: {tx_id}")
        return tx_id
    except Exception as e:
        print(f"YourPlace txn failed: {e}")
        with open(ERROR_LOG, "a") as f:
            f.write(f"{traceback.format_exc()}\n")
        return None
