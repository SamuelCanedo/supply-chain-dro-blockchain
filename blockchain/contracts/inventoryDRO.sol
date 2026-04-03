// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract inventoryDRO{
    
    struct Decision {
        uint256 forecast;  // DEMAND FORECAST 
        uint256 optimalQ;  // OPTIMAL QUANTITY TO ORDER
        uint256 riskCost;  // COST ASOCIATED WITH RISK
        uint256 timestamp;  // MOMENT OF THE DECISION
    }

    uint256 public currentStock;  // CURRENT STOCK  
    uint256 public reorderPoint;  // REORDER POINT 
    uint256 public lastOrderQuantity; // LAST ORDER QUATITY
    uint256 public lastOrderTimestamp; // MOMENT OF THE LAST ORDER

    Decision[] public decisions;  // ARRAY OF HISTORIY OF THE DECISIONS 

    // Mapping TO AVOID DUPLACATED ORDERS
    mapping(uint256 => bool) public processedOrders;
    uint256 public orderCooldown = 60; //WAITING TIME BETWEEN ORDERS

    // Events
    event DecisionRecorded(uint256 forecast, uint256 optimalQ, uint256 riskCost);
    event PurchaseOrderTriggered(uint256 quantity);
    event OrderConfirmed(uint256 quantity, uint256 timestamp);
    event Alert(string message);
    event Debug(uint256 stock, uint256 reorderPoint);
    event StockUpdated(uint256 newStock, uint256 oldStock);

    constructor(uint256 _initialStock, uint256 _reorderPoint) {
        currentStock = _initialStock;
        reorderPoint = _reorderPoint;
    }

    // SAVE THE OUTPUT OF THE MODEL
    function recorderDecision(
        uint256 forecast,
        uint256 optimalQ,
        uint256 riskCost
    ) public {
        
        emit Debug(currentStock, reorderPoint);

        decisions.push(Decision(
            forecast, 
            optimalQ,
            riskCost,
            block.timestamp
        ));

        emit DecisionRecorded(forecast, optimalQ, riskCost);

        // LOGIC OF THE AUTOMATIC PURCHASING ORDER
        _checkAndTriggerOrder(optimalQ);
    }

    // INTERNAL LOGIC TO VERIFY AND TRIGGER THE ORDERS
    function _checkAndTriggerOrder(uint256 optimalQ) internal {
        // VERIFY IF THERE'S A SHORTAGE
        bool isShortage = currentStock < reorderPoint;

        // VERIFY COOLDOWN
        bool cooldownPassed = (block.timestamp - lastOrderTimestamp) >= orderCooldown;

        // VERIFY THAT THE SAME QUANTITY HAS NOT BEEN ISSUED RECENTLY 
        bool notRecentlyOrdered = !processedOrders[optimalQ] || cooldownPassed;

        if (isShortage && notRecentlyOrdered) {
            emit PurchaseOrderTriggered(optimalQ);

            // REGISTER THE ORDER
            lastOrderQuantity = optimalQ;
            lastOrderTimestamp = block.timestamp;
            processedOrders[optimalQ] = true;

            emit Alert("Purchase order triggered - waiting for confirmation");
        } else if (isShortage) {
            emit Alert("Stock below reorder point! Order already in process");
        }
    }

    // COMFIRMATION OF RECIVING THE ORDER (CALL TO ERP WHEN THE ORDER HAS BEEN PROCESSED)
    function confirmOrder(uint256 quantity) public {
        require(quantity > 0, "Quantity must be greater than 0");

        uint256 oldStock = currentStock;
        currentStock += quantity;

        emit OrderConfirmed(quantity, block.timestamp);
        emit StockUpdated(currentStock, oldStock);

        // VERIFY IS THE STOCK IS NOT IN SHORTAGE ANYMORE
        if (currentStock >= reorderPoint) {
            emit Alert("Stock recovered above reorder point!");
        } else if (currentStock < reorderPoint) {
            emit Alert("Stock still below reorder point after order");
        }

        // CLEAN THE REGISTER
        processedOrders[quantity] = false;
    }

    // UPDATE THE STOCK 
    function updateStock(uint256 newStock) public {
        uint256 oldStock = currentStock;
        currentStock = newStock;

        emit StockUpdated(currentStock, oldStock);

        if (currentStock < reorderPoint) {
            emit Alert("Stock below reorder point!");
        } else if (currentStock >= reorderPoint && oldStock < reorderPoint) {
            emit Alert("Stock recovered above reorder point");
        }
    }

    // SET THE REORDER POINT
    function setReorderPoint(uint256 _newReorderPoint) public {
        reorderPoint = _newReorderPoint;
        emit Alert(string(abi.encodePacked("Reorder point updated to: ", _newReorderPoint)));
    }

    // SET THE COOLDOWN BETWEEN ORDERS IN SECONDS
    function setOrderCooldown(uint256 _cooldown) public {
        orderCooldown = _cooldown;
    }

    // VERIFY IF IS POSSIBLE TO ORDER NOW
    function canOrder() public view returns (bool) {
        bool isShortage = currentStock < reorderPoint;
        bool cooldownPassed = (block.timestamp - lastOrderTimestamp) >= orderCooldown;
        return isShortage && cooldownPassed;
    }

    // CURRENT STATE
    function getStatus() public view returns (
        uint256 stock,
        uint256 reorder,
        bool shortage,
        uint256 lastOrder,
        uint256 cooldownRemaining
    ) {
        stock = currentStock;
        reorder = reorderPoint;
        shortage = currentStock < reorderPoint;
        lastOrder = lastOrderQuantity;

        if (lastOrderTimestamp > 0 && block.timestamp < lastOrderTimestamp + orderCooldown) {
            cooldownRemaining = (lastOrderTimestamp + orderCooldown) - block.timestamp;
        } else {
            cooldownRemaining = 0;
        }
    }

    // PULL THE # OF DECISIONS
    function getDecisionCount() public view returns (uint256) {
        return decisions.length;
    }
}