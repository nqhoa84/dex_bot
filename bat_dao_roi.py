
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
requestData = []
mapPairReserves = {}
mapPairPriceList = {}
mapPairLP = {}
mapPairTickersDecimals = {}
lstTime = []

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


def PushPrice(price_q, c_price, time_q):
    price_q.append(c_price)
    time_q.append(round(time.time()))
    if(time_q[-1] - time_q[0] > 4000) :
        price_q.pop(0)
        time_q.pop(0)
    # logging.info(price_q)
    # logging.info(time_q)
    
    # if len(price_q) < 4:
    #     price_q.append(c_price)
    # elif len(price_q) == 4:
    #     price_q.append(c_price)
    #     price_q.pop(0)
    
    
def Change(price_q, time_q, secondsAgo):
    msLatest = time_q[-1];
    i = 1
    while(i < len(time_q)):
        if(msLatest - time_q[0 - i] > secondsAgo):
            # print('stop at i =' + str(i))
            return (price_q[-1] - price_q[0 - i]) / price_q[0 - i]
            break
        i = i + 1;
    # print('reach to i = 0')
    return (price_q[-1] - price_q[0]) / price_q[0]


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


def ClearPriceQ(price_q, time_q):
    price_q.clear()
    time_q.clear()


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
        time.sleep(0.1)


def LoadABI(json_file):
    global json_abi
    global proxy_json_abi
    abi_json_file = open(json_file, 'r')
    json_abi = json.load(abi_json_file)
    
    proxy_json_abi = json.load(open('proxyabi.json', 'r'))


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
        global proxy_contract
        global proxy_addr;
        pancake_factory = web3.eth.contract(address=factory_addr, abi=json_abi)
        pancake_router = web3.eth.contract(address=router_addr, abi=json_abi)
        proxy_contract = web3.eth.contract(address=proxy_addr, abi=proxy_json_abi)

        web3.eth.account.enable_unaudited_hdwallet_features()
        #my_account = web3.eth.account.from_mnemonic(privateKey, passphrase)
        my_account = web3.eth.account.from_key(privateKey)
        
        startBlock = web3.eth.block_number 
        
        
        # test get all reserves.
        requestData = [['0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', '0xF0A8EcBCE8caADB7A07d1FcD0f87Ae1Bd688dF43'], ['0x2963dCc52549573BBFBe355674724528532C0867', '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'], ['0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', '0xec6cA5A04B08e382d218De9Cb30C9d8176406D34'], ['0x9fD87aEfe02441B123c3c32466cD9dB4c578618f', '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'], ['0x3465fD2D9f900e34280aBab60E8d9987B5b5bb47', '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'], ['0x6397de0F9aEDc0F7A8Fa8B438DDE883B9c201010', '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56']]
        reseverData = proxy_contract.functions.getReversesMulti(factory_addr, requestData).call()
        logging.info('---------------------------------')
        logging.info(reseverData)
        logging.info('---------------------------------')
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
    
def RunCheck2():
    logging.info('run check 2----------')
    for [addr0, addr1] in requestData:
        pair1 = pancake_factory.functions.getPair(addr0, addr1).call()
        pair_contract1 = web3.eth.contract(address=pair1, abi=json_abi)
        token_contract0 = web3.eth.contract(address=addr0, abi=json_abi)
        token_contract1 = web3.eth.contract(address=addr1, abi=json_abi)
        decimal0 = token_contract0.functions.decimals().call()
        decimal1 = token_contract1.functions.decimals().call()
        symbol0 = token_contract0.functions.symbol().call()
        symbol1 = token_contract1.functions.symbol().call()
        
        tickersPair = f'{symbol0}/{symbol1}'
        if(symbol0 == 'BNB' or symbol0 == 'BUSD' or symbol0 == 'WBNB'):
            tickersPair = f'{symbol1}/{symbol0}'
            
        keyPair = addr0 + addr1
        mapPairTickersDecimals[keyPair] = {'tickers': [symbol0.upper(), symbol1.upper()], 
                                           'tickersPair' : tickersPair,
                                           'decimals': [decimal0, decimal1]}
        mapPairReserves[keyPair] = [1,1]
        mapPairPriceList[keyPair] = [1]
        mapPairLP[keyPair] = 1
        lstTime.append(round(time.time()))
        
    
    UpdateTable()
    keys = mapPairTickersDecimals.keys()
    for k in keys:
        logging.info(k)
        logging.info(mapPairTickersDecimals[k])
        # price = 
        # mapPairPriceList[k].append()
    
def RunCheck(position, token, trend, freq, value, action, flex_slip, trans_data):
    global ProgramTerminated
    global notifi_delay
    global get_price_delay 
    global dropBelow
    
    exit_condition = False

    price_q = []  
    time_q = []
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

    UpdatePairName(position, pair_name)
    
    LPinUsd = -1
    runCount = 0

# ======================START RUNNING LOOP TO CHECK PRICE====================
    while (not exit_condition) and (not ProgramTerminated): 
        try:
            # if (not web3.isConnected):
                
            if not web3.isConnected(): 
                raise Exception("Connection error")
            
            if(runCount % 100 == 0):
                bnbPrice = CalculateBnbPrice()
                LPinUsd = math.floor(CalculateLP(token, bnbPrice))
                UpdateLP(position, LPinUsd)
            
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
            # ClearPriceQ(price_q)
        else:
            
            UpdateCurrentPrice(position, current_price, latestBlock)
            logging.info("Block: %i, %s Price: %11f", latestBlock, pair_name, current_price)
            
            PushPrice(price_q, current_price, time_q)
            change1min = Change(price_q, time_q, 60)
            change5min = Change(price_q, time_q, 60 * 5)
            change15min = Change(price_q, time_q, 60 * 15)
            change30min = Change(price_q, time_q, 60 * 30)
            change1h = Change(price_q, time_q, 60 * 60)
            logging.info("change1h %f, change5min %f, change1min %f, ", change1h, change5min, change1min)
            # UpdateChange(position, change1h, change5min, change1min)
            UpdateChange(position, change1min, change5min, change15min, change30min, change1h);
            
            if(change15min < dropBelow or change5min < dropBelow or change1min < dropBelow or change1h < dropBelow):
                LPinUsd = math.floor(CalculateLP(token, bnbPrice))
                UpdateLP(position, LPinUsd)
                Notify(pair_name + ": change1h {:.1f}%,".format(change1h * 100) + " change5min {:.1f}%,".format(change5min * 100) + " change1min {:.1f}%,".format(change1min * 100) + " LP {:.0f}$,".format(LPinUsd))
                Notify('https://poocoin.app/tokens/' + str(token[0]))
                ClearPriceQ(price_q, time_q)
        Delay(get_price_delay)
            
    logging.info("Exit loop:%d:%s", position, pair_name)

def getTickers(keyPair):
    try :
        return mapPairTickersDecimals[keyPair]['tickers']
    except:
        return '-/-'
    
def getPriceLPFromReserves(keyPair):
    bnbPrice = 555
    [sym0, sym1] = mapPairTickersDecimals[keyPair]['tickers']
    [r0, r1] = mapPairReserves[keyPair]
    [dec0, dec1] = mapPairTickersDecimals[keyPair]['decimals']
    
    price = (r1 / (10**dec1))/(r0 / (10**dec0)) 
    if(sym0 == 'BNB' or sym0 == 'BUSD'):
        price = (r0 / (10**dec0))/(r1 / (10**dec1))
        pairName = f'{sym1}/{sym0}'
    
    lp = 0
    if(sym0 == 'BUSD'):
        lp = (r0 / (10**dec0)) * 2
    elif (sym0 == 'BNB'):
        lp = (r0 / (10**dec0)) * bnbPrice * 2
    elif (sym1 == 'BUSD'):
        lp = (r1 / (10**dec1)) * 2
    elif (sym1 == 'BNB'):
        lp = (r1 / (10**dec1)) * bnbPrice * 2
    
    return [price, lp]

def getData(keyPair):
    try :
        pairName = mapPairTickersDecimals[keyPair]['tickersPair']  
        logging.info('pairName = %s', pairName)
        lstPrice = mapPairPriceList[keyPair] 
        logging.info('lstPrice = %s', lstPrice)
        
        change1min = Change(lstPrice, lstTime, 60)
        change5min = Change(lstPrice, lstTime, 60 * 5)
        change15min = Change(lstPrice, lstTime, 60 * 15) 
        change30min = Change(lstPrice, lstTime, 60 * 30) 
        change1h = Change(lstPrice, lstTime, 60 * 60)
        
        return {'pairname' : pairName, 'price' : lstPrice[-1], 'lp': mapPairLP[keyPair], 
                'change1min': change1min,  
                'change5min' :change5min, 
                'change15min' : change15min,  
                'change30min' : change30min,  
                'change1h' : change1h
                }    
    except:
        return {'pairname' : '-/-', 'price' : '', 'lp': '', 
                'change1min': '',  
                'change5min' :'', 
                'change15min' : '',  
                'change30min' : '',  
                'change1h' : ''
                }  

def DrawTable():
    table = Texttable()
    
    while not ProgramTerminated:
        table.header(
            ["No.", "Pair", "Time", "Price", "LP", "1 Min", "5 Mins", "15 Mins", "30 Mins", "1 Hour" ])
        table.set_cols_width([3, 10, 10, 10, 10, 10, 9, 9, 9, 9])
        table.set_precision(6)
        table.add_rows(table_data, False)

        table.set_deco(Texttable.HEADER)

        Clear()
        print(table.draw())
        print(console_log)
        table.reset()
        Delay(3)

def UpdateTable():
    data_mutex.acquire()
    i = 0
    size = len(requestData)
    logging.info("size = %s", size)
    nowTime = datetime.now().strftime('%H:%M:%S')
    
    while (i < 20 and i < size) :
        keyPair = requestData[i][0] + requestData[i][1]
        data = getData(keyPair)
        
        table_data[i][1] = data['pairname']
        table_data[i][2] = nowTime
        table_data[i][3] = data['price']
        table_data[i][4] = data['lp']
        table_data[i][5] = data['change1min']
        table_data[i][6] = data['change5min']
        table_data[i][7] = data['change15min']
        table_data[i][8] = data['change30min']
        table_data[i][9] = data['change1h']
        
        i = i + 1
        
    data_mutex.release()
    
def UpdateCurrentPrice(pos, price, block = 1):
    data_mutex.acquire()
    #now = datetime.now()
    table_data[pos][2] = datetime.now().strftime('%H:%M:%S')
    table_data[pos][3] = price
    data_mutex.release()
    
def UpdateLP(pos, value):
    table_data[pos][4] = "{:,}".format(value)
    
def UpdateChange(pos, change1min, change5min, change15min, change30min, change1h):
    table_data[pos][5] = "{:.1f}%".format(change1min * 100)
    table_data[pos][6] = "{:.1f}%".format(change5min * 100)
    table_data[pos][7] = "{:.1f}%".format(change15min * 100)
    table_data[pos][8] = "{:.1f}%".format(change30min * 100)
    table_data[pos][9] = "{:.1f}%".format(change1h * 100)

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
        global proxy_addr
        global priKey
        global sound_alamp
        global msg_notifi
        global notifi_delay
        global get_price_delay
        global swap_in_stable
        global dropBelow
        
        global latestBlock

        pancake_factory_addr = general["PancakeFactory"]
        pancake_router_addr = general["PancakeRouter"]
        proxy_addr = general["ProxyAddr"]
        sound_alamp = BoolMap[general["SoundAlarm"]]
        msg_notifi = BoolMap[general["MessageNotification"]]
        notifi_delay = int(general["NotificationDelay"]) / 1000
        get_price_delay = int(general["GetPriceDelay"]) / 1000
        swap_in_stable = int(general["SwapInStable"]) / 1000
        dropBelow = int(general["DropBelow"]) / 100
        
        logging.info("==============CONFIG DATA======================")
        logging.info("pancake_factory_addr= %s", pancake_factory_addr)
        logging.info("pancake_router_addr= %s", pancake_router_addr)
        logging.info("proxy_addr= %s", proxy_addr)
        logging.info("sound_alamp= %s", str(sound_alamp))
        logging.info("msg_notifi= %s", str(msg_notifi))
        logging.info("notifi_delay= %s", str(notifi_delay))
        logging.info("get_price_delay= %s", str(get_price_delay)) 
        logging.info("dropBelow= %s", str(dropBelow)) 
        logging.info("==============END CONFIG DATA==================")
        
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
            Notify("Bot BatDaoRoi.py started, dropBelow =" + str(dropBelow * 100) + "%")

    LoadABI('abi.json')

    # First setup to connect to BSC
    if not ConnectBSC(pancake_factory_addr, pancake_router_addr, priKey, passphrase):
        return False

    # skip first section
    data = ConfigParser()
    data.read("data_batdaoroi.ini")

    thread_arr = []

    global table_data 
    
    global requestData
    global mapPairReserves
    global mapPairPriceList
    global mapPairTickersDecimals 
    
    for tokenPair in data.sections():
        try:
            token1 = Web3.toChecksumAddress(data[tokenPair]['Token1'])
            token2 = Web3.toChecksumAddress(data[tokenPair]['Token2'])

            token_list = [token1, token2]
            token_list.sort(key=None, reverse=False);
            requestData.append(token_list)
            logging.info(requestData)
            
        except:
            logging.error("data.ini format is incorrect")
            WriteConsoleLog("data.ini format is incorrect")
            global ProgramTerminated
            ProgramTerminated = True
            break
        
#["No.", "Pair", "Time", "Price", "LP", "1 Min", "5 Mins", "15 Mins", "30 Mins", "1 Hour" ])
    i = 0
    size = len(requestData)
    logging.info('Total pairs: %s', size)
        
    while (i < 20 and i < size) :
        table_data.append([i+1, '-/-', '','', '','','','','',''])
        i = i + 1
        # load json data
        
        # calling threading
        # time.sleep(0.1)
        # th = threading.Thread(target=RunCheck,
        #                       args=(index, token_list, 'alert_type', 'frequency', 'value', 'auto_swap', 'flex_slip', 'trans_data'))
        # th.start()
        #
        # thread_arr.append(th)

    if not ProgramTerminated:
        ht = threading.Thread(target=KeyHook, args=())
        ht.start()

        dr = threading.Thread(target=DrawTable, args=())
        dr.start()

        # ms = threading.Thread(target=MessageSendAll(), args=())
        # ms.start() 
        
        checkTh = threading.Thread(target=RunCheck2, args=())
        checkTh.start()

        ht.join()
        dr.join()
        # ms.join() 
        checkTh.join()

    for th in thread_arr:
        th.join()

    
    logging.info("Program Exit")



if __name__ == "__main__":
    # change1h = -0.82973434
    # print(": change1h {:.1f}%".format(change1h * 100))
    # priceL = [0.002788168446097627, 0.002788168446097627, 0.002788168446097627, 0.002788168446097627, 0.002788168446097627, 0.002788168446097627, 0.002788168446097627, 0.002788168446097627, 0.0027882607669355228, 0.0027871004609916123, 0.0027871004609916123, 0.0027871004609916123, 0.0027880472950288825, 0.0027881127447925646, 0.0027880196704073296, 0.0027880196704073296, 0.0027879966771077367, 0.0027879966771077367, 0.0027879966771077367, 0.0027879966771077367, 0.002788241723941262, 0.0027882273153963886, 0.002788419767842691, 0.0027884126413354037, 0.0027884126413354037, 0.002778545698738276, 0.002778545698738276, 0.0027775360625841307, 0.0027775654235904414, 0.00277776420045661, 0.0027779026023537394, 0.0027772482703226392, 0.0027774139652135903, 0.0027778993222494033, 0.0027749832237976744, 0.0027750309566323774, 0.002775497680549246, 0.002764400947715874, 0.0027613228720253565, 0.0027613228720253565, 0.0027607978842419004, 0.002760936414996105, 0.0027610541036073772, 0.0027610541036073772, 0.002760677142978238, 0.002758808633220286, 0.002758808633220286, 0.002758808633220286, 0.002758808633220286, 0.0027588034723769793, 0.002758441115289613, 0.0027580118826004596, 0.002758026408442382, 0.002757492602222301, 0.0027574871465714293, 0.0027574871465714293, 0.002757475183022341, 0.002771406124124312, 0.0027716788597953877, 0.0027717916194629484, 0.002771026338090431, 0.002771026338090431, 0.0027706444019245397, 0.0027706970580575383, 0.0027710666916211037, 0.0027699791068810896, 0.002770932211359809, 0.002771584558878148, 0.0027715263136998624, 0.0027715263136998624, 0.0027715117177377754, 0.0027715117177377754, 0.0027794377185364288, 0.0027795087358433676, 0.0027887458772493903, 0.002792503572508168, 0.0027924495518572593, 0.0027935648326708343, 0.002805285088256763, 0.0028055223707475576, 0.0028110025342246454, 0.0028113597494872373, 0.0028120307530653857, 0.002812481671731694, 0.002813225603616986, 0.002814685153975857, 0.002812319553507042, 0.0028155531882920752, 0.0028155531882920752, 0.002821914874931777, 0.002822647333408183, 0.0028210454550437907, 0.0028213208539990407, 0.002822937009460294, 0.0028251683883309744, 0.002825714210749568, 0.002831503450689458, 0.0028339744471374685, 0.002845606320548479, 0.0028520596447595033, 0.0028501044608921122, 0.0028501044608921122, 0.0028504859729894996, 0.0028571658754672985, 0.0028619128062962146, 0.0028676497362980316, 0.0028950181887028694, 0.0028847254452660075, 0.002884834008847895, 0.0028921211095365887, 0.002892886701754069, 0.002895644716260605, 0.002898714824799893, 0.0029021684468982867, 0.002905183843837574, 0.0029276874629128786, 0.0029321829963139543, 0.002932835808272138, 0.0029451668011869466, 0.002945264515219777, 0.002946121331852305, 0.0029539818854089597, 0.0029596190598162497, 0.0029615657159390188, 0.0029691225224861184, 0.0029737130972665384, 0.0029758666648096906, 0.0029780859754380824, 0.0030131400640650073, 0.0030131400640650073, 0.00303496343922085, 0.0030671800555313994, 0.0030880054620002523, 0.003092937795188321, 0.0031215634904320595, 0.0031284269035212376]
    # timeL = [1638780060, 1638780073, 1638780086, 1638780099, 1638780112, 1638780125, 1638780138, 1638780151, 1638780164, 1638780177, 1638780190, 1638780203, 1638780216, 1638780229, 1638780241, 1638780254, 1638780267, 1638780280, 1638780294, 1638780307, 1638780320, 1638780333, 1638780346, 1638780359, 1638780372, 1638780385, 1638780398, 1638780411, 1638780424, 1638780436, 1638780449, 1638780462, 1638780475, 1638780488, 1638780501, 1638780514, 1638780527, 1638780540, 1638780553, 1638780566, 1638780579, 1638780592, 1638780605, 1638780617, 1638780630, 1638780643, 1638780656, 1638780669, 1638780682, 1638780695, 1638780708, 1638780721, 1638780734, 1638780747, 1638780760, 1638780773, 1638780786, 1638780799, 1638780811, 1638780824, 1638780837, 1638780850, 1638780863, 1638780876, 1638780889, 1638780902, 1638780915, 1638780928, 1638780941, 1638780954, 1638780967, 1638780980, 1638780992, 1638781005, 1638781018, 1638781031, 1638781044, 1638781057, 1638781070, 1638781083, 1638781096, 1638781109, 1638781122, 1638781135, 1638781148, 1638781161, 1638781174, 1638781187, 1638781199, 1638781212, 1638781225, 1638781238, 1638781252, 1638781264, 1638781277, 1638781290, 1638781303, 1638781316, 1638781329, 1638781342, 1638781355, 1638781368, 1638781381, 1638781394, 1638781406, 1638781419, 1638781432, 1638781445, 1638781458, 1638781471, 1638781484, 1638781497, 1638781510, 1638781523, 1638781536, 1638781549, 1638781561, 1638781574, 1638781587, 1638781600, 1638781613, 1638781626, 1638781639, 1638781652, 1638781665, 1638781678, 1638781691, 1638781704, 1638781717, 1638781730, 1638781743, 1638781756, 1638781769, 1638781782, 1638781795, 1638781807]
    # change1h = Change(priceL, timeL, 3600)
    # change5m = Change(priceL, timeL, 60*5)
    # change1m = Change(priceL, timeL, 60) 
    # print("change1m {:.10f}%".format(change1m)) 
    # print("change5m {:.10f}%".format(change5m))
    # print("change1h {:.10f}%".format(change1h))
    
    # mym = {'pos':1, 'age':2}
    # print(mym.pos)
    # print('abc '.upper())
    main()
