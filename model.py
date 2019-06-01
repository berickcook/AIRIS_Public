import numpy as np
import heapq
import re
import sys
import copy
from other_useful_functions import *


class Model(object):

    def __init__(self, vis_env=None, aux_env=None,
                 prev_model=None, prev_model_index=None):

        # id for this model
        self.id = id(self)  # id() makes unique integer id
        # https://stackoverflow.com/questions/1045344/how-do-you-create-an-incremental-id-in-a-python-class

        self.focus_value = None  # least frequent value of the values that changed from the prior to posterior environment
        self.focus_pos = None  # (x, y) position of focus value (if focus value is a visual input)
        self.focus_index = None  # index of focus value (if focus value is an auxiliary input)
        self.focus_value_is_aux = None  # flag if the focus_value is an aux input or not

        # index of model that generated this model
        self.previous_model_index = prev_model_index
        self.previous_action = None
        self.previous_output = None

        self.best_conditions = []
        self.best_condition_dif = None
        self.best_condition_id = None
        self.best_condition_path = None
        self.source_condition_path = None
        self.depth = 0

        # same as vis_change and aux_change (not in model)
        self.predicted_vis_change = []  # [(x, y, prior_val, posterior_val)... ]
        self.predicted_aux_change = []  # [(i, prior_val, posterior_val)... ]

        if prev_model:
            self.initialize_from_model(prev_model)
        else:
            self.initialize_from_env(vis_env, aux_env)

    def initialize_from_env(self, vis_env, aux_env):

        # visual and non-visual inputs of this model
        self.vis_env = copy.deepcopy(vis_env)
        self.aux_env = copy.deepcopy(aux_env)

        # tally of how many of a particular visual subsymbolic input value
        # is in this model. (used to determine focus value)
        # In the puzzle game it counts how many walls, empty spaces, characters, etc.
        self.vis_count = {}

        # list of different inputs its ever seen since birth
        self.vis_count_list = []

        # dictionary of different subsymbolic visual input values
        # key: subsymoblic input value
        # value: list of position tuples of locations of said subsymbolic input key
        self.vis_count_pos = {}

        # fill self.vis_count with the frequency of input values in this vis_env
        # and append any never seen before values
        # fill and self.vis_count_list with the values never seen before
        for pos, val in np.ndenumerate(self.vis_env):
            try:
                self.vis_count[val] += 1
                self.vis_count_pos[val].append(pos)
            except KeyError:
                self.vis_count[val] = 1
                self.vis_count_pos[val] = [pos]
                if val not in self.vis_count_list:
                    self.vis_count_list.append(val)

        # heap (specifically a min-heap) of different sub-symbolic input values
        # key: count,  value: subsymbolic input value
        self.vis_count_heap = list(map(lambda x: (x[1], x[0]),
                                       list(self.vis_count.items())))
        heapq.heapify(self.vis_count_heap)

        # distance of the goal value in
        # this model's vis_env to the airis's goal source value
        self.compare = None

    def initialize_from_model(self, model):

        # visual and non-visual inputs of this model
        self.vis_env = copy.deepcopy(model.vis_env)
        self.aux_env = copy.deepcopy(model.aux_env)

        # copy the focus_value position from the source models
        self.focus_pos = copy.deepcopy(model.focus_pos)
        self.focus_value = copy.deepcopy(model.focus_value)
        self.focus_value_is_aux = copy.deepcopy(model.focus_value_is_aux)
        self.focus_index = copy.deepcopy(model.focus_index)

        # tally of how many of a particular visual subsymbolic input value
        # is in this model. (used to determine focus value)
        # In the puzzle game it counts how many walls, empty spaces, characters, etc.
        self.vis_count = copy.deepcopy(model.vis_count)

        # list of different inputs its ever seen since birth
        self.vis_count_list = copy.deepcopy(model.vis_count_list)

        # dictionary of different subsymbolic visual input values
        # key: subsymoblic input value
        # value: list of position tuples of locations of said subsymbolic input key
        self.vis_count_pos = copy.deepcopy(model.vis_count_pos)

        # heap (specifically a min-heap) of different sub-symbolic input values
        # key: count,  value: subsymbolic input value
        self.vis_count_heap = copy.deepcopy(model.vis_count_heap)

        # distance of the goal value in
        # this model's vis_env to the airis's goal source value
        self.compare = copy.deepcopy(model.compare)

    def update_vis_value(self, posterior_val, value_pos, focus_value=None):

        # things to modify:
        # vis_env
        # vis_count
        # vis_count_list
        # vis_count_heap
        # vis_count_pos

        # get the actual prior for the focus index
        x, y = value_pos
        prior_val = self.vis_env[x][y]

        # decrement the prior's count
        self.vis_count[prior_val] -= 1
        if self.vis_count[prior_val] == 0:
            del self.vis_count[prior_val]
            self.vis_count_list.remove(prior_val)
            self.vis_count_heap.remove((1, prior_val))
        else:
            for i, (count, val) in enumerate(self.vis_count_heap):
                if val == prior_val:
                    self.vis_count_heap[i] = (count - 1, val)
                    break
        heapq.heapify(self.vis_count_heap)

        # remove this pos from vis_count_pos
        self.vis_count_pos[prior_val].remove((x, y))
        if self.vis_count_pos[prior_val] == []:
            del self.vis_count_pos[prior_val]

        # set the value to the posterior
        self.vis_env[x][y] = posterior_val

        # increment the posterior's count
        try:
            self.vis_count[posterior_val] += 1
        except KeyError:
            self.vis_count[posterior_val] = 1
            self.vis_count_list.append(posterior_val)
            self.vis_count_heap.append((0, posterior_val))

        # increment the posterior's count in the heap
        for i, (count, val) in enumerate(self.vis_count_heap):
            if val == posterior_val:
                self.vis_count_heap[i] = (count + 1, val)
                break
        heapq.heapify(self.vis_count_heap)

        # add the posterior value to the model's vis_count_pos
        try:
            self.vis_count_pos[posterior_val].append((x, y))
        except KeyError:
            self.vis_count_pos[posterior_val] = [(x, y)]

        #if the posterior value is the focus_value, return the new position of the focus_value
        if posterior_val == focus_value:
            self.focus_pos = x, y

        self.predicted_vis_change.append((x, y, prior_val, posterior_val))

    def update_aux_value(self, posterior_val, focus_index):

        # things to modify:
        # aux_env
        # predicted_aux_change

        # get the actual prior and predicted posterior for the focus index
        prior_val = self.aux_env[focus_index]

        # set the value to the posterior
        self.aux_env[focus_index] = posterior_val

        self.predicted_aux_change.append((focus_index, prior_val, posterior_val))

    def print_model(self, title=None,
                    indent=DEFAULT_INDENT,
                    num_indents=0,
                    vis_env=False, aux_env=False,
                    vis_count_heap=False,
                    compare=False,
                    focus=False,
                    pred_vis_chng=False,
                    pred_aux_chng=False,
                    best_condition=False,
                    new_line_start=False,
                    new_line_end=False,
                    draw_line=DEFAULT_DRAW_LINE):

        if title:
            pprint(title, indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, draw_line=draw_line)
        pprint('size: %s' % sys.getsizeof(self),
            indent=indent, num_indents=num_indents + 1)


        pprint('id: %s' % self.id,
            indent=indent, num_indents=num_indents + 1)

        if vis_env:
            print_vis_env(self.vis_env, title='vis env:',
                indent=indent, num_indents=num_indents + 1)

        if aux_env:
            print_aux_env(self.aux_env, title='aux_env:',
                indent=indent, num_indents=num_indents + 1)

        if vis_count_heap:
            pprint('vis count heap:', indent=indent, num_indents=num_indents + 1)
            for count, value in self.vis_count_heap:
                pprint('  %d  \tinstances of\t%s' % (count, int(value)),
                    indent=indent, num_indents=num_indents + 1)

        if compare:
            pprint('compare (distance between goal values):\t%s' % self.compare,
                indent=indent, num_indents=num_indents + 1)

        if focus:
            pprint('focus value:',
                indent=indent, num_indents=num_indents + 1)
            pprint('    (least frequent value of the values that changed',
                indent=indent, num_indents=num_indents + 2)
            pprint('     from the prior to posterior environment)',
                indent=indent, num_indents=num_indents + 2)
            pprint('value:      %s' % self.focus_value,
                indent=indent, num_indents=num_indents + 2)
            pprint('pos:        %s' % self.focus_pos,
                indent=indent, num_indents=num_indents + 2)
            pprint('index:      %s' % self.focus_index,
                indent=indent, num_indents=num_indents + 2)
            pprint('is_aux:     %s' % self.focus_value_is_aux,
                indent=indent, num_indents=num_indents + 2)

        if pred_vis_chng:
            pprint('Predicted Visual Changes:\t%s' % self.predicted_vis_change,
                indent=indent, num_indents=num_indents + 1)

        if pred_aux_chng:
            pprint('Predicted Auxiliary Changes:\t%s' % self.predicted_vis_change,
                indent=indent, num_indents=num_indents + 1)

        if best_condition:
            pprint('Best Condition:', indent=indent, num_indents=num_indents + 1)
            pprint('dif:            %s' % self.best_condition_dif, indent=indent, num_indents=num_indents + 2)
            pprint('id:             %s' % self.best_condition_id, indent=indent, num_indents=num_indents + 2)
            pprint('focus value:    %s' % self.focus_value, indent=indent, num_indents=num_indents + 2,
                new_line_end=new_line_end, draw_line=draw_line)
            # also print out which part of the knowledge airis is
            # using to make a prediction and plans (uses predictions to make plans)
