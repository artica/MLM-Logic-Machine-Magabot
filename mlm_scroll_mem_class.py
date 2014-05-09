## ScrollingMemory class
##
## Attributes are:
## 1. an internal list holding the cinematic data:
##      self.memory_list
## 2. the maximum size of that list:
##      self.max_size
##
## Only the method
##      continuation(self, pattern_list, horizon)
##   produces an output, i.e. the continuation of a matching pattern_list.
##
## The methods
##      record(self, item)
##  and
##      move_item(self, item, displacement, discard_flag)
##  simply update the self.memory_list, according to the input data.
##   



import random

import mlm_util # bounded_add, bidx, bitem, list_unify

#############################################################################

class ScrollingMemory(object):
    '''A Finite Sized List of Frames or Scenes'''
    
    def __init__(self, max_size):
        # a negative max_size means a practically unbound memory
        if max_size > 0:
            self.max_size = max_size
        else:
            self.max_size = 9999
        self.memory_list = []

    # records a new item in top of self.memory_list
    def record(self, item):
        # insert on top (slower than append!)
        self.memory_list.insert(0,item)
        # trim the bottom of the list
        if len(self.memory_list) >= self.max_size:
            self.memory_list = self.memory_list[0:self.max_size]

    # move an item found in the memory_list
    # discard flag set discards items sent to the very bottom of self.memory_list
    def move_item(self, item, displacement, discard_flag):
        if item in self.memory_list:
            # remove item
            item_index = self.memory_list.index(item)
            self.memory_list.remove(item)
            # calculate displaced location within bounds
            new_item_index = mlm_util.bounded_add(item_index,displacement,
                                         0,len(self.memory_list))
            # if anchor_index is smaller than max_size, do reinsert item
            if new_item_index + 1 < self.max_size:
                self.memory_list.insert(new_item_index,item)
            # if anchor_index is equal or greater than max_size, check discard_flag
            elif discard_flag < 1:
                self.memory_list.insert(new_item_index,item)
                
    # locates a continuation for a pattern in memory_list, up to horizon
    # right now its time oriented to the left
    #    i.e. self.memory_list[0] is the most recent item
    def continuation(self, pattern_list, horizon):
        len_pattern = len(pattern_list)
        memory_list = self.memory_list
            # ... just for speed sake, use this local variable in the while loop
        len_memory_list = len(self.memory_list)
        found = False
        anchor_index = horizon
        search_result = []
        while (not(found) and anchor_index <= (len_memory_list - len_pattern)
               and len_pattern > 0 and len_memory_list > 0):
            bottom_anchor_index = anchor_index + len_pattern
            # here we use a simple unification criterion
            search_result = (mlm_util.list_unify
                             (pattern_list,
                              memory_list[anchor_index:bottom_anchor_index])
                             )
            if search_result[0]:        # Holds unification Success: True or False
                found = True
                return [memory_list[(anchor_index - horizon):anchor_index],
                            # ... this is the continuation to the left
                        memory_list[anchor_index:bottom_anchor_index],
                            # ... this is the located pattern that satisfied pattern_list
                        memory_list]
                            # ... this is the list that was successfully searched
            anchor_index += 2
        return [[],[],[]]

