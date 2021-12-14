// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockFAU is ERC20 {
    constructor() ERC20("FAU Token", "FAU") {
        _mint(address(this), 1000000000000000000000000); //1 million initial supply
    }
}
