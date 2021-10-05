
from web3 import Web3
from web3.middleware import geth_poa_middleware
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

tranCount = 0

lstMonitorTokens = [
    '0x758FB037A375F17c7e195CC634D77dA4F554255B' #dvi
    , '0x4e840AADD28DA189B9906674B4Afcb77C128d9ea' #hotbit- HTB
    , '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82' #Cake
    , '0xf0E406c49C63AbF358030A299C0E00118C4C6BA5' # NVT
    ]

bscHttpAnkr = "https://apis.ankr.com/97522e91a426495491f0246ba13ae63a/b8f7775c4893656bf95c6abb3cecfb2c/binance/full/main";
bscWssAnkr = "wss://apis.ankr.com/wss/97522e91a426495491f0246ba13ae63a/b8f7775c4893656bf95c6abb3cecfb2c/binance/full/main";
bscWssQuicknode = "wss://quiet-summer-cloud.bsc.quiknode.pro/e93f9bf5b881c4123a45e5496d4fc74a4d8c5194/";
polyWssAnkr = "wss://apis.ankr.com/wss/b2704173031a4cbb9509d03c25f7098b/b8f7775c4893656bf95c6abb3cecfb2c/polygon/full/main";
ethHttpAnkr = "https://apis.ankr.com/89da184e515f4a96a953699920c28d03/b8f7775c4893656bf95c6abb3cecfb2c/eth/fast/main";

usedUrl = bscHttpAnkr

    
pancake_factory = 0
pancake_router = 0
w3 = ""
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


notifi_mutex = threading.Lock()
sound_mutex = threading.Lock()
data_mutex = threading.Lock()
draw_mutex = threading.Lock()
console_mutex = threading.Lock()

logging.basicConfig(filename=F"./log/{datetime.now().strftime('%d-%m-%Y-%Hh%M')}.log",
                    filemode='w',
                    format='[%(asctime)s,%(msecs)03d][%(levelname)s][%(thread)d][%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

TransactionData = namedtuple('TransactionData',
                             ['slippage_tolerance', 'amount_input', 'gas_price', 'gas', 'time_limit'])


class SwapAction(enum.Enum):
    Buy_TkOut = 1
    Sell_TkIn = 2 
    NotIn = 3
    Other = 4

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
    
    # IF CANNOT SUBSCRIBE FOR TRANSACTION, USE BELOW NODE. 
    # key = 'a788fbe5-6832-4e23-864a-4a97f5a302a4'
    # bsc = 'https://bsc.getblock.io/mainnet/?api_key=' + key
     
    global w3
    global my_account, startBlock
    try:
        w3 = Web3(Web3.HTTPProvider(bsc))

        global pancake_factory
        global pancake_router
        pancake_factory = w3.eth.contract(address=factory_addr, abi=json_abi)
        pancake_router = w3.eth.contract(address=router_addr, abi=json_abi)

        w3.eth.account.enable_unaudited_hdwallet_features()
        #my_account = w3.eth.account.from_mnemonic(privateKey, passphrase)
        my_account = w3.eth.account.from_key(privateKey)
        
        startBlock = w3.eth.block_number 
        
    except:
        logging.error("Connect to BSC and Pancake failed")
        return False

    if w3.isConnected():
        logging.info("Connected to BSC")
        logging.info("Wallet Address: %s", my_account.address)
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
    
def CalculateBnbPrice():
    pair = pancake_factory.functions.getPair("0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56", "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c").call()
    pair_contract = w3.eth.contract(address=pair, abi=json_abi)
    
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
    
def CalculateLP(pair, bnbPrice = 500.0):
    
    pair = pancake_factory.functions.getPair(pair[0], pair[1]).call()
    pair_contract = w3.eth.contract(address=pair, abi=json_abi)

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


def RunCheck(position, token, trend, freq, value, action, flex_slip, trans_data):
    
    MonitorAllPendings()
    
    return True

    # IGNORE THE BELOW OLD CODE. DON'T CARE. 
    
    global ProgramTerminated
    global notifi_delay
    global get_price_delay 
    
    exit_condition = False

    price_q = []  
    latestBlock = startBlock 

    pair1 = pancake_factory.functions.getPair(token[0], token[1]).call()
    pair_contract1 = w3.eth.contract(address=pair1, abi=json_abi)
    reverse1 = not (pair_contract1.functions.token0().call().lower() == token[0].lower())

    token_contract0 = w3.eth.contract(address=token[0], abi=json_abi)
    token_contract1 = w3.eth.contract(address=token[1], abi=json_abi)

    decimal0 = token_contract0.functions.decimals().call()
    decimal1 = token_contract1.functions.decimals().call()

    decimal_pair1 = decimal0 - decimal1 if not reverse1 else decimal1 - decimal0

    decimal_list = [decimal0, decimal1]

    symbol0 = token_contract0.functions.symbol().call()
    symbol1 = token_contract1.functions.symbol().call()
    
    if len(token) == 3:
        pair2 = pancake_factory.functions.getPair(token[1], token[2]).call()
        pair_contract2 = w3.eth.contract(address=pair2, abi=json_abi)
        reverse2 = not (pair_contract2.functions.token0().call().lower() == token[1].lower())

        token_contract2 = w3.eth.contract(address=token[2], abi=json_abi)
        decimal2 = token_contract1.functions.decimals().call()

        decimal_pair2 = decimal1 - decimal2 if not reverse2 else decimal2 - decimal1

        decimal_list[1] = decimal2

        symbol1 = token_contract2.functions.symbol().call()

    pair_name = symbol0 + "/" + symbol1

    logging.info("Started checking price:%s", pair_name)

    UpdatePairName(position, pair_name)

# ======================START RUNNING LOOP TO CHECK PRICE====================
    while (not exit_condition) and (not ProgramTerminated):
        Delay(get_price_delay)
        try:
            # if (not w3.isConnected):
                
            if not w3.isConnected(): 
                raise Exception("Connection error")
            curr = w3.eth.block_number
            if(curr == latestBlock) :
                #do nothing
                continue
            elif (curr == latestBlock + 1) : 
                latestBlock = curr  
                if((latestBlock - startBlock) % 200 == 1):
                    bnbPrice = CalculateBnbPrice()
                    LPinUsd = CalculateLP(token, bnbPrice)
                    UpdateLP(position, math.floor(LPinUsd))
                    
            else :
                logging.error("Block changed fast: from %i to %i >> clear the price_queue", latestBlock, curr)
                latestBlock = curr
                ClearPriceQ(price_q) 
                continue
            
            #logging.info("Start calculation %s", pair_name)
            current_price1 = CalculatePrice(pair_contract1, reverse1, decimal_pair1)
            if len(token) == 3:
                current_price2 = CalculatePrice(pair_contract2, reverse2, decimal_pair2)
                current_price = current_price1 * current_price2
            else:
                current_price = current_price1
            
        except Exception as expt:
            # WriteConsoleLog("Can not calculate the Price - " + pair_name)
            UpdateCurrentPrice(position, '_', '---')
            logging.error("Can not calculate the Price %s", pair_name)
            logging.error(expt)
            ClearPriceQ(price_q) 

    logging.info("Exit loop:%d:%s", position, pair_name)


def DrawTable():
    table = Texttable()
    global ProgramTerminated

    while not ProgramTerminated:
        table.header(
            ["No.", "Pair", "Alert Type", "Frequency","Block", "Current Price", "LP","Value Meet", "Action", "Slip", "Amount In"])
        table.set_cols_width([3, 8, 12, 10, 8, 13, 9, 12, 7, 11, 12])
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
    table_data[pos][4] = block
    table_data[pos][5] = price
    data_mutex.release()
    
def UpdateLP(pos, value):
    table_data[pos][6] = f"{value:,}"

def UpdatePairName(pos, name):
    table_data[pos][1] = name

def KeyHook():
    global ProgramTerminated
    a = m.getch()
    while a != b'q':
        time.sleep(1)
        a = m.getch()

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
            if w3.isConnected() : 
                curr = w3.eth.block_number
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


def loadConfig():
    global pancake_factory_addr
    global pancake_router_addr
    global priKey
    global sound_alamp
    global msg_notifi
    global notifi_delay
    global get_price_delay
    global chat_id
    global latestBlock
    global api_key
    config_object = ConfigParser()
    config_object.read("config.ini")
    general = config_object["general"]
    pancake_factory_addr = general["PancakeFactory"]
    pancake_router_addr = general["PancakeRouter"]
    sound_alamp = BoolMap[general["SoundAlarm"]]
    msg_notifi = BoolMap[general["MessageNotification"]]
    notifi_delay = int(general["NotificationDelay"]) / 1000
    get_price_delay = int(general["GetPriceDelay"]) / 1000
    bot_cfg = config_object["bot"]
    api_key = bot_cfg["ApiKey"]
    chat_id = int(bot_cfg["ChatID"])
    wallet_info = config_object["wallet"]
    priKey = wallet_info["priKey"]
    #return pancake_factory_addr, pancake_router_addr, sound_alamp, msg_notifi, notifi_delay, get_price_delay, api_key, priKey

def logConfig(): 
    logging.info("==============CONFIG DATA======================")
    logging.info('[general]')
    logging.info("PancakeFactory= %s", pancake_factory_addr)
    logging.info("PancakeRouter= %s", pancake_router_addr)
    logging.info("sound_alamp= %s", str(sound_alamp))
    logging.info("msg_notifi= %s", str(msg_notifi))
    logging.info("notifi_delay= %s", str(notifi_delay))
    logging.info("get_price_delay= %s", str(get_price_delay))
    logging.info('[bot]')
    logging.info("ApiKey= %s", api_key)
    logging.info("ChatID= %s", chat_id)
    logging.info('[wallet]')
    logging.info("priKey= %s.....%s", priKey[0:5], priKey[-5:]) 
    logging.info("==============END CONFIG DATA======================")
  
def startTeleBot():
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

def MonitorAllPendings():
    global latestBlock
    
    if(not w3.isConnected()) :
        return False;
    
    event_filter = w3.eth.filter('pending')
    # txHashes = event_filter.get_all_entries()
    
    while True:
        time.sleep(0.3)
        a = time.time()
        latestBlock = w3.eth.block_number
        b = time.time()
        logging.info("time to get block number: %9f", b - a)
        try: 
            txHashes = event_filter.get_new_entries()
        except: 
            logging.exception("Can not filter new entries")
            continue
        
        c = time.time()
        logging.info("time to get_new_entries: %9f, total hx: %i", c - b, len(txHashes))
        
        for h in txHashes :
            
            # OPEN THREAD TO PROCESS HASH
            subT = threading.Thread(target=processTxInNewThread, args=(h,))
            subT.start() 
        
        d = time.time()
        logging.info("time to process all hashes: %9f", d - c)

def processTxInNewThread(txHash):
    logging.error("begin---- %s", txHash.hex())
    try:
        try :
            aa = time.time()
            tran = w3.eth.getTransaction(txHash)
            logging.info("time_to_get_1_tx: %9f", time.time() - aa)
        except Exception as e:
            logging.error(e)
        else: 
            aa2 = time.time()
            processTx(tran)
            logging.info("time_to_process1_tx: %9f", time.time() - aa2)
    # except TransactionNotFound as nfe:
    #     logging.info('not found')
    except Exception as e:
        logging.exception('============SOMETHING WRONG= PROCESS TX')
        
    logging.error("end---- %s", txHash.hex())

def processTx(tran):
    txHash = tran['hash']
    if(tran['to'] == pancake_router_addr) :
        logging.info('find tx on Cake router, hx %s', txHash.hex())
        # print('router action: ' + txHash.decode('ascii'))
        swapAct, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, tkPath, deadline = checkIsSwapTx(tran)
        logging.info("tx Hash %s, %s, %s, %i, %s, %0f, %s", txHash.hex(), swapAct, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, tkPath)
        #TODO Big BUY have not been processed. 
        if(swapAct == SwapAction.Sell_TkIn or swapAct == SwapAction.Buy_TkOut) :
            tkInInLP, tkOutInLp = getBalanceInpair(tkInAddr, [tkInAddr, tkPath[1]])
            logging.info('tkInInLP %s, tkOutInLp %s', tkInInLP, tkOutInLp) 

                #if you want to sell/buy do it here quickly. 


def checkIsSwapTx(tx): 
    
    # check tx is a SELL order AND sell-token is in monitor list ??
    funcObj, funcParams = decodeInput(tx)
    strFunc = str(funcObj)
    logging.info(strFunc)
    logging.info(str(funcParams))
    
    # this is 3 human-swapAtoB tx types. others type are bots. 
    # if(strFunc.find('swapExactTokensForETH')) :
    if(strFunc == '<Function swapExactTokensForETH(uint256,uint256,address[],address,uint256)>') :    
        logging.info(str(tx))
        #detect swapAtoB trans
        tkInAddr = funcParams['path'][0] 
        tkInValue = funcParams['amountIn'] 
        tkOutAddr = funcParams['path'][-1]
        tkOutValueMin = funcParams['amountOutMin'] 
        deadline = funcParams['deadline']
        
        if (tkInAddr in lstMonitorTokens) :
            return SwapAction.Sell_TkIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        if (tkOutAddr in lstMonitorTokens) :
            return SwapAction.Buy_TkOut, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        
        return SwapAction.NotIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
           
    elif (strFunc == '<Function swapExactTokensForTokens(uint256,uint256,address[],address,uint256)>' ): 
        logging.info(str(tx))
        tkInAddr = funcParams['path'][0]
        tkInValue = funcParams['amountIn']
        tkOutAddr = funcParams['path'][-1]
        tkOutValueMin = funcParams['amountOutMin']
        deadline = funcParams['deadline']
        if (tkInAddr in lstMonitorTokens) :
            return SwapAction.Sell_TkIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        if (tkOutAddr in lstMonitorTokens) :
            return SwapAction.Buy_TkOut, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        return SwapAction.NotIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        
    elif (strFunc == '<Function swapExactETHForTokens(uint256,address[],address,uint256)>'):
        logging.info(str(tx))
        tkInAddr = funcParams['path'][0]
        tkInValue = tx['value'] 
        tkOutAddr = funcParams['path'][-1]
        tkOutValueMin = funcParams['amountOutMin'] 
        deadline = funcParams['deadline']
        if (tkInAddr in lstMonitorTokens) :
            return SwapAction.Sell_TkIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        if (tkOutAddr in lstMonitorTokens) :
            return SwapAction.Buy_TkOut, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        return SwapAction.NotIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
    
    return SwapAction.Other, 0,0,0,0,[], 0
        
constInTokenPercent = [0,1.00,1.50,2.00,2.50,3.00,3.50,4.00,4.50,5.00,5.50,6.00,6.50,7.00,7.50,8.00,8.50,9.00,9.50,10.00,10.50,11.00,11.50,12.00,13.00,14.00,15.00,16.00,17.00,18.00,19.00,20.00,21.00,22.00,23.00,24.00,25.00,26.00,27.00,28.00,29.00,30.00,31.00,32.00,33.00,34.00,35.00,36.00,37.00,38.00,39.00,40.00,41.00,42.00,43.00,44.00,45.00,46.00,47.00,48.00,49.00,50.00,55.00,60.00,65.00,70.00,75.00,80.00,85.00,90.00,95.00,100.00,105.00,110.00,115.00,120.00,125.00,130.00 ]
constOuTokenPercent = [0,0.99,1.47,1.96,2.43,2.91,3.37,3.84,4.30,4.75,5.20,5.65,6.09,6.53,6.96,7.39,7.82,8.24,8.66, 9.07, 9.48, 9.89,10.29,10.69,11.48,12.25,13.02,13.76,14.50,15.22,15.93,16.63,17.32,18.00,18.66,19.32,19.96,20.59,21.22,21.83,22.44,23.03,23.62,24.20,24.77,25.33,25.88,26.42,26.96,27.49,28.01,28.52,29.03,29.53,30.02,30.50,30.98,31.45,31.92,32.38,32.83,33.28,35.43,37.44,39.33,41.12,42.80,44.38,45.88,47.31,48.66, 49.94, 51.16, 52.32, 53.43, 54.48, 55.49, 56.46 ]

def calculateExpectedOutPut(percentIn, totalTkInLP, totalOutInLP):
    
    if(percentIn > 100) :
        raise Exception("Too large sell, could be hack :((")
         
    for idx in range(1, 75):
        # print(constInTokenPercent[idx])
        print('idx =', idx, 'constInTokenPercent[idx]=', constInTokenPercent[idx], 'perc = ', percentIn, sep=',')
        if(constInTokenPercent[idx] <= percentIn) : 
            continue
        outLowPercent = constOuTokenPercent[idx-1]
        outHighPercent = constOuTokenPercent[idx]
        print('outLowPercent =', outLowPercent, outHighPercent, sep=", ")
        
        increToLow = (percentIn - constInTokenPercent[idx-1]) / (constInTokenPercent[idx] - constInTokenPercent[idx-1])
        amountOutPC = increToLow * (constOuTokenPercent[idx] - constOuTokenPercent[idx-1]) + constOuTokenPercent[idx-1]
        
        print('increToLow =', increToLow, 'amountOutPC=', amountOutPC, sep=", ")
        
        return amountOutPC * totalOutInLP / 100
        break
    return 0


def getBalanceInpair(sellToken, pair):
    # pair is list of 2 token addresses.
    #return: balance, price = sellToken / baseToken (normally bnb or busd)
    ## TODO should store contract object for each pair to quick access and avoid flood call.  
    pairAddr = pancake_factory.functions.getPair(pair[0], pair[1]).call()
    pair_contract = w3.eth.contract(address=pairAddr, abi=json_abi)

    addr0 = pair_contract.functions.token0().call()
    addr1 = pair_contract.functions.token1().call()
    
    r0, r1, tsp = pair_contract.functions.getReserves().call()
    
    if(addr0 == sellToken) :
        return r0, r1
    elif(addr1 == sellToken) :
        return r1, r0
    else: 
        raise Exception('Invalid token in pair: ' + pairAddr + ". pair: " + str(pair))

def decodeInput(tx):
    # Decode input data using Contract object's decode_function_input() method
    try :
        funcObj, funcParams = pancake_router.decode_function_input(tx["input"])
        return str(funcObj), funcParams;
    except: 
        logging.info("Can not decode input")
        return "Can not decode input", 0



def getTokenMonitoringsFromConfig():
    logging.info("========= MONITORED TOKEN==========")
    for i in range(0, len(lstMonitorTokens)):
        token_contract0 = w3.eth.contract(address=lstMonitorTokens[i], abi=json_abi)
        decimal0 = token_contract0.functions.decimals().call()
        symbol0 = token_contract0.functions.symbol().call()
        lstMonitorTokens[i] = lstMonitorTokens[i].lower()
        logging.info("token%i, %s, %s, decimal %i", i, lstMonitorTokens[i], symbol0, decimal0)
    
    logging.info("========= end MONITORED TOKEN==========")

def main():
    try: 
        loadConfig() 
        logConfig()
        startTeleBot()
        
        LoadABI('abi.json')
        # First setup to connect to BSC
        if not ConnectBSC(pancake_factory_addr, pancake_router_addr, priKey):
            return False
        
        getTokenMonitoringsFromConfig()
        
        MonitorAllPendings()
        
    except Exception as e:
        logging.error("Error %s", e)
        WriteConsoleLog("SOMETHING WRONG, CHECK LOG. ")
        return 0
    
    thread_arr = []
    # skip first section
    data = ConfigParser()
    data.read("dataV3.ini")
    #
    global table_data 
    #
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
    
            if auto_swap != Auto.No:
                slippage_tolerance = float(data.get(section, "SlippageTolerance"))
                amount_input = float(data.get(section, "AmountInput"))
                s_gas_price = data.get(section, "GasPrice")
                gas_price = w3.toWei(s_gas_price, 'gwei')
                s_gas = data.get(section, "Gas")
                gas = int(s_gas)
                time_limit = int(int(data.get(section, "TimeLimit")) / 1000)
                flex_slip = BoolMap[data.get(section, "FlexibleSlippage")]
    
                logging.info(
                    "Slippage Tolerance: %.3lf. Flexible Slippage: %s. Amount In: %.3lf. Gas Price: %ld. Gas: %d. Time limit: %d",
                    slippage_tolerance, str(flex_slip), amount_input, gas_price, gas, time_limit)
    
                trans_data = TransactionData(slippage_tolerance, amount_input, gas_price, gas, time_limit)
        except:
            logging.error("data.ini format is incorrect")
            WriteConsoleLog("data.ini format is incorrect")
            global ProgramTerminated
            ProgramTerminated = True
            break
    
        # load json data
        if auto_swap == Auto.No:
            table_data.append(
                [index + 1, "N/A", s_alert_type, s_frequency,0, 0, "_", str(value), s_auto_swap, "NA", "NA"])
        else:
            table_data.append(
                [index + 1, "N/A", s_alert_type, s_frequency,0, 0, "_", str(value), s_auto_swap, slippage_tolerance, amount_input])
    
        logging.info("Token list: {}".format(' '.join(map(str, token_list))))
        # calling threading
        # th = threading.Thread(target=RunCheck,
        #                       args=(index, token_list, alert_type, frequency, value, auto_swap, flex_slip, trans_data))
        # th.start()
        #
        # thread_arr.append(th)

    if not ProgramTerminated:
        ht = threading.Thread(target=KeyHook, args=())
        ht.start()
    
        dr = threading.Thread(target=DrawTable, args=())
        dr.start()
    
        ms = threading.Thread(target=MessageSendAll(), args=())
        ms.start()
    
        # pending = threading.Thread(target=MonitorAllPendings, args=())
        # pending.start() 
    
        ht.join()
        dr.join()
        ms.join()
        # pending.join()
    #     # bscBlock.join() 
    #
    for th in thread_arr:
        th.join()

    while True :
        # print("now is: " + str(time.time()))
        WriteConsoleLog("now is: " + str(time.time()))
        time.sleep(1)
    
    logging.info("Program Exit")

def getTransactionInfo(txHash):
    tx = w3.eth.getTransaction(txHash)
    print(str(tx))

if __name__ == "__main__":
    main()
