from brownie import RockPaperScissors, exceptions, config
from scripts.helpful_scripts import get_account, get_contract, fund_account_with_fau
import pytest
from web3 import Web3
import time

# get function parameters from @pytest.fixture inside conftest.py
def test_check_if_contract_intiliazed_correctly(rock_paper_scirrors_contract):
    # ASSERT
    assert (
        rock_paper_scirrors_contract.matches(0) != 0
    )  # check if fake match registered and if index now starts from 1
    assert rock_paper_scirrors_contract.fauTokenAddress() == get_contract(
        "fau_token"
    )  # check that fau token has been setup correctly


# get function parameters from @pytest.fixture inside conftest.py
def test_set_up_match(player_1, player_2, rock_paper_scirrors_contract, bet_amount):

    # ASSERT
    # try calling setUpMatch a second time
    rock_paper_scirrors_contract.setUpMatch(player_1, player_2, bet_amount)

    with pytest.raises(exceptions.VirtualMachineError):
        rock_paper_scirrors_contract.setUpMatch(
            player_1, player_2, bet_amount
        )  # make sure player1 can not start a second match

    with pytest.raises(exceptions.VirtualMachineError):
        rock_paper_scirrors_contract.setUpMatch(
            get_account(index=4), player_2, bet_amount
        )  # make sure player2 can not start a second match

    # check that player 1 save inside the new match
    assert rock_paper_scirrors_contract.matches(1)[2] == player_1
    assert rock_paper_scirrors_contract.matches(1)[3] == player_2

    # make sure player1 address is different from player 2 address
    assert (
        rock_paper_scirrors_contract.matches(1)[2]
        != rock_paper_scirrors_contract.matches(1)[3]
    )

    # make sure both player choices are 0 when match is started
    assert rock_paper_scirrors_contract.matches(1)[4] == "0x0"
    assert rock_paper_scirrors_contract.matches(1)[5] == "0x0"

    # make sure palyer to match id mapping has been updated, match id should be 1
    assert rock_paper_scirrors_contract.PlayerToMatchId(player_1) == 1
    assert rock_paper_scirrors_contract.PlayerToMatchId(player_2) == 1

    # return contract with test match created
    return rock_paper_scirrors_contract


def test_save_encrypted_choice_and_entrace_fee(
    player_1,
    player_2,
    player_1_move,
    player_2_move,
    bad_actor,
    player_1_local_key,
    bet_amount,
    fau_token,
    player_2_local_key,
    not_allowed_token,
    rock_paper_scirrors_contract,
):
    rock_paper_scirrors_contract = test_set_up_match(
        player_1, player_2, rock_paper_scirrors_contract, bet_amount
    )
    # ARRAGE

    player_1_move_in_bytes = str.encode(
        player_1_move
    )  # convert player 1 choice to bytes format

    player_1_local_key_bytes = str.encode(
        player_1_local_key
    )  # convert player 1 choice to bytes format

    player_2_move_in_bytes = str.encode(
        player_2_move
    )  # convert player 1 choice to bytes format

    player_2_local_key_bytes = str.encode(
        player_2_local_key
    )  # convert player 2 choice to bytes format

    encrypted_player1_move = Web3.solidityKeccak(
        ["bytes", "bytes"], [player_1_local_key_bytes, player_1_move_in_bytes]
    )  # hash player 1 choice with local key

    encrypted_player2_move = Web3.solidityKeccak(
        ["bytes", "bytes"], [player_2_local_key_bytes, player_2_move_in_bytes]
    )  # hash player 1 choice with local key

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: The match can continue only if both player have lock their move",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_1_move_in_bytes, player_1_local_key_bytes, {"from": player_1}
        ).wait(
            1
        )  # try calling decrypt choice before submiting choice a move

    fund_account_with_fau(player_1)  # fund player 1 address with 100 FAU
    fund_account_with_fau(player_2)  # fund player 2 address with 100 FAU

    fau_token.approve(
        rock_paper_scirrors_contract.address, bet_amount, {"from": player_1}
    ).wait(
        1
    )  # approve FAU token amount to transfer

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Smart Contract does not have enough allowace to transfer funds and start match!",
    ):
        rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
            encrypted_player2_move,
            fau_token,
            {"from": player_2, "value": bet_amount},
        )  # try trasfering player 2 funds wihtout approval

    fau_token.approve(
        rock_paper_scirrors_contract.address, bet_amount, {"from": player_2}
    ).wait(
        1
    )  # approve FAU token amount to transfer

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Amount Sent Does Not Match Bet Size",
    ):
        rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
            encrypted_player1_move,
            fau_token,
            {"from": player_1, "value": bet_amount + 1},
        )  # make sure bet amount is equal to value sent

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Token Sent is Not Allowed",
    ):
        rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
            encrypted_player1_move,
            not_allowed_token,
            {"from": player_1, "value": bet_amount},
        )  # make sure bet amount is equal to value sent #check if token sent is allowed

    # ACT

    # send player 1 move
    rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
        encrypted_player1_move,
        fau_token,
        {"from": player_1, "value": bet_amount},
    )

    assert rock_paper_scirrors_contract.matches(1)[0] == 1  # match state should be 1

    # send player 2 move
    rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
        encrypted_player2_move,
        fau_token,
        {"from": player_2, "value": bet_amount},
    )

    assert rock_paper_scirrors_contract.matches(1)[0] == 2  # match state should be 2

    # ASSERT
    with pytest.raises(exceptions.VirtualMachineError):
        rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
            encrypted_player1_move,
            fau_token,
            {"from": bad_actor, "value": bet_amount},
        )  # make sure random address can't set a value for a match

    with pytest.raises(exceptions.VirtualMachineError):
        rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
            encrypted_player1_move,
            fau_token,
            {"from": player_1, "value": bet_amount},
        )  # make sure player 1 can't change submited move

    with pytest.raises(exceptions.VirtualMachineError):
        rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
            encrypted_player2_move,
            fau_token,
            {"from": player_2, "value": bet_amount},
        )  # make sure player 2 can't change submited move

    assert (
        rock_paper_scirrors_contract.matches(1)[4] == encrypted_player1_move.hex()
    )  # check if player 1 encrypted choice saved (convert bytes to hex string with .hex())

    assert (
        rock_paper_scirrors_contract.matches(1)[5] == encrypted_player2_move.hex()
    )  # check if player 2 encrypted choice saved (convert bytes to hex string with .hex())

    assert (
        fau_token.balanceOf(rock_paper_scirrors_contract.address) == bet_amount * 2
    )  # check that contract has recevied the funds from both players

    return rock_paper_scirrors_contract


# check if contract works if match is won by player 1
def test_decrypt_choice_win_player1(
    player_1,
    player_2,
    player_1_move,
    player_2_move,
    bad_actor,
    player_1_local_key,
    player_2_local_key,
    bet_amount,
    fau_token,
    not_allowed_token,
    rock_paper_scirrors_contract,
):
    # get match with choices submited
    rock_paper_scirrors_contract = test_save_encrypted_choice_and_entrace_fee(
        player_1,
        player_2,
        player_1_move,
        player_2_move,
        bad_actor,
        player_1_local_key,
        bet_amount,
        fau_token,
        player_2_local_key,
        not_allowed_token,
        rock_paper_scirrors_contract,
    )

    player_1_move_in_bytes = str.encode(
        player_1_move
    )  # convert player 1 choice to bytes format

    player_1_local_key_bytes = str.encode(
        player_1_local_key
    )  # convert player 1 choice to bytes format

    player_2_move_in_bytes = str.encode(
        player_2_move
    )  # convert player 1 choice to bytes format

    player_2_local_key_bytes = str.encode(
        player_2_local_key
    )  # convert player 1 choice to bytes format

    starting_balance_player_1 = fau_token.balanceOf(player_1)
    starting_balance_player_2 = fau_token.balanceOf(player_2)

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player can't change the move mid match!",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_1}
        ).wait(
            1
        )  # make sure player can't change submited choice

    rock_paper_scirrors_contract.DecryptChoice(
        player_1_move_in_bytes, player_1_local_key_bytes, {"from": player_1}
    ).wait(1)

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player 1 Choice has already been decrypted!",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_1_move_in_bytes, player_1_local_key_bytes, {"from": player_1}
        ).wait(
            1
        )  # make sure player 1 can't change or submit chioce

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player does not have an active match or Match ended, other player has submited an invalid answer!",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_1_move_in_bytes, player_1_local_key_bytes, {"from": bad_actor}
        ).wait(
            1
        )  # make sure randmon person can't call function is not active match

    # check if player move save in plain text
    assert (
        convertHexToASCII(rock_paper_scirrors_contract.matches(1)[4]) == player_1_move
    )

    # check that player choice updated in plain text
    assert (
        rock_paper_scirrors_contract.matches(1)[0] == 3
    )  # check that match state updated to 3

    rock_paper_scirrors_contract.DecryptChoice(
        player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_2}
    ).wait(1)

    # check if player move save in plain text
    assert (
        convertHexToASCII(rock_paper_scirrors_contract.matches(1)[5]) == player_2_move
    )

    # check that player choice updated in plain text
    assert (
        rock_paper_scirrors_contract.matches(1)[0] == 6
    )  # check that match state updated to 6 winner found

    # check if winner paid
    assert fau_token.balanceOf(player_1) == starting_balance_player_1 + (bet_amount * 2)

    # check that loser not paid
    assert fau_token.balanceOf(player_2) == starting_balance_player_2

    # check that both players don't have an active match
    assert (
        rock_paper_scirrors_contract.PlayerToMatchId(player_1) == 0
        and rock_paper_scirrors_contract.PlayerToMatchId(player_2) == 0
    )


# check that match is ended when one of the moves is invalid (e.i. not ROCK, PAPER or SCISSORS)
def test_decrypt_not_valid_move(
    player_1,
    player_2,
    player_1_move,
    player_2_move,
    not_valid_move,
    bad_actor,
    player_1_local_key,
    player_2_local_key,
    bet_amount,
    fau_token,
    not_allowed_token,
    rock_paper_scirrors_contract,
):

    rock_paper_scirrors_contract = test_save_encrypted_choice_and_entrace_fee(
        player_1,
        player_2,
        not_valid_move,
        player_2_move,
        bad_actor,
        player_1_local_key,
        bet_amount,
        fau_token,
        player_2_local_key,
        not_allowed_token,
        rock_paper_scirrors_contract,
    )

    starting_balance_player_1 = fau_token.balanceOf(player_1)
    starting_balance_player_2 = fau_token.balanceOf(player_2)

    player_1_not_valid_move = str.encode(
        not_valid_move
    )  # convert player 1 choice to bytes format

    player_1_local_key_bytes = str.encode(
        player_1_local_key
    )  # convert player 1 choice to bytes format

    player_2_move_in_bytes = str.encode(
        player_2_move
    )  # convert player 1 choice to bytes format

    player_2_local_key_bytes = str.encode(
        player_2_local_key
    )  # convert player 1 choice to bytes format

    rock_paper_scirrors_contract.DecryptChoice(
        player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_2}
    ).wait(1)

    rock_paper_scirrors_contract.DecryptChoice(
        player_1_not_valid_move, player_1_local_key_bytes, {"from": player_1}
    ).wait(1)

    # make sure match has ended
    assert rock_paper_scirrors_contract.matches(1)[0] == 9

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="Player does not have an active match or Match ended, other player has submited an invalid answer!",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_2}
        ).wait(1)

    # make sure both palyers are refunded when invalid move deceted
    assert starting_balance_player_1 + bet_amount == fau_token.balanceOf(player_1)
    assert starting_balance_player_2 + bet_amount == fau_token.balanceOf(player_2)


# test if contract work when match is a draw
def test_decrypt_draw(
    player_1,
    player_2,
    not_valid_move,
    bad_actor,
    player_1_local_key,
    player_2_local_key,
    bet_amount,
    fau_token,
    not_allowed_token,
    rock_paper_scirrors_contract,
):
    player_2_move = "PAPER"
    player_1_move = "PAPER"

    rock_paper_scirrors_contract = test_save_encrypted_choice_and_entrace_fee(
        player_1,
        player_2,
        player_1_move,
        player_2_move,
        bad_actor,
        player_1_local_key,
        bet_amount,
        fau_token,
        player_2_local_key,
        not_allowed_token,
        rock_paper_scirrors_contract,
    )

    starting_balance_player_1 = fau_token.balanceOf(player_1)
    starting_balance_player_2 = fau_token.balanceOf(player_2)

    player_1_move_in_bytes = str.encode(
        player_1_move
    )  # convert player 1 choice to bytes format

    player_1_local_key_bytes = str.encode(
        player_1_local_key
    )  # convert player 1 choice to bytes format

    player_2_move_in_bytes = str.encode(
        player_2_move
    )  # convert player 1 choice to bytes format

    player_2_local_key_bytes = str.encode(
        player_2_local_key
    )  # convert player 1 choice to bytes format

    rock_paper_scirrors_contract.DecryptChoice(
        player_1_move_in_bytes, player_1_local_key_bytes, {"from": player_1}
    ).wait(1)

    rock_paper_scirrors_contract.DecryptChoice(
        player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_2}
    ).wait(1)

    assert rock_paper_scirrors_contract.matches(1)[0] == 7  # check that match is a draw

    # check that funds are returned if match is a draw
    assert fau_token.balanceOf(player_1) == starting_balance_player_1 + bet_amount
    assert fau_token.balanceOf(player_2) == starting_balance_player_2 + bet_amount

    # check that both players don't have an active match
    assert (
        rock_paper_scirrors_contract.PlayerToMatchId(player_1) == 0
        and rock_paper_scirrors_contract.PlayerToMatchId(player_2) == 0
    )


# check only 1 player submits move try getting back funds,
# make sure player 2 does not get refunded,
# when match stopped make sure player 2 can't continue
def test_decrypt_player_2_AFK_choice_1(
    player_1,
    player_2,
    player_1_move,
    player_2_move,
    not_valid_move,
    bad_actor,
    player_1_local_key,
    player_2_local_key,
    bet_amount,
    fau_token,
    not_allowed_token,
    rock_paper_scirrors_contract,
):

    rock_paper_scirrors_contract = test_set_up_match(
        player_1, player_2, rock_paper_scirrors_contract, bet_amount
    )

    # ARRAGE

    player_1_move_in_bytes = str.encode(
        player_1_move
    )  # convert player 1 choice to bytes format

    player_1_local_key_bytes = str.encode(
        player_1_local_key
    )  # convert player 1 choice to bytes format

    player_2_move_in_bytes = str.encode(
        player_2_move
    )  # convert player 1 choice to bytes format

    player_2_local_key_bytes = str.encode(
        player_2_local_key
    )  # convert player 1 choice to bytes format

    encrypted_player1_move = Web3.solidityKeccak(
        ["bytes", "bytes"], [player_1_local_key_bytes, player_1_move_in_bytes]
    )  # hash player 1 choice with local key

    encrypted_player2_move = Web3.solidityKeccak(
        ["bytes", "bytes"], [player_2_local_key_bytes, player_2_move_in_bytes]
    )  # hash player 1 choice with local key

    fund_account_with_fau(player_1)  # fund player 1 address with 100 FAU

    fau_token.approve(
        rock_paper_scirrors_contract.address, bet_amount, {"from": player_1}
    ).wait(
        1
    )  # approve FAU token amount to transfer

    # ACT
    starting_balance_player_1 = fau_token.balanceOf(player_1)
    starting_balance_player_2 = fau_token.balanceOf(player_2)

    # send player 1 move
    rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
        encrypted_player1_move,
        fau_token,
        {"from": player_1, "value": bet_amount},
    )

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Match Can not Be stopped Yet!",
    ):
        # try getting funds back asap
        rock_paper_scirrors_contract.cancelMatchAndReturnFunds(
            {"from": player_1},
        )

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player does not have an active match!",
    ):
        # make sure player with not active match can't cancel match
        rock_paper_scirrors_contract.cancelMatchAndReturnFunds(
            {"from": bad_actor},
        )

    time.sleep(6)
    # if test plays remeber to change minMatchLength to 6 seconds

    rock_paper_scirrors_contract.cancelMatchAndReturnFunds(
        {"from": player_1},
    )

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player does not have an active match!",
    ):
        rock_paper_scirrors_contract.cancelMatchAndReturnFunds(
            {"from": player_1},
        )  # try calling function a second time to get a double refund

    # make sure afk player that has not submited a move, doesn't  get refunded
    assert fau_token.balanceOf(player_2) == starting_balance_player_2

    # make sure that player 1 stuck in the match gets refunded
    assert fau_token.balanceOf(player_1) == starting_balance_player_1

    assert rock_paper_scirrors_contract.matches(1)[0] == 9

    # once match ended make sure player 2 can't continue the game
    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player does not have an active match!",
    ):
        rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
            encrypted_player2_move,
            fau_token,
            {"from": player_2, "value": bet_amount},
        )


# test that if both players have submited a move but then second players does not send local key to decrypt,
# cancel match and refund all players
def test_decrypt_player_2_AFK_choice_2(
    player_1,
    player_2,
    player_1_move,
    player_2_move,
    not_valid_move,
    bad_actor,
    player_1_local_key,
    player_2_local_key,
    bet_amount,
    fau_token,
    not_allowed_token,
    rock_paper_scirrors_contract,
):
    rock_paper_scirrors_contract = test_save_encrypted_choice_and_entrace_fee(
        player_1,
        player_2,
        not_valid_move,
        player_2_move,
        bad_actor,
        player_1_local_key,
        bet_amount,
        fau_token,
        player_2_local_key,
        not_allowed_token,
        rock_paper_scirrors_contract,
    )

    starting_balance_player_1 = fau_token.balanceOf(player_1)
    starting_balance_player_2 = fau_token.balanceOf(player_2)

    player_1_not_valid_move = str.encode(
        not_valid_move
    )  # convert player 1 choice to bytes format

    player_1_local_key_bytes = str.encode(
        player_1_local_key
    )  # convert player 1 choice to bytes format

    player_2_move_in_bytes = str.encode(
        player_2_move
    )  # convert player 1 choice to bytes format

    player_2_local_key_bytes = str.encode(
        player_2_local_key
    )  # convert player 1 choice to bytes format

    rock_paper_scirrors_contract.DecryptChoice(
        player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_2}
    ).wait(1)

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Match Can not Be stopped Yet!",
    ):
        # try getting funds back asap
        rock_paper_scirrors_contract.cancelMatchAndReturnFunds(
            {"from": player_2},
        )

    time.sleep(6)
    # if test plays remeber to change minMatchLength to 6 seconds

    rock_paper_scirrors_contract.cancelMatchAndReturnFunds(
        {"from": player_2},
    ).wait(1)

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player does not have an active match!",
    ):
        rock_paper_scirrors_contract.cancelMatchAndReturnFunds(
            {"from": player_2},
        )  # try calling function a second time to get a double refund

    # check that match has been ended
    assert rock_paper_scirrors_contract.matches(1)[0] == 9

    # make sure both players are refunded
    assert fau_token.balanceOf(player_2) == starting_balance_player_2 + bet_amount
    assert fau_token.balanceOf(player_1) == starting_balance_player_1 + bet_amount


# test a match with no bet
def test_with_bet_0(
    player_1,
    player_2,
    player_1_move,
    player_2_move,
    bad_actor,
    player_1_local_key,
    player_2_local_key,
    bet_amount,
    fau_token,
    not_allowed_token,
    rock_paper_scirrors_contract,
):
    bet_amount = 0
    # get match with choices submited
    rock_paper_scirrors_contract = test_set_up_match(
        player_1, player_2, rock_paper_scirrors_contract, bet_amount
    )
    # ARRAGE

    player_1_move_in_bytes = str.encode(
        player_1_move
    )  # convert player 1 choice to bytes format

    player_1_local_key_bytes = str.encode(
        player_1_local_key
    )  # convert player 1 choice to bytes format

    player_2_move_in_bytes = str.encode(
        player_2_move
    )  # convert player 1 choice to bytes format

    player_2_local_key_bytes = str.encode(
        player_2_local_key
    )  # convert player 2 choice to bytes format

    encrypted_player1_move = Web3.solidityKeccak(
        ["bytes", "bytes"], [player_1_local_key_bytes, player_1_move_in_bytes]
    )  # hash player 1 choice with local key

    encrypted_player2_move = Web3.solidityKeccak(
        ["bytes", "bytes"], [player_2_local_key_bytes, player_2_move_in_bytes]
    )  # hash player 1 choice with local key

    fund_account_with_fau(player_1)  # fund player 1 address with 100 FAU
    fund_account_with_fau(player_2)  # fund player 2 address with 100 FAU

    starting_balance_player_1 = fau_token.balanceOf(player_1)
    starting_balance_player_2 = fau_token.balanceOf(player_2)

    # send player 1 move
    rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
        encrypted_player1_move,
        fau_token,
        {"from": player_1, "value": bet_amount},
    )

    assert rock_paper_scirrors_contract.matches(1)[0] == 1  # match state should be 1

    # send player 2 move
    rock_paper_scirrors_contract.saveEncryptedChoiceAndEntranceFee(
        encrypted_player2_move,
        fau_token,
        {"from": player_2, "value": bet_amount},
    )

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player can't change the move mid match!",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_1}
        ).wait(
            1
        )  # make sure player can't change submited choice

    rock_paper_scirrors_contract.DecryptChoice(
        player_1_move_in_bytes, player_1_local_key_bytes, {"from": player_1}
    ).wait(1)

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player 1 Choice has already been decrypted!",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_1_move_in_bytes, player_1_local_key_bytes, {"from": player_1}
        ).wait(
            1
        )  # make sure player 1 can't change or submit chioce

    with pytest.raises(
        exceptions.VirtualMachineError,
        match="revert: Player does not have an active match or Match ended, other player has submited an invalid answer!",
    ):
        rock_paper_scirrors_contract.DecryptChoice(
            player_1_move_in_bytes, player_1_local_key_bytes, {"from": bad_actor}
        ).wait(
            1
        )  # make sure randmon person can't call function is not active match

    # check if player move save in plain text
    assert (
        convertHexToASCII(rock_paper_scirrors_contract.matches(1)[4]) == player_1_move
    )

    # check that player choice updated in plain text
    assert (
        rock_paper_scirrors_contract.matches(1)[0] == 3
    )  # check that match state updated to 3

    rock_paper_scirrors_contract.DecryptChoice(
        player_2_move_in_bytes, player_2_local_key_bytes, {"from": player_2}
    ).wait(1)

    # check if player move save in plain text
    assert (
        convertHexToASCII(rock_paper_scirrors_contract.matches(1)[5]) == player_2_move
    )

    # check that player choice updated in plain text
    assert (
        rock_paper_scirrors_contract.matches(1)[0] == 6
    )  # check that match state updated to 6 winner found

    # check if winner paid
    assert fau_token.balanceOf(player_1) == starting_balance_player_1

    # check that loser not paid
    assert fau_token.balanceOf(player_2) == starting_balance_player_2

    # check that both players don't have an active match
    assert (
        rock_paper_scirrors_contract.PlayerToMatchId(player_1) == 0
        and rock_paper_scirrors_contract.PlayerToMatchId(player_2) == 0
    )


def convertHexToASCII(hex):
    # for example convert  0x524f434b00000000000000000000000000000000000000000000000000000000 to -> "ROCK"
    bytes_object = bytes.fromhex(hex.hex())
    ascii_string = bytes_object.decode("ASCII").rstrip("\x00")
    return ascii_string
