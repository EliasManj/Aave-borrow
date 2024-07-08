from scripts.helpful_scrips import get_account
from brownie import interface, network, config
from web3 import Web3


def get_weth():
    """
    Mint WETH by depositing ETH
    """
    ## ABI
    ## Addres
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": Web3.to_wei(0.1, "ether")})
    tx.wait(1)
    print(f"Recieved 0.1 WETH")
    return tx


def main():
    get_weth()
