// SPDX-License-Identifier: MIT

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

pragma solidity ^0.8.0;

contract RockPaperScissors {
    bytes32 public constant ROCK = "ROCK";
    bytes32 constant PAPER = "PAPER";
    bytes32 constant SCISSORS = "SCISSORS";

    // for simplicity we have only have 1 ERC20 token
    address public fauTokenAddress;

    // match lengh in seconds, after which if one player afk or internet problem, the allow to end the match and return the funds
    uint256 public minMatchLength = 60;

    // STATES:
    // MATCH_CREATED = 0,
    // FIRST_PLAYER_IN = 1,
    // SECOND_PLAYER_IN = 2,
    // FIRST_PLAYER_DECRYPTED_ASNWER = 3,
    // SECOND_PLAYER_DECRYPTED_ANSWER = 4,
    // CHOOSING_WINNER = 5,
    // WINNER_FOUND = 6,
    // DRAW = 7,
    // WAITING_FOR_CALL_TO_CANCEL_MATCH = 8,
    // MATCH_STOPPED = 9

    // players array is a always a list of 2 addresses

    // player choice default is zero

    // winner can be: 0 if draw otherwise player address

    struct Match {
        uint256 state;
        uint256 betSize;
        address player_1;
        address player_2;
        bytes32 choice_1;
        bytes32 choice_2;
        address winner;
        uint256 StartedTime;
    }

    mapping(address => uint256) public PlayerToMatchId;
    Match[] public matches;

    constructor(address _fauTokenAddress) {
        fauTokenAddress = _fauTokenAddress;
        // on position 0 of matches array place fake match, so index starts from 1
        matches.push(
            Match(
                0,
                0,
                address(0),
                address(0),
                0,
                0,
                address(0),
                block.timestamp
            )
        );
    }

    // set up the match between 2 players
    // - create a mapping
    // - start match start time

    function setUpMatch(
        address _player1,
        address _player2,
        uint256 _match_bet
    ) public {
        // check player address
        require(
            _player1 != address(0) && _player2 != address(0),
            "Player address can not be 0"
        );
        require(
            PlayerToMatchId[_player1] == 0,
            "Player1 is already playing a Game"
        ); //make sure player 1 is not already inside an active match
        require(
            PlayerToMatchId[_player2] == 0,
            "Player2 is already playing a Game"
        ); //make sure player 2 is not already inside an active match

        require(_player1 != _player2, "Player2 is already playing a Game"); //address for player 1 and palyer 2 can not be the same

        //add new match to list

        matches.push(
            Match(
                0,
                _match_bet,
                _player1,
                _player2,
                bytes32(0),
                bytes32(0),
                address(0),
                block.timestamp
            )
        );
        // update mappings
        uint256 match_id = matches.length - 1;

        PlayerToMatchId[_player1] = match_id;
        PlayerToMatchId[_player2] = match_id;
    }

    // save encrypted choice! and receive payment
    function saveEncryptedChoiceAndEntranceFee(
        bytes memory _choiceEncoded,
        address _token
    ) public payable {
        //make sure the player is inside an active match
        require(
            PlayerToMatchId[msg.sender] != 0,
            "Player does not have an active match!"
        );
        uint256 match_id = PlayerToMatchId[msg.sender];

        uint256 player_id = getPlayerPosition(match_id, msg.sender);

        if (player_id == 1) {
            //check if player has not already chosen a value for this match
            require(
                matches[match_id].choice_1 == bytes32(0) &&
                    msg.sender == matches[match_id].player_1,
                "Player 1 has already made a Choice!"
            );
        } else {
            //check if player has not already chosen a value for this match
            require(
                matches[match_id].choice_2 == bytes32(0) &&
                    msg.sender == matches[match_id].player_2,
                "Player 2 has already made a Choice!"
            );
        }

        // check if amount sent matches agreed bet size
        require(
            matches[match_id].betSize == msg.value,
            "Amount Sent Does Not Match Bet Size"
        );
        //check if token address matches allowed tokens list
        require(_token == fauTokenAddress, "Token Sent is Not Allowed");

        // check if just a fun match without bets
        if (matches[match_id].betSize != 0) {
            //check if enough allowance
            require(
                IERC20(fauTokenAddress).allowance(msg.sender, address(this)) >=
                    msg.value,
                "Smart Contract does not have enough allowace to transfer funds and start match!"
            );
            IERC20(fauTokenAddress).transferFrom(
                msg.sender,
                address(this),
                msg.value
            ); //transfer funds to contract
        }

        if (player_id == 1) {
            matches[match_id].choice_1 = bytes32(_choiceEncoded); // save encrypted player 1 choice
        } else {
            matches[match_id].choice_2 = bytes32(_choiceEncoded); // save encrypted player 1 choice
        }

        matches[match_id].state = matches[match_id].state + 1; // update match state
    }

    // check if address is player 1 or player 2 -> return 1 or 2
    function getPlayerPosition(uint256 _match_id, address _address)
        internal
        view
        returns (uint256)
    {
        if (matches[_match_id].player_1 == _address) {
            return 1;
        } else {
            return 2;
        }
    }

    function DecryptChoice(
        bytes memory _choicePlain,
        bytes memory _PlayerRandomness
    ) public {
        //make sure the player is inside an active match
        require(
            PlayerToMatchId[msg.sender] != 0,
            "Player does not have an active match or Match ended, other player has submited an invalid answer!"
        );

        // get match id:
        uint256 match_id = PlayerToMatchId[msg.sender];
        uint256 player_id = getPlayerPosition(match_id, msg.sender);
        // this function can only be called if both player have sent in their ecrypted values
        require(
            matches[match_id].state != 8,
            "Match ended, other player has submited an invalid answer"
        );

        require(
            matches[match_id].state == 2 || matches[match_id].state == 3,
            "The match can continue only if both player have lock their move"
        );
        // make sure player can not call this function twice if already submited decode values

        bytes32 encoded_move = keccak256(
            abi.encodePacked(_PlayerRandomness, _choicePlain)
        );

        bytes32 player_submited_choice;
        if (player_id == 1) {
            require(
                matches[match_id].choice_1 != ROCK &&
                    matches[match_id].choice_1 != PAPER &&
                    matches[match_id].choice_1 != SCISSORS,
                "Player 1 Choice has already been decrypted!"
            );
            player_submited_choice = matches[match_id].choice_1;
        } else {
            require(
                matches[match_id].choice_2 != ROCK &&
                    matches[match_id].choice_2 != PAPER &&
                    matches[match_id].choice_2 != SCISSORS,
                "Player 2 Choice has already been decrypted!"
            );
            player_submited_choice = matches[match_id].choice_2;
        }

        // check if encoded_move sent is the same and has not been swaped
        require(
            encoded_move == player_submited_choice,
            "Player can't change the move mid match!"
        );

        //check if decoded choice is valid, if not block match
        if (
            bytes32(_choicePlain) == ROCK ||
            bytes32(_choicePlain) == PAPER ||
            bytes32(_choicePlain) == SCISSORS
        ) {
            if (matches[match_id].state == 2) {
                // only the first player has sent a choice, update state
                matches[match_id].state = matches[match_id].state + 1;
                // save decrypted choice
                if (player_id == 1) {
                    matches[match_id].choice_1 = bytes32(_choicePlain);
                } else {
                    matches[match_id].choice_2 = bytes32(_choicePlain);
                }
            } else if (matches[match_id].state == 3) {
                // if match state == 3 means that both players have called the function and,
                // both players have chosen valid values, call evalute the winner
                if (player_id == 1) {
                    matches[match_id].choice_1 = bytes32(_choicePlain);
                } else {
                    matches[match_id].choice_2 = bytes32(_choicePlain);
                } // save second player choice

                matches[match_id].state = 5; // update state directly to chosing winner
                evaluateWinner(match_id);
            }
        } else {
            // on of the players move is not allowed, stop match
            matches[match_id].state = 8; //
            //call cancel match and refund players
            cancelMatchAndReturnFunds();
        }
    }

    function evaluateWinner(uint256 _match_id) internal {
        // get players choices
        address player_1_address = matches[_match_id].player_1;
        address player_2_address = matches[_match_id].player_2;
        bytes32 player_1_choice = matches[_match_id].choice_1;
        bytes32 player_2_choice = matches[_match_id].choice_2;

        // if the choices are the same, the game is a draw, therefore returning 0x0000000000000000000000000000000000000000 as the winner
        if (player_1_choice == player_2_choice) {
            // change match state to DRAW
            matches[_match_id].state = 7;

            // check if match had a real bets
            if (matches[_match_id].betSize != 0) {
                // return money
                returnFunds(_match_id);
            }
            resetMappings(_match_id);
        } else {
            address winner;
            if (player_1_choice == ROCK && player_2_choice == PAPER) {
                winner = player_2_address;
            } else if (player_2_choice == ROCK && player_1_choice == PAPER) {
                winner = player_1_address;
            } else if (
                player_1_choice == SCISSORS && player_2_choice == PAPER
            ) {
                winner = player_1_address;
            } else if (
                player_2_choice == SCISSORS && player_1_choice == PAPER
            ) {
                winner = player_2_address;
            } else if (player_1_choice == ROCK && player_2_choice == SCISSORS) {
                winner = player_1_address;
            } else if (player_2_choice == ROCK && player_1_choice == SCISSORS) {
                winner = player_2_address;
            }

            // change match state to FOUND WINNER
            matches[_match_id].state = 6;
            payWinner(_match_id, winner);
        }
    }

    function payWinner(uint256 _match_id, address _winner_address) internal {
        // check if match had a real bet
        if (matches[_match_id].betSize != 0) {
            // calculate the amount won (double bet size)
            uint256 amount_won = matches[_match_id].betSize * 2;
            // pay winner
            IERC20(fauTokenAddress).transfer(_winner_address, amount_won);
        }
        resetMappings(_match_id);
    }

    // this is a functin that a player can call locally after the minimim time period
    // to cancel the match and get back the funds
    function cancelMatchAndReturnFunds() public {
        //make sure the player is inside an active match
        require(
            PlayerToMatchId[msg.sender] != 0,
            "Player does not have an active match!"
        );
        uint256 match_id = PlayerToMatchId[msg.sender];
        //make sure time interval have passed before allow to cancel the match, or if match state is already 8
        require(
            ((block.timestamp - matches[match_id].StartedTime) >
                minMatchLength) || (matches[match_id].state == 8),
            "Match Can not Be stopped Yet!"
        );
        //allow stopping a match only during certain match states, NOT when calculing a winner or already in the process of stopping a match.
        require(
            (matches[match_id].state == 0 ||
                matches[match_id].state == 1 ||
                matches[match_id].state == 2 ||
                matches[match_id].state == 3 ||
                matches[match_id].state == 4 ||
                matches[match_id].state == 8),
            "The Match Can not Be Stopped at this Stage!"
        );
        //change match State
        matches[match_id].state = 8;

        // check if match had a real bets
        if (matches[match_id].betSize != 0) {
            returnFunds(match_id);
        }
        resetMappings(match_id);
    }

    function returnFunds(uint256 _match_id) internal {
        address player_1_address = matches[_match_id].player_1;
        address player_2_address = matches[_match_id].player_2;
        uint256 bet_size = matches[_match_id].betSize;

        if (matches[_match_id].state == 7) {
            // return bets to both players if draw
            IERC20(fauTokenAddress).transfer(player_1_address, bet_size);
            IERC20(fauTokenAddress).transfer(player_2_address, bet_size);
        } else if (matches[_match_id].state == 8) {
            // change state before payment
            matches[_match_id].state = 9;
            // if match canceled, return funds only to player/s who participated
            if (matches[_match_id].choice_1 != bytes32(0)) {
                IERC20(fauTokenAddress).transfer(player_1_address, bet_size);
            }
            if (matches[_match_id].choice_2 != bytes32(0)) {
                IERC20(fauTokenAddress).transfer(player_2_address, bet_size);
            }
        }
    }

    function resetMappings(uint256 _match_id) internal {
        // reset mappings after match
        delete PlayerToMatchId[matches[_match_id].player_1];
        delete PlayerToMatchId[matches[_match_id].player_2];
    }
}
