from dotenv import load_dotenv
from yourplace_messages.bot import submit_note_transaction
import json
import traceback

load_dotenv()

ERROR_LOG = "yourplace_errors.log"

def create_and_submit_txn(note: str):
    try:
        tx_id = submit_note_transaction(note)
        if tx_id is None:
            return None
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
def set_bot(bot: bool):
    create_and_submit_txn(f'yp/1/mbot:{json.dumps({"bot": bot})}')
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
    set_bot(True)
    # set_avatar("https://example.com/avatar.png")
    # set_banner("https://example.com/banner.png")
