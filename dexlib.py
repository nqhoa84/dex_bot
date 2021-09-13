
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import enum
import time
import math
import logging
from datetime import datetime
import webbrowser 
import requests


logging.basicConfig(filename=F"./log/{datetime.now().strftime('%d-%m-%Y-%Hh%M')}.log",
                    filemode='w',
                    format='[%(asctime)s,%(msecs)03d][%(levelname)s][%(thread)d][%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

def swap1in(fromTokenAddress, toTokenAddress, amount, slippage, priKey) :
    # This will call to Nodejs server, then do a swap by 1 inch
    logging.info("Swap by 1 inch: from: %s, to: %s, amount: %f, slip: %f", fromTokenAddress, toTokenAddress, amount/pow(10, 18), slippage)
    # url = 'http://127.0.0.1:3000/swap?fromTokenAddress=0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee&toTokenAddress=0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56&amount=100000000000000000&slippage=1&priKey=5429d2d1702442881f65c309520c1ba1b534804833e817b3a5bc9d0fdb79d43f'
    baseUrl = 'http://127.0.0.1:3000/swap'
    PARAMS = {'fromTokenAddress':fromTokenAddress,
              'toTokenAddress':toTokenAddress,
              'amount':amount,
              'slippage':slippage,
              'priKey':priKey
              }
    
    r = requests.get(url = baseUrl, params = PARAMS)
  
    # extracting data in json format
    data = r.json()
    logging.info("Swap done: %s", str(data))
    return data;

def swapBnbToToken1in(toTokenAddress, amount, slippage, priKey) :
    return swap1in('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', toTokenAddress, amount, slippage, priKey);

def swapTokenToBnb1in(fromTokenAddress, amount, slippage, priKey) :
    return swap1in(fromTokenAddress, '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', amount, slippage, priKey);
