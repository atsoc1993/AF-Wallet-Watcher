from algokit_utils import AlgoAmount, AlgoClientNetworkConfig, AlgorandClient, PaymentParams, SigningAccount
from dotenv import load_dotenv
import json
import os
import traceback
from algosdk.account import address_from_private_key
load_dotenv()

ERROR_LOG = "yourplace_errors.log"
MAX_NOTE_BYTES = 1024
POST_NOTE_PREFIX = "yp/1/p:"

private_key = os.getenv("YOURPLACE_ALGO_PRIVATE_KEY")
assert private_key is not None, "YOURPLACE_ALGO_PRIVATE_KEY not set in .env"
address: str = address_from_private_key(private_key)

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
    note_bytes = note.encode("utf-8")
    if len(note_bytes) > MAX_NOTE_BYTES:
        print(f"YourPlace note exceeds {MAX_NOTE_BYTES} bytes; skipping submission")
        return None

    algorand = get_algorand_client()
    account = SigningAccount(address=address, private_key=private_key)
    algorand.set_signer_from_account(account)
    result = algorand.send.payment(
        PaymentParams(
            sender=account.address,
            receiver=account.address,
            amount=AlgoAmount.from_micro_algo(0),
            note=note_bytes,
        )
    )
    return result.tx_id or result.tx_ids[0]


def build_post_note(message: str) -> str:
    normalized_message = message.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")

    def serialize(candidate: str) -> str:
        return f'{POST_NOTE_PREFIX}{json.dumps({"p": candidate})}'

    serialized_note = serialize(normalized_message)
    if len(serialized_note.encode("utf-8")) <= MAX_NOTE_BYTES:
        return serialized_note

    low, high = 0, len(normalized_message)
    while low < high:
        mid = (low + high + 1) // 2
        candidate_note = serialize(normalized_message[:mid])
        if len(candidate_note.encode("utf-8")) <= MAX_NOTE_BYTES:
            low = mid
        else:
            high = mid - 1

    truncated_message = normalized_message[:low]
    return serialize(truncated_message)

def send_yourplace_post(message: str):
    try:
        tx_id = submit_note_transaction(build_post_note(message))
        if tx_id is None:
            return None
        print(f"YourPlace txn submitted: {tx_id}")
        return tx_id
    except Exception as e:
        print(f"YourPlace txn failed: {e}")
        with open(ERROR_LOG, "a") as f:
            f.write(f"{traceback.format_exc()}\n")
        return None
