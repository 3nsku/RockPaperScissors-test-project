# LOGIC

- To Start a Match, the contract requires 2 player addresses and a bet size. The player how wants to set up the match, starts by calling the the function **setUpMatch** inside the Smart Contract.

- Each player chooses a move! The move is enrypted with a random temporary key generated localy (e.g. "ROCK" + "123456"). Each player calls the function **saveEncryptedChoiceAndEntranceFee** and the move is stored encoded on chain.

- Encrypting the move guarantes that the second player will no be able look up the first player move on the Blockchain.

- Only after both players have submited their encoded moves, the match can proceed.

- The next step is for each player to call the **DecryptChoice** function. The player has pass their move in plain text (e.g. "ROCK") and thier local temporary secret_key (e.g. "123456"). If the player move is valid and has not been alterded, it is stored in plain text on the Blockchain.

- Once Both Players have decoded their move the function **evaluateWinner** is called by the Smart Contract to find the winner, distribute the Winnings and reset the mappings!

## RIGHT TO CANCEL MATCH

- If only 1 player submits an encoded move, and the other player goes offline or stops playing. After a minimin wait of 60 seconds the first player has the right to cancel the match and withdraw the submited bet by calling **cancelMatchAndReturnFunds**

---

# RockPaperScissors test project

You will create a smart contract named `RockPaperScissors` whereby:  
Alice and Bob can play the classic game of rock, paper, scissors using ERC20 (of your choosing).

- To enroll, each player needs to deposit the right token amount, possibly zero.
- To play, each Bob and Alice need to submit their unique move.
- The contract decides and rewards the winner with all token wagered.

There are many ways to implement this, so we leave that up to you.

## Stretch Goals

Nice to have, but not necessary.

- Make it a utility whereby any 2 people can decide to play against each other.
- Reduce gas costs as much as possible.
- Let players bet their previous winnings.
- How can you entice players to play, knowing that they may have their funds stuck in the contract if they face an uncooperative player?
- Include any tests using Hardhat.

Now fork this repo and do it!

When you're done, please send an email to zak@slingshot.finance (if you're not applying through Homerun) with a link to your fork or join the [Slingshot Discord channel](https://discord.gg/JNUnqYjwmV) and let us know.

Happy hacking!
