
from config import Config


class ReportItem:
    coin = '' 
    totalIn = 0
    totalOut = 0 

    def __init__(self) :
        self.coin = ''
        self.totalOut = 0
        self.totalIn = 0
    
    def toCSV(self):
        return f'{self.coin},{self.totalIn},{self.totalOut}'

class ReportLine:
    ownerAddr = ''
    keyCoin= ''
    keyIn = 0
    keyOut = 0
    items: list[ReportItem] = [] 
    
    
    def __init__(self, ownerAddr, keyC) :
        self.ownerAddr = ownerAddr
        self.keyCoin = keyC
        self.items = []
        self.keyIn = 0
        self.keyOut = 0

    def addItemIn(self, coin: str, value):
        for m in self.items:
            if(m.coin == coin) :
                m.totalIn += value
                return 
        #don't have any item for coin
        c = ReportItem()
        c.coin = coin
        c.totalIn = value
        self.items.append(c)
    
    def addItemOUT(self, coin: str, value):
        for m in self.items:
            if(m.coin == coin) :
                m.totalOut += value
                return 
        #don't have any item for coin
        c = ReportItem()
        c.coin = coin
        c.totalOut = value
        self.items.append(c)
 
    
    def getCsvHeader():
        return f'wallet,keyCoin,keyIn,KeyOut,coin,in,out,coin2,in2,out2,coin3,in3,out3'
    
    def toCSV(self):
        ms = ''
        for m in self.items:
            ms += f',{m.toCSV()}'

        return f'{self.ownerAddr},{self.keyCoin},{self.keyIn},{self.keyOut}{ms}'





