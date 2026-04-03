# demand_simulator_v2.py

import numpy as np 
import pandas as pd ## Handling tabular data and time series
from datetime import datetime ## Handling dates

# ============================================
# MAIN FUNCTION: GENERATE AUTOMOTIVE DEMAND
# ============================================


def generate_automotive_demand(days=90, seed=42):
    """
    Generate synthetic automotive supply chain demand data.
    
    Parameters: 
    - days: number of days to generate (default 90)
    - seed: seed for reproducibility (default 42)
    
    Returns:
    - DataFrame with demand by level (OEM, Tier1, Tier2, Tier3)
    """

    # ============================================
    # 1. INITIAL CONFIGURATION
    # ============================================
    
    # Set random seed for reproducibility
    np.random.seed(seed)

    # ============================================
    # 2. DATE GENERATION
    # ============================================

    # Create a date range from 'days' ago until today
    # E.g., if days=180, generates dates from 6 months ago until today
    
    dates = pd.date_range(end=datetime.now(), periods=days)

    # ============================================
    # 3. BASE OEM DEMAND (ORIGINAL EQUIPMENT MANUFACTURER)
    # ============================================

    # CONSTANT BASE DEMAND

    base = 120 

    # Linear trend: gradually increases over time (0 to 30 units in 30 days)
    trend = np.linspace(0, 30, days)

    # Weekly seasonality: 7-day cycle (Monday to Sunday)
    # Weekdays have higher demand than weekends
    weekly = 20 * np.sin(2 * np.pi * dates.dayofweek / 7)

    # Yearly seasonality: smooth seasonal cycle over the year
    yearly = 15 * np.sin(2 * np.pi * dates.dayofyear / 365)

    # Random noise (mean 0, standard deviation 10)
    noise = np.random.normal(0, 10, days)

    # Combine all components to get final OEM demand  
    oem = base + trend + weekly + yearly + noise 

    # ============================================  
    # 4. SHOCKS (UNEXPECTED INTERRUPTIONS)
    # ============================================    
    # Initialize array of zeros for shocks
    shocks = np.zeros(days)

    # Add random shocks on 5% of the days
    for _ in range(int(days * 0.05)):
        # Select random day to apply shock
        idx = np.random.randint(0, days)
        # Add spike (+80) or drop (-60) randomly
        shocks[idx] += np.random.choice([80, -60])

    # Apply shocks to OEM demand
    oem += shocks

    # Ensure demand is not negative (minimum 0 units)
    oem = np.maximum(oem, 0)

    # ============================================
    # 5. BULLWHIP EFFECT (CHAIN AMPLIFICATION)
    # ============================================
    # This effect causes variability to increase up the supply chain
    # (Tier 3 more volatile than Tier 1)

    def amplify(demand, factor): 
        """
        Amplify demand by adding proportional noise. 
        factor: amplification level (higher = more variability)
        """
        return demand * (1 + np.random.normal(0, factor, len(demand)))
    
    """
    # Convert to arrays to avoid indexing issues
    oem_demand_array = np.array(oem_demand)
    """

    # Apply amplification to each supply chain level
    tier1 = amplify(oem, 0.15)           # Variability +15%
    tier2 = amplify(tier1, 0.25)        # Variability +25% over Tier1
    tier3 = amplify(tier2, 0.35)        # Variability +35% over Tier2

    # ============================================
    # 6. INTERMITTENT DEMAND (TIER 3)
    # ============================================
    # Ensure tier3 is a Numpy array to modify it with a mask
    tier3 = np.array(tier3)

    # At higher levels (Tier 3), there are often days with no demand
    # Create mask: 30% of the days will have zero demand
    mask = np.random.rand(days) < 0.3 # True in 30% of the days
    tier3 = np.maximum(tier3, 1) # Ensure no negative values before applying mask
    tier3[mask] = 0 # Set demand to 0 where mask is true

    # ============================================
    # 7. LEAD TIMES (TIEMPOS DE ENTREGA)
    # ============================================
    # Different levels have different lead times
    # Tier 1: Faster (2-5 days)
    lead_tier1 = np.random.randint(2, 5, days)

    # Tier 2: Medium (5-10 days)
    lead_tier2 = np.random.randint(5, 10, days)

    # Tier 3: Slower (10-20 days)
    lead_tier3 = np.random.randint(10, 20, days)

    # ============================================
    # 8. CREATION OF THE FINAL DATAFRAME
    # ============================================
    df = pd.DataFrame({
        # Date column (time index)
        "date": dates,

        # DEMAND BY LEVEL (INTEGERS)
        "OEM": oem.astype(int),  # Original Equipment Manufacturer
        "tier1": tier1.astype(int),     # Tier 1 Supplier
        "tier2": tier2.astype(int),     # Tier 2 Supplier
        "tier3": tier3.astype(int),     # Tier 3 Supplier

        # Lead times
        "lead_tier1": lead_tier1, # Days for Tier 1
        "lead_tier2": lead_tier2, # Days for Tier 2
        "lead_tier3": lead_tier3, # Days for Tier 3

        # AUXILIARY VARIABLES (for analysis)
        "dow": dates.dayofweek, # Day of the week (0=Monday, 6=Sunday)
        "month": dates.month # Month of the year (1-12)
    })

    # Upstream dependency (correlation between levels)
    df["OEM_lag1"] = df["OEM"].shift(1) # OEM demand from the previous day
    df["tier1_lag1"] = df["tier1"].shift(1) # Tier 1 demand from the previous day

    # Shock flag (for DRO)
    df["shock_flag"] = (np.abs(shocks) > 0).astype(int)

    # Final data cleaning
    df = df.bfill() # Fill missing values (first days) with the next valid value

    # Return the generated DataFrame
    return df

# ============================================
# EXAMPLE USAGE (optional)
# ============================================

if __name__ == "__main__":
    # Generate data for 180 days 
    df_automotive = generate_automotive_demand(days=180, seed=42)

    # Show first 10 rows
    print("First 10 rows of generated data:")
    print(df_automotive.head(10))

    # Show basic statistics
    print("\nDescriptive statistics:")
    print(df_automotive[['OEM', 'tier1', 'tier2', 'tier3']].describe())

    # Check for zero demand in Tier 3 (intermittent demand)
    zero_demand_pct = (df_automotive['tier3'] == 0).mean() * 100
    print(f"\n Percentage of days with zero demand in Tier 3: {zero_demand_pct:.1f}%")

    # Check data types
    print("\n Data types in the DataFrame")
    print(df_automotive.dtypes)


# ============================================
# COMPACT VISUALIZATION (optional)
# ============================================

import matplotlib.pyplot as plt
import seaborn as sns

def quick_analysis(df):
    """Quick analysis of demand patterns and variability in the supply chain."""

    # Basic configuration
    tiers = ['OEM', 'tier1', 'tier2', 'tier3']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

    # MAIN FIGURE (more compact and focused on key insights)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle('Automotive Supply Chain Analysis', fontsize=14, fontweight='bold')

        # 1. Trend by level
    for tier, color in zip(tiers, colors):
        axes[0,0].plot(df['date'], df[tier], label=tier, color=color, alpha=0.7, linewidth=1)
    axes[0,0].set_title('Demand by Level')
    axes[0,0].legend(fontsize=8)
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Boxplot
    axes[0,1].boxplot([df[tier] for tier in tiers], tick_labels=tiers, patch_artist=True,
                      boxprops=dict(facecolor='lightblue'), showmeans=True)
    axes[0,1].set_title('Distribution by Level')
    axes[0,1].grid(True, alpha=0.3, axis='y')
    
    # 3. Heatmap by day of the week
    dow_avg = pd.DataFrame({tier: [df[df['dow']==i][tier].mean() for i in range(7)] 
                           for tier in tiers}, index=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    sns.heatmap(dow_avg.T, annot=True, fmt='.0f', cmap='YlOrRd', ax=axes[0,2], cbar_kws={'label': 'Demand'})
    axes[0,2].set_title('Demand by Day of Week')
    
    # 4. Coefficient of Variation (Bullwhip)
    cv = [df[tier].std()/df[tier].mean() for tier in tiers]
    axes[1,0].bar(tiers, cv, color=colors)
    axes[1,0].set_title('Coefficient of Variation (CV)')
    axes[1,0].set_ylabel('CV')
    for i, v in enumerate(cv):
        axes[1,0].text(i, v + 0.02, f'{v:.3f}', ha='center')
    
    # 5. Intermittent Demand Tier 3
    zero_pct = (df['tier3'] == 0).mean() * 100
    axes[1,1].pie([100-zero_pct, zero_pct], labels=['With Demand', 'No Demand'], autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
    axes[1,1].set_title(f'Tier 3 - Intermittent Demand')
    
    # 6. Lead times
    lead_means = [df['lead_tier1'].mean(), df['lead_tier2'].mean(), df['lead_tier3'].mean()]
    axes[1,2].bar(['Tier 1', 'Tier 2', 'Tier 3'], lead_means, color='#3498db')
    axes[1,2].set_title('Average Lead Time (days)')
    for i, v in enumerate(lead_means):
        axes[1,2].text(i, v + 0.5, f'{v:.1f}', ha='center')
    
    plt.tight_layout()
    plt.show()
    
    # Quick stats table
    print("\n" + "="*60)
    print("📊 QUICK STATISTICS")
    print("="*60)
    
    # Main table
    stats = pd.DataFrame({
        'Level': tiers,
        'Mean': [df[t].mean() for t in tiers],
        'Std': [df[t].std() for t in tiers],
        'CV': cv,
        'Zero Demand %': [0, 0, 0, (df['tier3']==0).mean()*100]
    }).round(2)
    print(stats.to_string(index=False))
    
    # Bullwhip Effect
    print("\n🔄 BULLWHIP EFFECT:")
    for i in range(1, len(tiers)):
        ratio = cv[i] / cv[i-1]
        print(f"  {tiers[i-1]} → {tiers[i]}: {ratio:.2f}x more variable")
    
    # Simple Correlation
    print("\n🔗 CORRELATION:")
    corr = df[tiers].corr().round(3)
    print(corr)

# ============================================
# RUNNING THE SIMULATOR
# ============================================
if __name__ == "__main__":
    # Generate data for 180 days
    df = generate_automotive_demand(days=180, seed=42)
    
    # Quick analysis
    quick_analysis(df)