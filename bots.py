from collections import deque
import heapq

# BotBasics class provides the reusable BFS Search and shortest path
# retrieval methods for Bot1, 2, and 3. 

class BotBasics: 
    def __init__(self): 
        pass 
    
    # reset bot attributes for Bot1, default to pass for others 
    def reset(self): 
        pass
    
    def bfs(self, ship, avoid = None) -> dict:    
        start = ship.bot
        goal = ship.button 
        avoid = avoid or set()
        
        cells = deque([start])
        visited = {start}
        prev = {start: None}
        
        while cells: 
            current = cells.popleft()
            if current == goal: 
                return prev

            # use the unburned neighbors list to avoid fire
            for nbr in ship.get_unburned_neighbors(current):
                if nbr not in visited and nbr not in avoid:
                    visited.add(nbr)
                    cells.append(nbr)
                    prev[nbr] = current
        return None
    
    def get_path(self, prev, goal) -> list:
        if prev is None or goal not in prev:
            return None
        path = []
        current = goal 
        
        while prev[current] is not None: 
            path.append(current)
            current = prev[current]
        
        path.reverse()
        return path
    
    def find_path(self, ship, avoid = None) -> list:
        result = self.bfs(ship, avoid)
        return self.get_path(result, ship.button)

# Bot1 stores the initial shortest path founded by BFS, then pops 
# from the left of the list for following moves.

class Bot1(BotBasics): 
    def __init__(self):
        super().__init__()
        self.path_plan = None
        
    def reset(self):
        self.path_plan = None
    
    def get_next_move(self, ship): 
        if self.path_plan is None: 
            self.path_plan = self.find_path(ship) or []
        
        if not self.path_plan:
            ship.game_status = ship.FAILURE
            return ship.bot
        return self.path_plan.pop(0)

# Since Bot2 recalculates the shortest path after each move, 
# the method will simply return the first element from the 
# result list and then disregard the rest.

# Note: if no path can be found that reaches the button (b/c of 
# blocked and/or fire cells), the game will end immediately and 
# the bot will remain stationary (return the bot's current position 
# for the get_next_move() function)

class Bot2(BotBasics): 
    def __init__(self):
        super().__init__()
        
    def get_next_move(self, ship): 
        path = self.find_path(ship)
        
        if not path:
            ship.game_status = ship.FAILURE
            return ship.bot
        return path[0]
    
# Bot3 build upon Bot2: first use the get_fire_cand() function
# to find all the cells adjacent to current fire cells, add them 
# to the avoid list and perform the BFS Search with extra restrictions. 
# If such path doesn't exist, perform the vanilla BFS. Then same as 
# Bot2, we return the first move from the constructed path.

class Bot3(BotBasics): 
    def __init__(self):
        super().__init__()
        
    def get_next_move(self, ship): 
        avoid = ship.get_fire_cand()
        path = self.find_path(ship, avoid)
        
        if not path:
            path = self.find_path(ship)
            
            if not path: 
                ship.game_status = ship.FAILURE
                return ship.bot 
        return path[0]

# Bot4: Logically similar to Bot3 in recalculating its path at each move 
# while considering proximity to burning cells. However, Bot4 evaluates 
# risk along a continuous gradient (preferring paths further from fire 
# across all distances), whereas Bot3 simply avoids immediate fire neighbors 
# 100% while treating all cells with d > 1 as equal risk).
    
class Bot4(BotBasics): 
    def __init__(self, risk_weight = 1.0): 
        super().__init__()
        # high risk_weight forces the bot to prioritize fire avoidance over path length
        self.risk_weight = risk_weight

    # multi-source BFS from all current fire cells to determine 
    # how far the remaining cells are from the fire
    def dist_to_fire(self, ship) -> dict: 
        dist = {cell: 0 for cell in ship.fire}
        queue = deque(ship.fire)
        visited = set(ship.fire)
        
        while queue: 
            current = queue.popleft()
            for nbr in ship.get_unburned_neighbors(current): 
                if nbr not in visited: 
                    dist[nbr] = dist[current] + 1
                    queue.append(nbr)
                    visited.add(nbr)
        return dist
    
    # calculate the Manhattan distance from a cell to the button 
    # (preferred over Euclidean since bot can't move diagonally)
    def manhattan_dist(self, cell, button) -> int: 
        return abs(cell[0] - button[0]) + abs(cell[1] - button[1])
    
    # Modified A* Search: f(cell) = g(cell) + h(cell)
    # f(cell): estimation of total cost from bot to button through cell 
    # g(cell): accumulated cost from bot to cell (a combination of physical distance 
    #          incremented by 1 and a risk penalty inverse to fire distance, i.e., 
    #          more costly closer to fire). Conceptually, g ≈ weighted actual cost.
    # h(cell): estimated cost from cell to button using Manhattan distance (which will 
    #          always be ≤ to the actual distance since the bot can't move diagonally;
    #          hence admissible, which guarantees this A* will find an optimal path)
    def a_star(self, ship, fire_dist) -> dict: 
        start = ship.bot 
        goal = ship.button
        
        prev = {start: None}
        accu_cost = {start: 0.0}
        pq = [(self.manhattan_dist(start, goal), start)]
        
        while pq:
            _, current = heapq.heappop(pq)   
            if current == goal:
                return prev
            
            for nbr in ship.get_unburned_neighbors(current): 
                step_cost = 1.0 + (self.risk_weight / (fire_dist.get(nbr, float('inf'))))
                temp_accu_cost = accu_cost[current] + step_cost
                
                # If it's the first time this neighbor is visited or the new path cost 
                # is less than the previously stored cost, update its weighted actual cost 
                # and push the new estimated total cost (total_dist_esti) into the priority queue.
                if nbr not in accu_cost or temp_accu_cost < accu_cost[nbr]:
                    accu_cost[nbr] = temp_accu_cost
                    prev[nbr] = current
                    total_dist_esti = temp_accu_cost + self.manhattan_dist(nbr, goal)
                    heapq.heappush(pq, (total_dist_esti, nbr)) 
        return None
                
    def get_next_move(self, ship): 
        fire_dist = self.dist_to_fire(ship)
        result = self.a_star(ship, fire_dist)
        
        path = self.get_path(result, ship.button) if result else []
        
        # since Bot4 uses prioritization instead of blocking off extra cells near fire like Bot3, 
        # if A* returns None, it means there's simply no viable path from the bot to the button
        if not path:
            ship.game_status = ship.FAILURE
            return ship.bot
        return path[0]