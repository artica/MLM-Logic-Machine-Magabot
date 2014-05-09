## MLM Magabot Robot
## Jose F Castro
## November 2012

##########################################
####    NEEDED IMPORTS FOR main() ########

import random

import subprocess       # to clear the python dos command line screen

import mlm_util
# ...imports some useful functions for the MLM
util = mlm_util

import magabot_module
# A simpler name for the module...
magabot = magabot_module

import mlm_cinematic_brain_class
# ...This module contains the BrainCinematic class
# It models the agent's subjective cinematic experience
# A simpler name for the module...
cbrclass = mlm_cinematic_brain_class


###############################
####   THE AGENT CLASS     #### 

class Agent(magabot.Magabot, cbrclass.BrainCinematic):
    
    '''This is an agent made of a Magabot, with a cinematic brain'''

    def __init__(self):
        
        magabot.Magabot.__init__(self)
        cbrclass.BrainCinematic.__init__(self)

        # some variables to hold statistics about the robot behaviour...        
        self.num_failed_to_predict = 0
        self.num_wrong_predictions = 0 
        self.num_correct_predictions = 0
        self.num_pure_reflex = 0
        self.num_basic_reflex = 0
        self.num_blind_actions = 0
        self.ltm_not_full = True
        self.step_full = 0           # when did the LTMDD reached max size
        self.action_source_list = [] # was it a voluntary, reflex, or blind action

       
    #---------------------------------------------------------------------------------
    # THE SENSORY MICRO-STEP
    # The function below first captures world data and records it in BM and STM and WM
    # It then updates the internal LTMDD and HEUR
    # It also finds actions based on predictive continuations for the current scene
    # and offers other actions in the absence of predictive continuations

    def sensory_micro_step(self,
                           cognitive_level,    
                           current_step): # a number, just for statistical purposes

        # FIRST gets sensory data
        # uses function from Magabot class:
        self.send_read_sensors_request()
        
        # Magabot sensors data is coded by a single number 
        ag_sensory_data = self.get_magabot_sensory_number()
        print ''
        print 'Sensory Number: ', ag_sensory_data

        # SECOND records data in Binding Memory BM
        # uses function from mlm_cinematic_brain_class
        self.record_in_bm(ag_sensory_data) 

        # THIRD transfers BM data to STM; Orienting reflexes fit here
        # uses function from mlm_cinematic_brain_class
        self.record_in_stm()

        # ---------------------------------------------------------
        # Here Begins: the B K confirmation and dominance update of LTMDD and HEUR
        #
        # confirmation can only be obtained for the present moment

        prediction = self.wm[1]  # Pred **** this is a [s,m] pair
        print 'Previous step [s,m] prediction:', prediction
            # ... This [s,m] previously defined prediction can now
            #           be compared to present-moment STM content
            
        ltmdd_scene_used = self.wm_aux[0]
        heur_id_used = self.wm_aux[1]
        filter_id_used = self.wm_aux[2]
        
        present_moment_knowledge = self.stm[0:2] # Know **** the latest [s,m] in STM
                                                # BM not used, since STM may be different

        # we place the present-moment knowledge in the WM knowledge slot
        self.wm[2] = present_moment_knowledge 
        print ' Current step [s,m] knowledge: ', present_moment_knowledge,

        # We relocate scenes used for successful predictions on top of LTMDD
        # Heuristic used in successful prediction also goes to top

        # The test with ltmdd_scene_used means this only applies for
        #   predictions found by the partial match process
        #       and that the used scene is still in the LTMDD
        
        # The ltmdd_scene_used is in ag1.ltmdd and present_moment_knowledge
        # is similar to prediction:
        # WHAT IS COMPARED IS MOTOR AND (VIRTUAL) DRIVING CHANNEL INFO
        # Similarity criterion is equivalent to having an abstract pain/pleasure channel
        
        if (ltmdd_scene_used in self.ltmdd
            and
            util.similar_pred_know(prediction, present_moment_knowledge,
                                   # Magabot attributes
                                   self.wanted_sensed_states, self.feared_sensed_states,
                                   self.wanted_sensed_states2, self.feared_sensed_states2)
            ):

            print '===> CORRECT PREDICTION (CURRENT STATE SIMILAR TO PREDICTION)',
            print ''
            self.num_correct_predictions += 1

            # print '**** similarity success',
            # print ''

            # dominance is now updated
            how_fast = 1    # how_fast>0 goes up (reward), how_fast<0 goes down (punish)

            self.update_dominance_ltmdd_and_heur(ltmdd_scene_used, heur_id_used, how_fast)

            # The used filter only goes up if the correctly predicted state was wanted
            print ' Current State:', present_moment_knowledge[0],
            if (present_moment_knowledge[0] in self.wanted_sensed_states or
                present_moment_knowledge[0] in self.wanted_sensed_states2):
                print '                    the filter', filter_id_used, ' is pulled UP',
                self.update_dominance_filter(filter_id_used, how_fast)


        # We relocate down scenes used for wrong predictions of LTMDD
        # Heuristic used in wrong prediction also goes ALL way down
        #   Same for continuation filters
            
        elif ltmdd_scene_used in self.ltmdd:

            print '===> WRONG PREDICTION',
            print ''
            self.num_wrong_predictions += 1

            how_fast = -1    # how_fast>0 goes up (reward), how_fast<0 goes down (punish)

            self.update_dominance_ltmdd_and_heur(ltmdd_scene_used, heur_id_used, how_fast)

            # used filter only goes down if it led to feared sensed state
            print ' Current State:', present_moment_knowledge[0],
            if (present_moment_knowledge[0] in self.feared_sensed_states or
                present_moment_knowledge[0] in self.feared_sensed_states2):
                print '                   the filter', filter_id_used, ' is pushed DOWN', 
                self.update_dominance_filter(filter_id_used, how_fast)

        else:
            print '**** NO PREVIOUS PREDICTION',
            print ''
            self.num_failed_to_predict += 1
            # this score is left alone
            

        #    
        # Here Ends: the B K confirmation and dominance update
        # ---------------------------------------------------------

        # now we transfer STM [s,m] data do LTMDD_BUFFER and LTMDD,
        #       according to RECORD MODE

        self.stm_to_ltmdd_and_ltmbuff_transfer(self.ltmdd_size)

        belief = []     # we start with an epmty belief
        scene_used = [] # and no scene used
        heur_id = 0         # heuristics ID (identifier) being used
        filter_id = 0
        question_past_context = ['None']
        
        if cognitive_level >= 3:

            # ------------------------------------------------------
            # Here Begins: the Q B prediction process
            #

            # Tries the heuristics identified in heur_id_dom
            # until a belief is generated

            h_index = 0         # heuristics ID dominance list index being used
            
            len_heur_id_list = len(self.heur_id_dom)
            
            while belief == [] and h_index < len_heur_id_list:
                
                # 1. A heuristic identifier is taken from heur_id_dom index location
                heur_id = self.heur_id_dom[h_index]
                # print '*** heuristic id:', heur_id,
                # print 'heuristic id index:', h_index,
                
                # 2. Method 'generateQ_past' copies the STM in different ways,
                #       according to the heuristic ID 
                question_past_context = self.generateQ_past(heur_id)
                # ... generating a list of (a+0j) complex numbers
                # print 'question context:', question_past_context

                # 3. Now begins the 'partial matching' process
                #       Scans the ltmdd for a scene that includes the
                #           past context recorded in question_past_context.

                ltmdd_index = 0
                len_ltmdd = len(self.ltmdd)
                            # ... just because local variables are accessed faster
                matching_result = [[], [], []]
                continuation = matching_result[0]
                filtered_continuation = []
                scene_used = []
                predictive_horizon = 8

                while continuation == [] and ltmdd_index < len_ltmdd:

                    # 3.1. Finds a continuation for the 'question_past_context' pattern
                    #       Use: continuation(pattern, horizon)
                    #           pattern made of complex numbers
                    #               defining context and interrogation
                    
                    # *** RETURNS: [[A][B][C]]
                    # ****** A is the [s,m,s,m,...,s,m] continuation for B; len(A) is horizon
                    # ****** B is the pattern used
                    # ****** C is the scene in LTM that provided a match for B

                    # ... horizon=8: A = [s,m,s,m,s,m,s,m], i.e. four sm pairs

                    matching_result = self.find_a_ltmdd_continuation(ltmdd_index,
                                                                    question_past_context,
                                                                    predictive_horizon)
                    
                    continuation = matching_result[0]  # this is A above
                    
                    # 3.2. At this point we filter the continuation
                    #       in order to reach a desired state
                    #           or avoid an undesired state
                    
                    # print continuation,
                    
                    filter_index = 0    # filter heuristics ID dominance list index being used
                    filter_id = 0       # filter heuristics ID (identifier) being used
                    len_filter_id_list = len(self.filter_id_dom)

                    while filtered_continuation == [] and filter_index < len_filter_id_list:

                        # 3.2.1. A heuristic identifier is taken
                        #       from 'self.filter_id_dom' index location
                        
                        filter_id = self.filter_id_dom[filter_index]

                        filtered_continuation = (self.continuation_filter
                                                 (continuation,
                                                  self.wanted_sensed_states,
                                                  self.feared_sensed_states,
                                                  self.wanted_sensed_states2,
                                                  self.feared_sensed_states2,
                                                  filter_id,
                                                  predictive_horizon)
                                                 )
                        ##if not filtered_continuation == []:
                        ##    print filtered_continuation,'Passed the filter', filter_id

                        filter_index += 1

                    ltmdd_index += 1
                    

                belief = filtered_continuation # this is also [A], the continuation
                # .... could still be []
                ## print 'belief:', belief,
                scene_used = matching_result[2] # this is [C]
                ## print 'scene used:', scene_used,
                # print 'matching result 2:', matching_result

                # goes to the next index in 'self.heur_id_dom' (the heuristic dominance list) 
                h_index += 1
            #
            # Here Ends: the Q B prediction process
            # ---------------------------------------------------------

        # NOTE: at this stage the belief can be empty, i.e. = []
        # print 'belief',belief,

        if cognitive_level >= 2:
        
            #------------------------------------------------------------------
            # here begins posterior REFLEX action (or INSTINCT) process
            #   dominated by any previous non-empty belief
            #
            
                   
            # Only if NO QB belief was previously generated,
            #   is here a random exploratory action generated.
            # This implements exploration instinct
            if belief == []:
                question_past_context = ['PostCinematicInstinct']
                self.num_pure_reflex += 1

                # The instictive requested force
                instinct_action = self.get_mvtreq_to_actnum_translation(
                    self.sonar_driven_choice())

                belief = [+1j, instinct_action] # [s,m] pair
                
                # clean WM of irrelevant data:
                scene_used = []
                heur_id = 0
                filter_id = 0

            # here ends posterior REFLEX beliefs
            #--------------------------------------------------------------------

        # NOTE: at this stage, beliefs can still be []

        if cognitive_level >= 1:
        
            #--------------------------------------------------------------
            # Here starts BASIC REFLEXES, independent of any prior belief states
            # These are programmed in the Magabot Arduino

            pass

            # Here ends BASIC REFLEXES, independent of prior belief states
            #---------------------------------------------------------------

        if cognitive_level == 0 or belief == []:

            # Blind agent: acts randomly if blind coglevel, or nothing produced so far
            # i.e. covers all situations not handled above
            # generating a random elementary action
            #--------------------------------------------------------------

            question_past_context = ['Blind']
            self.num_blind_actions += 1

            blind_action = random.choice([0,1,2,3,4,5,6,7,8,9])

            belief = [+1j, blind_action] # blind exploration...

            scene_used = []
            heur_id = 0
            filter_id = 0
            
            # Here ends Blind Agent
            #--------------------------------------------------------------

        # NOTE: we now have a belief (possibly random) different from []!!
        
        # we now record the results in the working memory WM
        self.wm[0] = question_past_context[:] # WARNING!! inner lists still share same ID !!
        self.wm[1] = belief[len(belief)-2:] # from end-1 to end of list
        #self.wm[1] = belief[len(belief)-2:len(belief)-1] 
        self.wm[2] = [] # erase wm knowledge
        
        print ''
        #print 'WM without K:', self.wm
        #print 'Scene used 2:', scene_used
        print '  XWANTED: ', self.wanted_sensed_states2
        print '   WANTED: ', self.wanted_sensed_states
        print '   FEARED: ', self.feared_sensed_states
        print '  XFEARED: ', self.feared_sensed_states2
        print ''
        self.wm_aux[0] = scene_used
        self.wm_aux[1] = heur_id
        self.wm_aux[2] = filter_id
        #print 'WM AUX:', self.wm_aux
        print '       CONTEXT HEUR ID DOMINANCE:', self.heur_id_dom
        print '  PREDICTIVE FILTER ID DOMINANCE:', self.filter_id_dom
        print ''
        print '  Current LTMDD size:', len(self.ltmdd),
        print '       Context Heuristic Used:', self.wm_aux[1],
        print '       Predictive Filter Used:', self.wm_aux[2]
        print ''


        # We can now tell to the br1 what is the requested action
        self.action_request = self.wm[1][1]
        
        # for analysis purposes, we code and record the action source
        action_source = 0
        if question_past_context == ['Blind']:
            print 'Blind Action'
            action_source = 20
##        elif question_past_context == ['Rbsic']:      # In Magabot Arduino
##            action_source = 30
        elif question_past_context == ['PostCinematicInstinct']:
            print '  ++++ INSTINCTIVE Action:',  # number and  tag printed below
            action_source = 40
        else:
            action_source = 60           # full cinematic
            print '  ++++++ VOLUNTARY Action:',
        
        self.action_source_list.append(action_source)
        
        # we note the step when the LTM size limit was reached

        if self.ltm_not_full and len(self.ltmdd) >= self.ltmdd_size:
            self.ltm_not_full = False
            self.step_full = current_step

    # ---- HERE ENDS the sensory micro-step function
    #---------------------------------------------------------------------------------


    #---------------------------------------------------------------------------------
    # THE MOTOR MICRO-STEP

    def motor_micro_step(self):

        # FIRST, THE AGENT ACTS...
        # functions from Magabot class

        # displays the cinematic brain action request in two formats
        print 'Number:', self.action_request, 
        action_request_tag = (self.get_actnumber_to_movementreq_translation
                              (self.action_request))
        print ' ===>  Tag:', action_request_tag,

        self.updates_known_actions_list(self.action_request)
        print ' // KNOWN:', self.list_of_known_actions,

        # calls the MAGABOT module function that sends actions to Arduino
        self.perform_movement_request(action_request_tag)

        # SECOND, THE AGENT SENSES ITS OWN ACTION FORCE...
        # the action number attribute is updated in the Magabot class

        actual_action_number = self.get_magabot_action_number()

        ### THIRD, WE PROCESS THE self INTERNAL MEMORY TRANSFERS FOR THE SENSED FORCE  

        ### we record the force in the BM:
        # cinematic brain function
        self.record_in_bm(actual_action_number)

        ### we copy it to the STM:
        # cinematic brain function
        self.record_in_stm()

        ### but we do not record to SLBUFF or LTM: it's a [m,s,..,m,s] configuration.

        ### At the [s,m,...,s,m] configuration, then the [s,m] pairs
        ###     will be inserted in SLBUFF and LTM;
        ###         the same happens for the LTM update 
    
    ## Here ends the MOTOR MICRO-STEP
    #----------------------------------------------------------------------------------


## A function to clear the Python command line shell

def cls():
    subprocess.call("cls", shell=True)
    return
    
####################################################################################
####   THE MAIN PROGRAM    ######################################################### 
####################################################################################

def main():

    # cls = ClearScreen()

    #  First, create Magabot agent and open serial port
    
    ag1 = Agent()
    
    ag1.open_serial_port()

    # Header to Main Loop...

    print 'world-brain loop for brain ag1:'

    step = 0 # to initialize

    ######################################################
    ### Here Starts The Main Loop
    
    while 1:
    ## for step in range(1200):

        cls()
        print '================================================= step ', step


        ############ THE AGENT SENSORY MICRO-STEP
        ############ (one for each existing agent)

        ag1.sensory_micro_step(3,step)  # 3 is the cognitive level
  
        # We now have a [s,m,...,s,m] configuration in BM and STM
        

        ############ THE AGENT MOTOR MICRO-STEP

        ag1.motor_micro_step()

        step = step + 1
                          
    # here ends the main loop
    # -----------------------------------------------------------------------------

    ag1.perform_movement_request('final_stop')    # stop
    print 'FINAL STOP ************* ', ag1.current_action                      

    ag1.close_serial_port()
    
###############################################################################
## RUN MAIN
###############################################################################

main()


