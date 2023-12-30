from collections import Counter, defaultdict
from copy import deepcopy
import numpy as np
import heapq

class State(object):

    def __init__(self, env1, env2, env2indexes, act, prev, step, last_pos_change_2d, prev_action):
        self.input_1D = env1.copy()
        self.input_2D = deepcopy(env2)
        self.action = act
        self.prev_state = prev
        self.prev_action = prev_action
        self.change_1D = []
        self.change_2D = []
        self.uncertainty = 0
        self.step = step
        self.input_2D_idx = deepcopy(env2indexes)
        self.input_2D_heap = []
        for key in self.input_2D_idx.keys():
            heapq.heappush(self.input_2D_heap, (len(self.input_2D_idx[key]), key))
        self.applied_rules = dict()
        self.applied_exceptions = dict()
        self.applied_exception_ids = set()
        self.applied_rule_ids = set()
        self.anti_goal = False
        self.last_1D = []
        self.last_2D = []
        self.compare = None
        self.confidence = None
        self.last_pos_change_2d = last_pos_change_2d
        self.no_change = False
        self.bad_rules = []
        self.check_set = set()

    def hash(self):
        return str(self.input_1D), str(self.input_2D)

    def heap(self):
        self.input_2D_heap = []
        self.input_2D_idx = defaultdict(list)
        for pos, val in np.ndenumerate(self.input_2D):
            self.input_2D_idx[val].append(pos)

        for key in self.input_2D_idx.keys():
            heapq.heappush(self.input_2D_heap, (len(self.input_2D_idx[key]), key))
