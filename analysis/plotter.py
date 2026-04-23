import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

def plot_pareto_frontier(results_df):
    """
    Plots the Pareto tradeoff: Sparseness Ratio vs Average Stretch.
    results_df should have columns: ['topology', 't', 'sparseness', 'avg_stretch']
    """
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=results_df, x='sparseness', y='avg_stretch', hue='topology', marker='o')
    
    plt.title('Pareto Frontier: Sparseness vs. Stretch')
    plt.xlabel('Sparseness Ratio (|E_spanner| / |E_original|)')
    plt.ylabel('Average Stretch')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('pareto_frontier.png')
    plt.show()

def plot_stretch_distribution(stretch_data):
    """
    Plots the distribution of stretch factors for a single run.
    stretch_data: list of stretch values for all pairs.
    """
    plt.figure(figsize=(8, 5))
    sns.histplot(stretch_data, kde=True, bins=30)
    plt.axvline(np.mean(stretch_data), color='red', linestyle='--', label='Mean Stretch')
    plt.title('Stretch Factor Distribution')
    plt.xlabel('Stretch')
    plt.ylabel('Frequency')
    plt.legend()
    plt.savefig('stretch_dist.png')
    plt.show()

if __name__ == "__main__":
    # Example usage (to be replaced with actual data from Person A)
    print("Plotting script ready. Waiting for data from Person A...")
    # example_data = pd.DataFrame({
    #     'topology': ['Social', 'Social', 'Road', 'Road'],
    #     't': [3, 5, 3, 5],
    #     'sparseness': [0.1, 0.05, 0.4, 0.2],
    #     'avg_stretch': [1.2, 1.8, 1.1, 1.4]
    # })
    # plot_pareto_frontier(example_data)
