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
    win_counts = [0] * len(bots)
    total_steps = [0] * len(bots)
    # Track failed seed numbers for each bot
    failed_seeds = [[] for _ in range(len(bots))]
    
    for seed in range(num_trials): 
        ship = Ship(dim, q)
        ship.setup_game(seed)
        
        for idx, bot in enumerate(bots): 
            status, step_count = run_single_trial(ship, bot)
            
            if status == Ship.SUCCESS: 
                win_counts[idx] += 1 
                total_steps[idx] += step_count
            else:
                # Record the seed if the bot failed
                failed_seeds[idx].append(seed)
    
    win_rates = calculate_win_rates(win_counts, num_trials)
    avg_steps = calculate_avg_steps(total_steps, win_counts)
    
    return win_rates, avg_steps, failed_seeds

def eval_bot_performance(dim, q_vals, num_trials, bots): 
    bot_names = [f"Bot {i + 1}" for i in range(len(bots))]
    results = {name: [] for name in bot_names}
    # Store failed seeds as: { bot_name: { q_val: [seed1, seed2, ...] } }
    failed_seeds_log = {name: {} for name in bot_names}
    
    for q in q_vals: 
        print(f"\n--- Testing Flammability q = {q:0.1f} ---")
        win_rates, _, failed_seeds = eval_win_rates_at_q(dim, q, num_trials, bots)
        
        for idx, name in enumerate(bot_names): 
            rate = win_rates[idx]
            results[name].append(rate)
            failed_seeds_log[name][q] = failed_seeds[idx]
            
            print(f"{name:8s} | q={q:0.1f} | Win Rate: {rate:5.1f}% | Failed Seeds ({len(failed_seeds[idx])}): {failed_seeds[idx]}")
            
    return results, failed_seeds_log

    
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

dim = 10
num_trials = 50
q_vals = [0.5]

bots = [Bot1(), Bot2(), Bot3(), Bot4(risk_weight=5)]

results, failed_seeds_log = eval_bot_performance(dim, q_vals, num_trials, bots)

# Print clean summary of failed seeds for each bot
print("\n=== Failed Seeds Summary (q = 0.5, dim = 10) ===")
for bot_name, q_data in failed_seeds_log.items():
    failed_list = q_data[0.5]
    print(f"{bot_name} Failed Seeds ({len(failed_list)} total): {failed_list}")


def visualize_simulation(dim, q):
    bots = [Bot1(), Bot2(), Bot3(), Bot4(5)] 

    ship = Ship(dim, q)
    ship.setup_game(47)

    for i, bot in enumerate(bots, start=1): 
        ship.reset()
        bot.reset()
        
        print(f"==== Bot {i} ====\n")
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

#visualize_simulation(10, 0.5)