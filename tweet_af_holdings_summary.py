from requests_oauthlib import OAuth1Session
from algokit_utils import AlgorandClient
from algosdk.transaction import LogicSigAccount
from base64 import b64decode
from dotenv import load_dotenv
import time
import os

load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_SECRET")


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
}

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

def balance_summary_tweet():

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

    
    total_value_text = f'Foundation Wallet Weekly Summary: \n\nTotal Remaining Foundation Funds: {total_algo:,.2f}A | ${total_value:,.2f}\n\n'

    tweet_text = total_value_text + balances_text
    tweet_text = tweet_text + '#Algofam #Algorand' + '\nCreated and Hosted by @atsoc93'
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


while True:
    balance_summary_tweet()
    time.sleep(604_800)
