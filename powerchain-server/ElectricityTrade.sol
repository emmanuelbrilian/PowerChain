// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2 <0.9.0;

contract ElectricityTrade {
    uint256 energyQuantity;
    uint256 price;
    address payable seller;
    address buyer;
    mapping(address => uint256) balances;

    constructor(address _buyer, uint256 _energyQuantity, uint256 _price) {
        seller = payable(msg.sender);
        energyQuantity = _energyQuantity;
        price = _price;
        buyer = _buyer;
    }

    function buy(uint256 amount) public {
        if (msg.sender != buyer) {
            revert Unauthorized();
        }
        if (amount < price) {
          revert WrongPrice();
        }
        if (price > buyer.balance) {
            revert InsufficientBalance({
                requested: price,
                available: balances[msg.sender]
            });
        }

        payable(seller).transfer(price);
    }

    error InsufficientBalance(uint requested, uint available);

    error Unauthorized();

    error WrongPrice();
}
