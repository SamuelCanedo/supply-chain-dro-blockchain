const hre = require("hardhat");

async function main() {
  const initialStock = 500;
  const reorderPoint = 150;
  
  const InventoryDRO = await hre.ethers.getContractFactory("inventoryDRO");
  const inventory = await InventoryDRO.deploy(initialStock, reorderPoint);
  
  await inventory.waitForDeployment();
  
  console.log("✅ Contract deployed to:", await inventory.getAddress());
}

main().catch(console.error);