'''
Created on Oct 1, 2011

@author: djweiss
'''

from src.batchlocalengine import BatchLocalEngine
from greedybot import GreedyBot
from src.features import CompositingFeatures, MovingTowardsFeatures, QualifyingFeatures
from valuebot import ValueBot
import random
import copy

def win_rate(bot_wins, bot_games):
    """ Compute the win % and sort accordingly given # of wins and games.
    
    Outputs a sorted list of tuples (i, rate), where i is the original index of the bot
    in bot_wins.
    
    """
    
    win_rate = [(i, float(bot_wins[i]) / float(bot_games[i])) for i in range(0, len(bot_wins))]
    win_rate.sort(key=lambda x: x[1], reverse=True)
    
    return win_rate

def pick_random_feature(features, num_base, num_qual, gen):
    # prefer the untrained weights until there are no untrained weights
    list = []
    base = 0
    qual = 0
    ind = random.randint(0, len(features)-1)
    return ind
    '''for i in range(len(features)):
        if features[i] == 0:
            list.append(i)
            if i < num_base:
                base += 1
            else:
                qual += 1
                
    if len(list) == 0:
        return random.randint(0, len(features)-1)
    else:
        if base == 0 or qual == 0:
            return list[random.randint(0, len(list)-1)]
        ind = random.randint(0, len(list)-1)
        # favor the base features early on then treat them evenly
        if gen < 6:
            type = random.randrange(0, 10)
            if type < max(10*base/len(list), type + 5 - gen):
                ind = random.randint(0, base-1)
            else:
                ind = random.randint(base, len(list)-1)
        return list[ind]'''

BOTS_PER_GEN = 10
SURVIVORS_PER_GEN = 2
TOTAL_WEIGHTS = 7

if __name__ == '__main__':
    engine = BatchLocalEngine()

    # Run quick games: 100 turns only
    engine.PrepareGame(["--run", "-t", "100"])
    
    base_file = "saved_bots/bot_"
    generation = 0
    import sys
    full_feature = False
    new = False
    base_file = "saved_bots/bot_"
    for i in range(len(sys.argv)):
        print sys.argv[i]
        if sys.argv[i] == "-gen":
            generation = int(sys.argv[i+1])
        elif sys.argv[i] == "-base":
            print sys.argv[i+1]
            base_file = sys.argv[i+1]
        elif sys.argv[i] == "-new":
            new = True
            generation = 0
    
    features = CompositingFeatures(MovingTowardsFeatures(full_feature), QualifyingFeatures(full_feature), full_feature)
    
    prev_gen = [QLearnerBot(engine.GetWorld(), load_file=(base_file + str(generation) + "_" + str(i) + ".json" if not new else None)) for i in xrange(SURVORS_PER_GEN)]
    TOTAL_WEIGHTS = len(prev_gen[0].weights)
    num_gens = -1
    gen_size = 10
    weight_range = 1
    # if num_gens is -1 continue infinitely
    while generation < num_gens or num_gens == -1:
        generation+=1
        num_turns = min(max_turns, num_turns + 1)
        # Initialize a random set of bots
        
        team_a = [QLearnerBot(engine.GetWorld(), load_file=None) for i in xrange(gen_size*len(prev_gen))]
        team_b = prev_gen
        change_ind = generation % TOTAL_WEIGHTS#pick_random_feature(prev_gen.weights, features.base_f.num_features(), features.qual_f.num_features(), generation)
        print "Gen: " + str(generation) + " Training: " + str(features.feature_name(change_ind))
        x = 0
        for bot in team_a:
            w = copy.copy(prev_gen.weights)
            w[change_ind] += weight_delta*random.uniform(-1,0) if x < gen_size/2 else weight_delta*random.uniform(0,1)
            x += 1
            
            bot.set_features(features)        
            bot.set_weights(w)
        
        # Play several games against GreedyBot
        engine.PrepareGame(["--run", "-t", str(num_turns)])
        (bot_scores, bot_wins, bot_score_diffs, bot_games) = engine.RunTournament(5, team_a, team_b, [30, 30])
    
        # Sort bots by their score diff
        a_rate = win_rate(bot_wins[0], bot_games[0])
        # Sort bots by their average score differentials
        a_diffs = win_rate(bot_score_diffs[0], bot_games[0])
        
        # update prev_gen only if it is beaten by a current gen bot
        if a_diffs[0][1] > 0:
            prev_gen = team_a[a_diffs[0][0]]
        
        # Print out tournament results according to win rates 
        print "Bot %d: Win diff = %g" % (a_diffs[0][0], a_diffs[0][1])
        print team_a[a_diffs[0][0]].print_out()
        team_a[i].save(base_file + str(generation) + "_bestnew.json")
            
        print prev_gen.print_out()
        prev_gen.save(base_file + "%d_win.json" % generation)
        
        # Print out tournament results according to score differentials
        #for i, diff in a_diffs:
        #    print "Bot %d: Score diff = %g " % (i, diff)
        #    print team_a[i]
        #    team_a[i].save("saved_bots/bot_%d.json" % i)
    
    