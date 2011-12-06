'''
Created on Oct 1, 2011

@author: djweiss
'''

from src.batchlocalengine import BatchLocalEngine
from greedybot import GreedyBot
from valuebot import ValueBot
from qlearner import QLearnBot
import random
import copy
import subprocess as sub
import sys
import os

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
    

def run_qlearner(base_dir, ind, learner):
    dir = base_dir + "/" + str(ind) + "/"
    
    num_games = 10
    command = "python qlearner.py"
    
    if os.path.exists(base_dir) is False:
        os.mkdir(base_dir)
    if os.path.exists(dir) is False:
        os.mkdir(dir)
        
    learner.save_params(dir+'/learner.json')
        
    for i in range(num_games):
    
        # Try to run one game and capture standard out/err. 
        current_command = command + " " + str(i) + " " + dir
        print 'Executing ' + current_command + " ..."
        process = sub.Popen(current_command, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
        output, errors = process.communicate()
        print output
        print errors
    
    return dir + "qbot.json"

GAMES_PER_PAIR = 3
BOTS_PER_GEN = 5
SURVIVORS_PER_GEN = 1
TOTAL_WEIGHTS = 6
RUN_MODE = 'batch'

if __name__ == '__main__':
    engine = BatchLocalEngine()

    # Run quick games: 100 turns only
    engine.PrepareGame(["--run", "-t", "1500"])
    
    base_file = "saved_bots/"
    generation = 0
    import sys
    full_feature = False
    new = False
    base_file = "saved_bots/"
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
    
    base_dir = "./learner"
    
    prev_gen = [QLearnBot(engine.GetWorld(), load_file=(base_file + str(generation) + "_" + str(i) + ".json" if not new else None)) for i in xrange(SURVIVORS_PER_GEN)]
    prev_gen_p = [ValueBot(engine.GetWorld(), run_qlearner(base_dir, i, prev_gen[i])) for i in xrange(len(prev_gen))]
    
    TOTAL_WEIGHTS = len(prev_gen[0].get_params())
    num_gens = -1
    gen_size = BOTS_PER_GEN/SURVIVORS_PER_GEN
    weight_range = 5.
    num_turns = 30
    # if num_gens is -1 continue infinitely
    while generation < num_gens or num_gens == -1:
        if generation % TOTAL_WEIGHTS == 0:
            weight_range /= 5.;
        generation+=1
        
        num_turns = min(500, num_turns + 1)
        # Initialize a random set of bots
        
        team_a = [QLearnBot(engine.GetWorld(), load_file=None) for i in xrange(gen_size*len(prev_gen))]
        team_b = prev_gen
        
        change_ind = (generation-1) % TOTAL_WEIGHTS#pick_random_feature(prev_gen.weights, features.base_f.num_features(), features.qual_f.num_features(), generation)
        #print "Gen: " + str(generation) + " Training: " + str(features.feature_name(change_ind))
        x = 0
        weight_delta = weight_range/gen_size;
        for j in xrange(gen_size):
            for i in xrange(len(team_b)):
                bot = team_a[j]
                pg = team_b[i]
                w = copy.copy(pg.get_params())
                w[change_ind] += weight_delta*(i - gen_size/2)
                bot.set_params(w)
        
        team_a_p = [ValueBot(engine.GetWorld(), run_qlearner(base_dir, i+len(prev_gen), team_a[i])) for i in xrange(len(team_a))]     
        team_b_p = prev_gen_p       
        
        # Play several games against GreedyBot
        engine.PrepareGame(["--run", "-t", str(num_turns)])
        (bot_scores, bot_wins, bot_score_diffs, bot_games) = engine.RunTournament(GAMES_PER_PAIR, team_a_p, team_b_p, [30, 30])
    
        # Sort bots by their score diff
        a_rate = win_rate(bot_wins[0], bot_games[0])
        # Sort bots by their average score differentials
        a_diffs = win_rate(bot_score_diffs[0], bot_games[0])
        
        prev_gen = []
        
        prev_gen_b = []
        # update prev_gen only if it is beaten by a current gen bot
        for i in xrange(SURVIVORS_PER_GEN):
            if a_diffs[i][1] > 0:
                prev_gen.append(team_a[a_diffs[i][0]])
                prev_gen_b.append(team_a_p[a_diffs[i][0]])
        remain = SURVIVORS_PER_GEN
        for i in xrange(remain):
            prev_gen.append(team_b[i])
            prev_gen_b.append(team_b_p[i])
        
        if a_diffs[0][1] > 0:
            team_a_p[0].save(base_file + "bot_%d.json" % generation)
            team_a_p[0].save(base_file + "bot.json")
        else:
            team_b_p[0].save(base_file + "bot_%d.json" % generation)
        
        # Print out tournament results according to win rates 
        for i in xrange(len(prev_gen)):
            prev_gen[i].save_params(base_file + "learner_" + str(generation) + "_" + str(i) + ".json")
            
        print "Bot %d: Win diff = %g" % (a_diffs[0][0], a_diffs[0][1])
        #print team_a[a_diffs[0][0]].print_out()
            
        #print prev_gen.print_out()
        prev_gen[0].save_params(base_file + "learner_%d_win.json" % generation)
        
        # Print out tournament results according to score differentials
        #for i, diff in a_diffs:
        #    print "Bot %d: Score diff = %g " % (i, diff)
        #    print team_a[i]
        #    team_a[i].save("saved_bots/bot_%d.json" % i)
    
    