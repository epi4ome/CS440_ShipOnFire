import random

class Ship: 
    BLOCKED = "\u2588"
    OPEN = "."
    FIRE = "\u2591"
    BOT = "@"
    BUTTON = "+"
    WASTED = "\u2593"
    
    NBR = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    SUCCESS = 0
    FAILURE = 1
    IN_PROGRESS = 2
    
    def __init__(self, dim, q):
        self.dim = dim
        self.q = q
        self.grid = [[self.BLOCKED for _ in range(dim)] for _ in range(dim)]
        self.fire = set()
        self.bot = None 
        self.button = None 
        self.dead_ends = set()
        self.candidates = set()  
        self.game_status = self.IN_PROGRESS
        
        # --- backup ---
        # Saving the initial grid layout and PRNG state immediately after generation to 
        # reduce runtime. This avoids redundant layout regeneration and guarantees that all 
        # bots encounter the exact same layout and fire spread sequence when reset.
        
        self.initial_grid = None
        self.initial_fire = None
        self.initial_bot = None
        self.rng_state = None
        
    def view(self): 
        for row in self.grid:
            print(" ".join(str(cell) for cell in row))
        print("\n")
        
    def get_state(self, coord) -> str: 
        r, c = coord
        return self.grid[r][c]
    
    def in_bound(self, coord) -> bool:
        r, c = coord
        return 0 <= r < self.dim and 0 <= c < self.dim
        
    # --- neighbor helpers --- 

    def get_neighbors(self, coord) -> list: 
        r, c = coord
        return [(r + dr, c + dc) for dr, dc in self.NBR if self.in_bound((r + dr, c + dc))]
    
    def count_open_neighbors(self, coord) -> int:
        return sum(1 for nbr in self.get_neighbors(coord) if self.get_state(nbr) == self.OPEN)
    
    def get_blocked_neighbors(self, coord) -> list:
        return [nbr for nbr in self.get_neighbors(coord) if self.get_state(nbr) == self.BLOCKED]
        
    # --- candidate helpers (blocked cell w/ 1 open neighbor) ---
    # We know that only block cells that are adjacent to previously openned cells will 
    # satisfy the candidate requirement. So instead of scanning the entire grid at each 
    # iteration, a set is used to keep track of all the neighboring cells of a opened cell
    # that could be a candidate (fast lookup for better runtime).
    
    # check hecks if a cell is a valid candidate; adds to or removes from the candidate set accordingly
    def update_cand(self, coord):
        if self.get_state(coord) == self.BLOCKED and self.count_open_neighbors(coord) == 1:
            self.candidates.add(coord)
        else:
            self.candidates.discard(coord)

    # updates candidate status for the target cell and its neighboring cells after a grid state change
    def sync_grid_cand(self, coord): 
        self.update_cand(coord)
        for nbr in self.get_neighbors(coord): 
            self.update_cand(nbr)
    
    # used for both candidate and dead-end logic; select behavior using "mode"
    def open_cell(self, coord, mode = "c"):
        r, c = coord
        self.grid[r][c] = self.OPEN
        if mode == "c": 
            self.sync_grid_cand(coord) 
        elif mode == "d": 
            self.sync_grid_dead_ends(coord) 
                
    # --- dead end helpers (open cell w/ 1 open neighbor) ---
    # For the second phase of ship layout generation process, a similar approach 
    # to finding the candidates is used to track and reduce dead ends.
    
    # locates all dead-ends using a single dim x dim scan after candidate phase
    def scan_dead_ends(self):
        for r in range(self.dim):
            for c in range(self.dim):
                coord = (r, c)
                if self.get_state(coord) == self.OPEN and self.count_open_neighbors(coord) == 1:
                    self.dead_ends.add(coord)
                    
    def update_dead_end(self, coord):
        if self.get_state(coord) == self.OPEN and self.count_open_neighbors(coord) == 1:
            self.dead_ends.add(coord)
        else:
            self.dead_ends.discard(coord)

    def sync_grid_dead_ends(self, coord):
        self.update_dead_end(coord)
        for nbr in self.get_neighbors(coord):
            self.update_dead_end(nbr)
            
    # --- fire spread helpers ---
    
    def count_fire_neighbors(self, coord) -> int: 
        return sum(1 for nbr in self.get_neighbors(coord) if self.get_state(nbr) == self.FIRE)
    
    def get_unburned_neighbors(self, coord) -> list:
            # fire could also spread to the button cell because it's not blocked
            valid_states = (self.OPEN, self.BOT, self.BUTTON)
            return [nbr for nbr in self.get_neighbors(coord) if self.get_state(nbr) in valid_states]
    
    # collect immidiate unburned neighbors of current fire cells 
    def get_fire_cand(self) -> set: 
        fire_cand = set()
        for f in self.fire: 
            fire_cand.update(self.get_unburned_neighbors(f))
        return fire_cand
    
    # uses the wasted bot icon to indicate fire has spread to the bot
    def set_cell_fire(self, coord): 
        self.fire.add(coord)
        if coord == self.bot:
            self.grid[coord[0]][coord[1]] = self.WASTED
        else: 
            self.grid[coord[0]][coord[1]] = self.FIRE
        
    # --- main functions --- 
    
    # create the ship layout (start from the initial interior cell, find 
    # all closed cells w/ 1 open neighbor, then reduce dead ends by half)
    def generate_layout(self): 
        start = (random.randint(1, self.dim - 2), random.randint(1, self.dim - 2))
        self.open_cell(start) 
        
        while len(self.candidates) > 0: 
            self.open_cell(random.choice(tuple(self.candidates)))
            
        self.scan_dead_ends()
        
        target = len(self.dead_ends) // 4; 
        while len(self.dead_ends) > target: 
            cell = random.choice(tuple(self.dead_ends))
            nbr = random.choice(self.get_blocked_neighbors(cell)) 
            self.open_cell(nbr, mode = "d")
    
    # pick random cells to place the fire origin, bot, and button
    def place_objects(self): 
        open_cells = [(r, c) for r in range(self.dim) for c in range(self.dim) if self.grid[r][c] == self.OPEN]
        fire_start, self.button, self.bot = random.sample(open_cells, 3)
        
        self.set_cell_fire(fire_start)
        self.grid[self.button[0]][self.button[1]] = self.BUTTON
        self.grid[self.bot[0]][self.bot[1]] = self.BOT
    
    # for each cell adjacent to current fire cells, calculate the 
    # flammability (prob) based on the number of burning neighbors (k) 
    def advance_fire(self): 
        new_fires = set()
        
        for f in self.get_fire_cand(): 
            k = self.count_fire_neighbors(f)
            prob = 1 - ((1 - self.q) ** k) 
            
            if random.random() < prob: 
                new_fires.add(f)
        
        for nf in new_fires: 
            self.set_cell_fire(nf)
            
    def advance_turn(self, target):
        # sets the original bot location state back to OPEN 
        self.grid[self.bot[0]][self.bot[1]] = self.OPEN

        # sets state to wasted if bot steps into fire, else move normally
        self.bot = target
        self.grid[target[0]][target[1]] = self.WASTED if target in self.fire else self.BOT
        
        if self.update_game_status() != self.IN_PROGRESS:
            return
        
        self.advance_fire()
        self.update_game_status()
            
    # --- simulation run helpers ---
    
    # orchestrator function to prepare the ship, place objects, and record state at t = 0
    def setup_game(self, seed): 
        # ensure maze generation process is matched with a particular seed 
        random.seed(seed)
        self.generate_layout()
        self.place_objects()
        
        self.initial_grid = [row[:] for row in self.grid]
        self.initial_fire = set(self.fire)
        self.initial_bot = self.bot
        self.initial_rng_state = random.getstate()
    
    # rewind to the t = 0 state
    def reset(self): 
        self.grid = [row[:] for row in self.initial_grid]
        self.fire = set(self.initial_fire)
        self.bot = self.initial_bot
        self.game_status = self.IN_PROGRESS
        
        # restore RNG state so fire spreads identically for every bot
        random.setstate(self.initial_rng_state)
        
    def update_game_status(self) -> int:
        if self.game_status != self.IN_PROGRESS:
            return self.game_status
        
        # game ends when the fire reaches either the bot or the button
        if self.bot in self.fire or self.button in self.fire:
            self.game_status = self.FAILURE
        elif self.bot == self.button:
            self.game_status = self.SUCCESS
            
        return self.game_status