// SPDX-License-Identifier: MIT

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

pragma solidity ^0.8.0;

contract RockPaperScissors {
    bytes32 constant ROCK = "ROCK";
    bytes32 constant PAPER = "PAPER";
    bytes32 constant SCISSORS = "SCISSORS";

    // for simplicity we have only have 1 ERC20 token
    address public fauTokenAddress;

    // match lengh in seconds, after which if one player afk or internet problem, end match and return funds
    uint256 public matchLength = 30;

    // STATES:
    // MATCH_CREATED = 0,
    // FIRST_PLAYER_IN = 1,
    // SECOND_PLAYER_IN = 2,
    // FIRST_PLAYER_DECRYPTED_ASNWER = 3,
    // SECOND_PLAYER_DECRYPTED_ANSWER = 4,
    // CHOOSING_WINNER = 5,
    // WINNER_FOUND = 6,
    // DRAW = 7,
    // MATCH_ERROR_RETURN_FUNDS = 8

    // players array is a always a list of 2 addresses

    // player choice default is zero

    // winner can be: 0 if draw otherwise player address

    struct Match {
        uint256 state;
        uint256 betSize;
        address[2] players;
        bytes32[2] choices;
        address winner;
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
                [address(0), address(0)],
                [bytes32(0), bytes32(0)],
                address(0)
            )
        );
    }

    // set up the match between 2 players
    // - create a mapping
    // - start 1min timer
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
            PlayerToMatchId[_player1] != 0,
            "Player1 is already playing a Game"
        ); //make sure player 1 is not already inside an active match
        require(
            PlayerToMatchId[_player2] != 0,
            "Player2 is already playing a Game"
        ); //make sure player 2 is not already inside an active match
        require(_match_bet > 0, "Match Bet must be Bigger Than 0"); //stake must be

        //add new match to list
        matches.push(
            Match(
                0,
                _match_bet,
                [_player1, _player2],
                [bytes32(0), bytes32(0)],
                address(0)
            )
        );
        // update mappings
        uint256 match_id = matches.length - 1;
        PlayerToMatchId[_player1] = match_id;
        PlayerToMatchId[_player2] = match_id;

        //TODO SET TIMER FOR CALLBACK WITH 2 PLAYER ADDRESSES
        //
        // do do do do do doo
        //
    }

    // save encrypted choice! and receive payment
    function saveEncryptedChoiceAndEntranceFee(bytes32 _choice, address _token)
        public
        payable
    {
        //make sure the player is inside an active match
        require(
            PlayerToMatchId[msg.sender] != 0,
            "Player does not have an active match!"
        );
        uint256 match_id = PlayerToMatchId[msg.sender];
        uint256 player_position_id = getPlayerPosition(match_id, msg.sender);
        //check if player has not already chosen a value for this match
        require(
            matches[match_id].choices[player_position_id] != bytes32(0),
            "Choice Already Made!"
        );
        // check if amount sent matches agreed bet size
        require(
            matches[match_id].amount == msg.value,
            "Amount Sent Does Not Match Bet Size"
        );
        //check if token address matches allowed tokens list
        require(_token == fauTokenAddress, "Token Sent is Not Allowed");

        // save encrypted player choice
        matches[match_id].choices[player_position_id] = _choice;

        //transfer funds to contract
        IERC20(fauTokenAddress).transfer(address(this), msg.value);

        // update match state
        matches[match_id].state = matches[match_id].state + 1;
    }

    // check if address is player 1 or player 2 -> return 0 or 1
    function getPlayerPosition(uint256 _match_id, address _address)
        internal
        view
        returns (uint256)
    {
        if (matches[_match_id].players[0] == _address) {
            return 0;
        } else {
            return 1;
        }
    }

    function DecryptChoice(bytes32 _choice, bytes32 _PlayerRandomness) public {
        //make sure the player is inside an active match
        require(
            PlayerToMatchId[msg.sender] != 0,
            "Player does not have an active match!"
        );
        //player randomness can not be 0
        require(_PlayerRandomness != bytes32(0), "Randomn value can not be 0");
        // get match id:
        uint256 match_id = PlayerToMatchId[msg.sender];
        uint256 player_position_id = getPlayerPostion(match_id, msg.sender);
        // this function can only be called if both player have sent in their ecrypted values
        require(matches[match_id].state == 2 || matches[match_id].state == 3);
        // make sure player can not call this function twice if already submited decrypted value
        require(
            matches[match_id].choices[player_position_id] != ROCK ||
                matches[match_id].choices[player_position_id] != PAPER ||
                matches[match_id].choices[player_position_id] != SCISSORS,
            "Player Choise has already been decrypted!"
        );

        //decrypt values and check if inside array
        bytes32 decrypted_value = keccak256(
            abi.encodePacked(_choice, _PlayerRandomness)
        );

        //check if choice sent is valid
        if (
            decrypted_value == ROCK ||
            decrypted_value == PAPER ||
            decrypted_value == SCISSORS
        ) {
            if (matches[match_id].state == 2) {
                // only the first player has sent a choice
                matches[match_id].state == matches[match_id].state + 1;
                // save decrypted choice
                matches[match_id].choices[player_position_id] = decrypted_value;
            } else {
                // if match state == 3 means that both players have called the function and,
                // both players have chosen valid values, call evalute the winner

                matches[match_id].state = 5; // set state to choose winner
                matches[match_id].choices[player_position_id] = decrypted_value; // save second player choice

                evaluateWinner(match_id);
            }
        } else {
            // on of the players choice is not allowed, block the match
            matches[match_id].state = 8;
        }
    }

    function evaluateWinner(uint256 _match_id) internal {
        // get players choces
        address player_1_address = matches[_match_id].players[0];
        address player_2_address = matches[_match_id].players[1];
        bytes32 player_1_choice = matches[_match_id].choices[0];
        bytes32 player_2_choice = matches[_match_id].choices[1];

        // if the choices are the same, the game is a draw, therefore returning 0x0000000000000000000000000000000000000000 as the winner
        if (player_1_choice == player_2_choice) {
            // change match state to DRAW
            matches[_match_id].state = 7;
            // return money
            returnFunds(_match_id);
        }

        address winner;
        if (player_1_choice == ROCK && player_2_choice == PAPER) {
            winner = player_2_address;
        } else if (player_2_choice == ROCK && player_1_choice == PAPER) {
            winner = player_1_address;
        } else if (player_1_choice == SCISSORS && player_2_choice == PAPER) {
            winner = player_1_address;
        } else if (player_2_choice == SCISSORS && player_1_choice == PAPER) {
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

    function payWinner(uint256 _match_id, address _winner_address) internal {
        // pay winner
        uint256 amount_won = 
        IERC20(fauTokenAddress).transfer(_winner_address, amount_won);

        resetMappings(_match_id);
    }

    function returnFunds(uint256 _match_id) internal {
        // return entry fee to players

        resetMappings(_match_id);
    }

    function resetMappings(uint256 _match_id) internal {
        // reset mappings after match
        delete PlayerToMatchId[matches[_match_id].players[0]];
        delete PlayerToMatchId[matches[_match_id].players[1]];
    }
}

// entrace fee
// check if min entrace fee met | entrace must be above 0

// set up the match: player vs player and stake

// rock + random value generated locally (encrypt locally and send to the blockchain)

// store choise encrypted and start timer 30 seconds for callback function

// the other player has 30 seconds to choose a move after the the first player move has been stored. if he does not submit anything on time the match is ended.

// 1) if after 30 seconds of first choise registred not received a second choise, then end match, and return money

// 2) if the other choise arrives before the timer ends, both values are stored on the chain.
// A local function on both devices query to chain every 5 seconds, once they get a confirmation that the match can start they will send the stored local values and decrypt the choises. and store the non encrypted choise
// wait for callback after 30 seconds and choose winner. or if both values decrypted call choose winner asap

// 3) encrypted choises have been stored on chain, but one of the players looses the internet connection and does not send the local value.
// then after 30 seconds if only 1 value has been decrypted don't choose end match

// 4) if value sent is not correct cancel match
