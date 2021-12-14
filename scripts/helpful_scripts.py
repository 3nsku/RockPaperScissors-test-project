from brownie import (
    network,
    accounts,
    config,
    MockFAU,
    Contract,
)

FORKED_LOCAL_ENRIVONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = [
    "development",
    "ganache-local",
]  # this is a list of local networks so that we know when to deploy mocks


def get_account(index=None, id=None):
    # index will choose one of the addresses inside accounts array
    # id will use one of the accounts saved inside brownie -> $ brownie accounts list
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENRIVONMENTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {"fau_token": MockFAU}


def get_contract(contract_name):
    """The function will grab the contract addresses from the brownie config if
    defined, otherwise, it will deploy a mock version of the contract
    and return that mock contract.

        Arg:
            contract_name (string)

        Return:
            brownie.network.contract.ProjectContract: The most recently deployed version of this contract.
    """
    contract_type = contract_to_mock[contract_name]
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
    ):  # check if we are using a local blockchain
        if len(contract_type) <= 0:  # check if mocks have already been deployed
            deploy_mocks()
        contract = contract_type[-1]
    else:  # if you want to deploy to a test net
        contract_address = config["networks"][network.show_active()][contract_name]
        # to interact with a contract on a test net we need the ABI and the address
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


def deploy_mocks():
    account = get_account()
    MockFAU.deploy({"from": account})
    print("Deployed Mocks!")


def fund_account_with_fau(account_address, amount=100):
    # funds all test account with 100 fau
    MockFAU[-1].transfer(account_address, amount, {"from": MockFAU[-1].address})
