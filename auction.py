
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
from time import sleep

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
    global my_account, startBlock
    try:
        w3 = Web3(Web3.HTTPProvider(bsc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0) 
        
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
        # Notify("Auction Monitor started")
        
        if not ConnectBSC():
            return False 
    except:
        logging.exception("Fail to start")
        WriteConsoleLog("Fail to start")
        return 0
     
    if not ProgramTerminated:
        # ht = threading.Thread(target=KeyHook, args=())
        # ht.start()
        
        fromBlk = 0 #10667269 - 2
        dr = threading.Thread(target=monitorAc, args=(fromBlk,))
        dr.start() 
        
        ms = threading.Thread(target=MessageSendAll(), args=())
        ms.start()
        
        # bscBlock = threading.Thread(target=getLatestBlock, args=())
        # bscBlock.start()

        # ht.join()
        dr.join() 
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
    url = 'https://api.bscscan.com/api?module=account&action=tokentx&address='+ str(strAddr) +'&startblock=' + str(fromBlk)+'&endblock='+ str(toBlock) +'&sort=asc&apikey=KVSYTVNS7ZCISVCCZQDU4G1F3436XA3HMW'
    print('get txs: block = ', fromBlk, ' toblock', toBlock, ' addr: ', strAddr, sep = " ")
    print(url)
    baseUrl = 'https://api.bscscan.com/api'
    PARAMS = {'module':'account',
              'action':'txlist',
              'address':strAddr,
              'startblock':fromBlk,
              'endblock':toBlock,
              'sort':'asc',
              'apikey':bscScanApiKey
              }
    
    # r = requests.get(url = baseUrl, params = PARAMS)
    
    r = requests.get(url = url)
  
    # extracting data in json format
    data = r.json()
    print(data)
    if(data['status'] == '1') : 
        return data['result']
    return []

def getCakeBal(holderWallet):
    url = 'https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress=0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82&address='+ str(holderWallet) +'&tag=latest&apikey=KVSYTVNS7ZCISVCCZQDU4G1F3436XA3HMW'
    r = requests.get(url = url)
    data = r.json()
    print(data)
    if(data['status'] == '1') : 
        return data['result'] / 1000000000000000000
    return 0
    
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

mapAddrName = {
    '0x6a2d41c87c3f28c2c0b466424de8e08fc2e23edc'     :     ["BBT", '0xd48474e7444727bf500a32d5abe01943f3a59a64', 240000],
    '0x4ad72a0841808b431525de29a7781d948675bac7'     :     ['HTD', '0x5e2689412fae5c29bd575fbe1d5c1cd1e0622a8f'],
    '0xb8614fabf4bba416b9db620e12272ad63b14387e'     :     ['8PAY', '0xfeea0bdd3d07eb6fe305938878c0cadbfa169042'],
    '0x46d8e47b9a6487fdab0a700b269a452cfeed49aa'     :     ['MCRN', '0xacb2d47827c9813ae26de80965845d80935afd0b'],
    '0xcb70f0b3791d05d0d2aec36805fd2411a89f3aa1'     :     ['PRL', '0xd07e82440A395f3F3551b42dA9210CD1Ef4f8B24'],
    '0x05adabb0f3bff63f5f7712f05f04f509494a18f3'     :     ['HOTcross', '0x4fa7163e153419e0e1064e418dd7a99314ed27b6'],
    '0xe9ab352015928cbe21771564e97bdaa3f5fbcbac'     :     ['GRAV', '0xa6168c7e5eb7c5c379f3a1d7cf1073e09b2f031e'],
    '0xe60035673bafdad24c5b14e9556f5793dffb3362'     :     ['LOA', '0x94b69263FCA20119Ae817b6f783Fc0F13B02ad50'],
    '0x3591b656d753226de239d2b9a48221daf0751fca'     :     ['HE', '0x20d39a5130f799b95b55a930e5b7ebc589ea9ed8'],
    '0x73e60b46908319b17f1de07c5d38437bff684e50'     :     ['GEAR', '0xb4404DaB7C0eC48b428Cf37DeC7fb628bcC41B36'],
    '0x820e53c3198db5904938bec31b3ec3864a754c31'     :     ['Antex', '0xca1acab14e85f30996ac83c64ff93ded7586977c'],
    '0x8e762609cea5ddd3234b9d41cf8d0d8b4f2581a6'     :     ['TEM', '0x19e6BfC1A6e4B042Fb20531244D47E252445df01'],
    '0xf113b815e24cc866137c4933b39fe2878ed1f2d2'     :     ['RDR', '0x92da433da84d58dfe2aade1943349e491cbd6820'], #BUSD
    '0x38408a0d905930f44fe6c53321684824b22c30c5'     :     ['FIGHT', '0x4f39c3319188a723003670c3f9b9e7ef991e52f3'],
    '0xadb2d11817cd16595e4454ad03f95575c3b388f2'     :     ['MONI', '0x9573c88aE3e37508f87649f87c4dd5373C9F31e0'],
    '0xadf88a1edc8f15cea27f2674ed2ba1382f46a8a5'     :     ['DOME', '0x475bfaa1848591ae0e6ab69600f48d828f61a80e'],
    '0x1723d77afde343323b769271a83d5aecada25e01'     :     ['ZOO', '0x1D229B958D5DDFca92146585a8711aECbE56F095'],
    '0xde78f42bff7edf1e70450e7bcfd8abcf94e3a65e'     :     ['TINC', '0x05aD6E30A855BE07AfA57e08a4f30d00810a402e'],
    '0x71f36803139cac2796db65f373fb7f3ee0bf3bf9'     :     ['BLP', '0xfe1d7f7a8f0bda6e415593a2e4f82c64b446d404'],
    '0x5735bb4e439474828235a5f4048edf0240dca7f2'     :     ['YEL', '0xd3b71117e6c1558c1553305b44988cd944e97300'],
    '0x638fbd99fe8cc28535fa05d3825a028c0a1e430d'     :     ['MNFT', '0x36953B5Ec00A13eDcEceB3aF258D034913D2A79D'],
    
    #'0xffd8457466baa1f11bb585c7fd772ad1a8b82b64'     :     ['GMEE', '0xed8c8aa8299c10f067496bb66f8cc7fb338a3405'],
    # '0x5905a1f7baf19844874b8b16e5fc4cde639b7a32'     :     ['SIP', '0x9e5965d28e8d44cae8f9b809396e0931f9df71ca'],
    # '0x20c99830967a18563d2d3ed51094add9fbe06e2a'     :     ['SDAO', '0x90ed8f1dc86388f14b64ba8fb4bbd23099f18240'], 
    #
    # '0xb8ce421729232ecd5dfc7bd0adfe1f4dad9d9cce'     :     ['BATH', '0x0bc89aa98Ad94E6798Ec822d0814d934cCD0c0cE'],
    
    
    # '0xacc34268f5d7cb9b11bfb1ba4d8bd2bc2b49ee4e'     :     ['DPS', '0xf275e1AC303a4C9D987a2c48b8E555A77FeC3F1C'],
    # '0x88f0a6cb89909838d69e4e6e76ec21e2a7bdca66'    :     ["BREW", '0x790Be81C3cA0e53974bE2688cDb954732C9862e1', 1500000],
    # '0x73a4c2d21282dd9f9f2df2ad3e06fd25ab487c9c'     :     ['XWIN', '0xd88ca08d8eec1E9E09562213Ae83A7853ebB5d28'],  #check
    # '0xb651a851819638cb120a46db0e01fa89006ee290'     :     ['CART', '0x5C8C8D560048F34E5f7f8ad71f2f81a89DBd273e'],
    # '0xc1d204015268cd808b765f024e04ce01d5bff58d'     :     ['Sheesha', '0x232FB065D9d24c34708eeDbF03724f2e95ABE768'],
    #
    # '0xfad3b5feac1aaf86b3f66d105f2fa9607164d86b'     :     ["FEED", '0x67d66e8Ec1Fd25d98B3Ccd3B19B7dc4b4b7fC493', 7500000],
    # '0x377056416332d017d2c2d140a097ba8c2872bb60'     :     ['XMS', '0x7859b01bbf675d67da8cd128a50d155cd881b576'],
    # '0x6ff9b88eb94a976b0e1db7713d8d765b8be437a7'     :     ['LIGHT', '0x037838b556d9c9d654148a284682c55bb5f56ef4'],
    # '0xc55a7183f6d060271010a4441c106f6a81d46e34'     :     ['WSPP', ''],
    # '0xb2bef43cb487bfc89770e2e88c23f6a2163133ee'     :     ['BSCS', '0xbcb24AFb019BE7E93EA9C43B7E22Bb55D5B7f45D'],
    # '0x47e947f01a17f8004d486fc7e37222b205a4c20b'     :     ['ARV', '0x6679eB24F59dFe111864AEc72B443d1Da666B360'],
    # '0xf1dd352ef3a94f60b3047b607c2bd976401f538c'     :     ['GNT', '0xf750a26eb0acf95556e8529e72ed530f3b60f348'],
    # '0x6524b3b11979d5b5c354d5a804be9711d767f38f'     :     ['XEUS', '0x4e141769366634d9c4e498257fa7ec204d22b634'],
    # '0x1aa800be7e9829ddf97c54ef750f5e42c2a6a884'     :     ['SHARPPEI', '0xfe3af7376e412a377358d5894c790bb3e00d0dc1'],
    # '0x2c32e56756964acdb650521c1f10bdb939d5ff7b'     :     ['PIP', '0x1215Ed20aa507578ca352E195016F289e7A17f3A']
    
    
    # '0x9ed5a62535a5dd2db2d9bb21bac42035af47f630'     :     ['NAV'],
    # '0x8f8c77987c0ea9dd2400383b623d9cbcbbaf98cf'     :     ['GMR'],
    # '0xd1c35c3f5d9d373a3f7c0668fbe75801886e060f'     :     ['SWG', '0xe792f64c582698b8572aaf765bdc426ac3aefb6b', 0], 
    # '0xae126b90d2835c5a2d720b0687ec59f59b768183'     :     ["WOW", '0x4DA996C5Fe84755C80e108cf96Fe705174c5e36A', 165000], 
    # '0x0cf86283ad1a1b7d04669696ed13bae3d5925a0a'    :     ["SAKE", '0x8bd778b12b15416359a227f0533ce2d91844e1ed', 60000],
    # '0xce059e8af96a654d4afe630fa325fbf70043ab11'    :     ["xBLZD", '0x9a946c3Cb16c08334b69aE249690C236Ebd5583E', 3000000],
    # '0xcbd932ac66f645a3764733aacd30ce50e522fac1'     :     ['dvi'],
    # '0xe596470d291cb2d32ec111afc314b07006690c72'     :     ['PHX', '0xb98d864ddcb573567b3a2258c9e5cab58fe7974e'],
    # '0x8ac06b55c9812e3e574cf5a5f3b49619df33099c'     :     ['NMX' ,'0xd32d01a43c869edcd1117c640fbdcfcfd97d9d65'],
    # '0x70d7ecee276ad5fdfc91b3c30d2c1cdb9dd442fb'     :     ['DPET', '0xfb62ae373aca027177d1c18ee0862817f9080d08'] ,
    # '0x6cfa3ff4e96abe93a290dc3d7a911a483c194758'     :     ['ANY', '0xF68C9Df95a18B2A5a5fa1124d79EEEffBaD0B6Fa'],
    # '0x1ba962acab22be9e49c4cebe7710c9201a72dfcc'     :     ['BABYCAKE', '0xdb8d30b74bf098af214e862c90e647bbb1fcc58c',],
    # '0xcccc0b22799e82a79007814dbc6a194410dccea5'     :     ['BMON', '0x08ba0619b1e7a582e0bce5bbe9843322c954c340'], #bnb
    
    # '0x7a4bae68836f486e2c99dca0fbda1845d4532194'     :     ['META HERO'],
    # '0xd27e57ff5dd3d78b03c85e2a2bb8dc37e67c5140'     :     ['POOLZ', '0x77018282fd033daf370337a5367e62d8811bc885'],
    # '0x0767a2f9c644b364bc88eea5a535afe506ba6802'     :     ['ODDZ', '0xcd40f2670cf58720b694968698a5514e924f742d'],
    # '0x2b6b2701d7f7b65ba2e1ec2d2daa17d46b85a4fe'     :     ['UBXT', '0xbbeb90cfb6fafa1f69aa130b7341089abeef5811'],
    # '0x875831249ba511a6f1e49c84d66e1a6f5601f7c6'     :     ['DND', '0x14c358b573a4ce45364a3dbd84bbb4dae87af034'],
    # '0xb7d303bbae2573513801c5f94ae0b61fa5b3426f'     :     ['ZOON', '0x9d173e6c594f479b4d47001f8e6a95a7adda42bc'],
    # '0x22d56946c6cc1d4ed09f02858ddb990fcc981c55'     :     ["HGET", '0xC7d8D35EBA58a0935ff2D5a33Df105DD9f071731', 240000], 
    # '0x027d50f36fe3b64630170b3ba82fc64bfc9bc088'     :     ['FAN', '0xfac3a1ed2480da8f5c34576c0da13f245239717d'],
    # '0x73f9eb8eb7109b171396c8cbffcb29839c8b3064'     :     ['PKMON', '0x609D183Fb91a0fce59550b62ab7d2c931b0Bb1BE'],
    # '0x88dba2cf8911a80cc50a1b392b5ff6b47b930330'     :     ['SFUND','0x477bc8d23c634c154061869478bce96be6045d12'], 
    # '0x75015b56da228a5367d313866f6520495344c65c'     :     ['BNX', '0x8C851d1a123Ff703BD1f9dabe631b69902Df5f97'],
    # '0xb9a32da7f33731ffda8e7eccb91325eee8a524ac'     :     ['SMG', '0x6bfd576220e8444CA4Cc5f89Efbd7f02a4C94C16'],
    # '0x5ed6b80f0e8b1c7fdb783202d4a926bbed2d49ee'     :     ["TENFI", '0xd15C444F1199Ae72795eba15E8C1db44E47abF62', 1420000],
    # 
    # '0xea96c1970b9e3d4258620f68af95dddeb5fbd68f'     :     ['SALE', '0x04f73a09e2eb410205be256054794fb452f0d245'], 
    # '0xda6e741a7f7d4d88d4210340069348704fdf21bf'     :     ['PROS', ''],  
    # '0x7db4456a73a9c94a381d244e9dfc76e83c05913e'     :     ['SWAPP', '0x0efE961C733FF46ce34C56a73eba0c6a0E18E0F5'], #check
    # '0xb93a33f4ca46c1e1d65387313706cb8728b75703'     :     ['AIRT', '0x016CF83732f1468150D87dCC5BdF67730B3934D3'], 
    # '0x235540bd639308e51efa89abf2a9af8bc1dec877'     :     ['GENS', ''],
    # '0xc55a7183f6d060271010a4441c106f6a81d46e34'     :     ['WOPP', ''], 
    # '0x8595c4ad15d51c5bf920c249869ec5b3250c2d4d'     :     ['aaa', ''],
    
    }
 

mapBidResult = { }
acFromBlk = 16081390 
acToBlk   = 16539350

def calBid(acFromBlk, acToBlk):
    txs = getAllTxs("0xb92Ab7c1edcb273AbA24b0656cEb3681654805D2", acFromBlk, acToBlk)
    global mapBidResult
    mapBidResult = {}
    for tx in txs:
        logging.info(tx)
        tokenSymbol = tx['tokenSymbol']
        toAddr = tx['to']
        logging.info('----------------- %s ---%s', toAddr, tokenSymbol)
        if (toAddr.lower() == '0xb92ab7c1edcb273aba24b0656ceb3681654805d2' and tokenSymbol.lower() == 'cake'):
            fromPrjAddr = tx['from']
            cakeVal = float(tx['value']) / 1000000000000000000.0
            logging.info('----------------- %s ---%s -- cake %f', fromPrjAddr, tokenSymbol, cakeVal)
            if fromPrjAddr in mapBidResult.keys():
                mapBidResult[fromPrjAddr] = mapBidResult[fromPrjAddr] + cakeVal
            else:
                mapBidResult[fromPrjAddr] = cakeVal
    print('cal bid ok');
    
def monitorAc(fromBlk = 0): 
    print('====================monitorAuc')
    logging.info('=====================monitorAuc')
    global w3
    global cakeContractObj
    
    currBlk = w3.eth.block_number
    
    abi_json_file = open('./abi/cakeAbi.json', 'r')
    cakeabi = json.load(abi_json_file)
    
    cakeContractObj = w3.eth.contract(address='0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82', abi=cakeabi) # declaring the token contract
# token_balance = token.functions.balanceOf({your address}).call() # returns int with balance, without decimals
    
    # printEstimate()
    # ProgramTerminated = True
    # return
    
    
        
    global mapBidResult
    remainBlk = 1000000;
    print('currBlk = ' + str(currBlk) + ' acToBlk ' + str(acToBlk) + ' pro ' + str(ProgramTerminated))
    while not ProgramTerminated and currBlk < acToBlk: 
        Delay(1)
        currBlk = w3.eth.block_number
        # print('currBlk = ' + str(currBlk))
        if(remainBlk != acToBlk - currBlk): 
            remainBlk = acToBlk - currBlk
            print(acToBlk - currBlk, ' block to end, current ', currBlk)
        if((acToBlk - currBlk) % 2 == 1):
            printEstimate()
        
    try: 
        calBid(acFromBlk, acToBlk)
            #TODO check cancel transaction
        printResult();
    except: 
        logging.exception("error")
        print('--------- ERROR------------------')    
    
def printEstimate():
    global auctionOrder
    # calBid(acFromBlk, acToBlk)
    print('==printEstimate===')
    mapCakeReverve = {}
    mapTotal = {}
    for key in mapAddrName:
        addr = Web3.toChecksumAddress(key)
        # addr = key
    
        cakeBal = cakeContractObj.functions.balanceOf(addr).call() / 1000000000000000000
        # cakeBal = getCakeBal(addr)
        # logging.info('%s -- cake hold: %f', addr, cakeBal)
        # print(addr + '-- cake hold: ' + str(cakeBal))
        # sleep(1)
        mapCakeReverve[key] = cakeBal
        mapTotal[key] = cakeBal
        if(key in mapBidResult) :
             mapTotal[key] = cakeBal + mapBidResult[key];
    
    maxrow = 5
    nowOrder = 'Total Cake (bid + wallet)';
    print('===============cake in wallet + bid=================')
    i = 0
    for k, v in sorted(mapTotal.items(), key=lambda item: item[1], reverse=True) :
        if (i < maxrow):
            coin = mapAddrName[k][0];
            coinAddr = mapAddrName[k][1];
            print(coin, '\t', k, '\t', str(v))
            i = i + 1
            nowOrder = nowOrder + '\n' + str(i) + ': ' + coin + ', bidder ' + k + ', contract ' + coinAddr + ', total cake ' + str(v)
    
    if(nowOrder != auctionOrder):
        auctionOrder = nowOrder
        # SoundAlert()
        AddMessage(nowOrder)
    
    print('===============bid=================')
    i = 0
    for k, v in sorted(mapBidResult.items(), key=lambda item: item[1], reverse=True) :
        if k in mapAddrName.keys():
            if(i < maxrow) :
                coin = mapAddrName[k][0];
                print(coin, '\t', k, '\t', str(v))
                i = i + 1
    
    print('===============IN wallet=================')
    i = 0
    for k, v in sorted(mapCakeReverve.items(), key=lambda item: item[1], reverse=True) :
        if(i < maxrow) :
            coin = mapAddrName[k][0];
            print(coin, '\t', k, '\t', str(v))
            i = i + 1
    
def printResult():
    global mapBidResult
    i = 0;
    for k, v in sorted(mapBidResult.items(), key=lambda item: item[1], reverse=True) :
        i = i + 1
        name = '--'
        if k in mapAddrName.keys():
            name = mapAddrName[k]
            if(i <= 3 and len(name) >= 2) :
                webbrowser.open('https://poocoin.app/tokens/' + name[1])
                webbrowser.open('https://app.1inch.io/#/56/swap/BNB/' + name[1])
                
                
        # pName = mapAddrName[k][0], 
        # contract2Buy = mapAddrName[k][1], 
        print(k, 'Bid ', v, name)
         

if __name__ == "__main__":
    global auctionOrder
    auctionOrder = ''
    print ('what the fcuk is going on ')
    main()
