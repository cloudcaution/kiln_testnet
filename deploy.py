from eth_utils.conversions import to_hex
import web3
from web3 import Web3
from base import *
from config import config
import json
import names
import decimal


def generateRandomGreeting():
    return names.get_full_name()


class Contract:

    def __init__(self, index, key) -> None:
        self.w3: web3.Web3
        self.account: web3.Account
        self.w3, self.account = init_web3_and_account(
            endpoint_name=KILN, private_key=key)

        self.abi, self.bytecode, self.set_greeting_method_code_tpl = self.parseData(
        )
        self.name = generateRandomGreeting()
        self.index = index
        self.address = ''

    def parseData(self):
        abi = []
        bytecode = ''
        with open('./Greeter.json', 'r') as f:
            data = json.load(fp=f)
            abi = data['abi']
            bytecode = data['bytecode']
            set_greeting_method_code_tpl = data['setGreetingCodeTemplate']
            f.close()
        return abi, bytecode, set_greeting_method_code_tpl

    def deploy(self):
        receipt, ok = send(w3=self.w3,
                           account=self.account,
                           chain_id=to_hex(1337802),
                           data=self.bytecode)
        if receipt is None or ok == False:
            return None
        self.address = receipt['contractAddress']
        print(f'contract `Greeter` is deployed at address: {self.address}')

    def setGreeting(self):
        if self.address == None:
            return
        # reconnect to the provider
        self.w3, self.account = init_web3_and_account(
            endpoint_name=KILN, private_key=config['PRIVATTE_KEY'])
        new_greeting = generateRandomGreeting()
        new_greeting_hex = new_greeting.encode("utf-8").hex()
        data = self.set_greeting_method_code_tpl.format(new_greeting_hex)
        print(f'setGreeting for {new_greeting}')
        send(w3=self.w3,
             account=self.account,
             chain_id=to_hex(1337802),
             to=self.address,
             data=data)

def createaddress(number, filename):
    print("Creating ETH address...")
    f = open("./"+ filename, "a")
    
    w3 = web3
    for i in range(number):
        new_acct = w3.eth.Account.create()

        f.write(json.dumps({
            "privateKey" : Web3.toHex(new_acct.privateKey),
            "address" :    new_acct.address
        }))
        f.write("\n")
        print(Web3.toHex(new_acct.privateKey))
        print(new_acct.address)

    f.close()

def getkey(filename):
    f = open("./" + filename, "r")
    keys = f.readlines()
    f.close()

    keylist = []
    for line in keys:
        dict = json.loads(line)
        keylist.append(dict)
    
    return keylist

def sendBackTrasaction(w3, fromstr, toaddr):
    balance = Web3.fromWei(w3.eth.get_balance(fromstr['address']),'ether') - decimal.Decimal(0.001)
    if balance < 0:
        return
        
    transaction = {
        'to' : toaddr,
        'value': Web3.toWei(balance, 'ether'),
        'gas' : 200000,
        'nonce': w3.eth.getTransactionCount(fromstr['address']),
        'gasPrice': w3.eth.gasPrice,
        'chainId': 1337802
    }
    key = fromstr['privateKey']

    signed = w3.eth.account.sign_transaction(transaction, key)
    send_tx_and_wait_recipt(w3=w3, signed_tx=signed)

def sendOutTransaction(w3, fromstr, toaddr, key, send_value):

    transaction = {
        'to' : toaddr,
        'value': Web3.toWei(send_value, 'ether'),
        'gas' : 200000,
        'nonce': w3.eth.getTransactionCount(fromstr),
        'gasPrice': w3.eth.gasPrice,
        'chainId': 1337802
    }

    signed = w3.eth.account.sign_transaction(transaction, key)
    send_tx_and_wait_recipt(w3=w3, signed_tx=signed)

if __name__ == '__main__':
    # recommend 11
    contract_count = int(input('how many contracts do you want to deploy: '))
    interaction_count_per_contract = int(
        input(
            'how many interactions do you want to do for each contract you deployed: '
        ))
    number_of_address = int(input('how many ETH address you want to create: '))
    number_of_send = int(input('How many ETH you want to send out to child address: '))
    is_send_back = str(input("are you willing to send back your ETH from child address to your main address? please type in y/n: "))
    w3 = init_web3(endpoint_name=KILN, endpoint='')

    if number_of_address != 0:
        createaddress(number_of_address, config['ADDRESS_FILE_NAME'])
    keys = getkey(config['ADDRESS_FILE_NAME'])
    mainkey = config['PRIVATTE_KEY']
    mainAddress = config['ADDRESS']

    if number_of_send != 0:
        for i in range(len(keys)):
            sendOutTransaction(w3, mainAddress, keys[i]['address'], mainkey, number_of_send)
    
    if contract_count != 0 or interaction_count_per_contract != 0:
        for i in range(len(keys)):
            counter = contract_count
            while counter > 0:
                contract = Contract(counter, keys[i]['privateKey'])
                contract.deploy()
                interact_count = interaction_count_per_contract
                while interact_count > 0:
                    contract.setGreeting()
                    interact_count -= 1
                counter -= 1

    if is_send_back == 'y':
        for i in range(len(keys)):
            sendBackTrasaction(w3, keys[i], mainAddress)