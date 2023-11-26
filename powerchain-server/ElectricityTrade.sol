// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2 <0.9.0;

/**
 * @title Transfer
 * @dev Sell and buy electricity
 */
contract ElectricityTrade {

    uint256 amount;
    uint256 price;
    address seller;
    mapping(address => uint) public balances;

    /**
     * @dev Sell an amount of electricity at the given price
     * @param electricAmount that is sent to buyer
     * @param electricPrice total price of electricAmount
     */
    constructor(uint256 electricAmount, uint256 electricPrice) {
        seller = msg.sender;
        amount = electricAmount;
        price = electricPrice;
    }

    /**
     * @dev Buy the electricity
     */
    function buy() public {
        if (price > balances[msg.sender])
            revert InsufficientBalance({
                requested: price,
                available: balances[msg.sender]
            });

        balances[msg.sender] -= amount;
        balances[seller] += amount;
    }

    error InsufficientBalance(uint requested, uint available);

}