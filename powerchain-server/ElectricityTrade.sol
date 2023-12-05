// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2 <0.9.0;

contract ElectricityTrade {
    uint256 public constant electricityPrice = 1000000000000000000;

    mapping(address => uint256) balances;

    uint256 energyQuantity;
    address payable seller;
    address payable buyer;

    constructor(address _buyer, uint256 _energyQuantity) {
        seller = payable(msg.sender);
        buyer = payable(_buyer);
        energyQuantity = _energyQuantity;
    }

    function getPrice() view public returns (uint256) {
      return energyQuantity * electricityPrice;
    }

    function buy() public payable {
        if (msg.sender != buyer) {
            revert Unauthorized();
        }
        if (msg.value < energyQuantity * electricityPrice) {
          revert WrongPrice();
        }
        if (balances[msg.sender] < energyQuantity * electricityPrice) {
            revert InsufficientBalance({
                requested: energyQuantity * electricityPrice,
                available: balances[msg.sender]
            });
        }

        payable(seller).transfer(energyQuantity * electricityPrice);
    }

    error InsufficientBalance(uint requested, uint available);

    error Unauthorized();

    error WrongPrice();
}
