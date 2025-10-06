from algokit_utils import AlgorandClient, AlgoClientConfigs, AlgoClientNetworkConfig
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
import time
import os

load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_SECRET")
node_token = os.getenv('ALGOD_TOKEN')
node_port = os.getenv('PORT')

config = AlgoClientConfigs(
    algod_config=AlgoClientNetworkConfig(server='http://localhost', port=node_port, token=node_token),
    indexer_config=None,
    kmd_config=None,
)
foundation_market_wallets = {
    'KEU3FQHJ5CVO7DC5OJKHR74Z6M3X26O4IZYHHAIV6T7SLYHJJG32LCHICQ': 'Foundation: Treasury 1',
    '6OZQ3ENWXS4JFMIUKMKHPTQPWJVSN6VGBMSBR2E3BY3S5CPF2JPLGUXAJQ': 'Foundation: Treasury 3',
    '2ZHDNJEHQ7NIDKRML7IWSYJXGCN6WUURKT5LGTLF7I5ABFCM2KE4NL3XT4': 'Foundation: Treasury 4',
    'JB2EEILIBYWA3WACBIERYPG5TV6K6IHOWJKDFDHRGSCOEHTMEUUML7YXGE': 'Foundation: Treasury 5',
    'XUPBGF6OXIRVIGU2VHHYJFI4JEHLLIPNLMWNCSUZ7F44KYFRPV52ULIYNI': 'Foundation: Ecosystem Support 46',
    'VAOTJJLJP54QIKGCCFNJZVNHXXFZUZ3AAXCVGX5LRDQXQOUZRWBFBASUDQ': 'Foundation: Ecosystem Support 48',
    '3NGBML54PC7AJATJGW5BXMF6ZOFO2V4VTKKRTS3EAZXTVVHSPXTNV2GKEA': 'Foundation: Ecosystem Support 47',
    'OM2NLTOCWVDGX5XI6ETIQPW2CEILSEJFOC4NX5TJCTU6WMNC2KT2OUCT4M': 'Foundation: Ecosystem Support 49',
    '37VPAD3CK7CDHRE4U3J75IE4HLFN5ZWVKJ52YFNBX753NNDN6PUP2N7YKI': 'Foundation: Market Operations Addresses 1',
    '44GWRTQGSAYUJJCQ3GFINYKZXMBDVKCF75VMCXKORN7ZJ6BKPNG2RMGH7E': 'Foundation: Market Operations Addresses 2',
    '5WCIZNGQQT747WX3RTQIBJHOMJTQRUQBBH3PMK4YLP2X33AICJEUTL6F2E': 'Foundation: Foundation Endowment 1',
    'TBN2J7U3J5D4I7R2EK7XIBFNTEGVLHNORAXQ6YBJY5IVNY5IIKOXSJRYCE': 'Foundation: Foundation Endowment 2',
    '4H5UNRBJ2Q6JENAXQ6HNTGKLKINP4J4VTQBEPK5F3I6RDICMZBPGNH6KD4': 'Foundation: Foundation Endowment 3',
    'VEJGTLTKNT3VGLG2GVB2LMXC55WYW6J6WPZ76XTY2Y46TRJQOORWERYXYE': 'Foundation: Foundation Endowment 4',
    'L5BLJ4FNK6FNM7V5NUVT5QI6NQAERLLHYT24XH6RS2DUC4WDHPM5LOLGBY': 'Foundation: Foundation Endowment 5',
    '2JGGWKOIKYZB4HLG2X5DWHD5EWCUOQR7DC6VOEMWELIVNVVAF3BEUWJR7Y': 'Foundation: Foundation Endowment 6',
    'NRDDQ7MFRTUTMDAP4CBXDQ2IVP5VSLKDASADLLANYLFIKR7NQOGOUINYM4': 'Foundation: Foundation Endowment 7',
    'XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA': 'Foundation: Foundation Endowment 8',
    'LHVWNRKGGOTSSDYK4P4WKXTHZI5SAFKUO5ALAW7NJ6G76RG4UXLBCWN5LQ': 'Foundation: Foundation Endowment 9',
    'WDWBXGJIXO3N6A7AZ25XU4UX5Q3FJJ5CCKFCUEUWE75ZF5I6H47X37EY6M': 'Foundation: Foundation Endowment 10',
    'EG6JXQ3TQBWRSTR3OEDUS5RTPLMA4KTMJIV3N6DO7XN2XRKIFEN64DY3BU': 'Foundation: Foundation Endowment 11',
    'LLDPRZJUNWC75TS4GUGH5WFDD4GFMFKLAMLCGO4SX5WDMIKCQPCZ6ESERM': 'Foundation: Foundation Endowment 12',
    'BWM3QGF2EIBSSE2YND52F7KR7TMFJIKAHR4FLRH5W2H3VWUQUNG6V6LWYM': 'Foundation: Foundation Endowment 13',
    'BOYDCIT7PLRNGQWLPV3TONU3I6YJZVCNIIZNZ2GT4JKOD6SGT5FETAU6JE': 'Foundation: Ecosystem Support 27',
    '2LTZXETMTLAWET4CL3AZ353CXJ2HZE4RXFIGVD3HIBLB66G32HHGOAQOXE': 'Foundation: Ecosystem Support 28',
    '2V26XPENXHP2WRI4S4NFDIELZID2NTNA4MFQD5OM6SBBSG6NTJECHJHM5I': 'Foundation: Ecosystem Support 29',
    'UHCZHQASE5UA36NJNH4PYGF2H2XBJGSMTIPGA4NS4YA2L44VLQBWNLWQCA': 'Foundation: Ecosystem Support 30',
    'HD4IX4PGBCCLIUGPVTD3DTBWMQFIRJ4UBI67KXLTSJ23FUP54F67IXNLRE': 'Foundation: Ecosystem Support 31',
    'OFTMUIRIUX5YZDBIWJOGGK5IPR46HYHQ5OJTBYWDI5QOLVTSCUKPOODZ5U': 'Foundation: Ecosystem Support 32',
    '7ZCTFU4SA7KOYWCHEDYC5QTTH3NWOS3WDGSGJ5J263IRFWOMWNU2VIRSEA': 'Foundation: Ecosystem Support 33',
    'E4VMOYKWJCTKYVY447ALPOZMORITQYQVZVSYJ4ABLCCAAX4ZE6RNFDXZPI': 'Foundation: Ecosystem Support 50',
    'OMHYS6DGAS2GQIMALPYPSMNDQ2735J7Z76RQFH7KP2MIPDHXOZYVV3TVO4': 'Foundation: Ecosystem Support 51',
    'VZBMOTCMEHRITULBNLCWHA5U62UUXLQZMLVM6HPBPCMIM2YOMHDQRTK64E': 'Foundation: Ecosystem Support 52',
    'EOU3RSLHSCS247TWWMWQY2FPMOTEALFCNXCR2BV4B3E2HMIIHWCJNIGKFM': 'Foundation: Ecosystem Support 53',
    'GKKTNJ42QIW2BO7UUWGLTMFPVN744LJ5T3QXVSRAV5752476LXTQHWOUUM': 'Foundation: Ecosystem Support 54',
    'CFB4XBBO6KDDFPGWT2LDF7O7FJBVSPXH2ZBBTRAZAC4DVUM6KB5IU7XH3E': 'Foundation: Ecosystem Support 55',
    '4STCN6LMGELTGPF5JTOIPNWM3UBJL6IGBZG6I4TKAL2K3BEJBBYVE56QQY': 'Foundation: Ecosystem Support 56',
    'SSXTVQ2W3EICPJZ4SGX273KO2A6S37URYRF2ZKGBAQCFVKPC5MXUUI6UB4': 'Foundation: Ecosystem Support 57',
    'PS5RV6QGU5IVOFBTCYQVZHB3PQSVLR335OY7BVGB62ZV52SDEQ2PNTYUUQ': 'Foundation: Ecosystem Support 58',
    'DAV5VECJYNSFQFKWX37YANONLSMWHGUVPGNLLQLX6ANW4WN2SFLZQPXRXI': 'Foundation: Ecosystem Support 59',
    'JGIPWSM6QR6XYZIKDRJ54OGSYATLGPSTUMETAFULUS3JXWFALPLGU7OMOI': 'Foundation: Ecosystem Support 60',
    'EU6CHYSH7ZXLJQAPPIN6W3KS7VAURYZCB5P3ZCXMYCWNJF6V5RTVL2UPHU': 'Foundation: Ecosystem Support 62',
    'GJGK42UVZK4IDKN5MGP53A6FJEHRI52PI4E3BBJZRZCQZ666BKYILYXI2E': 'Foundation: Ecosystem Support 63',
    'O4N25TS4Z5SC34VZ6R6RU74PCEIUTJFSDSKETNDYU4CXI3C2BFYXCYEKAU': 'Foundation: Ecosystem Support 64',
    '62UUOSMOMD6XOSRROCIIMVVF2VX6N4CMVLCUFUVWV4Q4T4BHD7ETFNWMOI': 'Foundation: Ecosystem Support 65',
    'IHYR5OZGAIRSCDCNQJVFOPAOJT2SPG3YXAE3GGJPZRI6JV2GQSJAYG5NUY': 'Foundation: Ecosystem Support 66',
    'MKZIWVBDBZV7UK6XQY3DFLYSBLSJWCDHDJWK3JAHWCFMNJOH4ZXQSMOUCE': 'Foundation: Ecosystem Support 67',
    'A66JRYUOU523Z4MU53AJL3YAEHESH3KMVV7OJI4SMFRVIDNNVDK2LHSL4Y': 'Foundation: Ecosystem Support 68',
    'HRLD25IMT2Q4UPYOEUZIWHDI3ELCUIC5NLNC75O2NE7OLDJK7GZXDIK5QQ': 'Foundation: Ecosystem Support 69',
    'ROVA2AHXIEUFK63ULPXQJOMAGDRG2C4EZMGD63QHMGJTMTBLHTG5RPZUTM': 'Foundation: Miscellaneous Addresses 1',
    'V3ZJHYSUMAUZXMSPO6GNDO6QQUGB5OWCHNAB5A743TKYC3RWBPAL3P5IIA': 'Foundation: Miscellaneous Addresses 2',
    'IOSADRTSZUE6WBNXH7ANZANFDQ3GVCVUGZI3IP6T3AQI6RLGLI6TPNJQZA': 'Unlabeled Foundation Wallet',
    'XNFDTOTUQME3NI2UWDJ5Y6LYOJKHNP4C7BKZYQ5GSDQ7JBXKEJ6HLM3LOE': 'Unlabeled Foundation Wallet',
    '2TZAMEZZDWFY37QV66HXWQIYWYJIZKE2KP3QNPI2QHHKSMKUZEICNMMUFU': 'Unlabeled Foundation Wallet',
    'TVUQW6NXMHZFZAV6D7PQMW4DIUL5UB42L2JLIYNGRHH6UW362HGNVI26DY': 'Unlabeled Foundation Wallet',
    'B223SVF452UWAMMLNIHIUAPHYPX5J3HLVJF6MNOHUJE2NWJBG7C66JILGE': 'Unlabeled Foundation Wallet',
    '4E7OINW7M6G6OT2SQZ7ZKFPWJ7CAAFTPOG2RZISJ3YZU5VCJQ64ZIROC44': 'Unlabeled Foundation Wallet',
    'EQPH5S3T5YQCYXR6H42QQDBNDIATT7BMJPIU43TRVRZZ2UPMZIHFM2HKJM': 'Midas RWA'
}

def tweet(tx_id: str, sender: str, receiver: str, asset: int, amount: int, tx_type: str, unknown_activity: bool):
 
    sender_label = foundation_market_wallets.get(sender)
    receiver_label = foundation_market_wallets.get(receiver)

    sender_is_af = sender_label is not None
    receiver_is_af = receiver_label is not None

    sender_is_mops = sender_is_af and "Market Operations" in sender_label
    receiver_is_mops = receiver_is_af and "Market Operations" in receiver_label

    if asset == 0:
        asset_name, decimals = "Algo", 6
    else:
        info = algorand.asset.get_by_id(asset)
        asset_name = info.asset_name
        decimals = info.decimals

    amt_fmt = f"{amount / 10**decimals:,.2f}"

    if asset == 470842789: #Ignore Defly airdrops
        return
    
    if unknown_activity:
        tweet_text = f"Foundation Wallet Activity:\n {sender_label or sender} ({sender}) performed an uncrawled application call or key registration transaction."
        

    elif tx_type == 'keyreg':
        algo_balance = algorand.client.algod.account_info(sender)['amount'] / 10**6
        tweet_text = f"{sender_label} renewed participation keys or removed {algo_balance:,.0f} Algorand from online stake!"

    elif sender == receiver:
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
    time.sleep(2)  


previous_round = 0

algorand = AlgorandClient(config=config)

while True:
    try:
        next_round = algorand.client.algod.status()['last-round']
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
    except Exception as e:
        if 'txns' not in str(e):
            print(e)
        time.sleep(5)
        algorand = AlgorandClient(config=config)
        pass
