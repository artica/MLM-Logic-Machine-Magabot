import random

import mlm_scroll_mem_class
# ...this module contains the ScrollingMemory class
#   Many MLM memories are scrolling memories (inserts made at the top, drops made at the bottom)
#   class attributes: self.memory_list and self.max_size
#   Note: if max_size <= 0, then self.max_size = 9999
# A simpler name for the module...
memclass = mlm_scroll_mem_class

from mlm_util import *
# ...imports some useful functions for the MLM


##################################    
###  THE CINEMATIC BRAIN CLASS ###
    
# The subjective inner aspects of the cinematic brain:
# 1. Defines the brain memories and their sizes
# 2. Defines the ways past memories are looked at to generate continuations
# 3. Defines the ways continuations are filtered according to some wanted/feared evaluation
# 4. Defines the number and type of inner action requests

class BrainCinematic(object):

    def __init__(self):

        self.bm_size = 4
        self.bm = []
        self.stm_size = 12
        self.stm = []
        self.rec_mode = [0,0]
        self.slbuffer = []
        self.ltmdd_size = 100
        self.ltmdd = []

        # context heuristics ID dominance list
        # ...CHECK generateQ_past BELOW!!
        self.heur_id_dom = ['sm1','sm2','sm3','sm4','sm5','m2','m4']
        # interrogation heuristics ID dominance list
        # ...CHECK continuation_filter BELOW!!
        self.filter_id_dom = ['ls','gr1','xgr1','gr2','xgr2'] # drop 'srch' (much worse in robots)
        
        self.wm = [[],[],[]]    # Holds Working Memory Q, B, K lists
        self.wm_aux = [[], 0, 0] # Holds the used LTMDD scene and the used Heuristic and filter ID
        self.action_request = 0

        # attribute for the systematic exploration of the action space:
        self.list_of_known_actions = []
        

    # a function that allows some reconfigurations of __init__(self)
    def set_brain(self,
                  bm_size,
                  stm_size,
                  ltmdd_size):
        
        self.bm_size = bm_size
        self.stm_size = stm_size
        self.ltmdd_size = ltmdd_size


########### KNOWN ACTION METHODS ############################################

    def updates_known_actions_list(self, action_request):
        if not (action_request in self.list_of_known_actions):
            self.list_of_known_actions.append(action_request)
        else:
            pass

        

########### INTERNAL DATA FLOW METHODS ######################################


    # record_in_bm(sensor_values) function:
    # updates scrolling binding memory BM with size-limit BM_SIZE
    def record_in_bm(self, sensor_values):
        scrmem_bm = memclass.ScrollingMemory(self.bm_size)
        scrmem_bm.memory_list = self.bm[:]
        # records mem_ltmdd.memory_list item (item)
        scrmem_bm.record(sensor_values)
        self.bm = scrmem_bm.memory_list[:]


    # updates scrolling short-term memory STM with size limit STM_SIZE
    def record_in_stm(self):

        # **** FUTURE WORK: insert here orienting filters BM ==> STM 

        scrmem_stm = memclass.ScrollingMemory(self.stm_size)
        scrmem_stm.memory_list = self.stm[:]
        # records mem_ltmdd.memory_list item (item)
        scrmem_stm.record(self.bm[0])
        self.stm = scrmem_stm.memory_list[:]


    ## The main STM to LTMDD buffer function

    def stm_to_ltmdd_and_ltmbuff_transfer(self, ltmdd_size):
     
        ratio_ltmdd = len(self.ltmdd) * 0.8 / ltmdd_size
        
        self.record_rec_mode(self.define_ltmdd_rec_mode(ratio_ltmdd))
        # ... this updates record mode bounded list. self.rec_mode: [RM1,RM0]
        
        self.record_sl_buff()
        # ... records the last two STM frames [s,m]


    ## Function that generates the new record_mode value; 1 is ON, 0 is OFF
    # This is only done at the s step, therefore only sm pairs are recorded
    
    def define_ltmdd_rec_mode(self,ratio_ltmdd):
        # start recording when prediction is wrong and record buffer still small
        # and on-target total score is small enough
        if (self.rec_mode[0] == 0
            and
            (not (self.wm[1] == self.wm[2]))
            and
            len(self.slbuffer) < self.stm_size + 8
            ):
            return 1
            ## damps as it reaches size limit
            #return int((2-ratio_ltmdd) * random.random())
        
        # if already recording, keep doing so for at least four sm pairs 
        elif (self.rec_mode[0] == 1
              and
              len(self.slbuffer) < self.stm_size + 8
              ):
            return 1
        
        # do not record when prediction is right and ltmdd not too small
        # and on-target sc1.score (= happiness emotion) is good
        elif (self.wm[1] == self.wm[2]
              and
              (len(self.ltmdd) > 200)
              and
              score >= 90):
            return 0
        
        # otherwise, 1/3 probability of changing state
        else:
            rec_mode = (self.rec_mode[0] - int(1.5 * random.random())) % 2
            return rec_mode
    

    ## Function that updates the record_mode sequence list [RM1,RM0]
    # this list is needed to identify the [0,0][0,1](STOP)[1,1][1,0](START) situations

    def record_rec_mode(self, RM):

        scrmem_rec_mode = memclass.ScrollingMemory(2) 
        scrmem_rec_mode.memory_list = self.rec_mode[:]
        # records mem_ltmdd.memory_list item (item)
        scrmem_rec_mode.record(RM)
        self.rec_mode = scrmem_rec_mode.memory_list[:]


    ## Function that updates short-term to long-term memory buffer SLBuffer

    def record_sl_buff(self):
        # case START: just copies STM into slbuffer
        if self.rec_mode == [1,0]:      
            self.slbuffer = self.stm[:]  # A copy of STM is assigned to slbuffer  
            ## !! IMPORTANT NOTE: if there are sublists, they still share the same ID !!
            ## This means that changing the copy sublists will also change the original
            ## sublists. For this reason we use numbers instead of sublists.
            ## self.slbuffer = [i for i in self.stm] has the same problem

        # case CONTINUE: add the two newest states: [s,m]
        #     from STM into slbuffer
        if self.rec_mode == [1,1]:                  

            scrmem_slbuffer = memclass.ScrollingMemory(-1) # no memory size limit
            scrmem_slbuffer.memory_list = self.slbuffer[:] # initialize
            # records mem_ltmdd.memory_list item (item)
            scrmem_slbuffer.record(self.stm[1])           # first the prior m
            scrmem_slbuffer.record(self.stm[0])           # then the latter s
            self.slbuffer = scrmem_slbuffer.memory_list[:]
            
        #  case STOP: inserts slbuffer in LTMDD, and empties slbuffer
        if self.rec_mode == [0,1]:              

            scrmem_ltmdd = memclass.ScrollingMemory(self.ltmdd_size) 
            scrmem_ltmdd.memory_list = self.ltmdd[:]
            # records mem_ltmdd.memory_list item (item)
            scrmem_ltmdd.record(self.slbuffer)
            self.ltmdd = scrmem_ltmdd.memory_list[:]
            
            ### print self.slbuffer

            self.slbuffer = []



######### UPDATING DOMINANCE METHODS ##########################

    # Updates dominance of LTMDD
    # and self.heur_id_dom = ['sm1','sm2','sm3','sm4','sm5','m2','m4']

    def update_dominance_ltmdd_and_heur(self, ltmdd_scene_used, heur_id_used, how_fast):

        mem_ltmdd = memclass.ScrollingMemory(self.ltmdd_size)  # the limit size
        mem_ltmdd.memory_list = self.ltmdd[:]
        # moves the mem_ltmdd.memory_list item (item, displacement, discard flag)
        # displacements are made in multiples of 10
        # after LTMDD reaching its limit size, items can be pushed to oblivion
        mem_ltmdd.move_item(ltmdd_scene_used, -10*how_fast, 1)
        self.ltmdd = mem_ltmdd.memory_list[:]

        mem_heur = memclass.ScrollingMemory(len(self.heur_id_dom))
        mem_heur.memory_list = self.heur_id_dom[:]
        # moves the mem_heur.memory_list item (item, displacement, discard flag)
        # id used goes all the way up or down in the list
        # no element is discarded
        mem_heur.move_item(heur_id_used, -1*how_fast*len(mem_heur.memory_list), 0)
        self.heur_id_dom = mem_heur.memory_list[:]


    # Updates dominance of self.filter_id_dom = ['ls','gr1','gr2','xgr2','srch']

    def update_dominance_filter(self, filter_id_used, how_fast):
        mem_filter = memclass.ScrollingMemory(len(self.filter_id_dom))
        mem_filter.memory_list = self.filter_id_dom[:]
        # moves the mem_filter.memory_list item (item, displacement, discard flag)
        # id used goes all the way up or down in the list
        # no element is discarded
        mem_filter.move_item(filter_id_used, -1*how_fast*len(mem_filter.memory_list), 0)
        self.filter_id_dom = mem_filter.memory_list[:]


############# PAST CONTEXT QUESTION GENERATION ################################### 

## This must match self.heur_id_dom = ['sm1','sm2','sm3','sm4','sm5','m2','m4']
            
    def generateQ_past(self, heur_ID):
        
        # heuristic ID = 'sm1': Q context is a list built from the most recent sm pair
        if heur_ID == 'sm1' and len(self.stm) > 1:
            complex_context = build_context(self.stm[0:2]) # function from mlm_util
            return complex_context
        # heuristic ID = 'sm2': Q context is a list built from the 2 most recent sm pairs
        elif heur_ID == 'sm2' and len(self.stm) > 3:
            complex_context = build_context(self.stm[0:4])
            return complex_context
        # heuristic ID = 'sm3': Q context is a list built from the 3 most recent sm pairs
        elif heur_ID == 'sm3' and len(self.stm) > 5:
            complex_context = build_context(self.stm[0:6])
            return complex_context
        # heuristic ID = 'sm4': Q context is a list built from the 4 most recent sm pairs
        elif heur_ID == 'sm4' and len(self.stm) > 7:
            complex_context = build_context(self.stm[0:8])
            return complex_context
        # heuristic ID = 'sm5': Q context is a list built from the 5 most recent sm pairs
        elif heur_ID == 'sm5' and len(self.stm) > 9:
            complex_context = build_context(self.stm[0:10])
            return complex_context
        # heuristic ID = 'm2': Q context is the last two motor actions [js,m]
        elif heur_ID == 'm2' and len(self.stm) > 3:
            i_s = complex(self.stm[0],1)    # sensory interrogation: s+1j
            c_m = complex(self.stm[1],0)    #         motor context: m+0j
            i_s2 = complex(self.stm[2],1)
            c_m2 = complex(self.stm[3],0)
            complex_context = [i_s, c_m, i_s2, c_m2]
            return complex_context
        # heuristic ID = 'm4': Q context is the last four motor actions [js,m]
        elif heur_ID == 'm4' and len(self.stm) > 7:
            i_s = complex(self.stm[0],1)    # sensory interrogation: s+1j
            c_m = complex(self.stm[1],0)    #         motor context: m+0j
            i_s2 = complex(self.stm[2],1)
            c_m2 = complex(self.stm[3],0)
            i_s3 = complex(self.stm[4],1)
            c_m3 = complex(self.stm[5],0)
            i_s4 = complex(self.stm[6],1)
            c_m4 = complex(self.stm[7],0)
            complex_context = [i_s, c_m, i_s2, c_m2, i_s3, c_m3, i_s4, c_m4]
            return complex_context
        # more heuristics here
        else:
            return []


######### FINDING CONTINUATION METHODS ##############################

    def find_a_ltmdd_continuation(self, ltmdd_index, question_past_context, horizon):
        # 3.1. Finds a continuation for the 'question_past_context' pattern
        #       Use: continuation(pattern, horizon)
        #           pattern made of complex numbers
        #               defining context (real part) and interrogation (imaginary part)

        # creates a LTMDD scene-scrolling memory object
        mem_scene = memclass.ScrollingMemory(-1)
        # puts in the scrolling memory object a single scene from LTMDD
        mem_scene.memory_list = self.ltmdd[ltmdd_index] 
        
        # *** mem_scene.continuation(question_past_context,horizon)
        # *** RETURNS: [[A][B][C]]
        # ****** A is the [s,m,s,m,...,s,m] continuation for B; len(A) is horizon
        # ****** B is the pattern used
        # ****** C is the scene in LTM that provided a match for B
        
        matching_result = mem_scene.continuation(question_past_context,horizon)
        
        return matching_result 


############## CONTINUATION FILTERING METHODS ###################################### 

    ### **** CHECK THE CORRESPONDING LISTS ABOVE !!!! **** mismatch may bypass
    ###         self.filter_id_dom = ['ls','gr1','xgr1','gr2','xgr2','srch'] ('srch' dropped)

    def continuation_filter(self, continuation,
                            wanted_world_states, feared_world_states,
                            wanted_world_states2, feared_world_states2,
                            filter_ID,
                            horizon):
        '''If return is [], it forces the matching process to keep searching'''

        # 1. This filters according to a global score of part of the continuation
        if filter_ID == 'ls' and len(continuation) == horizon:
            # inside the not() we put what we require for the continuation
            # we want a positive local score of the filtered continuation
            local_sc = self.local_score(continuation,
                                   wanted_world_states,
                                   feared_world_states,
                                   wanted_world_states2,
                                   feared_world_states2) 
            if not (local_sc > 0):
                # the returned empty list keeps the 'while' loop running
                return []
            else:
                return continuation # because it satisfies this filter
            
        # 2. This filters according to a greedy evaluation of the immediate continuation
        elif filter_ID == 'gr1' and len(continuation) == horizon:
            # inside the not() we put what we require for the continuation
            # [s0,m0]: s in wanted (#, resulting from m0=0)
            if not(continuation[horizon-2] in wanted_world_states
                   #and
                   #continuation[7] == 0
                   ):
                # the returned empty list keeps the 'while' loop running
                return []
            else:
                return continuation   # because it satisfies this filter

        # 2a. This filters according to a greedy evaluation of the immediate continuation
        elif filter_ID == 'xgr1' and len(continuation) == horizon:
            # inside the not() we put what we require for the continuation
            # [s0,m0]: s in wanted (#, resulting from m0=0)
            if not(continuation[horizon-2] in wanted_world_states2
                   #and
                   #continuation[7] == 0
                   ):
                # the returned empty list keeps the 'while' loop running
                return []
            else:
                return continuation   # because it satisfies this filter

        # 3. This filters according to two steps ahead evaluation
        # but avoids immediate pain
        elif filter_ID == 'gr2' and len(continuation) == horizon:
            # inside the not() we put what we require for the continuation
            # [s1,m1,s0,m0]: s1 in wanted states,
            # (dropped: resulting from m1=0);
            # s0 not feared or xfeared
            if not(continuation[horizon-4] in wanted_world_states
                   ##and
                   ##continuation[horizon-3] == 0  # idle action
                   and
                   not(continuation[horizon-2] in feared_world_states
                       or
                       continuation[horizon-2] in feared_world_states2)
                   ):
                # the returned empty list keeps the 'while' loop running
                return []
            else:
                return continuation   # because it satisfies this filter

        # 4. This ignores immediate pain, and just looks two steps ahead
        elif filter_ID == 'xgr2' and len(continuation) == horizon:
            # inside the not() we put what we require for the continuation
            # [s1,m1,s0,m0]: s1 in x-wanted (greedy distance 2)
            # and s0 not xfeared
            if not(continuation[horizon-4] in wanted_world_states2
                   ##and
                   ##continuation[5] == 0   # idle action
                   and
                   not(continuation[6] in feared_world_states2)
                   ):
                # the returned empty list keeps the 'while' loop running
                return []
            else:
                return continuation   # because it satisfies this filter

        # 5. For now, srch simply tries randomly an already known action
        #    that is different from the action currently found in the continuation
        #    Very poor results in simulated robot world
        # WORK TO DO: check ALL past continuations and find an untried action
        elif filter_ID == 'srch' and len(continuation) == horizon:
            choice = []
            past_action_choice = continuation[1]
            reduced_known_action_list = []
            # builds a list with known actions different from the continuation action
            for action in self.list_of_known_actions:
                if not (action == past_action_choice):
                    reduced_known_action_list.append(action)
            # if reduced action list has 1 or more actions, choose randomly         
            if len(reduced_known_action_list) > 0:
                choice = random.choice(reduced_known_action_list)
                continuation[1] = choice  # changes the next motor action in continuation
                return continuation
            else:
                return[]

        # 6. Just in case... for a filter ID outside the above defined filters,
        #    ignore filtering
        else:
            return continuation

    ## The Local Score Method
    ## calculates an overall score for the considered continuation
    def local_score(self, continuation, wanted_world_states, feared_world_states,
                    wanted_world_states2, feared_world_states2):
        local_score = 0
        for i in range(len(continuation)):
            # score for states (found in the even positions of the continuation)
            if i % 2 == 0 and continuation[i] in wanted_world_states:
                local_score += 1
            elif i % 2 == 0 and continuation[i] in feared_world_states:
                local_score -= 1
            elif i % 2 == 0 and continuation[i] in wanted_world_states2:
                local_score += 2
            elif i % 2 == 0 and continuation[i] in feared_world_states2:
                local_score -= 2

            # punishes non-idle actions (found in the odd positions of the continuation) 
            # this makes sense when action cost is important and world actions are
            # correctly modelled, i.e. stopped is 0
            if i % 2 == 1 and not(continuation[i] == 0):
                local_score -= 0.1
        return local_score


    
