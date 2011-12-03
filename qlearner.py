'''
Created on Oct 19, 2011

@author: bensapp
'''
from src.worldstate import AIM, AntStatus, RewardEvents
from src.mapgen import SymmetricMap
from src.features import BasicFeatures, CompositingFeatures, QualifyingFeatures
from src.state import GlobalState
from valuebot import ValueBot
import json
import os.path
import random

class QLearnBot(ValueBot):
    
    def __init__(self,world, load_file="save_bots/qbot.json", param_file="saved_qlearners/qLearn.json"):
        ValueBot.__init__(self,world, load_file)
        self.nturns = 0
        self.percentSeen = 0
        self.lastPercentSeen = 0
        # Try to load saved configuration from file
        if param_file is not None and os.path.exists(param_file):
            fp = file(param_file, "r")
            data = json.load(fp)
            self.set_params(data['weights'])
            fp.close()
        else:
            weights = [.5,.5,.5,.5,.5,.5,.5]
            self.set_params(weights)
        
    def set_params(self, weights):
        self.seenCoef = weights[0]
        self.deathDealtCoef = weights[1]
        self.foodEatenCoef = weights[2]
        self.wasKilledCoef = weights[3]
        self.doNothingPunishment = weights[4]
        self.alpha = weights[5]
        self.discount = weights[6]
    
    def get_params(self):
        weights = [self.seenCoef, self.deathDealtCoef, self.foodEatenCoef, self.wasKilledCoef, self.doNothingPunishment, self.alpha, self.discount]
        return weights
        
    def save_params(self, filename):
        """Save Weights to File"""
        fp = file(filename, "w")
        data = {'weights': self.get_params()}
        json.dump(data, fp)
        fp.close()
    
    def get_reward(self,reward_state):
        """ 
        Hand-tuned rewards for a state.  The RewardState reward_state tracks the
        following events for which you can tailor rewards:
            reward_state.food_eaten: Fraction of a food item this ant ate (between 0 and 1)
            reward_state.was_killed: boolean flag whether the ant died this turn
            reward_state.death_dealt: Fraction of responsibility this ant contributed to killing other ants (e.g., if 2 ants killed an enemy an, each would have death_dealt=1/2
        """
        reward = self.seenCoef*(self.percentSeen-self.lastPercentSeen)
        if reward_state.death_dealt > 0:
            reward += self.deathDealtCoef/reward_state.death_dealt
        reward += self.foodEatenCoef*reward_state.food_eaten
        reward += self.wasKilledCoef*reward_state.was_killed
        if reward == 0:
            reward = doNothingPunishment
        return reward
    
    def avoid_collisions(self):
        """ 
        Simple logic to avoid collisions.  No need to touch this function.
        """
        next_locations = {}
        for ant in self.world.ants:
            if ant.status == AntStatus.ALIVE:
                # Basic collision detection: don't land on the same square as another friendly ant.
                nextpos = self.world.next_position(ant.location, ant.direction) 
                if nextpos in next_locations.keys():  
                    ant.direction = None
                else:
                    next_locations[nextpos] = ant.ant_id
                        
    def do_turn(self):
        """
        do_turn just does some bookkeeping and calls the update+explore/exploit 
        loop for each living or just killed ant.  You shouldn't need to modify 
        this function.
        """
        self.nturns += 1
        self.lastPercentSeen = self.percentSeen
        self.percentSeen = len([loc for loc in self.world.map if loc > -5])/self.world.width*self.world.height
        
        # Grid lookup resolution: size 10 squares
        if self.state == None:
            self.state = GlobalState(self.world, resolution=10)
        else:
            self.state.update()
            
        # explore or exploit and update values for every ant that's alive or was just killed
        for ant in self.world.ants:
            if ant.status == AntStatus.ALIVE or ant.previous_reward_events.was_killed:
                ant.direction = self.explore_and_exploit(ant)
                
        self.avoid_collisions()
        
        # record features for action taken so we can update when we arrive in the next state next turn
        for ant in self.world.ants:    
            ant.prev_features = self.features.extract(self.world, self.state, ant.location, ant.direction,self.percentSeen)
            ant.prev_value = self.value(self.state,ant.location,ant.direction)

        print self.world.L.info(str(self))

    def update_weights(self,alpha,discount,reward,maxval,prevval,features):
        """
            Perform an update of the weights here according to the Q-learning
            weight update rule described in the homework handout.
            
            alpha = alpha
            discount = gamma
            reward = R(s)
            maxval = maxQw(s',a')
            prevval = Qw(s,a)

            YOUR CODE HERE
        """
        for i in range(len(self.weights)):
            self.weights[i] += alpha*(reward+discount*maxval-prevval)*features[i]
        

    def explore_and_exploit(self,ant):
        '''
        Update weights and decide whether to explore or exploit here.  Where all the magic happens.
        YOUR CODE HERE
        '''

        actions = self.world.get_passable_directions(ant.location, AIM.keys())
        random.shuffle(actions)
        if len(actions)==0:
            return 'halt'
        
        # if we have a newborn baby ant, init its rewards and quality fcns
        if 'prev_value' not in ant.__dict__:
            ant.prev_value = 0
            ant.previous_reward_events = RewardEvents()
            ant.prev_features = self.features.extract(self.world, self.state, ant.location, actions[0], self.percentSeen)
            return actions[0]
        
        # step 1, update Q(s,a) based on going from last state, taking
        # the action issued last round, and getting to current state
        R = self.get_reward(ant.previous_reward_events)
        
        # should be max_a' Q(s',a'), where right now we are in state s' and the
        # previous state was s.  You can use
        # self.value(self.state,ant.location,action) here
        max_next_value = float('-inf')
        # should be argmax_a' Q(s',a')
        max_next_action = 'halt'
        for action in actions:
            newVal = self.value(self.state,ant.location,action)
            if newVal > max_next_value:
                max_next_value = newVal
                max_next_action = action
        
        # now that we have all the quantities needed, adjust the weights
        self.update_weights(self.alpha,self.discount,R,max_next_value,ant.prev_value,ant.prev_features)

                
        # step 2, explore or exploit? you should replace decide_to_explore with
        # something sensible based on the number of games played so far, self.ngames
        decide_to_explore = False
        if random.random() < 1./(self.ngames+1):
            decide_to_explore = True
        if decide_to_explore:
            return actions[0]
        else:      
            return max_next_action
        

# Set BOT variable to be compatible with rungame.py                            
BOT = ValueBot

if __name__ == '__main__':
    from src.localengine import LocalEngine
    from greedybot import GreedyBot
    import sys
    import time

    start_time = time.time()
    
    if len(sys.argv) < 3:
        print 'Missing argument ---'
        print 'Usage: python qlearner.py <game number> <qLearner_trainer parameter file>'
        sys.exit()
    game_number = int(sys.argv[1])
    dir = str(sys.argv[2])
    #parameters = str(sys.argv[3])
    
#    PLAY_TYPE = 'step'
    PLAY_TYPE = 'batch'
#    PLAY_TYPE = 'play'

    # Run the local debugger
    engine = LocalEngine(run_mode=PLAY_TYPE)

    if game_number > 0:
        qbot = QLearnBot(engine.GetWorld(), load_file=dir + '/qbot.json', param_file=dir+'/leaner.json')
    else:
        # init qbot with weights 0
        qbot = QLearnBot(engine.GetWorld(), load_file=None, param_file=None)
        qbot.set_features(CompositingFeatures(BasicFeatures(), BasicFeatures()))
        qbot.set_weights([0 for j in range (0, qbot.features.num_features())])
        
    # Generate and play on random 30 x 30 map
    random_map = SymmetricMap(min_dim=50, max_dim=50)
    random_map.random_walk_map()
    fp = file("src/maps/2player/my_random.map", "w")
    fp.write(random_map.map_text())
    fp.close()
        
    # set up a game between current qbot and GreedyBot
    engine.AddBot(qbot)        
    engine.AddBot(GreedyBot(engine.GetWorld()))
    qbot.ngames = game_number + 1
    engine.Run([sys.argv[0]] + ["--run", "-m", "src/maps/2player/my_random.map"], run_mode=PLAY_TYPE)
    qbot.save(dir + '/qbot.json')
    # this is an easy way to look at the weights
    qbot.save_readable(dir + '/qbot-game-%d.txt' % game_number)
        
    end_time = time.time()
    print 'training done, delta time = ', end_time-start_time