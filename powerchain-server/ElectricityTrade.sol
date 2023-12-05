// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2 <0.9.0;

contract ElectricityTrade {
    uint256 public constant electricityPrice = 1000000000000000000;

    mapping(address => uint256) balances;

    uint256 energyQuantity;
    address seller;
    address buyer;

    constructor(address _buyer, uint256 _energyQuantity) {
        seller = msg.sender;
        buyer = _buyer;
        energyQuantity = _energyQuantity;
    }

    function getPrice() view public returns (uint256) {
      return energyQuantity * electricityPrice;
    }

    function buy() public payable {
        if (msg.sender != buyer) {
            revert Unauthorized();
        }
        require(msg.value == getPrice(), 'Need to send exact amount of wei');
        payable(seller).transfer(getPrice());
    }

    error InsufficientBalance(uint requested, uint available);

    error Unauthorized();

    error WrongPrice();
}
