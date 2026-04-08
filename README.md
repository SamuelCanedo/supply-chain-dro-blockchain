# 🏭 Supply Chain Control Tower with DRO + Blockchain

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.0-black.svg)](https://soliditylang.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-red.svg)](https://streamlit.io/)

## 🎯 Overview

Inventory optimization system integrating:
- **Wasserstein DRO** with CVaR optimization
    - Realistic demand simulation (automotive with bullwhip effect, shocks, intermittent demand).
    - Forecasting with LightGBM + feature engineering.
    - Approximate DRO (Distributionally Robust Optimization) using a Wasserstein approach (bootstrap + CVaR-like on the tail).
- **Smart contracts** in Solidity for traceability
    - Blockchain (Solidity + Hardhat + Web3.py) for immutable decision logging and automated purchase orders.
- **Real-time dashboard** with Streamlit
    - Streamlit dashboard with auto-refresh, KPIs, charts, and Excel export.
 
## Thesis and Motivation
During my time at TE Connectivity, I realized how painful the lack of an objective and trackable system can be. Many suppliers and even people within the organization frequently misrepresented their responsibilities regarding lead times and product deliveries. One of my main operational tasks was to constantly fix errors in the system caused by this deficient delivery and inventory tracking process.

It is well known that in supply chain management — especially in the automotive industry — the bullwhip effect has a severe impact on the entire chain. Many products pass through multiple agents before reaching the final customer. A single delay anywhere in this chain can trigger a bullwhip effect that disrupts the whole business. In Just-In-Time (JIT) environments, these disruptions can even result in significant fines for production line stoppages.

This problem stayed in my mind for many months. Last semester, during the first part of my Master’s, I attended a seminar by Professor Shuming Wang (from UCAS) on supply chain optimization. That was my first exposure to Distributionally Robust Optimization (DRO) models, and the topic fascinated me for weeks.

This semester, I had the opportunity to attend a seminar by Professor Wolfgang Härdle on Blockchain, where one of the topics was the application of blockchain in supply chain, particularly in maritime transportation. That was the missing piece I needed. It allowed me to finally connect all the ideas I had been thinking about since my time at TE.

The result is an immutable tracking system based on blockchain, fed by a self-adjusting inventory model powered by DRO. This is the current MVP you can find in this repository.

## 🏗️ Architecture
```
simulate_live.py (loop every 30s)
↓
decision_engine.run_decision("wasserstein")
├── 1. generate_automotive_demand() → realistic synthetic data
├── 2. SupplyChainMVP (LightGBM) → 30-day forecast
├── 3. run_wasserstein() → computes Q_opt (approximate DRO)
├── 4. update_stock_simple(Q_opt) + set_reorder_point()
├── 5. generate_order(Q_opt) → creates JSON + calls confirmOrder() on blockchain
├── 6. send_decision() → recordsDecision() on blockchain
└── 7. compare_policies() → metrics (savings, stockouts, CVaR)
↓ (saves to JSONs for dashboard)
Dashboard (Streamlit app.py with autorefresh 2s)
└── Reads status from blockchain + JSON files (stock_history, epsilon_history, metrics, orders)
```

**Demand simulator**:
Includes trend, seasonality (weekly + yearly), noise, random shocks, and especially the bullwhip effect with progressive amplification by supply chain level (Tier 1 → Tier 3) + intermittent demand in Tier 3.

**Forecast**:
Generates realistic synthetic demand data (using demand_simulator_v2.py):
- Performs advanced feature engineering: lags, rolling statistics, shock flags, temporal variables.
- Trains a LightGBM model (a very powerful gradient boosting tree) to predict demand for the next 30 days recursively (with added noise to simulate uncertainty).
- Produces a forecast that directly feeds the next layer.
It is the prediction and uncertainty handling layer.

Converts raw demand data into a usable signal: "How much demand is expected from the market in the coming weeks?"

**DRO Optimizer**: 
Optimize safety stocks using a robust approach to uncertainty (Distributionally Robust Optimization) based on Wasserstein distance, balancing:

- Overstock cost
- Stockout cost
- Tail risk (CVaR - Conditional Value at Risk)

**Example of the math**

<img width="600" height="200" alt="image" src="https://github.com/user-attachments/assets/db644805-b8cd-4f7d-b957-a44350c02134" />

**Process**: 
1. Take historical data (last 60 days) + forecast (15 days)
2. Generate 200 bootstrap demand scenarios
3. Test 150 possible order quantities (Q)
4. Calculate CVaR (tail risk) for each Q
5. Select the Q that minimizes the worst-case scenario
6. Return: Q_opt, risk, epsilon

**Blockchain**:
Receives the output from the DRO optimizer (Q_opt = optimal order quantity, forecast, risk cost).
Records each decision in the inventoryDRO.sol smart contract via the recorderDecision() function.
Maintains the current inventory state (currentStock, reorderPoint).

Triggers automatic events:
- **DecisionRecorded**
- **PurchaseOrderTriggered (when there is a shortage and conditions are met)**
- **OrderConfirmed**
- **Alert**

Allows order confirmation (confirmOrder()) and stock updates in an auditable manner.

Everything is **immutably** recorded on the local blockchain (Hardhat).

- **Role within the project**:

It is the governance and auditability layer.
Converts model decisions (which are just numbers in Python) into recorded, transparent actions.
Allows multiple stakeholders (suppliers, auditors, management) to trust that optimization decisions were made and executed correctly.
Partially automates the replenishment process (order triggering).



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
### DASHBOARD RUNNING

<img width="1873" height="888" alt="Captura de pantalla 2026-04-08 140610" src="https://github.com/user-attachments/assets/fdc615e6-3e94-4355-a287-13051391efc9" />

### TERMINALS RUNNING

<img width="1896" height="966" alt="image" src="https://github.com/user-attachments/assets/8d8d384e-afe2-40fb-984d-5c020421eabc" />

### RESULTS FROM THE MODEL FOR 30 CYCLES (collected by the automatic export function on the dashboard)

<img width="1328" height="49" alt="image" src="https://github.com/user-attachments/assets/603c95c2-149b-4b85-9d72-dda886df6889" />

### RESULTS FROM THE MODEL FOR 84 CYCLES (collected by the automatic export function on the dashboard)
<img width="1328" height="49" alt="image" src="https://github.com/user-attachments/assets/ee1fa170-6d81-432f-b9b5-70422a7437d0" />



## Summary of the models behavior and results

| Metric | First Run (30 cycles) | Second Run (84 cycles) | General Trend |
|--------|----------------------|------------------------|----------------|
| Savings vs Baseline | 2.50% average | 3.90% average | Improving |
| Average Savings USD per cycle | ~$2,983 | ~$3,897 | Improving |
| Stockout Reduction | 4.17% average | ~5-6% (estimated) | Positive |
| CVaR Savings (risk protection) | +10 average | +11.6 average | Slight improvement |
| Epsilon (uncertainty) | 0.106 average | 0.105 average | Stable |
| Q_opt DRO vs Baseline | +19.5 units | Similar (+20 approx.) | DRO orders ~10-12% more |

### Conclusions
The DRO-Wasserstein model is performing consistently. It generates modest but positive savings (2.5% → 3.9%) and slightly reduces stockouts. The risk protection (CVaR) is generally positive, although in some cycles it is negative (which is normal in simulation). With an average of 10 - 12% + on the orders the model rathers to pay more stock to avoid the risk of the tail (CVaR).


## Implementation gaps that can be developed on future versions

1. **Rebuild the inventory simulation**
- Implement a real day-by-day simulation:
  - Actual demand consumption each cycle
  - Pending orders with stochastic lead time
  - Accumulated stock (no replacement)
  - Real holding + stockout + ordering costs
- This will make the savings and stockout metrics much more reliable.

2. **Improve the DRO core**
- Move from heuristics (bootstrap + tail) to a more rigorous formulation:
  - Use cvxpy or scipy.optimize to solve a convex approximation of Wasserstein DRO.
  - Or at least implement Sample Average Approximation (SAA) + robust optimization.
  - Add explicit sensitivity to the uncertainty radius (epsilon).
- Goal: raise average savings to 7-12% and make CVaR consistently positive.

3. **More mature blockchain**
- Add roles (onlyOwner, SupplyChainManager)
- Implement richer events and an oracle for external data
- Consider migrating to a testnet (Polygon or BSC) or Hyperledger Fabric for enterprise

4. **More rigorous evaluation**
- Multiple seeds and sensitivity analysis
- Comparison against several strong baselines (Newsvendor, (s,S), SAA, etc.)
- Backtesting with real historical data (not just synthetic)
