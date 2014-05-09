import random
            

############################################
# MLM useful functions !!!!DO NOT CHANGE!!!
############################################


# 
# *** biased 0,1 binary distribution function
# bias is float between 0 and 1
def biased_random(bias, number_of_variables):
    rand = random.random()
    if rand < bias:
        return 0
    else:
        rand_non_zero_state = int(1+(number_of_variables-1)*random.random())
        return rand_non_zero_state

#
# *** bounded addition function
# needed for mlm memories index updatings

def bounded_add(n,m,min,max):
    sum = n + m
    if sum < min:
        return min
    if sum > max:
        return max
    return sum

#### LIST TOOLS functions

### take every even index element from a list of sm elements -> the s list
def take_even(source_list):
    len_source = len(source_list)
    if len_source % 2 == 0:
        result_list = []
        i = 0
        while i < len_source:
            result_list.append(source_list[i])
            i += 2
        return result_list
    else:
        return []
            
### take every odd index element from a list of pairs sm -> the m list
def take_odd(source_list):
    len_source = len(source_list)
    if len_source % 2 == 0:
        result_list = []
        i = 1
        while i < len_source:
            result_list.append(source_list[i])
            i += 2
        return result_list
    else:
        return []

            
### shortcut for bottom index of a list
def bidx(my_list):
    return len(my_list)-1

### shortcut for bottom item of a list
def bitem(my_list):
    return my_list[bidx(my_list)]

### turns a list into a context pattern coded with complex numbers
def build_context(integer_list):
    context_list = []
    for i in range(len(integer_list)):
        c = complex(integer_list[i],0)
        context_list.append(c)
    return context_list 
        
### turns a list into a interrogation pattern coded with complex numbers
def build_interrogation(integer_list):
    interrogation_list = []
    for i in range(len(integer_list)):
        c = complex(integer_list[i],1)
        interrogation_list.append(c)
    return interrogation_list 

### unify lists
##      the pattern list is made of complex numbers
##      n.imag == 0 is a context
##      n.imag == 1 is a interrogation
##      n.real are the values to be compared to the target list
def list_unify(pattern_list, target_list):

##  No need to check lengths: equal by construction in mlm_scroll_mem_class.continuation
##    if not len(pattern_list) == len(target_list):
##        return [False, []]
##    else:
    
    unified_list = []
    unified = True
    i = 0
    while unified and i < len(pattern_list):
    # for i in range(len(pattern_list)):
        if pattern_list[i].imag > 0:        # interrogation, get target value
            unified_list.append(target_list[i])
            i += 1
        elif pattern_list[i].real == target_list[i]:   # context, and value match
            unified_list.append(target_list[i])
            i += 1
        else:
            unified = False
            unified_list = []
    return [unified, unified_list]

## Evaluate number of different items in list
def eval_number_of_w_states(mylist):
    list_of_states = []
    for i in range(len(mylist)):
        if not mylist[i] in list_of_states:
            list_of_states.append(mylist[i])
    number_of_states = len(list_of_states)
    #return [number_of_states, list_of_states]
    return number_of_states
                
            
# compares two [s,m]
def similar_pred_know(prediction, knowledge,
                      wanted_world_states, feared_world_states,
                      wanted_world_states2, feared_world_states2):       
    s_pred = prediction[0]
    s_know = knowledge[0]
    m_pred = prediction[1]
    m_know = knowledge[1]
    if (s_pred == s_know
        and
        m_pred == m_know
        ):
        return True
    
    elif (s_pred in wanted_world_states
        and
        s_know in wanted_world_states
        and
        m_pred == m_know
        ):
        return True

    elif (s_pred in wanted_world_states2
        and
        s_know in wanted_world_states2
        and
        m_pred == m_know
        ):
        return True

    elif (s_pred in feared_world_states
          and
          s_know in feared_world_states
          and
          m_pred == m_know
          ):
        return True

    elif (s_pred in feared_world_states2
          and
          s_know in feared_world_states2
          and
          m_pred == m_know
          ):
        return True

    elif (not(s_pred in feared_world_states2
              or
              s_pred in feared_world_states
              or
              s_pred in wanted_world_states2
              or
              s_pred in wanted_world_states)    # s_pred neutral
          and
          not(s_know in feared_world_states2
              or
              s_know in feared_world_states
              or
              s_know in wanted_world_states2
              or
              s_know in wanted_world_states)   # s_know neutral
          and
          m_pred == m_know
          ):
        return True

    else:
        return False
    


###===========================================
### Internal module tests

##def this_module_tests():
##    l = [i+1 for i in range(15)]
##    print 'The list', l
##    print 'Bottom Index', bidx(l), 'because it starts at 0'
##    print 'Bottom Item', bitem(l)


##this_module_tests()


##ctxt = build_context([1,2,3])
##interr = build_interrogation([1,2,3])
##print ctxt
##print interr
##ctxt.extend(interr)
##print ctxt
##print list_unify(ctxt,
##                 [1,3,3,1,2,3])
##

## print eval_number_of_w_states([1,2,3,4,5,6,1,2,3,4,5,6,7,8,1,2,3,4,5,12,13,14])

##print take_even([1,2,3,4,5,6,7,8,9,10,11,12,13,14])
##print take_odd([1,2,3,4,5,6,7,8,9,10,11,12,13,14])


##print local_score([1, -1, 0, 0, 0, -1, 1, 0], [0], [])
