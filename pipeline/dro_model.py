import numpy as np

class DROInventory:

    def __init__(self, demand_record):
        """
        Input - demand_record: list o array of historical demands
            [day1, day2, day3, ..., dayN]

        Purpose:
        Store the observed demand as a basis for generating scenarios

        Transformation:
        - Convert to numpy array for vectorized operations
        """
        self.demand = np.array(demand_record)

        """
        Example:
        demand_record = [100, 120, 80, 150, 90]
        self.demand = array([100, 120, 80, 150, 90])
        """

## 1. Generate adversarial scenarios
    def generate_adversarial_scenarios(self, n_scenarios=100, epsilon=0.2):
        """
          PUZZLE THEORY:
    
        Nature (demand) is adversarial:
        - Wants you to make the worst decision
        - Can modify the distribution within what is "plausible"
    
        UNCERTAINTY SET:
        {distributions: ||P - P₀|| ≤ ε}
       
        WHERE:
        - P₀: empirical distribution (your data)
        - ε: uncertainty radius (how adversarial it can be)
        - ||·||: Wasserstein distance
        """

        """
        Perturb the distribution (Wasserstein ball type) around the empirical data:
        - Add noise to historical demand
        """
        scenarios = []
        for _ in range(n_scenarios):
            noise = np.random.normal(0, epsilon * np.std(self.demand), size=len(self.demand))
            perturbed = self.demand + noise

            # adversarial bias (push towards worst case)
            perturbed += np.random.choice([1, -1]) * epsilon * self.demand.mean()  # No negatives
            scenarios.append(perturbed)
        return scenarios
    
    # 2. Cost function for inventory decisions
    def cost(self, Q, demand, c_o, c_u):
        """
        Cost of holding inventory and cost of stockout
        c_o: cost of overstock
        c_u: cost of understock
        """
        overstock = np.maximum(Q - demand, 0)  # Cost for excess
        stockout = np.maximum(demand - Q, 0)  # Cost for shortage
        return np.mean(c_o * overstock + c_u * stockout)
    
    # 3. DRO Optimization
    def optimize(self, c_o=1, c_u=5, epsilon=0.2):

        scenarios = self.generate_adversarial_scenarios(epsilon=epsilon)

        Q_candidates = np.linspace(
            np.min(self.demand),
            np.max(self.demand) * 1.5,
            100
        )
        
        worst_costs = []
        for Q in Q_candidates:
            scenarios_costs = [
                self.cost(Q, s, c_o, c_u) 
                for s in scenarios
            ]

            worst_cost = np.max(scenarios_costs)
            worst_costs.append(worst_cost)

        best_Q = Q_candidates[np.argmin(worst_costs)]

        return { 
            "Q_opt": int(best_Q),
            "worst_cost": float(np.min(worst_costs))
        }