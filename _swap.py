
from web3 import Web3
import json
import beepy
import enum
import time
import math
import threading
from configparser import ConfigParser
import telebot
from texttable import Texttable
import msvcrt as m
from os import system, name
import logging
from datetime import datetime
from collections import namedtuple
import webbrowser 
import dexlib 
from dexlib import swapBnbToToken1in, swapTokenToBnb1in, swap1in, isBnbAddr

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
swap_in_stable = 0
canStart = False


notifi_mutex = threading.Lock()
sound_mutex = threading.Lock()
data_mutex = threading.Lock()
draw_mutex = threading.Lock()
console_mutex = threading.Lock()

logging.basicConfig(filename=F"./log/{datetime.now().strftime('%d-%m-%Y')}.log",
                    filemode='w',
                    format='[%(asctime)s,%(msecs)03d][%(levelname)s][%(thread)d][%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

TransactionData = namedtuple('TransactionData',
                             ['slippage_tolerance', 'amount_input', 'gas_price', 'gas', 'time_limit', 'dex'])


class Trend(enum.Enum):
    RiseUpTo = 1
    DropTo = 2
    ChangeIsOver = 3


class Freq(enum.Enum):
    OneTime = 1
    Always = 2


class PriceRev(enum.Enum):
    Above = 1
    Under = 2


class Auto(enum.Enum):
    No = 0
    Buy = 1
    Sell = 2


AlertTypeMap = {
    'RiseUpTo': Trend.RiseUpTo,
    'DropTo': Trend.DropTo,
    'ChangeIsOver': Trend.ChangeIsOver
}

FreqMap = {
    'OneTime': Freq.OneTime,
    'Always': Freq.Always
}

ActionMap = {
    'No': Auto.No,
    'Buy': Auto.Buy,
    'Sell': Auto.Sell
}

BoolMap = {
    'True': True,
    'False': False
}


def Clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


def PushPrice(price_q, c_price):
    if len(price_q) < 4:
        price_q.append(c_price)
    elif len(price_q) == 4:
        price_q.append(c_price)
        price_q.pop(0)


def Diff1Condition(price_q):
    diff = (price_q[0] - price_q[2]) / price_q[2]

    if abs(diff) < 0.01:
        return True
    else:
        return False


def Diff2(price_q):
    #'''Returned diff of current price and previous price, in float_percentage'''    
    return (price_q[3] - price_q[2]) / price_q[2]

def PricePumpOver(price_q, thresholdInPercent):
    currPercent = (price_q[3] - price_q[2]) / price_q[2] * 100.0
    pre1Percent = (price_q[3] - price_q[1]) / price_q[1] * 100.0
    pre2Percent = (price_q[3] - price_q[0]) / price_q[1] * 100.0
    
    return thresholdInPercent > 0 and currPercent > thresholdInPercent and pre1Percent > thresholdInPercent and pre2Percent > thresholdInPercent

def PriceDumpOver(price_q, thresholdInPercent):
    currPercent = (price_q[3] - price_q[2]) / price_q[2] * 100.0
    pre1Percent = (price_q[3] - price_q[1]) / price_q[1] * 100.0
    pre2Percent = (price_q[3] - price_q[0]) / price_q[1] * 100.0
    
    return thresholdInPercent < 0 and currPercent < thresholdInPercent and pre1Percent < thresholdInPercent and pre2Percent < thresholdInPercent


def ClearPriceQ(price_q):
    price_q.clear()


def DataValid(price_q):
    return len(price_q) >= 4


def PrevPrice(price_q):
    return price_q[2]


def WriteConsoleLog(log_msg):
    global console_log
    console_mutex.acquire()
    console_log = console_log + "\n" + log_msg
    console_mutex.release()


def Delay(p):
    #Delay how many second. Float parameter.
    global ProgramTerminated
    recent = time.time()
    while (not ProgramTerminated) and ((time.time() - recent) < p):
        time.sleep(0.2)


def LoadABI(json_file):
    global json_abi
    abi_json_file = open(json_file, 'r')
    json_abi = json.load(abi_json_file)

def ConnectBscUsingConfigInfo():
    global pancake_factory_addr
    global pancake_router_addr
    global priKey
    ConnectBSC(pancake_factory_addr, pancake_router_addr, priKey)

def ConnectBSC(factory_addr, router_addr, privateKey, passphrase=''):
    # privateKey is the private key
    bsc = "https://bsc-dataseed.binance.org/"
    global web3
    global my_account, startBlock
    try:
        web3 = Web3(Web3.HTTPProvider(bsc))

        global pancake_factory
        global pancake_router
        pancake_factory = web3.eth.contract(address=factory_addr, abi=json_abi)
        pancake_router = web3.eth.contract(address=router_addr, abi=json_abi)

        web3.eth.account.enable_unaudited_hdwallet_features()
        #my_account = web3.eth.account.from_mnemonic(privateKey, passphrase)
        my_account = web3.eth.account.from_key(privateKey)
        
        startBlock = web3.eth.block_number 
        
    except:
        logging.error("Connect to BSC and Pancake failed")
        return False

    if web3.isConnected():
        logging.info("Connected to BSC")
        logging.info("Wallet Address: %s", my_account.address)
    else:
        logging.error("Failed to connect to BSC")
        return False

    return True


def CalculatePrice(pair_contract, reverse=False, decimal=0):
    #return humanPrice, amount_token0, amount_token1
    r0, r1, tsp = pair_contract.functions.getReserves().call()
      
    if reverse:
        return (r0 / r1) * pow(10, decimal)
    else:
        return (r1 / r0) * pow(10, decimal)
    # f = open("./test.txt", "r")
    # v = float(f.readline())
    # f.close()
    # return v
    
def CalculateBnbPrice():
    pair = pancake_factory.functions.getPair("0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56", "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c").call()
    pair_contract = web3.eth.contract(address=pair, abi=json_abi)
    
    addr0 = pair_contract.functions.token0().call().lower();
    #addr1 = pair_contract.functions.token1().call().lower();
    
    r0, r1, tsp = pair_contract.functions.getReserves().call()
    
    #because bnb and busd have the same decimal. 
    if(addr0 == "0xe9e7cea3dedca5984780bafc599bd69add087d56"): #busd
        logging.debug("BnbPrice: %f, ", r0/r1)
        return r0/r1
    else:
        logging.debug("BnbPrice: %f, ", r1/r0)
        return r1/r0
    
def CalculateLP(token, bnbPrice = 359.0):
    
    pair = pancake_factory.functions.getPair(token[0], token[1]).call()
    pair_contract = web3.eth.contract(address=pair, abi=json_abi)

    addr0 = pair_contract.functions.token0().call().lower();
    addr1 = pair_contract.functions.token1().call().lower();
    
    r0, r1, tsp = pair_contract.functions.getReserves().call()
    totalLP = 0
    if(addr0 == "0xe9e7cea3dedca5984780bafc599bd69add087d56"): #busd
        totalLP = r0/1000000000000000000*2
    elif(addr0 == "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"): #bnb
        totalLP = r0/1000000000000000000*2*bnbPrice
    elif(addr1 == "0xe9e7cea3dedca5984780bafc599bd69add087d56"): #busd
        totalLP = r1/1000000000000000000*2
    elif(addr1 == "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"): #bnb
        totalLP = r1/1000000000000000000*2*bnbPrice
    
    logging.debug("r0: %s : %f, r1: %s: %f, totalLP %f", addr0, r0, addr1, r1, totalLP)
    
    return totalLP; 
    

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
        WriteConsoleLog("Error sending Telegram message. Retry" + str(retry))
        return False
    else:
        logging.info("Message Notification:%s", message)
        return True


def Notify(message):
    if sound_alamp:
        SoundAlert()

    if msg_notifi:
        AddMessage(message)

def getBalance(tokenAddr = 'native'):
    global my_account
    wallet_address = my_account.address
    
    if('native' == tokenAddr or isBnbAddr(tokenAddr)) :
        return web3.eth.get_balance(wallet_address) - 0.01 * pow(10, 18) #0.01 bnb is use for tx fee.
    else :
        return web3.eth.contract(address = tokenAddr, abi=json_abi).functions.balanceOf(wallet_address).call()

def Swap1in(token_list, trans_data, price, decimal):
    logging.info("Token list: {}".format(' '.join(map(str, token_list))))
    logging.info("Price: %lf", price)
    global my_account, priKey
    # wallet_address = my_account.address 
    
    amount_in = int(trans_data.amount_input * pow(10, decimal[0]))
    # currBal = web3.eth.contract( address=token_list[0], abi=json_abi).functions.balanceOf(wallet_address).call()
    currBal = getBalance(token_list[0])
    logging.info("currBal: %s", currBal)
    if(currBal < amount_in):
        amount_in = currBal 
    
    if amount_in > 0:
        try:
            if token_list[0].lower() == '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c':  
                txn = swapBnbToToken1in(toTokenAddress=token_list[-1], amount=amount_in, 
                                  slippage=trans_data.slippage_tolerance,
                                  priKey=priKey) 
            elif token_list[-1].lower() == '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c':
                txn = swapTokenToBnb1in(fromTokenAddress=token_list[0], amount=amount_in, 
                                  slippage=trans_data.slippage_tolerance,
                                  priKey=priKey) 
            else:
                txn = swap1in(fromTokenAddress=token_list[0], toTokenAddress= token_list[-1], 
                        amount=amount_in, slippage=trans_data.slippage_tolerance,
                                  priKey=priKey) 
             
            url = "https://bscscan.com/tx/" + str(txn['data']['hash'])
            logging.info("============%s", url);
            WriteConsoleLog(url)
            AddMessage(url)
            webbrowser.open(url)
            return True
        except: 
            logging.exception("===================ERROR")
    else:
        logging.info("======================AmountIn = 0")
        return False

def SwapDirect(token_list, trans_data, price, decimal):
    logging.info("Token list: {}".format(' '.join(map(str, token_list))))
    logging.info("Price: %lf", price)
    global my_account
    wallet_address = my_account.address

    # amount_in = int(
    #     trans_data.amount_input * pow(10, decimal[0])) if trans_data.amount_input != 0 else web3.eth.contract(
    #     address=token_list[0], abi=json_abi).functions.balanceOf(wallet_address).call() 
    
    amount_in = int(trans_data.amount_input * pow(10, decimal[0]))
    # currBal = web3.eth.contract( address=token_list[0], abi=json_abi).functions.balanceOf(wallet_address).call()
    currBal = getBalance(token_list[0])
    logging.info("currBal: %s", currBal)
    if(currBal < amount_in):
        amount_in = currBal 
    
    if(isBnbAddr(token_list[0])) :
        amount_in = max(0, amount_in - 0.01 * pow(10, 18));
        
    amount_out_min = int(
    amount_in * price * (1 - trans_data.slippage_tolerance / 100) * pow(10, decimal[1] - decimal[0])) if (
        trans_data.slippage_tolerance >= 0) else 0

    logging.info("In: %d. Min out:%d", amount_in, amount_out_min)

    if amount_in > 0:
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
        print("Swap1in done: https://bscscan.com/tx/" + tx_token.hex())
        AddMessage("Swap1in done: https://bscscan.com/tx/" + tx_token.hex())
        logging.info("Swap1in done: https://bscscan.com/tx/%s", str(tx_token.hex()))
        webbrowser.open('https://bscscan.com/tx/' + tx_token.hex())


        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_token.hex())
        if tx_receipt['status'] == 1:
            print("Status: Success")
        else:
            print("Status: Failed")
    else:
        logging.info("AmountIn = 0")
        print("Swap1in Failed. Amount int = 0")

def Buy(token_list, trans_data, price, decimal):
    reverse_list = token_list[::-1]
    decimal_reverse = decimal[::-1]
    if(trans_data.dex == '1inch'):
        Swap1in(reverse_list, trans_data, 1 / price, decimal_reverse)
    elif (trans_data.dex == 'direct') :
        SwapDirect(reverse_list, trans_data, 1 / price, decimal_reverse)


def Sell(token_list, trans_data, price, decimal):
    if(trans_data.dex == '1inch'):
        Swap1in(token_list, trans_data, price, decimal)
    elif (trans_data.dex == 'direct') :
        SwapDirect(token_list, trans_data, price, decimal)
    
     


def RunCheck(position, token, trend, freq, value, action, flex_slip, trans_data):
    global ProgramTerminated
    global notifi_delay
    global get_price_delay 
    global canStart
     
    exit_condition = False

    price_q = []  
    latestBlock = startBlock 

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

    pair_name = symbol0 + "/" + symbol1

    logging.info("Started checking price:%s", pair_name)

    UpdatePairName(position, pair_name)
    
    myCountTran = 0
    
    # LPinUsd = CalculateLP(token, bnbPrice = 450)
    # UpdateLP(position, math.floor(LPinUsd))
    countLoop = 1
    LPinUsd = 0
# ======================START RUNNING LOOP TO CHECK PRICE====================
    while (not exit_condition) and (not ProgramTerminated):
        Delay(get_price_delay) 
        
        try: 
            if not web3.isConnected(): 
                raise Exception("Connection error") 
            # current_price = 0
            current_price = CalculatePrice(pair_contract1, reverse1, decimal_pair1) 
            countLoop = countLoop + 1;
            if(LPinUsd == 0 or countLoop % 10 == 9):
                LPinUsd = CalculateLP(token, bnbPrice = 450)
                UpdateLP(position, math.floor(LPinUsd))
            
        except Exception as expt:
            # WriteConsoleLog("Can not calculate the Price - " + pair_name)
            UpdateCurrentPrice(position, '_', '---')
            logging.error("Can not calculate the Price %s", pair_name)
            logging.error(expt)
            ClearPriceQ(price_q)
        else:
                
            UpdateCurrentPrice(position, current_price, latestBlock)
            logging.info("Pair %s Price: %11f, LP= %f, canStart = %s, trend=%s, value=%f", pair_name, current_price, LPinUsd, canStart, trend, value)  
        
            if canStart and (trend == Trend.RiseUpTo) and (current_price >= value) and LPinUsd > 50000:
                myCountTran += 1
                logging.info("%s = %11f. Rise Up To %11f", pair_name, current_price, value)
                if action == Auto.Sell:
                    # logging.info("-----------SELL-------------")
                    Sell(token, trans_data, current_price, decimal_list)
                
                exit_condition = (freq == Freq.OneTime)
                Notify(pair_name + ": " + str(current_price))
                Delay(3)
                
            elif canStart and (trend == Trend.DropTo) and (current_price <= value) and LPinUsd > 50000:
                logging.info("%s = %9f. Drop to %9f", pair_name, current_price, value)
                myCountTran += 1
                if action == Auto.Buy:
                    # logging.info("-----------BUY-------------")
                    Buy(token, trans_data, current_price, decimal_list) 

                exit_condition = (freq == Freq.OneTime)
                Notify(pair_name + ": " + str(current_price))
                Delay(3)
                 
    logging.info("Exit loop:%d:%s", position, pair_name)


def DrawTable():
    table = Texttable()
    global ProgramTerminated

    while not ProgramTerminated:
        table.header(
            ["No.", "Pair", "Type", "Frequency","Time", "Current Price", "LP","Value Meet", "Action", "Slip", "Amount In", "Dex"])
        table.set_cols_width([3, 8, 12, 10, 10, 13, 9, 12, 7, 11, 12, 10])
        table.set_precision(9)
        table.add_rows(table_data, False)

        table.set_deco(Texttable.HEADER)

        Clear()
        print(table.draw())
        print(console_log)
        table.reset()
        Delay(3)


def UpdateCurrentPrice(pos, price, block = 1):
    data_mutex.acquire()
    #now = datetime.now()
    table_data[pos][4] = datetime.now().strftime('%H:%M:%S')
    table_data[pos][5] = price
    data_mutex.release()
    
def UpdateLP(pos, value):
    table_data[pos][6] = value

def UpdatePairName(pos, name):
    table_data[pos][1] = name



def KeyHook():
    global ProgramTerminated, canStart
    global canStart
    a = m.getch()
    while a != b'q':
        time.sleep(1)
        a = m.getch()
        if(canStart == False and a == b's') : 
            logging.info("Key Q pressed - Exit")
            WriteConsoleLog("Program started.")
            canStart = True;

    ProgramTerminated = True
    WriteConsoleLog("Terminate")
    logging.info("Key Q pressed - Exit")


def MessageSendAll():
    global ProgramTerminated
    while not ProgramTerminated:
        if len(message_queue) > 0:
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

        time.sleep(1)
        
def getLatestBlock():
    # global latestBlock
    logging.error("come here========================")
    try: 
        while True :
            Delay(0.1)
            if web3.isConnected() : 
                curr = web3.eth.block_number
                if(curr > latestBlock) :
                    logging.info("Block change from %d to %d", latestBlock, curr)
                    latestBlock = curr
                    Delay(2)
            else: 
                logging.error("NOT CONNECTED=======================")
                latestBlock = 0;
    except:
        logging.error("CAN NOT GET LATEST BLOCK")
        Notify("CAN NOT GET LATEST BLOCK")

def main():
    try:
        config_object = ConfigParser()
        config_object.read("config.ini")

        general = config_object["general"]

        global pancake_factory_addr
        global pancake_router_addr
        global priKey
        global sound_alamp
        global msg_notifi
        global notifi_delay
        global get_price_delay
        global swap_in_stable
        
        global latestBlock

        pancake_factory_addr = general["PancakeFactory"]
        pancake_router_addr = general["PancakeRouter"]
        sound_alamp = BoolMap[general["SoundAlarm"]]
        msg_notifi = BoolMap[general["MessageNotification"]]
        notifi_delay = int(general["NotificationDelay"]) / 1000
        get_price_delay = int(general["GetPriceDelay"]) / 1000
        swap_in_stable = int(general["SwapInStable"]) / 1000
        
        logging.info("==============CONFIG DATA======================")
        logging.info("pancake_factory_addr= %s", pancake_factory_addr)
        logging.info("pancake_router_addr= %s", pancake_router_addr)
        logging.info("sound_alamp= %s", str(sound_alamp))
        logging.info("msg_notifi= %s", str(msg_notifi))
        logging.info("notifi_delay= %s", str(notifi_delay))
        logging.info("get_price_delay= %s", str(get_price_delay)) 
        logging.info("==============END CONFIG DATA======================")
        
        if msg_notifi:
            global chat_id

            bot_cfg = config_object["bot"]
            api_key = bot_cfg["ApiKey"]
            chat_id = int(bot_cfg["ChatID"])

        wallet_info = config_object["wallet"]
        priKey = wallet_info["priKey"]
        passphrase = wallet_info["Passphrase"] if config_object.has_option("wallet", "Passphrase") else ""

    except:
        logging.error("config.ini format is incorrect")
        WriteConsoleLog("config.ini format is incorrect")
        return 0

    if msg_notifi:
        try:
            global bot
            bot = telebot.TeleBot(api_key)
        except:
            logging.error("Telegram bot can not connect")
            WriteConsoleLog("Telegram bot can not connect")
        else:
            logging.info("Telegram bot connected")
            Notify("Bot started")

    LoadABI('abi.json')

    # First setup to connect to BSC
    if not ConnectBSC(pancake_factory_addr, pancake_router_addr, priKey, passphrase):
        return False

    # skip first section
    data = ConfigParser()
    data.read("dataSwap.ini")

    thread_arr = []

    global table_data 
    
    for index, section in enumerate(data.sections()):
        try:
            token1 = Web3.toChecksumAddress(data.get(section, "Token1"))
            token2 = Web3.toChecksumAddress(data.get(section, "Token2"))

            token_list = [token1, token2]
            if data.has_option(section, "Token3"):
                token3 = Web3.toChecksumAddress(data.get(section, "Token3"))
                token_list.append(token3)

            s_alert_type = data.get(section, "AlertType")
            alert_type = AlertTypeMap[s_alert_type]

            s_frequency = data.get(section, "Frequency")
            frequency = FreqMap[s_frequency]

            value = float(data.get(section, "Value"))

            s_auto_swap = data.get(section, "AutoSwap")
            auto_swap = ActionMap[s_auto_swap]

            trans_data = []
            flex_slip = False
            dex = "NA"
            if auto_swap != Auto.No:
                slippage_tolerance = float(data.get(section, "SlippageTolerance"))
                amount_input = float(data.get(section, "AmountInput"))
                s_gas_price = data.get(section, "GasPrice")
                gas_price = web3.toWei(s_gas_price, 'gwei')
                s_gas = data.get(section, "Gas")
                gas = int(s_gas)
                time_limit = int(int(data.get(section, "TimeLimit")) / 1000)
                flex_slip = BoolMap[data.get(section, "FlexibleSlippage")]
                dex = data.get(section, "Dex")

                logging.info(
                    "Slippage Tolerance: %.3lf. Flexible Slippage: %s. Amount In: %.3lf. Gas Price: %ld. Gas: %d. Time limit: %d, dex %s",
                    slippage_tolerance, str(flex_slip), amount_input, gas_price, gas, time_limit, dex)

                trans_data = TransactionData(slippage_tolerance, amount_input, gas_price, gas, time_limit, dex)
        except:
            logging.error("data.ini format is incorrect")
            WriteConsoleLog("data.ini format is incorrect")
            global ProgramTerminated
            ProgramTerminated = True
            break

        # load json data
        if auto_swap == Auto.No:
            table_data.append(
                [index + 1, "N/A", s_alert_type, s_frequency,0, 0, "_", str(value), s_auto_swap, "NA", "NA", "NA"])
        else:
            table_data.append(
                [index + 1, "N/A", s_alert_type, s_frequency,0, 0, "_", str(value), s_auto_swap, slippage_tolerance, amount_input, dex])

        logging.info("Token list: {}".format(' '.join(map(str, token_list))))
        # calling threading
        th = threading.Thread(target=RunCheck,
                              args=(index, token_list, alert_type, frequency, value, auto_swap, flex_slip, trans_data))
        th.start()

        thread_arr.append(th)

    if not ProgramTerminated:
        ht = threading.Thread(target=KeyHook, args=())
        ht.start()

        dr = threading.Thread(target=DrawTable, args=())
        dr.start()

        ms = threading.Thread(target=MessageSendAll(), args=())
        ms.start()
        
        # bscBlock = threading.Thread(target=getLatestBlock, args=())
        # bscBlock.start()

        ht.join()
        dr.join()
        ms.join()
        # bscBlock.join() 

    for th in thread_arr:
        th.join()

    WriteConsoleLog("Press s to start.")
    logging.info("Program Exit")



if __name__ == "__main__":
    main()
