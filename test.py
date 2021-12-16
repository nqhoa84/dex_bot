
import json
import beepy
import enum
import time
import math
import threading
from configparser import ConfigParser
import dexlib
import telebot
from texttable import Texttable
import msvcrt as m
from os import system, name
import logging
from datetime import datetime
from collections import namedtuple
import webbrowser 

from web3 import Web3
from web3.middleware import geth_poa_middleware
from fileinput import input
from dexlib import swap1in

tranCount = 0

lstMonitorTokens = [
    0x758FB037A375F17c7e195CC634D77dA4F554255B #dvi
    , 0x4e840AADD28DA189B9906674B4Afcb77C128d9ea #hotbit- HTB
    ]

minBuyInBnb = 1
minBuyInUsd = 500
maxBuyInBnb = 4
maxBuyInUsd = 2000

pancake_factory = 0
pancake_router = 0
w3 = ""
sound_alamp = True
msg_notifi = True
notifi_delay_ms = 30  # ms
bot = 0
chat_id = 0
table_data = []
ProgramTerminated = False
console_log = ""
message_queue = []
get_price_delay = 0
my_account = 0
json_abi = '' 


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

class SwapAction(enum.Enum):
    Buy_TkOut = 1
    Sell_TkIn = 2
    Other = 3

class Freq(enum.Enum):
    OneTime = 1
    Always = 2

class Auto(enum.Enum):
    No = 0
    Buy = 1
    Sell = 2
 

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

def receiveTran(error, result):
    tranCount += 1;
    print('new transaction detected: ' + str(tranCount))

def getPending():
    key = 'a788fbe5-6832-4e23-864a-4a97f5a302a4'
    wss = 'wss://bsc.getblock.io/mainnet/?api_key=' + key
    
    web3Ws = Web3(Web3.WebsocketProvider(wss));
    web3Ws.eth.subscribe('pendingTransactions', receiveTran)


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

def ConnectBSC(factory_addr, router_addr, privateKey = ''):
    # privateKey is the private key
    bsc = "https://bsc-dataseed.binance.org/"
    global w3
    global my_account, startBlock
    try:
        w3 = Web3(Web3.HTTPProvider(bsc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        global pancake_factory 
        global pancake_router  
        
        pancake_factory = w3.eth.contract(address=factory_addr, abi=json_abi)
        pancake_router = w3.eth.contract(address=router_addr, abi=json_abi)

        w3.eth.account.enable_unaudited_hdwallet_features() 
        my_account = w3.eth.account.from_key(privateKey)
        
        startBlock = w3.eth.block_number 
        
    except Exception as e:
        WriteConsoleLog("Connect to BSC and Pancake failed")
        raise e
        return False    

    return True 

def Test():
    global w3
    global pancake_factory 
    global pancake_router  
    # getBlockNode = 'https://eth.getblock.io/mainnet/?api_key=a788fbe5-6832-4e23-864a-4a97f5a302a4'
    
    
    # w3 = Web3(Web3.HTTPProvider(getBlockNode))
    # w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    
    # # w3 = Web3(Web3.HTTPProvider(no))
    # w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161'))
    #
    # # w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    # print('latest block is: ')
    # # lB = web3.eth.getBlock('latest')
    
    if(w3.isConnected()) :
        lB = w3.eth.block_number
        print(lB)
        time.sleep(1)
        
        tx = w3.eth.getTransaction(hex(0x9318aecd1488dcec126797c6f336a8b8fca527cf42c25403ba8ad4487b33c370 ))
        
        print(tx)
        
        print('decode input data: ' + str(tx["input"]))
        # Decode input data using Contract object's decode_function_input() method
        func_obj, func_params = pancake_router.decode_function_input(tx["input"])
        
        print("func_obj: " + str(func_obj))
        print("func_params: " + str(func_params))
        

        # tran = w3.eth.getTransaction('0xb3994ae350f761ab46fc198e384a1dd7c5f8c3ebce56c2d45085d47dd89bcb59')
        # print(tran)
        
        event_filter = w3.eth.filter('pending')
        hashes = event_filter.get_all_entries()
        hashes = event_filter.get_new_entries()
        
        print(hashes)
        
        for h in hashes :
            try:
                tran = w3.eth.getTransaction(h)
                print(h)
                print(tran)
            except Exception as e: 
                print(h)
                print(e)
            
                
        # transactions = [w3.eth.getTransaction(h) for h in hashes]
        # print(transactions)
                
        
        # //10417248
        # lB2 = w3.eth.get_block('latest', False)
        # print(lB2)
    else:
        print('NOT connected')

def MonitorAllPendings():
    global w3
    
    if(not w3.isConnected()) :
        return False;
    
    lB = w3.eth.block_number
    print(lB)
    
    event_filter = w3.eth.filter('pending')
    # txHashes = event_filter.get_all_entries()
    txHashes = event_filter.get_new_entries()
    
    print(txHashes)
    
    while True:
        
        for h in txHashes :
            try:
                tran = w3.eth.getTransaction(h)
                processTx(tran)
            except Exception as e:
                logging.error(e)
        
        time.sleep(1.0)
        txHashes = event_filter.get_new_entries()

def processTx(tran):
    txHash = tran['hash']
    if(tran['to'] == pancake_router_addr) :
        print('find tx on Cake router, hx ' + txHash.hex())
        # print('router action: ' + txHash.decode('ascii'))
        swapAct, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, tkPath, deadline = checkIsSwapTx(tran)
        logging.info("tx Hash %s, %s, %s, %i, %s, %0f, %s", txHash.hex(), swapAct, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, str(tkPath))
        #TODO Big BUY have not been processed. 
        if(swapAct == SwapAction.Other or swapAct == SwapAction.Buy_TkOut) :
            return False
        
        tkInInLP, tkOutInLp = getBalanceInpair(tkInAddr, [tkInAddr, tkPath[1]])
        percentSell = tkInValue / tkInInLP * 100.0
        logging.info("percentSell: %f, tkInInLP: %s, tkOutInLp: %s", percentSell, tkInInLP, tkOutInLp)
        if(percentSell > 2.5) : #>> price changes ~5% 
            expectedOut = calculateExpectedOutPut(percentSell, tkInInLP, tkOutInLp)
            tkInLP_now = tkInInLP + tkInValue
            tkOutLP_now = tkOutInLp - expectedOut
            gas = tran['gas']
            gasPrice = tran['gasPrice']
            
            # In now become out because we want to buy token
            if(isBnbAddr(tkOutAddr)) :
                wantToSpendBNB = 0.1 * tkOutLP_now;
                if(wantToSpendBNB < 1 * pow(10, 18)):
                    logging("10% is less than 1 bnb, ignore this.");
                    return False
                if(wantToSpendBNB > 4 * pow(10, 18)) :
                    wantToSpendBNB = 4 * pow(10, 18)
                    
                minReceived = calculateExpectedOutPut(wantToSpendBNB * 100 / tkOutLP_now, 
                                                      tkOutLP_now, tkInLP_now)
                minReceived = math.floor(minReceived * 1.01) #slippage 1%
                swapAtoB(tkOutAddr, wantToSpendBNB,  tkInAddr, minReceived)
                
            elif isBusdAddr(tkOutAddr): 
                a = 0 
            else:
                a = 0

                
                #if you want to sell/buy do it here quickly. 
def swapAtoB(addrA, amountA, addrB, minReceivedB, gasLimit, gasPrice, timeLimit):
    #gasPrice the the Wei
    logging.info("swapAtoB from %s-%s to %s-", addrA, amountA, addrB, minReceivedB)
    global my_account
    wallet_address = my_account.address
    tranCount += 1
    
    if(isBnbAddr(addrA)):
        txn = pancake_router.functions.swapExactETHForTokens(
                minReceivedB,
                [addrA, addrB],
                wallet_address,
                timeLimit,
            ).buildTransaction({
                'from': wallet_address,
                'value': amountA, #w3.toWei(trans_data.amount_input, 'ether'),
                'gas': gasLimit,
                'gasPrice': gasPrice,
                'nonce': tranCount,
            })
    elif isBnbAddr(addrB) :
        txn = pancake_router.functions.swapExactTokensForETH(
                amountA,
                minReceivedB,
                [addrA, addrB],
                wallet_address,
                timeLimit,
            ).buildTransaction({
                'from': wallet_address,
                'gas': gasLimit,
                'gasPrice': gasPrice,
                'nonce': tranCount,
            })
    else:
        txn = pancake_router.functions.swapExactTokensForTokens(
                amountA,
                minReceivedB,
                [addrA, addrB],
                wallet_address,
                timeLimit
            ).buildTransaction({
                'from': wallet_address,
                'gas': gasLimit,
                'gasPrice': gasPrice,
                'nonce': tranCount,
            })
    signed_txn = my_account.sign_transaction(txn)
    tx_token = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    WriteConsoleLog("Swap done: https://bscscan.com/tx/" + tx_token.hex())
    logging.info("Swap done: https://bscscan.com/tx/%s", str(tx_token.hex()))
    AddMessage("Swap done: https://bscscan.com/tx/" + tx_token.hex())
    webbrowser.open('https://bscscan.com/tx/' + tx_token.hex())
    True       
    #
    # if amount_in != 0:
    #     if token_list[0].lower() == '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c':
    #
    #     elif token_list[-1].lower() == '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c':
    #
    #     else:
    #
    #
    #     signed_txn = my_account.sign_transaction(txn)
    #     tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    #     WriteConsoleLog("Swap done: https://bscscan.com/tx/" + tx_token.hex())
    #     logging.info("Swap done: https://bscscan.com/tx/%s", str(tx_token.hex()))
    #     AddMessage("Swap done: https://bscscan.com/tx/" + tx_token.hex())
    #     webbrowser.open('https://bscscan.com/tx/' + tx_token.hex())
    #     True
    # else:
    #     logging.info("AmountIn = 0")

def isBnbAddr(addr):
    return addr == '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'

def isBusdAddr(addr):
    return addr == '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'

def checkIsSwapTx(tx): 
    
    # check tx is a SELL order AND sell-token is in monitor list ??
    funcObj, funcParams = decodeInput(tx)
    print(funcObj)
    
    # this is 3 human-swapAtoB tx types. others type are bots. 
    if(funcObj.find('swapExactTokensForETH')) :
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
           
    elif (funcObj.find('swapExactTokensForTokens')): 
        tkInAddr = funcParams['path'][0]
        tkInValue = funcParams['amountIn']
        tkOutAddr = funcParams['path'][-1]
        tkOutValueMin = funcParams['amountOutMin']
        deadline = funcParams['deadline']
        if (tkInAddr in lstMonitorTokens) :
            return SwapAction.Sell_TkIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        if (tkOutAddr in lstMonitorTokens) :
            return SwapAction.Buy_TkOut, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
    elif (funcObj.find('swapExactETHForTokens')):
        tkInAddr = funcParams['path'][0]
        tkInValue = tx['value'] 
        tkOutAddr = funcParams['path'][-1]
        tkOutValueMin = funcParams['amountOutMin'] 
        deadline = funcParams['deadline']
        if (tkInAddr in lstMonitorTokens) :
            return SwapAction.Sell_TkIn, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
        if (tkOutAddr in lstMonitorTokens) :
            return SwapAction.Buy_TkOut, tkInAddr, tkInValue, tkOutAddr, tkOutValueMin, funcParams['path'], deadline
    
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
    print('decode input data: ' + str(tx["input"]))
    # Decode input data using Contract object's decode_function_input() method
    funcObj, funcParams = pancake_router.decode_function_input(tx["input"])
    return str(funcObj), funcParams;

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

def loadConfig():
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
    global chat_id
    global api_key
    
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

def startTeleBot():
    if msg_notifi:
        logging.info("start tele bot")
        global bot
        bot = telebot.TeleBot(api_key)

def main3():
    global latestBlock
    try:
        loadConfig()
        logConfig()
        startTeleBot()
        
        LoadABI('abi.json')
        
        # First setup to connect to BSC
        if not ConnectBSC(pancake_factory_addr, pancake_router_addr, priKey):
            return False
        
        if w3.isConnected():
            WriteConsoleLog("Connected to BSC")
            logging.info("Wallet Address: %s", my_account.address)
        else:
            WriteConsoleLog("Failed to connect to BSC")
            return False
        
        input("Press Enter to continue...")
        
    except Exception as e:
        logging.error(e)
        WriteConsoleLog("SOMETHING WRONG, PLEASE CHECK LOG " + e)
        return 0
  
    # # skip first section
    # data = ConfigParser()
    # data.read("data.ini")
    #
    # thread_arr = []
    #
    # global table_data 
    #
    # for index, section in enumerate(data.sections()):
    #     try:
    #         token1 = Web3.toChecksumAddress(data.get(section, "Token1"))
    #         token2 = Web3.toChecksumAddress(data.get(section, "Token2"))
    #
    #         token_list = [token1, token2]
    #         if data.has_option(section, "Token3"):
    #             token3 = Web3.toChecksumAddress(data.get(section, "Token3"))
    #             token_list.append(token3) 
    #
    #         s_frequency = data.get(section, "Frequency")
    #         frequency = FreqMap[s_frequency]
    #
    #         value = float(data.get(section, "Value"))
    #
    #         s_auto_swap = data.get(section, "AutoSwap")
    #         auto_swap = ActionMap[s_auto_swap]
    #
    #         trans_data = []
    #         flex_slip = False
    #
    #         if auto_swap != Auto.No:
    #             slippage_tolerance = float(data.get(section, "SlippageTolerance"))
    #             amount_input = float(data.get(section, "AmountInput"))
    #             s_gas_price = data.get(section, "GasPrice")
    #             gas_price = w3.toWei(s_gas_price, 'gwei')
    #             s_gas = data.get(section, "Gas")
    #             gas = int(s_gas)
    #             time_limit = int(int(data.get(section, "TimeLimit")) / 1000)
    #             flex_slip = BoolMap[data.get(section, "FlexibleSlippage")]
    #
    #             logging.info(
    #                 "Slippage Tolerance: %.3lf. Flexible Slippage: %s. Amount In: %.3lf. Gas Price: %ld. Gas: %d. Time limit: %d",
    #                 slippage_tolerance, str(flex_slip), amount_input, gas_price, gas, time_limit)
    #
    #             # trans_data = TransactionData(slippage_tolerance, amount_input, gas_price, gas, time_limit)
    #     except:
    #         logging.error("data.ini format is incorrect")
    #         WriteConsoleLog("data.ini format is incorrect")
    #         global ProgramTerminated
    #         ProgramTerminated = True
    #         break
    #
    #     # load json data
    #     # if auto_swap == Auto.No:
    #     #     table_data.append(
    #     #         [index + 1, "N/A", s_alert_type, s_frequency,0, 0, "_", str(value), s_auto_swap, "NA", "NA"])
    #     # else:
    #     #     table_data.append(
    #     #         [index + 1, "N/A", s_alert_type, s_frequency,0, 0, "_", str(value), s_auto_swap, slippage_tolerance, amount_input])
    #     #
    #     # logging.info("Token list: {}".format(' '.join(map(str, token_list))))
    #     # # calling threading
    #     # th = threading.Thread(target=RunCheck,
    #     #                       args=(index, token_list, alert_type, frequency, value, auto_swap, flex_slip, trans_data))
    #     # th.start()
    #     #
    #     # thread_arr.append(th)
    #
    # if not ProgramTerminated:
    #     ht = threading.Thread(target=KeyHook, args=())
    #     ht.start()
    #
    #     dr = threading.Thread(target=DrawTable, args=())
    #     dr.start()
    #
    #     ms = threading.Thread(target=MessageSendAll(), args=())
    #     ms.start()
    #
    #     # bscBlock = threading.Thread(target=getLatestBlock, args=())
    #     # bscBlock.start()
    #
    #     ht.join()
    #     dr.join()
    #     ms.join()
    #     # bscBlock.join() 
    #
    # for th in thread_arr:
    #     th.join()
    #
    #
    # logging.info("Program Exit")


    
def main2():
    a = abc()
    print (a)
    # print (b)
    hai = 929674.3
    bnb = 226.34
    tkIn = 999
    outTk = calculateExpectedOutPut(tkIn,hai, bnb)
    print(hai, bnb, tkIn, outTk, sep=",")
    
def abc():
    a = 'so a'
    b = 3
    return a,b

def apeTL():
    input('Checking ape timelock')
    bsc = "https://bsc-dataseed.binance.org/"
    apeTLaddr = '0x2F07969090a2E9247C761747EA2358E5bB033460'
    apeChefAddr = '0x5c8D727b265DBAfaba67E050f2f739cAeEB4A6F9'
    
    global w3
    global apeTLcontract, chefContract
    global apeTLabi, apeChefContractAbi
    
    apeTLabi = json.load(open('abi/apeTLabi.json', 'r'))
    
    abi_json_file = open('abi/apeChefAbi.json', 'r')
    apeChefContractAbi = json.load(abi_json_file)
   
    w3 = Web3(Web3.HTTPProvider(bsc))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0) 
    
    apeTLcontract = w3.eth.contract(address = apeTLaddr, abi=apeTLabi)
    chefContract = w3.eth.contract(address=apeChefAddr, abi=apeChefContractAbi)
    
    tx = w3.eth.getTransaction(0x1eae2a98c6448094094cf2f6add67fab9d6ca0a599c5407d8fe6a22c62e653d8)
    
    print(tx)
    
    print('decode input data: ' + str(tx["input"]))
    # Decode input data using Contract object's decode_function_input() method
    funcObj, funcParams = apeTLcontract.decode_function_input(tx["input"])
    
    print(str(funcObj))
    print(str(funcParams))
    
    
    funcObj, funcParams = chefContract.decode_function_input(funcParams["data"])
    
    print('decode data from above tran')
    print(str(funcObj))
    print(str(funcParams))
      
      
def ab():
    a = b = 0
    print(a, b)
    
        

if __name__ == "__main__":
    i = 0
    while(i < 10) :
        print(round(time.time()))
        time.sleep(1);
        i = i + 1;
    # swap1in('from', 'to', 10000, 1, 'prikey')
