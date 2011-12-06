'''
Created on Aug 23, 2011

@author: bensapp
'''
from worldstate import AIM
from heapq import *
import copy

class AntPathSearch():
    ''' This is a base class for all specific search classes. '''
    
    def __init__(self,_world, use_cache = True):
        self.world = _world
        if use_cache:
            self.cache = {}
        else:
            self.cache = None
        
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
        q = [[start]]
        visited = set()
        while len(q) > 0:
            path = q[0]
            q.remove(path)
            loc = path[-1]
            if loc == goal:
                return path
            if loc in visited:
                continue
            visited.add(loc)
            for p in self.get_successors(loc):
                if p not in visited:
                    new_path = copy.deepcopy(path)
                    new_path.append(p)
                    q.append(new_path)
                    
        return [goal]*100
        
        
class DepthFirstSearch(AntPathSearch):
    
    def get_path(self,start,goal):
        q = [[start]]
        visited = set()
        while len(q) > 0:
            path = q[0]
            q.remove(path)
            loc = path[-1]
            if loc == goal:
                return path
            if loc in visited:
                continue
            visited.add(loc)
            for p in self.get_successors(loc):
                if p not in visited:
                    new_path = copy.deepcopy(path)
                    new_path.append(p)
                    q.insert(0,new_path)
                    
        return [goal]*100
    
    
class aStarSearch(AntPathSearch):
    
    def heuristic_cost(self,state,goal):
        return self.world.manhattan_distance(state,goal)
    
    def cache_result(self, path):
        if self.cache is None:
            return
        for i in xrange(len(path)):
            for j in xrange(len(path)-1, len(path)):
                if (path[i], path[j]) not in self.cache and (path[j], path[i]) not in self.cache:
                    self.cache[(path[i], path[j])] = j-i

    def lookup(self, start, goal):
        if self.cache is None:
            return None
	    if (start, goal) in self.cache:
	        return self.cache[(start, goal)]
	    if (goal, start) in self.cache:
                return self.cache[(goal, start)]
	    return None
			
    def get_path(self,start,goal, max_length=100):
        if start is None or goal is None:
            return None
        p  = self.lookup(start, goal)
        if p:
            return p
        if self.world.manhattan_distance(start, goal) > max_length:
            return None
        q = []
        f = self.heuristic_cost(start, goal)
        heappush(q, (f, ([start], 0)) )
        visited = set()
        while len(q) > 0:
            (fit, (path, steps)) = heappop(q)
            loc = path[-1]
            self.cache_result(path)
            if len(path) > max_length+1:
                continue
            if loc == goal:
                # cache shortest path results to speed up latter run time
                self.cache_result(path)
                return len(path)-1
            if loc in visited:
                continue
            visited.add(loc)
            for p in self.get_successors(loc):
                if p not in visited:
                    new_path = copy.deepcopy(path)
                    new_path.append(p)
                    fit = steps + self.heuristic_cost(loc, goal) + 1
                    if fit > max_length+1:
                        continue
                    heappush(q, (fit, (new_path, steps+1)))
                    
        return None
