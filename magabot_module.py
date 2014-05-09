# -*- coding: cp1252 -*-
# Module: MagabotClass.py
# Created: December 2012
# Author: José Castro
# castrojfgf/at/gmail.com
# Version: 1.7
# Works with Magabot Arduino using PySerial
# Magabot working with high-level requests
################################################
import serial
import time
import random

class Magabot(object):

    def __init__(self):
        self.current_action = ''
        self.current_readline = ''
        self.last_magabot_code = ''

        # Magabot port number
        #self.port_number = 'COM31'  # FCUL 2
        #self.port_number = 'COM28'  # FCUL 1
        #self.port_number = 'COM29'  # Artica
        self.offline_test = 1  # 1 means Magabot is offline, and COM6 is used

        # The following attributes define what is present in the MLM SM
        # Actually, they may replace the CinBrain Sensory Memory
        
        # Magabot hardwired alerts
        self.bumper_right_alert = 0
        self.bumper_left_alert = 0
        self.ir_alert = 0

        # IR data
        self.ir_data = [0,0,0]
        self.ir_mean_data = [0,0,0]
        self.ir_bin_inc_code = [0,0,0]

        # Sonar data
        self.sonar_danger_distance = 25
        
        self.sonar_data = [0,0,0,0,0]
        self.sonar_mean_data = [0,0,0,0,0]
        self.sonar_bin_dec_code = [0,0,0,0,0]

        self.sonar_frontal_obstacle_alert = 0
        self.sonar_left_side_obstacle_alert = 0
        self.sonar_right_side_obstacle_alert = 0
        self.sonar_any_low_value_alert = 0
        
        # Sensory code sent to cinematic brain (CB)
        self.output_sensory_number = 0

        # Action codes sent to Magabot from CB and sent back to CB
        self.input_action_number = 0
        self.actual_action_number = 0   # ideally not just a copy of the input

        # These list are gradually built from the actual Magabot sensory codes found
        self.wanted_sensed_states = []
        self.feared_sensed_states = []
        self.wanted_sensed_states2 = []
        self.feared_sensed_states2 = [] 

        # Magaboot saccade tuning        
        self.caution_mood = 0.0
        self.pain_level = 0.0
        self.mood_bin_code = 0
        
        # just for statistics
        self.number_of_bumps = 0
        
        
        # Fake raw data for offline program testing
        self.raw_ir_data = self.bump_ir_model()

        self.raw_sonar_data = ['s:300;340;230;350;200; ',
                               's:300;340;230;350;230; ',
                               's:300;340;230;350;300; ',
                               's:300;340;230;350;300; ',
                               's:300;340;230;350;300; ',
                               's:300;340;230;350;300; ',
                               's:300;340;230;350;250; ',
                               's:300;340;230;50;50; ',
                               's:30;34;23;35;20; ',
                               's:50;50;233;350;200; ']


    # a bumper and ir model to fake reality
    
    def bump_ir_model(self):
        ##print 'LSIDE ALERT FOR bl RAW DATA ===', self.sonar_left_side_obstacle_alert
        ##print 'RSIDE ALERT FOR br RAW DATA ===', self.sonar_right_side_obstacle_alert
        if self.sonar_left_side_obstacle_alert > 0 and random.random() > 0.8:
            return 'bl'
        elif self.sonar_right_side_obstacle_alert > 0 and random.random() > 0.8:
            return 'br'
        elif random.random() > 0.95:
            return 'i'
        else:
            return 'r:30;34;23; '


    ###########################################
    # Serial Port management
    
    def open_serial_port(self):
        print 'Opening Port...'
        if self.offline_test:
            # reading timeout avoids waiting forever
            self.ser = serial.Serial('COM6',9600,timeout=3)  
        else:
            self.ser = serial.Serial(self.port_number,9600,timeout=3)
        # allows some time for arduino to reset
        time.sleep(2)                       
        print 'Is Port Open?  ', self.ser.isOpen()
        print 'Port Used:     ', self.ser.portstr       
        
    def close_serial_port(self):
        print 'Closing port... ', self.ser.close()
        print 'Is Port Open?   ', self.ser.isOpen()
        print 'Port Used:      ', self.ser.portstr       


    ###############################################################################

                        
    # Evaluate state values for the MLM sensory steps, and gradually builds 
    # the wanted and feared (WF) states list from the actual output numbers
    
    def get_magabot_sensory_number(self):
        
        # the current mood is evaluated and coded
        if self.caution_mood > 1.0:
            self.mood_bin_code = 1
        else:
            self.mood_bin_code = 0

        # orienting filters drop useless information, avoiding too many sensory states

        bumper_ir_filter = ((1 - self.bumper_right_alert)
                            * (1 - self.bumper_left_alert)
                            * (1 - self.ir_alert))
        
        # the output sensory number defines the MLM sensory state
        self.output_sensory_number = ((self.sonar_left_side_obstacle_alert * 1
                                      + self.sonar_right_side_obstacle_alert * 2
                                      # neutral
                                      + self.sonar_frontal_obstacle_alert * 4
                                      + self.sonar_any_low_value_alert * 8
                                      # wanted and feared mood threshold
                                      + self.mood_bin_code * 16) * bumper_ir_filter
                                      # pain and fear alerts
                                      + self.ir_alert * 32
                                      + self.bumper_right_alert * 64
                                      + self.bumper_left_alert * 128
                                      )
        
        # the wanted and feared sensory states lists are updated 
        self.update_wf_lists(self.output_sensory_number)

        return self.output_sensory_number

    # The wanted/feared thresholds here articulate with the state values
    # given by self.output_sensory_number.  
    # States not included here are neutral states.

    def update_wf_lists(self, output_sensory_number):
        # no alerts at all, most desired state
        if output_sensory_number < 1:
            no_dup_append(self.wanted_sensed_states2, output_sensory_number)

        # one side alerts without bad mood, or bumper or ir alerts, are ok states 
        elif output_sensory_number < 3:
            no_dup_append(self.wanted_sensed_states, output_sensory_number)

        # bad mood is not ok
        elif output_sensory_number >= 16 and output_sensory_number < 32:
            no_dup_append(self.feared_sensed_states, output_sensory_number)

        # if bumper or ir alarm, most feared state
        elif output_sensory_number >= 32:
            no_dup_append(self.feared_sensed_states2, output_sensory_number)


    # Next, a function just to output the Magabot sensor values, mean values,
    # and fast changing values
    
    def read_magabot_sensors(self):
        return (self.bumper_right_alert,
                self.bumper_left_alert,
                self.ir_alert,
                self.sonar_data,
                self.sonar_mean_data,
                self.sonar_bin_dec_code,
                self.ir_data,
                self.ir_mean_data,
                self.ir_bin_inc_code) 


    ####################################
    # Output functions for motor step
    
    def get_magabot_action_number(self):
        # just returns the last input action number sent from Cin Brain to Magabot,
        # since there is no way of measuring the actual action
        # *** project: change Arduino sketch to get that info ****
        self.actual_action_number = self.input_action_number
        return self.actual_action_number


    ############################################################
    # Input functions for motor step
    # Send movement request and updates current_action attribute

    # translation from cinematic brain action numbers to module action tags
    def get_actnumber_to_movementreq_translation(self, action_number):
        # updates attribute
        self.input_action_number = action_number
        
        if action_number == 0:
            return 'stop'
        elif action_number == 1:
            return 'left'
        elif action_number == 2:
            return 'right'
        elif action_number == 3:
            return 'forward'
        elif action_number == 4:
            return 'backward'
        elif action_number == 5:
            return 'ts_stop'
##        elif action_number == 6:
##            return 'left_and_forward'
##        elif action_number == 7:
##            return 'right_and_forward'
##        elif action_number == 8:
##            return 'backward_and_turn_right'
##        elif action_number == 9:
##            return 'backward_and_turn_left'
        else:
            return 'stop'

    # Request given by Magabot module action tags,
    # then translated to high-level Arduino controls
    # It can be a saccade approach if all movements end with stop command
    def perform_movement_request(self, request):
        turn_time = 0.0
        self.current_action = request
        # print 'sending action request ', request 
        if request == 'left':
            # self.stop_command()
            self.turn_left_command()
        elif request == 'right':
            # self.stop_command()
            self.turn_right_command()
        elif request == 'forward':
            self.forward_command()
            # self.stop_command()
        elif request == 'backward':
            self.backward_command()
            self.stop_command()
        elif request == 'stop':
            self.stop_command()
        elif request == 'final_stop':
            self.ser.write('p')
        elif request == 'ts_stop':
            time.sleep(1)
            self.stop_command()
##        elif request == 'backward_and_turn_right':
##            self.backward_command()
##            self.stop_command()
##            self.turn_right_command()
##            #self.stop_command()
##            #self.forward_command()
##        elif request == 'backward_and_turn_left':
##            self.backward_command()
##            self.stop_command()
##            self.turn_left_command()
##            #self.stop_command()
##            #self.forward_command()
        else:
            time.sleep(0.1)

    # translation from module tags to MAGABOT high-level controls
    # with action duration given by Python time.sleep(Time)
    
    def stop_command(self):
        if not self.last_magabot_code == 'p':
            self.ser.write('p')
            self.last_magabot_code = ''
        time.sleep(0.1)

    def turn_left_command(self):
        if not self.last_magabot_code == 'a':
            self.ser.write('a')
            self.last_magabot_code = ''
        # turns more when caution mood is higher
        time.sleep(self.turn_time())
        
    def turn_right_command(self):
        if not self.last_magabot_code == 'd':
            self.ser.write('d')
            self.last_magabot_code = ''
        # turns more when caution mood is higher
        time.sleep(self.turn_time())

    def turn_random_command(self):
        # random left or right turn
        rand_choice = random.choice(['d','a'])
        if not self.last_magabot_code == rand_choice:
            self.ser.write(rand_choice)
            self.last_magabot_code = ''
        # turns more when caution mood is higher
        time.sleep(self.turn_time())
            
    def forward_command(self):
        if not self.last_magabot_code == 'w':
            self.ser.write('w')
            self.last_magabot_code = ''
        # advances less when caution mood is higher
        time.sleep(self.forward_mvt_time())

    def backward_command(self):
        if not self.last_magabot_code == 's':
            self.ser.write('s')
            self.last_magabot_code = ''
        time.sleep(self.forward_mvt_time())

    # action times are modulated according to the caution mood
    
    def forward_mvt_time(self):
        w_time = (0.3 / (1 + 2 * self.caution_mood)) + 0.2
        print ' ...... W or S time:', w_time
        return w_time

    def turn_time(self):
        turn_time = (0.2 +
                     0.3 * self.caution_mood +
                     (self.sonar_left_side_obstacle_alert +
                      self.sonar_right_side_obstacle_alert) # % 2
                     ) 
        print ' ...... A or D time:', turn_time
        return turn_time
        
    ######################################################################    
    # Sensor reading functions for sensory step
    # Send sensor reading request and updates Magabot sensor attributes

    def send_read_sensors_request(self):
        # print 'sending v request to get IR and Sonar data'
        self.ser.write('v')
        time.sleep(0.1)
        self.get_bumper_or_ir_alerts()
        self.display_bumper_and_ir_alerts()
        self.get_ir_values()
        self.get_sonar_values()
        self.get_derived_features()
        # displays values as horizontal bars
        self.display_ir_data()
        self.display_sonar_data()


    def get_bumper_or_ir_alerts(self):
        # detects if first readings result from bumper alert (data 'br' or 'bl')
        # or IR alert (data 'i')
        # repeat until all 'bl', 'br', and 'i' are captured
        bumper_right_alert = 0
        bumper_left_alert = 0
        ir_alert = 0

        # get first readline
        if self.offline_test:
            # if offline, read fake data randomly
            self.raw_ir_data = self.bump_ir_model()
            self.current_readline = self.raw_ir_data
        else:
            # if online with MAGABOT, read Arduino data
            self.current_readline = self.ser.readline()

        # print 'First captured data **** ', self.current_readline   # to check Magabot reading
        # print len(self.current_readline)

        # if data exists, repeats ser.readline() until all 'b's and 'i's are collected 
        if len(self.current_readline) > 0:
            while self.current_readline[0] == 'b' or self.current_readline[0] == 'i':

                # first, define the bumper and ir alerts
                if self.current_readline[0] == 'i':
                    ir_alert = 1
                elif self.current_readline[0:2] == 'br':
                    bumper_right_alert = 1
                    self.number_of_bumps = self.number_of_bumps + 1
                elif self.current_readline[0:2] == 'bl':
                    bumper_left_alert = 1
                    self.number_of_bumps = self.number_of_bumps + 1    
                # second, read the next readline
                if self.offline_test:
                    self.raw_ir_data = self.bump_ir_model()
                    self.current_readline = self.raw_ir_data
                else:
                    self.current_readline = self.ser.readline()  # read real Magabot output

                # print 'while loop sensor data **** ', self.current_readline   # to check Magabot reading
                
            # records bumper data in Magabot attributes at the end of the while loop
            self.bumper_right_alert = bumper_right_alert
            self.bumper_left_alert = bumper_left_alert
            self.ir_alert = ir_alert

    def display_bumper_and_ir_alerts(self):
        if self.bumper_right_alert > 0:
            print 'BUMPER R: A PAUSE IS GIVEN TO FINISH REFLEX'

        else:
            print 'BUMPER R:'
        if self.bumper_left_alert > 0:
            print 'BUMPER L: A PAUSE IS GIVEN TO FINISH REFLEX'
        else:
            print 'BUMPER L:'
        if self.ir_alert > 0:
            print '   I RED: A PAUSE IS GIVEN TO FINISH REFLEX'
        else:
            print '   I RED:'

        if (self.bumper_right_alert > 0 or
            self.bumper_left_alert > 0 or
            self.ir_alert > 0):
            # waits for the reflex to finish before sending command
            time.sleep(1.0)
            self.stop_command()
            

    def get_ir_values(self):
        # this 'r' test should be useless, since the ir+sonar data sequence is defined
        # in Magabot high-level command to answer the 'v' request
        if len(self.current_readline) > 0:
            if self.current_readline[0] == 'r':
                raw_ir_data = self.current_readline

                # cleans and converts text IR data to integers
                # separate the r tag from the IR numbers that are separated by ;
                ir_data_list = raw_ir_data.split(":")
                # separate the numbers
                ir_data_list2 = ir_data_list[1].split(";")
                ir_data_list3 = ir_data_list2[0:3]
                # records numeric IR data in Magabot attributes if no IR alarm is present
                if self.ir_alert < 1:
                    self.ir_data = [int(x) for x in ir_data_list3]
                    print ''
                else:
                    print 'IR alert, no IR magabot attributes changed'
        else:
            print 'Void IR data, no attributes changed'

    def get_sonar_values(self):
        if self.offline_test:
            self.current_readline = random.choice(self.raw_sonar_data)
        else:
            # print 'readline for sonar data...'
            self.current_readline = self.ser.readline()

        # cleans and converts text SONAR data to integers
        if len(self.current_readline) > 0:
            if self.current_readline[0] == 's':
                
                # cleans and converts text Sonar data to integers
                sonar_data_list = self.current_readline.split(":")
                sonar_data_list2 = sonar_data_list[1].split(";")
                sonar_data_list3 = sonar_data_list2[0:5]
                # records numeric SONAR data in Magabot attributes
                self.sonar_data = [int(x) for x in sonar_data_list3]
        else:
            print 'Void SONAR data, no attributes changed'

    def get_derived_features(self):
        # Sonar derived attributes

        # Evaluates fast decrement/increments relative to mean value
        # A. Evaluates mean value (= 0.7 prior Mean Value + 0.3 Current Value)
        self.sonar_mean_data = mean_vector(self.sonar_mean_data,
                                           self.sonar_data)
        # B. Binary evaluation of fast decrease (0 ort 1)
        self.sonar_bin_dec_code = dif_binary_coding(self.sonar_mean_data,
                                                self.sonar_data,
                                                'dec')

        # Alerts used to claculate self.caution_mood
        # Sonar alerts:

        ### 1. Frontal obstacle alert 
        if self.sonar_data[2] < 2 * self.sonar_danger_distance:
            #
            self.sonar_frontal_obstacle_alert = 1
        else:
            self.sonar_frontal_obstacle_alert = 0
            
        ### 2. Left side obstacle alert
        if (self.sonar_data[0] < 3 * self.sonar_danger_distance
            or
            self.sonar_data[1] < 2 * self.sonar_danger_distance):
            #
            self.sonar_left_side_obstacle_alert = 1
        else:
            self.sonar_left_side_obstacle_alert = 0

        ### 3. Right side obstacle alert
        if (self.sonar_data[3] < 2 * self.sonar_danger_distance
            or
            self.sonar_data[4] < 3 * self.sonar_danger_distance):
            #
            self.sonar_right_side_obstacle_alert = 1
        else:
            self.sonar_right_side_obstacle_alert = 0

        ### 4. Any low value of a single sonar
        if (self.sonar_data[0] < self.sonar_danger_distance or
            self.sonar_data[1] < self.sonar_danger_distance or
            self.sonar_data[2] < self.sonar_danger_distance or
            self.sonar_data[3] < self.sonar_danger_distance or
            self.sonar_data[4] < self.sonar_danger_distance):
            #
            self.sonar_any_low_value_alert = 1
        else:
            self.sonar_any_low_value_alert = 0

        # The caution mood is evaluated. This will affect duration of motor micro-step
        if (self.bumper_right_alert > 0 or
            self.bumper_left_alert > 0 or
            self.ir_alert > 0 or
            self.sonar_any_low_value_alert > 0 or
            self.sonar_frontal_obstacle_alert > 0):
            self.caution_mood = self.caution_mood + (1 / (1 + self.caution_mood))
        elif self.caution_mood > 0.2:
            self.caution_mood = 0.5 * self.caution_mood
        else:
            self.caution_mood = 0.0
        print 'Caution Mood: ', self.caution_mood

        # IR derived attributes
        self.ir_mean_data = mean_vector(self.ir_mean_data,
                                        self.ir_data)
        self.ir_bin_inc_code = dif_binary_coding(self.ir_mean_data,
                                             self.ir_data,
                                             'inc')
        
    # Values are graphically displayed with horizontal bars
            
    def display_ir_data(self):
        print ''
        ir_data = self.ir_data
        for i in range(3):
            ir_display_value = ir_data[i] // 20
            for j in range(ir_display_value-1):
                print '=',
            print '=', ir_data[i],
            print '/', self.ir_mean_data[i],
            print '/i:', self.ir_bin_inc_code[i]

    def display_sonar_data(self):
        print ''
        sonar_data = self.sonar_data
        for i in range(5):
            sonar_display_value = sonar_data[i] // 10
            for j in range(sonar_display_value-1):
                print '*',
            print '*', sonar_data[i],
            print '/', self.sonar_mean_data[i],
            print '/d:', self.sonar_bin_dec_code[i]
        # print sonar alerts
        print ''
        print 'SONAR ALERTS: ',
        if  self.sonar_frontal_obstacle_alert > 0:
            print '*** FRONTAL ***',
        if self.sonar_right_side_obstacle_alert > 0:
            print '*** RIGHT-SIDE ***',
        if self.sonar_left_side_obstacle_alert > 0:
            print '*** LEFT-SIDE ***',
        if self.sonar_any_low_value_alert > 0:
            print '*** LOW VALUE ***',
        print ''
            
    ###############################################################
    # Reflex Actions Dominated by Cinematic Decisions

    # The function beblow named "sonar_driven_choice" will be actually used
    # Change the names of the unused functions to "sonar_driven_choice_1", etc...
    
    #1. Random exploratory behaviour

    def sonar_driven_choice(self):
        
        # wait_message = ''
        if (self.bumper_right_alert > 0 or
            self.bumper_left_alert > 0 or
            self.ir_alert > 0):
            self.stop_command()
            rand_choice = random.choice(['left','right'])
        elif  self.sonar_frontal_obstacle_alert > 0:
            rand_choice = random.choice(['left','right','stop'])
        else:
            rand_choice = random.choice(['forward','forward','forward',
                                         ##'left','right','forward','forward','forward',
                                         ##'left','right','forward','forward','forward',
                                         ##'backward',
                                         'left','right','stop'])
##        print ''
##        print '*** Random Reflex:', rand_choice, ' ***'# , wait_message

        return rand_choice

    # 2. obstacle avoidance behavior
    # (cheks side where sonar readings or alerts are smaller)

    def sonar_driven_choice_1(self):

        if (self.bumper_right_alert < 1 and
            self.bumper_left_alert < 1 and
            self.ir_alert < 1):

            # The action choices in the absence of Bumper or IR alerts...

            if  self.sonar_frontal_obstacle_alert > 0:
                print ''
                print '*** Sonar Driven Reflex: FRONTAL OBSTACLE DETECTED ***'
                # what was the last action performed (recorded in self.current_action)
                # determines present choice...
                if self.current_action == 'stop':
                    return random.choice(['left','right'])
                elif self.current_action == 'left':
                    return 'left'
                elif self.current_action == 'right':
                    return 'right'
                else:
                    return 'stop'
            
            elif (self.sonar_right_side_obstacle_alert > 0 and
                  self.sonar_left_side_obstacle_alert == 0):
                print ''
                print '*** Sonar Driven Reflex: RIGHT SIDE OBSTACLE DETECTED ***'
                return 'left'

            elif (self.sonar_left_side_obstacle_alert > 0 and
                  self.sonar_right_side_obstacle_alert == 0):
                print ''
                print '*** Sonar Driven Reflex: LEFT SIDE OBSTACLE DETECTED ***'
                return 'right'

            elif (self.sonar_left_side_obstacle_alert > 0 and
                  self.sonar_right_side_obstacle_alert > 0):
                print ''
                print '*** Sonar Driven Reflex: LEFT&RIGHT SIDE OBSTACLE DETECTED ***'
                return 'backward'       # includes a stop

            elif self.sonar_any_low_value_alert > 0:
                print ''
                print '*** Sonar Driven Reflex: VERY LOW INDIVIDUAL VALUE ***'
                return 'backward'       # includes a stop

            else:
                print ''
                print '*** Sonar Driven Reflex: NO OBSTACLE DETECTED ***'
                return 'forward'
            
        # The choice with Bumper or IR alerts
        
        elif (self.bumper_right_alert > 0 and
              self.bumper_left_alert < 1 and
              self.ir_alert < 1):
            print ''
            print '*** Bumper Driven Reflex: RIGHT BUMPER wait... ***'
            # time.sleep(1.0)              
            return 'ts_stop'

        elif (self.bumper_right_alert < 1 and
              self.bumper_left_alert > 0 and
              self.ir_alert < 1):
            print ''
            print '*** Bumper Driven Reflex: LEFT BUMPER wait... ***'
            # time.sleep(1.0)
            return 'ts_stop'

        elif (self.bumper_right_alert > 0 and
              self.bumper_left_alert > 0 and
              self.ir_alert < 1):
            print ''
            print '*** Bumper Driven Reflex: LEFT AND RIGHT BUMPER wait... ***'
            # time.sleep(1.0)
            return 'ts_stop'
        else:
            print ''
            print '*** InfraRed Driven Reflex: IR wait... ***'
            #time.sleep(1.0)
            return 'ts_stop'
            
    # Translates a sonar driven choice module tag back into a CinBrain number
    # Should match the inverse CinBrain -> module tag translation defined above
    def get_mvtreq_to_actnum_translation(self, action_tag):
        
        if action_tag == 'stop':
            return 0
        elif action_tag == 'left':
            return 1
        elif action_tag == 'right':
            return 2
        elif action_tag == 'forward':
            return 3
        elif action_tag == 'backward':
            return 4
        elif action_tag == 'ts_stop':
            return 5
##        elif action_tag == 'left_and_forward':
##            return 6
##        elif action_tag == 'right_and_forward':
##            return 7
##        elif action_tag == 'backward_and_turn_right':
##            return 8
##        elif action_tag == 'backward_and_turn_left':
##            return 9
        else:
            return 0
        

###############################
# Generic Math and List Utilities...

def mean_vector(v1, v2):
    v3 = []
    if len(v1) == len(v2):
        for i in range(len(v1)):
            v3.append(int(0.7 * v1[i] + 0.3 * v2[i]))
    return v3

def dif_binary_coding(v1, v2, id):
    # v1 is list of mean values, v2 list of current values
    v3 = []
    if len(v1) == len(v2):
        for i in range(len(v1)):
            # print id, v1[i], v2[i]
            if 0.7 * v1[i] > v2[i] and id == 'dec': # fast decrease of current value
                v3.append(int(1))
            elif v1[i] < 0.7 * v2[i] and id == 'inc': # fast increase of current value
                v3.append(int(1))
            else:
                v3.append(int(0))
    return v3
            
def no_dup_append(list1,b):
    if b not in list1:
        list1.append(b)


