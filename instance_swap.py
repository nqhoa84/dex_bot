from web3 import Web3
import json
import beepy
import time
import threading
from configparser import ConfigParser
import telebot
import logging
from datetime import datetime
from collections import namedtuple
import enum
import msvcrt as m
import webbrowser

pancake_factory = 0
pancake_router = 0
web3 = ""
sound_alamp = True
msg_notifi = True
notifi_delay = 30  # ms
bot = 0
chat_id = 0
table_data = []
ProgramTerminated = False
console_log = ""
message_queue = []
get_price_delay = 0
my_account = 0
json_abi = ''
tele_api_key = ''
mnemonic = ''
passphrase = ''
transaction_info = []
token_list = []
auto_swap = 0


notifi_mutex = threading.Lock()
sound_mutex = threading.Lock()
console_mutex = threading.Lock()

logging.basicConfig(filename="./log_insw/" + datetime.now().strftime("%d-%m-%Y-%Hh%M") + ".log",
                    filemode='a',
                    format='[%(asctime)s,%(msecs)d][%(levelname)s][%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

TransactionData = namedtuple('TransactionData',
                             ['slippage_tolerance', 'amount_input', 'gas_price', 'gas', 'time_limit'])


class Auto(enum.Enum):
    No = 0
    Buy = 1
    Sell = 2

class UserAction(enum.Enum):
    NoAction = 0
    Quit = 1
    Swap = 2

user_action = UserAction.NoAction

BoolMap = {
    'True': True,
    'False': False
}

ActionMap = {
    'No': Auto.No,
    'Buy': Auto.Buy,
    'Sell': Auto.Sell
}


def Delay(p):
    global ProgramTerminated
    recent = time.time()
    while (not ProgramTerminated) and ((time.time() - recent) < p):
        time.sleep(0.5)


def LoadABI(json_file):
    global json_abi
    abi_json_file = open(json_file, 'r')
    json_abi = json.load(abi_json_file)
    return True


def ConnectBSC(factory_addr, router_addr, privateKey, passphrase):
    bsc = "https://bsc-dataseed.binance.org/"
    global web3
    global my_account
    try:
        web3 = Web3(Web3.HTTPProvider(bsc))

        global pancake_factory
        global pancake_router
        pancake_factory = web3.eth.contract(address=factory_addr, abi=json_abi)
        pancake_router = web3.eth.contract(address=router_addr, abi=json_abi)

        web3.eth.account.enable_unaudited_hdwallet_features()
        my_account = web3.eth.account.from_mnemonic(privateKey, passphrase)
    except:
        logging.error("Connect to BSC and Pancake failed")
        return False

    if web3.isConnected():
        logging.info("Connected to BSC")
        logging.info("Wallet Address: %s", my_account.address)

        print("Connected to BSC")
        print("Wallet Address: " + my_account.address)

    else:
        logging.error("Failed to connect to BSC")
        return False

    return True


def CalculatePrice(pair_contract, reverse=False, decimal=0):
    r0, r1, tsp = pair_contract.functions.getReserves().call()
    if reverse:
        return (r0 / r1) * pow(10, decimal)
    else:
        return (r1 / r0) * pow(10, decimal)
    # f = open("./test.txt", "r")
    # v = float(f.readline())
    # f.close()
    # return v


def AddMessage(message):
    notifi_mutex.acquire()
    message_queue.append(message)
    notifi_mutex.release()


def SoundAlert():
    sound_mutex.acquire()
    beepy.beep(6)
    logging.info("Sound Alert")
    sound_mutex.release()


def MessageNotify(message, retry):
    global bot
    global chat_id

    try:
        bot.send_message(chat_id, message)
    except:
        logging.error("Error sending Telegram message. Retry %d", retry)
        print("Error sending Telegram message. Retry" + str(retry))
        return False
    else:
        logging.info("Message Notification:%s", message)
        return True


def Notify(message):
    if sound_alamp:
        SoundAlert()

    if msg_notifi:
        AddMessage(message)


def Swap(token_list, trans_data, price, decimal):
    logging.info("Token list: {}".format(' '.join(map(str, token_list))))
    logging.info("Price: %lf", price)
    global my_account
    wallet_address = my_account.address

    amount_in = int(
        trans_data.amount_input * pow(10, decimal[0])) if trans_data.amount_input != 0 else web3.eth.contract(
        address=token_list[0], abi=json_abi).functions.balanceOf(wallet_address).call()
    amount_out_min = int(
        amount_in * price * (1 - trans_data.slippage_tolerance / 100) * pow(10, decimal[1] - decimal[0])) if (
            trans_data.slippage_tolerance >= 0) else 0

    logging.info("In: %d. Min out:%d", amount_in, amount_out_min)

    if amount_in != 0:
        if token_list[0].lower() == '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c':
            txn = pancake_router.functions.swapExactETHForTokens(
                amount_out_min,
                token_list,
                wallet_address,
                (int(time.time()) + trans_data.time_limit),
            ).buildTransaction({
                'from': wallet_address,
                'value': web3.toWei(trans_data.amount_input, 'ether'),
                'gas': trans_data.gas,
                'gasPrice': trans_data.gas_price,
                'nonce': web3.eth.get_transaction_count(wallet_address),
            })
        elif token_list[-1].lower() == '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c':
            txn = pancake_router.functions.swapExactTokensForETH(
                amount_in,
                amount_out_min,
                token_list,
                wallet_address,
                (int(time.time()) + trans_data.time_limit),
            ).buildTransaction({
                'from': wallet_address,
                'gas': trans_data.gas,
                'gasPrice': trans_data.gas_price,
                'nonce': web3.eth.get_transaction_count(wallet_address),
            })
        else:
            txn = pancake_router.functions.swapExactTokensForTokens(
                amount_in,
                amount_out_min,
                token_list,
                wallet_address,
                (int(time.time()) + trans_data.time_limit)
            ).buildTransaction({
                'from': wallet_address,
                'gas': trans_data.gas,
                'gasPrice': trans_data.gas_price,
                'nonce': web3.eth.get_transaction_count(wallet_address),
            })

        signed_txn = my_account.sign_transaction(txn)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print("Swap done: https://bscscan.com/tx/" + tx_token.hex())
        AddMessage("Swap done: https://bscscan.com/tx/" + tx_token.hex())
        logging.info("Swap done: https://bscscan.com/tx/%s", str(tx_token.hex()))
        webbrowser.open('https://bscscan.com/tx/' + tx_token.hex())


        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_token.hex())
        if tx_receipt['status'] == 1:
            print("Status: Success")
        else:
            print("Status: Failed")
    else:
        logging.info("AmountIn = 0")
        print("Swap Failed. Amount int = 0")


def Buy(token_list, trans_data, price, decimal):
    reverse_list = token_list[::-1]
    decimal_reverse = decimal[::-1]
    Swap(reverse_list, trans_data, 1 / price, decimal_reverse)


def Sell(token_list, trans_data, price, decimal):
    Swap(token_list, trans_data, price, decimal)


def RunSwap(token, action, trans_data):
    pair1 = pancake_factory.functions.getPair(token[0], token[1]).call()
    pair_contract1 = web3.eth.contract(address=pair1, abi=json_abi)
    reverse1 = not (pair_contract1.functions.token0().call().lower() == token[0].lower())

    token_contract0 = web3.eth.contract(address=token[0], abi=json_abi)
    token_contract1 = web3.eth.contract(address=token[1], abi=json_abi)

    decimal0 = token_contract0.functions.decimals().call()
    decimal1 = token_contract1.functions.decimals().call()

    decimal_pair1 = decimal0 - decimal1 if not reverse1 else decimal1 - decimal0

    decimal_list = [decimal0, decimal1]

    symbol0 = token_contract0.functions.symbol().call()
    symbol1 = token_contract1.functions.symbol().call()

    if len(token) == 3:
        pair2 = pancake_factory.functions.getPair(token[1], token[2]).call()
        pair_contract2 = web3.eth.contract(address=pair2, abi=json_abi)
        reverse2 = not (pair_contract2.functions.token0().call().lower() == token[1].lower())

        token_contract2 = web3.eth.contract(address=token[2], abi=json_abi)
        decimal2 = token_contract1.functions.decimals().call()

        decimal_pair2 = decimal1 - decimal2 if not reverse2 else decimal2 - decimal1

        decimal_list[1] = decimal2

        symbol1 = token_contract2.functions.symbol().call()

    pair_name = symbol0 + "/" + symbol1

    logging.info("Started checking price:%s", pair_name)
    print("Started checking price: ", pair_name)

    global my_account
    wallet_address = my_account.address

    amount_input = 0

    if trans_data.amount_input != 0:
        amount_input = trans_data.amount_input
    elif action == Auto.Buy:
        if len(token) == 3:
            amount_input = token_contract2.functions.balanceOf(wallet_address).call() * pow(10, -decimal2)
        else:
            amount_input = token_contract1.functions.balanceOf(wallet_address).call() * pow(10, -decimal1)
    elif action == Auto.Sell:
        amount_input = token_contract0.functions.balanceOf(wallet_address).call() * pow(10, -decimal0)
    else:
        print("No Action")
        return

    print("Press Q to quit")
    print("Press S to swap")
    print("Amount in: ", amount_input)

    global user_action

    while user_action == UserAction.NoAction:
    
        if web3.isConnected():
            current_price1 = CalculatePrice(pair_contract1, reverse1, decimal_pair1)
            if len(token) == 3:
                current_price2 = CalculatePrice(pair_contract2, reverse2, decimal_pair2)
                current_price = current_price1 * current_price2
            else:
                current_price = current_price1

            logging.info("Price = %lf", current_price)
            est_out = (amount_input * current_price) if action == Auto.Sell else (amount_input / current_price)
            print("Price = ", current_price, " Estimated output:", est_out,end="\r")
    
    print("Price = ", current_price, ". Estimated output:", est_out)

    if user_action == UserAction.Swap:
        print("Swapping......")
        if action == Auto.Sell:
            Sell(token, trans_data, current_price, decimal_list)
        elif action == Auto.Buy:
            Buy(token, trans_data, current_price, decimal_list)


def MessageSendAll():
    while len(message_queue) > 0:
        notifi_mutex.acquire()
        msg = message_queue.pop(0)
        notifi_mutex.release()

        result = False
        retry = 0

        while (result == False) and (retry < 5):
            result = MessageNotify(msg, retry)
            retry = retry + 1

            if not result:  # sleep 5sec if send failure
                time.sleep(5)

def KeyHook():
    global user_action
    a = m.getch()
    while (a != b'q') and (a != b's'):
        a = m.getch()

    if a == b'q':
        user_action = UserAction.Quit
    elif a == b's':
        user_action = UserAction.Swap


def LoadConfig(config_file):
    try:
        config_object = ConfigParser()
        config_object.read(config_file)

        general = config_object["general"]

        global pancake_factory_addr
        global pancake_router_addr
        global sound_alamp
        global msg_notifi
        global notifi_delay
        global get_price_delay
        global mnemonic
        global passphrase
        global tele_api_key

        pancake_factory_addr = general["PancakeFactory"]
        pancake_router_addr = general["PancakeRouter"]
        sound_alamp = BoolMap[general["SoundAlarm"]]
        msg_notifi = BoolMap[general["MessageNotification"]]
        notifi_delay = int(general["NotificationDelay"]) / 1000
        get_price_delay = int(general["GetPriceDelay"]) / 1000

        if msg_notifi:
            global chat_id

            bot_cfg = config_object["bot"]
            tele_api_key = bot_cfg["ApiKey"]
            chat_id = int(bot_cfg["ChatID"])

        wallet_info = config_object["wallet"]
        mnemonic = wallet_info["Mnemonic"]
        passphrase = wallet_info["Passphrase"] if config_object.has_option("wallet", "Passphrase") else ""

        return True

    except:
        logging.error("config.ini format is incorrect")
        print("config.ini format is incorrect")
        return False


def ConnectTeleBot(api_key):
    global bot
    if msg_notifi:
        try:
            bot = telebot.TeleBot(api_key)
        except:
            logging.error("Telegram bot can not connect")
            print("Telegram bot can not connect")
            return False
        else:
            logging.info("Telegram bot connected")
            return True


def LoadData(data_file):
    data = ConfigParser()
    data.read(data_file)

    global transaction_info
    global token_list
    global auto_swap

    sw_input = data["Input"]

    try:
        token1 = Web3.toChecksumAddress(sw_input["Token1"])
        token2 = Web3.toChecksumAddress(sw_input["Token2"])

        token_list = [token1, token2]

        if data.has_option("Input", "Token3"):
            token3 = Web3.toChecksumAddress(sw_input["Token3"])
            token_list.append(token3)

        s_auto_swap = sw_input["AutoSwap"]
        auto_swap = ActionMap[s_auto_swap]

        if auto_swap != Auto.No:
            slippage_tolerance = float(sw_input["SlippageTolerance"])

            amount_input = float(sw_input["AmountInput"])

            s_gas_price = sw_input["GasPrice"]
            gas_price = web3.toWei(s_gas_price, 'gwei')

            s_gas = sw_input["Gas"]
            gas = int(s_gas)

            time_limit = int(int(sw_input["TimeLimit"]) / 1000)

            logging.info("Slippage Tolerance: %.3lf. Amount In: %.3lf. Gas Price: %ld. Gas: %d. Time limit: %d",
                         slippage_tolerance, amount_input, gas_price, gas, time_limit)

            transaction_info = TransactionData(slippage_tolerance, amount_input, gas_price, gas, time_limit)
            return True
        else:
            return False
    except:
        logging.error("data.ini format is incorrect")
        print("data.ini format is incorrect")
        return False


def main():
    if not LoadConfig('config.ini'):
        return False

    if not ConnectTeleBot(tele_api_key):
        return False

    if not LoadABI('abi.json'):
        return False

    if not ConnectBSC(pancake_factory_addr, pancake_router_addr, mnemonic, passphrase):
        return False

    if not LoadData('data_insw.ini'):
        return False

    key_th = threading.Thread(target=KeyHook, args=())
    key_th.start()

    RunSwap(token_list, auto_swap, transaction_info)

    MessageSendAll()

    key_th.join()

    logging.info("Program Exit")


if __name__ == "__main__":
    main()
