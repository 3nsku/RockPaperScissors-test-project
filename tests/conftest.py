from scripts.helpful_scripts import get_account, get_contract
from brownie import RockPaperScissors
import pytest


@pytest.fixture
def player_1():
    return get_account(index=1)


@pytest.fixture
def player_1_move():
    return "ROCK"


@pytest.fixture
def player_2_move():
    return "SCISSORS"


@pytest.fixture
def not_valid_move():
    return "ROCKSANDPAPPERS"


@pytest.fixture
def player_2():
    return get_account(index=2)


@pytest.fixture
def bad_actor():
    return get_account(index=3)


@pytest.fixture
def player_1_local_key():
    return "123"


@pytest.fixture
def player_2_local_key():
    return "777"


@pytest.fixture
def bet_amount():
    return 10


@pytest.fixture
def not_allowed_token():
    return "0xFab46E002BbF0b4509813474841E0716E6730196"


@pytest.fixture
def rock_paper_scirrors_contract():
    return RockPaperScissors.deploy(
        get_contract("fau_token"), {"from": get_account(index=0)}
    )  # deploy contract and set constructor values


@pytest.fixture
def fau_token():
    return get_contract("fau_token")  # deploy contract and set constructor values
