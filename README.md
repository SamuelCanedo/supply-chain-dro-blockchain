# 🏭 Supply Chain Control Tower with DRO + Blockchain

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.0-black.svg)](https://soliditylang.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-red.svg)](https://streamlit.io/)

## 🎯 Overview

Sistema de optimización de inventario que integra:
- **DRO Wasserstein** con optimización CVaR
- **Smart contracts** en Solidity para trazabilidad
- **Dashboard** en tiempo real con Streamlit

## 📊 Resultados

| Métrica | Mejora |
|---------|--------|
| Ahorro vs baseline | 2-15% |
| Reducción de stockouts | 10-20% |
| Protección CVaR | $100-200/ciclo |

## 🏗️ Arquitectura
Demand Simulator → Forecast → DRO Optimizer → Blockchain → Dashboard


## 🚀 Quick Start

### Prerrequisitos
- Python 3.10+
- Node.js 16+ (para Hardhat)
- Git

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/immutable_system.git
cd immutable_system

# Crear entorno virtual
python -m venv dro_env
source dro_env/bin/activate  # Linux/Mac
# dro_env\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp config.example.py config.py
# Editar config.py con tus valores

# Iniciar blockchain local
npx hardhat node

# Desplegar contrato (en otra terminal)
npx hardhat run scripts/deploy.js --network localhost

# Ejecutar simulador
python simulate_live.py

# Iniciar dashboard (en otra terminal)
streamlit run dashboard/app.py

# Estructura
├── blockchain/          # Smart contracts
├── dashboard/           # Streamlit UI
├── pipeline/            # DRO + Forecast models
├── integration/         # Blockchain integration
└── scripts/             # Deployment scripts

# Tecnologias 
- Backend: Python, NumPy, Pandas

- ML: DRO Wasserstein, CVaR

- Blockchain: Solidity, Hardhat, Web3.py

- Frontend: Streamlit

# Dashboard
- Stock en tiempo real

- KPIs de rendimiento

- Historial de decisiones

- Alertas automáticas

# Ciclo de decision
1. Generar demanda simulada

2. Forecast 30 días

3. DRO calcula Q_opt

4. Actualizar blockchain

5. Dashboard refresca cada 2s

# Licence 
MIT

# Author 
Samuel Canedo Linkedin: www.linkedin.com/in/samuelcanedo