# forecast_model.py

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

class SupplyChainMVP: 
    
    def __init__(self):
        self.model = None
        self.features = None
        self.last_data= None

## Feature Engineering

    def prepare_data(self, df, target='demand', date='date'):
        df = df.copy()
        df[date] = pd.to_datetime(df[date])

        # Time features
        df['dow'] = df[date].dt.dayofweek
        df['month'] = df[date].dt.month

        # Weekend flag 
        df['is_weekend'] = (df['dow'] >= 5).astype(int)

        # Lags
        for lag in [1, 7, 14, 30]:
            df[f'lag_{lag}'] = df[target].shift(lag)
        
        # Rolling stats 
        df['rolling_mean_7'] = df[target].rolling(window=7).mean()
        df['rolling_std_7'] = df[target].rolling(window=7).std()

        df['rolling_mean_30'] = df[target].rolling(30).mean()
        df['rolling_std_14'] = df[target].rolling(14).std()

        # Shock detection (proxy)
        df['shock'] = (df[target] > df['rolling_mean_7'] * 1.5).astype(int)

        df = df.dropna().reset_index(drop=True)

        self.features = [c for c in df.columns if c not in [target, date]]

        return df 
    
    ## Model Training
    def fit(self, df, target='demand'):
        X = df[self.features]
        y = df[target]

        self.model = LGBMRegressor(
            min_data_in_leaf=5, 
            min_gain_to_split=0.01,
            num_leaves=10,
            max_depth=3,
            verbose=-1    
        )

        self.model.fit(X, y)
        self.last_data = df.copy()

    # Recursive forecasting (STOCHASTIC)
    def predict(self, steps=30, noise_scale=0.1):
        df = self.last_data.copy()
        preds = []

        for _ in range(steps):
            last_row = df.iloc[-1:].copy()

        # Predict
            X = last_row[self.features]
            base_pred = self.model.predict(X)[0]

            # Add uncertainty (100% RIAL no FAKE)
            noise = np.random.normal(0, noise_scale * base_pred)
            pred = max(base_pred + noise, 0)

            preds.append(pred)

        # Create a new row for the next iteration
            new_row = last_row.copy()
            new_row['demand'] = pred
            new_row['date'] = new_row['date'] + pd.Timedelta(days=1)
        
        # update lags manually
            for lag in [1, 7, 14, 30]:
                if len(df) >= lag:
                    new_row[f'lag_{lag}'] = df['demand'].iloc[-lag]

            # Rolling update (simple approximation)
            window = df['demand'].iloc[-6:].tolist() + [pred]
            new_row['rolling_mean_7'] = np.mean(window)
            new_row['rolling_std_7'] = np.std(window)   

            new_row['rolling_mean_30'] = df['demand'].iloc[-29:].mean()
            new_row['rolling_std_14'] = df['demand'].iloc[-13:].std()

            # Update time features 
            new_row['dow'] = new_row['date'].dt.dayofweek
            new_row['month'] = new_row['date'].dt.month
            new_row['is_weekend'] = (new_row['dow'] >= 5).astype(int)

            # Shock proxy 
            new_row['shock'] = int(pred > new_row['rolling_mean_7'].iloc[0] * 1.5)

            df = pd.concat([df, new_row], ignore_index=True)

        return np.array(preds)
    
    # -----------------------------
    # DISTRIBUTION FORECAST (PARA DRO)
    # -----------------------------
    def predict_distribution(self, steps=30, n_scenarios=50):
        scenarios = []

        for _ in range(n_scenarios):
            preds = self.predict(steps=steps)
            scenarios.append(preds)

        return np.array(scenarios)