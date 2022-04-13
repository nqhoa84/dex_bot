
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
import requests

pancake_factory = 0
pancake_router = 0 
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

def ConnectBSC():
    # privateKey is the private key
    bsc = "https://bsc-dataseed.binance.org/"
    global w3
    global priKey, my_account, startBlock
    try:
        w3 = Web3(Web3.HTTPProvider(bsc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if(w3.isConnected()):
            my_account = w3.eth.account.from_key(priKey)
            print("ADDR: ", my_account.address)
            logging.info("ADDR: %s", my_account.address)
        
    except:
        logging.exception("Connect to BSC and Pancake failed")
        return False

    if w3.isConnected():
        logging.info("Connected to BSC") 
    else:
        logging.error("Failed to connect to BSC")
        return False

    return True
  

def AddMessage(message):
    try :    
        notifi_mutex.acquire()
        message_queue.append(message)
        notifi_mutex.release()
    except: 
        logging.exception('======ERROR SENDING TELEGRAM MESSAGE===========')

def SoundAlert():
    try :    
        sound_mutex.acquire()
        beepy.beep(6)
        logging.info("Sound Alert")
        sound_mutex.release()
    except: 
        logging.exception('======ERROR PLAYING SOUND===========')
        
    


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
  
def loadCfg():
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
    global api_key
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
    return config_object, msg_notifi, api_key, pancake_factory_addr, pancake_router_addr, priKey, passphrase

def main():
    try:
        loadCfg()
        if msg_notifi:
            global bot
            bot = telebot.TeleBot(api_key)
        Notify("Bot Monitor started")
        
        if not ConnectBSC():
            return False 
    except:
        logging.exception("Fail to start")
        WriteConsoleLog("Fail to start")
        return 0
 

    # First setup to connect to BSC
    

    WriteConsoleLog("Bot started")
    
    if not ProgramTerminated:
        ht = threading.Thread(target=KeyHook, args=())
        ht.start()
        
        fromBlk = 0
        dr = threading.Thread(target=apeTL, args=(fromBlk,))
        dr.start()
        #
        # fromBlk2 = 0
        # dr2 = threading.Thread(target=biTL, args=(fromBlk2,))
        # dr2.start()
        
        test = threading.Thread(target=testIn, args=())
        test.start()
        
        ms = threading.Thread(target=MessageSendAll(), args=())
        ms.start()
        
        # bscBlock = threading.Thread(target=getLatestBlock, args=())
        # bscBlock.start()

        ht.join()
        # dr.join()
        # dr2.join()
        test.join()
        ms.join()
        # bscBlock.join()  
    
    logging.info("Program Exit")

bscScanApiKey = 'KVSYTVNS7ZCISVCCZQDU4G1F3436XA3HMW'
apeTLaddr = '0x2F07969090a2E9247C761747EA2358E5bB033460'
bsc = "https://bsc-dataseed.binance.org/"
apeChefAddr = '0x5c8D727b265DBAfaba67E050f2f739cAeEB4A6F9'

biTLaddr = '0xf5D6fed0f4735Ff2036cE4be535bD32e77dAE9fe'
biChefAddr = '0xDbc1A13490deeF9c3C12b44FE77b503c1B061739'

def getAllTxs (strAddr, fromBlk = 10000000, toBlock = 99999999):
    url = 'https://api.bscscan.com/api?module=account&action=txlist&address=' + strAddr + '&startblock=' + str(fromBlk) + '&endblock=99999999&sort=asc&apikey=' + bscScanApiKey
    print('get txs: block = ', fromBlk, 'addr: ', strAddr, sep = " ")
    baseUrl = 'https://api.bscscan.com/api'
    PARAMS = {'module':'account',
              'action':'txlist',
              'address':strAddr,
              'startblock':fromBlk,
              'endblock':toBlock,
              'sort':'asc',
              'apikey':bscScanApiKey
              }
    
    r = requests.get(url = baseUrl, params = PARAMS)
  
    # extracting data in json format
    data = r.json()
    print(data)
    if(data['status'] == '1') : 
        return data['result']
    return []
    
def processTx(apeTLcontract, chefContract, tx, projectName= 'APE'):
    global w3
    if(not w3.isConnected()) :
        w3 = Web3(Web3.HTTPProvider(bsc))
    
    funcObj, funcParams = apeTLcontract.decode_function_input(tx["input"])
    strFunctionName = str(funcObj)
    logging.info(strFunctionName)
    logging.info(str(funcParams))
    if (strFunctionName == '<Function queueTransaction(address,uint256,string,bytes,uint256)>' 
        #or strFunctionName == '<Function cancelTransaction(address,uint256,string,bytes,uint256)>' 
        #or strFunctionName == '<Function executeTransaction(address,uint256,string,bytes,uint256)>'
        ):
        try:
            funcObj, funcParams = chefContract.decode_function_input(funcParams["data"])
            logging.info(str(funcObj))
            logging.info(str(funcParams))
            Notify(projectName + ': ' + strFunctionName + ' \n' + str(funcObj) + '\n' + str(funcParams))
        except:
            logging.exception("error")
            Notify(projectName + ': ' + strFunctionName + ', check quick')
    else:
        try:
            funcObj, funcParams = chefContract.decode_function_input(funcParams["data"])
            logging.info(str(funcObj))
            logging.info(str(funcParams))
            AddMessage(projectName + ': ' + strFunctionName + ' \n' + str(funcObj) + '\n' + str(funcParams))
        except:
            logging.exception("error")
            AddMessage(projectName + ': ' + strFunctionName + ', check quick')

def apeTL(fromBlk = 0): 
    WriteConsoleLog('====================checking APE TL')
    logging.info('==========================checking APE TL')
    global w3
    # global apeTLcontract, chefContract
    # global apeTLabi, apeChefContractAbi
    
    apeTLabi = json.load(open('abi/apeTLabi.json', 'r'))
    
    abi_json_file = open('abi/apeChefAbi.json', 'r')
    apeChefContractAbi = json.load(abi_json_file)
    
    # f"https://api.etherscan.io/api?module=contract&action=getabi&address={tx['to']}&apikey={ETHERSCAN_API_KEY}"
    if(not w3.isConnected()) :
        w3 = Web3(Web3.HTTPProvider(bsc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0) 
    
    apeTLcontract = w3.eth.contract(address = apeTLaddr, abi=apeTLabi)
    chefContract = w3.eth.contract(address=apeChefAddr, abi=apeChefContractAbi)
    
    currBlk = w3.eth.block_number
    startBlk = currBlk
    if (fromBlk >= 10507286) :
        startBlk = fromBlk
    
    countRun = 0
    while not ProgramTerminated :
        try:
             
            countRun += 1
            if (countRun % 120 == 119 and msg_notifi) :
                AddMessage("Bot check ape timelock running.") 
                
            logging.info("getting all txs from block " + str(startBlk))
            txs = getAllTxs(apeTLaddr, startBlk) 
            for tx in txs:
                logging.info(tx)
                blk = int(tx['blockNumber'], 10)
                if(blk >= startBlk): 
                    startBlk = blk + 1
                
                processTx(apeTLcontract, chefContract, tx, 'APE')
                #TODO check cancel transaction
        except: 
            logging.exception("error")
            print('--------- ERROR------------------')
        Delay(120)

def biTL(fromBlk = 0): 
    WriteConsoleLog('====================checking BI TL')
    logging.info('==========================checking BI TL')
    global w3
    # global contractTL, contractChef
    # global abiTL, abiChef
    
    abiTL = json.load(open('abi/biTLabi.json', 'r'))
    
    abi_json_file = open('abi/biChefAbi.json', 'r')
    abiChef = json.load(abi_json_file)
    
    # f"https://api.etherscan.io/api?module=contract&action=getabi&address={tx['to']}&apikey={ETHERSCAN_API_KEY}"
    if(not w3.isConnected()) :
        w3 = Web3(Web3.HTTPProvider(bsc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0) 
    
    contractTL = w3.eth.contract(address = biTLaddr, abi=abiTL)
    
    # abi_endpoint = f"https://api.etherscan.io/api?module=contract&action=getabi&address={biChefAddr}&apikey={bscScanApiKey}"
    # abi = json.loads(requests.get(abi_endpoint).text)
    # contractChef = w3.eth.contract(address=biChefAddr, abi=abi["result"])
    #

    contractChef = w3.eth.contract(address=biChefAddr, abi=abiChef)
    
    currBlk = w3.eth.block_number
    startBlk = currBlk
    if (fromBlk >= 10007286) :
        startBlk = fromBlk
    countRun = 0
    while not ProgramTerminated : 
        try:
            countRun += 1
            if (countRun % 40 == 119 and msg_notifi) :
                AddMessage("Bot check BI timelock running.")
                
            WriteConsoleLog("getting all txs from block " + str(startBlk))
            logging.info("getting all txs from block " + str(startBlk))
            
            txs = getAllTxs(biTLaddr, startBlk) 
            for tx in txs:
                logging.info(tx)
                blk = int(tx['blockNumber'], 10)
                if(blk >= startBlk): 
                    startBlk = blk + 1
                    
                processTx(contractTL, contractChef, tx, 'Biswap')
                #TODO check cancel transaction
        except: 
            logging.exception("error")
            print('--------- ERROR------------------')  
        Delay(300)

def testIn():
    swapBy1in(fromTkn = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 
              toTkn = '0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82', 
              amountInWei = 100000000000000000)
    

oneInSwapUrl = 'https://api.1inch.exchange/v3.0/56/swap'
def swapBy1in(fromTkn, toTkn, amountInWei, slippage=1):
    '''0xeee...eee is the native token of chain. No need to approve. 
    you need to approve unlimited for fromTkn to swapped. 
    '''
    global w3, my_account
    print('swapBy1in from ', fromTkn, ' to ', toTkn, ' with amount ', str(amountInWei / pow(10, 18)), ' slippage = ', slippage,'%')
    logging.info('swapBy1in from %s  to %s  with amount %s  slippage = %f', fromTkn, toTkn,  str(amountInWei / pow(10, 18)), slippage)
    
    PARAMS = {'fromTokenAddress':fromTkn,  
              'toTokenAddress':toTkn, 
              'amount': amountInWei, #str(0.01 * pow(10, 18)),
              'fromAddress':my_account.address,
              'slippage':slippage
              } 
    
    nonce = w3.eth.get_transaction_count(my_account.address) + 1 
    txnData = apiCaller(oneInSwapUrl,PARAMS, nonce) #       //call the api to get the data, and wait until it returns
    logging.info('Global data==============================');
    logging.info(txnData);                
    signed_txn = my_account.sign_transaction(txnData)
    tx_token = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("Swap done: https://bscscan.com/tx/" + tx_token.hex())
    logging.info("Swap done: https://bscscan.com/tx/%s", str(tx_token.hex()))
    AddMessage("Swap done: https://bscscan.com/tx/" + tx_token.hex())
    webbrowser.open('https://bscscan.com/tx/' + tx_token.hex())
        
    
    
def apiCaller(url, paras, nonce) :
    logging.info(url)
    temp = requests.get(url = oneInSwapUrl, params = paras)               #//get the api call
    # print (temp, "get call")
    # print (temp.text, "TEXT")
    # print (temp.content, "CONTENT")
    # logging.info('temp1 ============');
    # logging.info(temp);
    # temp = temp.content;                               #//we only want the data object from the api call
    # logging.info('temp2 ============');
    # logging.info(temp);
    
    data = temp.json()
    print('encode', str(data))
    temp = data

    #//we also need value in the form of hex
    value = int(temp['tx']["value"])          #  //get the value from the transaction
    value = str(hex(value))             #//add a leading 0x after converting from decimal to hexadecimal
    # console.log('temp.tx===============');
    # console.log(temp.tx);
    # console.log('value===============');
    # console.log(value);
    temp['tx']["value"] = value;                       # //set the value of value in the transaction object. value referrs to how many of the native token
    logging.info('GasPrice = %s', temp['tx']['gasPrice'])
    logging.info('GasPrice = %s', temp['tx']['gas'])
    # //temp.tx["nonce"] = nonce;                    # //ethersjs will find the nonce for the user
    # //temp.tx.chainId = 137                        # //this allows the transaction to NOT be replayed on other chains, ethersjs will find it for the user
    return temp                                  #//return the data

    
def getQuote():
    url = 'https://api.1inch.exchange/v3.0/1/quote?fromTokenAddress=0xdac17f958d2ee523a2206206994597c13d831ec7&toTokenAddress=0x2260fac5e5542a773aa44fbcfedf7c193bc2c599&amount=10000000000'
    # r = requests.get(url = url, params = PARAMS)
    r = requests.get(url = url)
  
    # extracting data in json format
    data = r.json()
    print(data)

if __name__ == "__main__":
    main()
