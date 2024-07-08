from brownie import config, network, interface
from scripts.get_weth import get_weth
from scripts.helpful_scrips import get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from web3 import Web3

AMOUNT = Web3.to_wei(0.1, "ether")


def get_lending_pool():
    lending_pool_addresses_provider = interface.IPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getPool()
    lending_pool = interface.IPool(lending_pool_address)
    print(f"Lending Pool Address: {lending_pool_address}")
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved ERC20")
    return tx


def check_allowance(erc20_address, owner, spender):
    erc20 = interface.IERC20(erc20_address)
    allowance = erc20.allowance(owner, spender)
    print(
        f"Allowance for {spender} to spend {owner}'s tokens: {Web3.from_wei(allowance, 'ether')} ETH"
    )
    return allowance


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt,
        available_borrows_base,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    print(f"Raw collateral: {total_collateral_eth}")
    print(f"Raw debt: {total_debt}")
    print(f"Raw borrowable: {available_borrows_base}")

    available_borrows_base = Web3.from_wei(available_borrows_base, "ether")
    total_debt = Web3.from_wei(total_debt, "ether")
    total_collateral_eth = Web3.from_wei(total_collateral_eth, "ether")

    print(f"You have {total_collateral_eth} ETH in collateral")
    print(f"You can borrow {available_borrows_base} ETH")
    print(f"You have {total_debt} ETH in debt")
    return (float(total_collateral_eth), float(total_debt))


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.from_wei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    print(f"Account: {account}")
    print(f"WETH Token Address: {erc20_address}")
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        get_weth()
    lending_pool = get_lending_pool()
    # approve
    approve_tx = approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    check_allowance(erc20_address, account.address, lending_pool.address)

    print("Depositing")
    tx = lending_pool.supply(
        erc20_address, AMOUNT, account.address, 0, {"from": account}
    )
    tx.wait(1)  # Wait for the transaction to be confirmed
    print("Deposited")
    # account status
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * borrowable_eth * 0.9
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")
    dai_token = config["networks"][network.show_active()]["dai_token"]
    borrow_txn = lending_pool.borrow(
        dai_token,
        Web3.to_wei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_txn.wait()
    print("We borrowed some DAI")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)


if __name__ == "__main__":
    main()
