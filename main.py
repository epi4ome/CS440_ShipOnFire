import matplotlib.pyplot as plt
from ship import Ship
from bots import Bot1, Bot2, Bot3, Bot4 

# --- simulation helpers ---

def run_single_trial(ship, bot): 
    ship.reset()
    bot.reset()
    
    step_count = 0
    while ship.game_status == ship.IN_PROGRESS: 
        next_move = bot.get_next_move(ship)
        if ship.game_status != ship.IN_PROGRESS: 
            break
        
        ship.advance_turn(next_move)
        step_count += 1 
        
    return ship.game_status, step_count

def calculate_win_rates(win_counts, num_trials): 
    return [(wins / num_trials) * 100 for wins in win_counts]

def calculate_avg_steps(total_steps, win_counts):
    return [
        (total_steps[i] / win_counts[i]) if win_counts[i] > 0 else 0.0
        for i in range(len(win_counts))
    ]

def eval_win_rates_at_q(dim, q, num_trials, bots): 
    # track performance stats for each bot across trials
    win_counts = [0] * len(bots)
    total_steps = [0] * len(bots)
    
    for seed in range(num_trials): 
        ship = Ship(dim, q)
        # use (seed + c) for some c in N to obtain a fresh set of seeds
        ship.setup_game(seed)
        
        for idx, bot in enumerate(bots): 
            status, step_count = run_single_trial(ship, bot)
            # record metrics if run succeeded 
            if status == Ship.SUCCESS: 
                win_counts[idx] += 1 
                total_steps[idx] += step_count
    
    win_rates = calculate_win_rates(win_counts, num_trials)
    avg_steps = calculate_avg_steps(total_steps, win_counts)
    
    return win_rates, avg_steps

# --- function wrappers for scaled simulation runs --- 

# evaluate Bot 4 across a range of risk weight parameters and flammability 
# values (q) over multiple trials (num_trials).
def eval_risk_weight_param(dim, q_vals, num_trials, weights): 
    results = {q: [] for q in q_vals}
    
    for q in q_vals: 
        print(f"\n--- Testing Flammability q = {q:0.1f} ---")
        bots = [Bot4(w) for w in weights]
        win_rates, _ = eval_win_rates_at_q(dim, q, num_trials, bots)
        results[q] = win_rates
        
        for i in range(len(weights)):
            print(f"q={q:0.1f} | Weight: {weights[i]:4.1f} | Win Rate: {win_rates[i]:5.1f}%")
        
    return results

# scaled simulation trials to compare the overall win rates of all four bots across 
# different q's. To control variables so that the bot algorithm is the only variation 
# in each set of tests, the random number seed feature is utilized. Additionally, to 
# optimize performance, the function evaluates each map layout across all bots in a 
# single iteration rather than generating 100 layouts repeatedly for each bot.
def eval_bot_performance(dim, q_vals, num_trials, bots): 
    bot_names = [f"Bot {i + 1}" for i in range(len(bots))]
    results = {name: [] for name in bot_names}
    
    for q in q_vals: 
        print(f"\n--- Testing Flammability q = {q:0.1f} ---")
        win_rates, _ = eval_win_rates_at_q(dim, q, num_trials, bots)
        
        for idx, name in enumerate(bot_names): 
            rate = win_rates[idx]
            results[name].append(rate)
            print(f"{name:8s} | q={q:0.1f} | Win Rate: {rate:5.1f}%")
            
    return results

# --- plotting helpers --- 
# Reference: https://foundations.projectpythia.org/core/matplotlib/matplotlib-basics/

def plot_weight_comparisons(weights, rate_results):
    plt.figure(figsize=(8, 6))
    
    for q, win_rates in rate_results.items(): 
        plt.plot(weights, win_rates, marker='s', linewidth=2, label=f"q = {q:0.1f}")
    
    plt.title(f"Bot 4: Win Rate vs. Risk Weight Across Different q's", fontsize=14, fontweight='bold')
    plt.xlabel("Risk Weight Parameter", fontsize=12)
    plt.ylabel("Win Rate (%)", fontsize=12)
    
    plt.ylim(20, 100)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title="Flammability (q)", loc="best")
    plt.tight_layout()
    plt.show()
    
def plot_bot_performance(q_vals, bot_results):
    plt.figure(figsize=(11, 7))
    
    for bot_name, win_rates in bot_results.items():
        plt.plot(q_vals, win_rates, marker='o', linewidth=2, label=bot_name)
        
    plt.title("Bot Win Rate vs. Flammability Rate (q)", fontsize=14, fontweight='bold')
    plt.xlabel("Flammability Rate (q)", fontsize=12)
    plt.ylabel("Win Rate (%)", fontsize=12)
    
    plt.ylim(45, 70)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title="Bots", loc="lower left")
    plt.tight_layout()
    plt.show()
    
# --- simulation data visualization ---

dim = 50
num_trials = 100
q_vals = [(1/x) for x in range(1, 10)]
weights = [0.0, 0.5, 1.0, 3.0, 6.0, 12.0, 18.0]

# weight_win_rates = eval_risk_weight_param(dim, q_vals, num_trials, weights)
# plot_weight_comparisons(weights, weight_win_rates)

bots = [Bot1(), Bot2(), Bot3(), Bot4(risk_weight = 5)]
results = eval_bot_performance(dim, q_vals, num_trials, bots)
plot_bot_performance(q_vals, results)

# --- ship layout and fire spread snapshots (optional) --- 
# Simple grid visualization that prints each step to observe the 
# algorithms in action and gain a better understanding of each bot's 
# behavior for a specific q on a constant layout across all bots.

def visualize_simulation(dim, q):
    bots = [Bot3(), Bot4(1)] 

    ship = Ship(dim, q)
    ship.setup_game(1)

    for i, bot in enumerate(bots, start=1): 
        ship.reset()
        bot.reset()
        
        print(f"==== Bot {i + 2} ====\n")
        ship.view()

        while ship.game_status == ship.IN_PROGRESS:
            next_move = bot.get_next_move(ship)
            ship.advance_turn(next_move)
            ship.view()

        if ship.game_status == ship.SUCCESS: 
            print("Bot has reached the button!")
        else:
            print("Bot has failed...")
        print("\n")
