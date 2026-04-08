# 🏭 Supply Chain Control Tower with DRO + Blockchain

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.0-black.svg)](https://soliditylang.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-red.svg)](https://streamlit.io/)

## 🎯 Overview

Inventory optimization system integrating:
- **Wasserstein DRO** with CVaR optimization
- **Smart contracts** in Solidity for traceability
- **Real-time dashboard** with Streamlit

## 📊 Results

| Metric | Improvement |
|--------|-------------|
| Savings vs baseline | 2-15% |
| Stockout reduction | 10-20% |
| CVaR protection | $100-200/cycle |

## 🏗️ Architecture
Demand Simulator → Forecast → DRO Optimizer → Blockchain → Dashboard

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+ (for Hardhat)
- Git

### Installation

```bash
# Clone repository
git clone git@github.com:SamuelCanedo/supply-chain-dro-blockchain.git
cd supply-chain-dro-blockchain

# Create virtual environment
python -m venv dro_env
source dro_env/bin/activate  # Linux/Mac
# dro_env\Scripts\activate   # Windows

# Move contracts folder to root and delete blockchain folder
# From: blockchain/contracts/ → To: contracts/

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp config.example.py config.py
# Edit config.py with your values once you run the node and the contract

# Install Hardhat (if not installed)
npm install hardhat@2.22.0 --save-dev
npm install --save-dev @nomicfoundation/hardhat-toolbox@5.0.0

# Create hardhat.config.js
New-Item -Path hardhat.config.js -ItemType File -Force

## Add this to hardhat.config.js:
"""
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.28",
  networks: {
    localhost: {
      url: "http://127.0.0.1:8545"
    }
  }
};
"""
```

### Run the System
```bash
# Terminal 1 - Start blockchain:
bash
npx hardhat node

# Terminal 2 - Deploy contract:
bash
npx hardhat run scripts/deploy.js --network localhost

# Terminal 3 - Run listener:
bash
py -m integration.listener

# Terminal 4 - Run simulator:
bash
py simulate_live.py

# Terminal 5 - Start dashboard:
bash
streamlit run dashboard/app.py
```
