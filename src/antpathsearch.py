'''
Created on Aug 23, 2011

@author: bensapp
'''
# We need a priority queue for A*
import heapq

from antsgame import AIM

class AntPathSearch():
    ''' This is a base class for all specific search classes. '''
    
    def __init__(self,_world):
        self.world = _world
        
    def get_path(self,start,goal):
        ''' 
        Input: start and goal are both 2-tuples containing (x,y) coordinates
        Output: Returns a list of 2-tuples which are a sequence of locations to get from START to GOAL
            - path[0] should equal START
            - path[-1] should equal GOAL
            - path[i+1] should be reachable from path[i] via exactly one step in some cardinal direction, for all i
        '''
        raise NotImplementedError
        
    def get_successors(self,loc):
        ''' 
        Returns a list of valid next reachable locations from the input LOC.
        All derived classes should use this function, otherwise testing your implementation might fail.        
        '''
        
        alldirs = AIM.keys()
        s = []
        for d in alldirs:
            l = self.world.next_position(loc, d)
            if self.world.passable(l):
                s.append(l)
        return s
         

class BreadthFirstSearch(AntPathSearch):
    
    def get_path(self,start,goal):
        ''' 
        YOUR CODE HERE.
        (See specifications in AntPathSearch.get_path above)
        '''
        fringe = [start]
        # We want to keep track of already visited places
        visited = set(fringe)
        # To get a path we need to know how we got to the state
        # Will effectively build the BFS-Tree
        parent = {}
        while len(fringe) > 0:
            # Queue behavior for BFS: Directions are appended and we take the first one
            state = fringe.pop(0)
            if state == goal:
                break
            for pos in self.get_successors(state):
                if pos not in visited:
                    visited.add(pos)
                    fringe.append(pos)
                    # We got to pos from state, so set parent accordingly
                    parent[pos] = state
        path = [goal]
        while state != start:
            # Prepend parent to list.
            path = [parent[state]] + path
            state = parent[state]
        return path
        
        
class DepthFirstSearch(AntPathSearch):
    
    def get_path(self,start,goal):
        ''' 
        YOUR CODE HERE.
        (See specifications in AntPathSearch.get_path above)
        '''
        fringe = [start]
        # We want to keep track of already visited places
        visited = set(fringe)
        # To get a path we need to know how we got to the state
        # Will effectively build the DFS-Tree
        parent = {}
        while len(fringe) > 0:
            # Stack behavior for DFS: Directions are appended and we take the last one
            state = fringe.pop(-1)
            if state == goal:
                break
            for pos in self.get_successors(state):
                if pos not in visited:
                    visited.add(pos)
                    fringe.append(pos)
                    # We got to pos from state, so set parent accordingly
                    parent[pos] = state
        path = [goal]
        while state != start:
            # Prepend parent to list.
            path = [parent[state]] + path
            state = parent[state]
        return path
    
    
class aStarSearch(AntPathSearch):
    
    def heuristic_cost(self,state,goal):
        ''' Make some admissable heuristic for how far we are from the goal '''
        return self.world.manhattan_distance(state, goal)
    
    def get_path(self,start,goal):
        ''' 
        YOUR CODE HERE.
        (See specifications in AntPathSearch.get_path above)
        '''
        fringe = []
        heapq.heappush(fringe, (0,start))
        # We want to remember where we've been
        visited = set()
        # g saves the cost of getting to a certain location from the start
        g = {}
        # Heuristic costs
        h = {}
        # Estimated total costs
        f = {}
        g[start] = 0
        # Is there an A*-Tree? If so, we're probably building that in parent.
        parent = {}
        while len(fringe) > 0:
            state = (heapq.heappop(fringe))[1]
            if state == goal:
                break
            if state not in visited:
                visited.add(state)
                for pos in self.get_successors(state):
                    if pos not in visited:
                        g[pos] = g[state] + 1
                        h[pos] = self.heuristic_cost(state, goal)
                        f[pos] = g[pos] + h[pos]
                        if (g[pos] <= 8):
                            # Try to improve performance: We don't look more than 8 states ahead.
                            heapq.heappush(fringe, (f[pos], pos))
                        parent[pos] = state
        if (state == goal):
            # We found the goal in the 8 states
            path = [goal]
            while state != start:
                # Prepend parent to list.
                path = [parent[state]] + path
                state = parent[state]
            return path
        else:
            return None
