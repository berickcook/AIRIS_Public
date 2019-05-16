import sys
import copy
import numpy as np
import heapq
import json
import random
from operator import itemgetter
from datetime import datetime
from model import Model
from other_useful_functions import *


class AIRIS(object):

    def __init__(self, vis_env, aux_env, action_space, action_output_list):

        # clear logfile
        if DEBUG_WITH_LOGFILE:
            open(DEBUG_LOGFILE_PATH, 'w').close()

        pprint('initializing AIRIS ...', new_line_start=True, draw_line=False)
        start_time = datetime.now()

        # visual and non-visual (auxiliary)
        # environment BEFORE the action is taken
        self.prior_vis_env = np.array(vis_env, dtype=np.float32)
        self.prior_aux_env = np.array(aux_env, dtype=np.float32)

        # visual and non-visual
        # environment AFTER the action is taken
        self.posterior_vis_env = np.array(vis_env, dtype=np.float32)
        self.posterior_aux_env = np.array(aux_env, dtype=np.float32)

        # load existing knowledge or create a new knowledge dictionary
        try:
            self.load_knowledge()
            self.condition_id = self.knowledge['last condition id'] + 1
        except:
            self.knowledge = {}
            self.knowledge['action set'] = []
            self.knowledge['focus set'] = []
            self.condition_id = 0  # id of condition in the knowledge

        # list of all models AIRIS has made
        self.current_model_index = None
        self.models = []

        # set of all unique visual and non-visual values ever seen since birth
        self.vis_global_set = set()
        self.focus_global_set = set()
        self.not_focus_global_set = set()
        self.aux_global_set = set()

        # list of all possible actions AIRIS can take
        self.action_space = action_space
        # output range of each action [min, max, increment size]
        self.action_output_list = action_output_list
        self.action_plan = []  # sequence of planned actions
        self.action_plan_depth_limit = 50

        self.goal_type_default = 'Random'
        self.goal_type = 'Random'
        self.goal_action = None
        self.goal_output = None
        self.goal_source = {
            'value': None,
            'x': None,  # x of goal value relative to focus value
            'y': None,  # y of goal value relative to focus value
            'i': None  # i is for if the goal_source is an auxiliary input
        }
        self.goal_condition = None
        self.goal_value = None

        # lists of visual and auxiliary changes in the env from prior to posterior
        self.vis_change_list = []
        self.aux_change_list = []
        self.aux_change_list_prev = []
        self.vis_change_list_prev = []

        self.posterior_focus_value = None  #
        self.vis_change_index = None  # index of the visual change we're focusing on
        self.aux_change_index = None

        # working prediction(s) of what the visual input will be after a given action and visual and aux inputs
        self.env_count = {}
        self.env_count_list = []

        self.worst_set = set()
        self.display_hold = False
        self.display_plan = [0]

        pprint('initialization complete. duration: %s' % (datetime.now() - start_time))

    def print_mind(self, indent=DEFAULT_INDENT, num_indents=0,
                   new_line_start=False, new_line_end=False,
                   draw_line=DEFAULT_DRAW_LINE,
                   prior=True, post=True, focus_value=True,
                   models=True, knowledge=True, best_condition_id=True,
                   global_sets=True, current_model_index=True,
                   goal=True, action_plan=True, change_lists=True):

        # print the environment variables of AIRIS's mind

        if DEBUG_WITH_CONSOLE:

            pprint('/--------------------------------------------------------\\')

            if prior:
                pprint('ACTION PRIOR:')
                print_vis_env(self.prior_vis_env, title='Visual Environment:')
                pprint('Auxiliary Environment')
                pprint(self.prior_aux_env.astype(int))

            if post:
                pprint('\nACTION POSTERIOR:')
                print_vis_env(self.posterior_vis_env, title='Visual Environment:')
                pprint('Auxiliary Environment')
                pprint(self.posterior_aux_env.astype(int))

                if change_lists:
                    self.print_change_lists()

            if focus_value:
                pprint('focus_value:\t\t\t%s' % self.models[self.current_model_index].focus_value)

            if global_sets:
                self.print_global_sets()

            if current_model_index:
                pprint('Current Model Index:\t\t%s' % self.current_model_index)

            if models:
                self.print_models()

            if knowledge:
                pprint('Knowledge:')
                pprint(self.knowledge)
                self.print_knowledge(indent=indent, num_indents=num_indents, draw_line=draw_line)
                # pass  # tbd ... how do we print this in a concise way? this might be where a gui comes in handy

            if goal:
                pprint('Goal Type:\t%s' % self.goal_type)
                pprint('Goal Action:\t%s' % self.goal_action)
                pprint('Goal Output:\t%s' % self.goal_output)
                self.print_goal_source()

            if action_plan:
                pprint('Action Plan:\n%d actions' % len(self.action_plan))
                for goal_action, goal_output in self.action_plan:
                    pprint(goal_action, goal_output)

            pprint('\\--------------------------------------------------------/\n')

    def print_models(self, new_line_start=False, new_line_end=False):
        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:
            if new_line_start:
                print()
            print('\nModels:')
            print('num models = %s' % len(self.models))
            for index, model in enumerate(self.models):
                print('Model %d:' % index)
                model.print_model(vis_env=True, aux_env=True,
                                    compare=True, best_condition=True)
            if new_line_end:
                print()

    def print_global_sets(self, indent=DEFAULT_INDENT, num_indents=0,
                          new_line_start=False, new_line_end=False,
                          draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Global Sets:', indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, draw_line=draw_line)

            pprint('all visual values ever seen:   \t%s' %
                np.array(list(self.vis_global_set)).astype(int),
                indent=indent, num_indents=num_indents + 1)

            pprint('all focus values ever seen:   \t%s' %
                np.array(list(self.focus_global_set)).astype(int),
                indent=indent, num_indents=num_indents + 1)

            pprint('all auxiliary values ever seen:\t%s' %
                np.array(list(self.aux_global_set)).astype(int),
                indent=indent, num_indents=num_indents + 1,
                new_line_end=new_line_end, draw_line=draw_line)

    def print_goal_source(self, indent=DEFAULT_INDENT, num_indents=0,
                          new_line_start=False, new_line_end=False,
                          draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Goal Source:',
                indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, draw_line=draw_line)

            pprint('Source value:\t%s' % self.goal_source['value'],
                indent=indent, num_indents=num_indents + 1)
            pprint('x:    \t%s' % self.goal_source['x'],
                indent=indent, num_indents=num_indents + 1)
            pprint('y:    \t%s' % self.goal_source['y'],
                indent=indent, num_indents=num_indents + 1)
            pprint('i:    \t%s' % self.goal_source['i'],
                indent=indent, num_indents=num_indents + 1)
            pprint('Goal value:    \t%s' % self.goal_value,
                indent=indent, num_indents=num_indents + 1,
                new_line_end=new_line_end, draw_line=draw_line)

    def print_change_lists(self, indent=DEFAULT_INDENT, num_indents=0,
                           new_line_start=False, new_line_end=False,
                           draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Visual Change List:   \t\t%s' % self.vis_change_list,
                indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, draw_line=draw_line)

            pprint('Auxiliary Change List:\t\t%s' % self.aux_change_list,
                indent=indent, num_indents=num_indents,
                new_line_end=new_line_end, draw_line=draw_line)

    def print_condition_id(self, indent=DEFAULT_INDENT, num_indents=0,
                           new_line_start=False, new_line_end=False,
                           draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Condition ID:\t\t%s' % self.condition_id,
                indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, new_line_end=new_line_end,
                draw_line=draw_line)

    def print_knowledge(self, indent=DEFAULT_INDENT, num_indents=0,
                         new_line_start=False, new_line_end=False,
                         draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Knowledge:', indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, draw_line=draw_line)
            pprint('size: %s' % sys.getsizeof(self.knowledge),
                indent=indent, num_indents=num_indents + 1)

            # action/output/focus_value/condition_id
            # focus_value/condition_id/[data]

            if self.knowledge:
                pprint('Actions:', indent=indent, num_indents=num_indents + 1)
                for action in self.knowledge['action set']:
                    action = str(action)
                    action_path = action
                    try:
                        action_outputs = self.knowledge[action_path]
                        pprint(action, indent=indent, num_indents=num_indents + 2)
                        pprint('Outputs:', indent=indent, num_indents=num_indents + 3)
                        for output in action_outputs:
                            output = str(output)
                            output_path = action_path + '/' + output
                            try:
                                condition_focus_values = self.knowledge[output_path]
                                pprint(output, indent=indent, num_indents=num_indents + 4)
                                pprint('Condition Focus Values:', indent=indent, num_indents=num_indents + 5)
                                for condition_focus_value in condition_focus_values:
                                    condition_focus_value = str(condition_focus_value)
                                    focus_path = output_path + '/' + condition_focus_value
                                    try:
                                        condition_ids = self.knowledge[focus_path]
                                        pprint(condition_focus_value, indent=indent, num_indents=num_indents + 6)
                                        pprint('Condition IDs:', indent=indent, num_indents=num_indents + 7)
                                        for condition_id in condition_ids:
                                            condition_id = str(condition_id)
                                    except KeyError:
                                        pass
                            except KeyError:
                                pass
                    except KeyError:
                        pass

                pprint('Focus Values:', indent=indent, num_indents=num_indents + 1)
                for condition_focus_value in self.knowledge['focus set']:
                    focus = str(condition_focus_value)
                    focus_path = focus
                    try:
                        condition_ids = self.knowledge[focus_path]
                        pprint(focus, indent=indent, num_indents=num_indents + 2)
                        pprint('Condition IDs:', indent=indent, num_indents=num_indents + 3)
                        for condition_id in condition_ids:
                            condition_id = str(condition_id)
                            id_path = focus_path + '/' + condition_id
                            try:
                                # path + '/posterior_val' is used b/c all conditions have one
                                id_exists = self.knowledge[id_path + '/posterior_val']
                                pprint(condition_id, indent=indent, num_indents=num_indents + 4)
                            except:
                                continue  # don't search for knowledge of this condition_id if it doesnt exist
                            try:
                                pprint('rel_abs:        %s' % self.knowledge[id_path + '/rel_abs'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('posterior_val:        %s' % self.knowledge[id_path + '/posterior_val'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                x, y = self.knowledge[id_path + '/focus_x'], self.knowledge[id_path + '/focus_y']
                                pprint('(focus_x, focus_y):   (%s, %s)' % (x, y), indent=indent, num_indents=num_indents + 9)
                            except KeyError:
                                pass
                            try:
                                pprint('focus_i:              %s' % self.knowledge[id_path + '/focus_i'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('action_cause:              %s' % self.knowledge[id_path + '/action_cause'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('aux_cause:              %s' % self.knowledge[id_path + '/aux_cause'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('aux_prev_cause:              %s' % self.knowledge[id_path + '/aux_prev_cause'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('aux_ref:              %s' % self.knowledge[id_path + '/aux_ref'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('aux_data:             %s' % self.knowledge[id_path + '/aux_data'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('vis_cause:              %s' % self.knowledge[id_path + '/vis_cause'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('vis_prev_cause:              %s' % self.knowledge[id_path + '/vis_prev_cause'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('vis_ref:              %s' % self.knowledge[id_path + '/vis_ref'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                print_vis_env(self.knowledge[id_path + '/vis_data'], title='vis_data', indent=indent,
                                              num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                pprint('post_aux_data:             %s' % self.knowledge[id_path + '/post_aux_data'], indent=indent,
                                       num_indents=num_indents + 5)
                            except KeyError:
                                pass
                            try:
                                print_vis_env(self.knowledge[id_path + '/post_vis_data'], title='post_vis_data', indent=indent,
                                              num_indents=num_indents + 5)
                            except KeyError:
                                pass
                    except KeyError:
                        pass
            else:
                pprint('Empty', indent=indent, num_indents=num_indents + 1)

            # bug: the line isn't drawn regardless, buts not a big deal
            if new_line_end:
                pprint('', indent=indent, num_indents=num_indents, draw_line=draw_line)

    def print_knowledge_dictionary_raw(self, indent=DEFAULT_INDENT, num_indents=0,
                           new_line_start=False, new_line_end=False,
                           draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Knowledge:', indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, draw_line=draw_line)

            if self.knowledge:
                first = True
                for k, v in self.knowledge.items():

                    if first:
                        first = False
                        pprint('key:     %s' % k, indent=indent, num_indents=num_indents + 1)
                    else:
                        pprint('key:     %s' % k, indent=indent,
                            num_indents=num_indents + 1, new_line_start=True, draw_line=False)

                    if isinstance(v, np.ndarray) and v.ndim == 2:
                        pprint('value:', indent=indent, num_indents=num_indents + 1)
                        print_vis_env(v, indent=indent, num_indents=num_indents + 1)
                    else:
                        pprint('value:   %s' % v, indent=indent, num_indents=num_indents + 1)

            else:
                pprint('Empty', indent=indent, num_indents=num_indents + 1)

    def print_focus_value(self, indent=DEFAULT_INDENT, num_indents=0,
                          new_line_start=False, new_line_end=False,
                          draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Focus Value:\t\t%s' % self.models[self.current_model_index].focus_value,
                indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, new_line_end=new_line_end,
                draw_line=draw_line)

    def print_goal_condition(self, indent=DEFAULT_INDENT, num_indents=0,
                          new_line_start=False, new_line_end=False,
                          draw_line=DEFAULT_DRAW_LINE):

        if DEBUG_WITH_CONSOLE or DEBUG_WITH_LOGFILE:

            pprint('Goal Condition:\t\t%s' % self.goal_condition,
                indent=indent, num_indents=num_indents,
                new_line_start=new_line_start, new_line_end=new_line_end,
                draw_line=draw_line)

    def capture_input(self, vis_env, aux_env, action, prior=True, num_indents=0):

        # main loop of AIRIS

        pprint('capturing input ...', num_indents=num_indents,
            new_line_start=True)
        start_time = datetime.now()

        # if the vis_env and aux_env being input is
        # prior to the action being taken
        if prior:

            # save this environment
            pprint('storing env before the action (prior) ...',
                num_indents=num_indents + 1, new_line_start=True)
            self.prior_vis_env = np.array(vis_env, dtype=np.float32)
            self.prior_aux_env = np.array(aux_env, dtype=np.float32)
            print_vis_env(self.prior_vis_env, title='self.prior_vis_env:', num_indents=num_indents + 2)
            print_aux_env(self.prior_aux_env, title='self.prior_aux_env:', num_indents=num_indents + 2)

            # if its not made a plan yet
            while not self.action_plan:
                pprint('no plan has been made yet',
                    num_indents=num_indents + 1, new_line_start=True)
                pprint('self.action_plan:\t%s' % self.action_plan,
                    num_indents=num_indents + 2)

                # clear old models, create a new model of this environment
                # and set the current model index to that model
                self.current_model_index = None
                for i in self.models:
                    del i

                self.current_model_index = self.create_model(-1, num_indents=num_indents + 2)

                # why is this a while loop ................................
                pprint('while there is no plan ...',
                    num_indents=num_indents + 2, new_line_start=True)

                self.store_worst_index = None
                self.store_worst = None
                # not really sure what this does .......................
                self.set_goal(self.goal_type, num_indents=num_indents + 3)

                # make a plan to achieve the set goal
                self.make_plan(action, num_indents=num_indents + 3)
                self.display_hold = True

            # get the action at the end of the list
            if self.store_worst_index != None and len(self.action_plan) == 1:
                pprint('Adding to worst set: '+str(self.store_worst),
                    num_indents=num_indents + 1, new_line_start=True)
                self.worst_set.add(self.store_worst)

            if self.goal_type == 'Observe':
                print('Observed: ',self.action_plan)

            self.display_plan = [0]
            hold_plan = copy.deepcopy(self.action_plan)
            while hold_plan:
                self.display_plan.append(hold_plan.pop()[2])

            pprint('popping the next action/output off the end of the plan ...',
                num_indents=num_indents + 1, new_line_start=True)
            action, output, predicted_model_index = self.action_plan.pop()

            self.current_model_index = predicted_model_index

            pprint('(action, output, predicted_model_index) = (%s, %s, %s)'
                % (action, output, predicted_model_index),
                num_indents=num_indents + 1)

            pprint('do the action in the game', num_indents=1, new_line_start=True)
            pprint('input captured. duration: %s' % (datetime.now() - start_time),
                new_line_start=True, draw_line=True)

            return (action, self.models[self.current_model_index].predicted_vis_change, self.models[self.current_model_index].predicted_aux_change)

        # else, the vis_env and aux_env being input is posterior
        # to the action that was taken
        else:

            # save this environment
            pprint('storing env after the action (posterior) ...',
                num_indents=num_indents + 1, new_line_start=True)
            self.posterior_vis_env = np.array(vis_env, dtype=np.float32)
            self.posterior_aux_env = np.array(aux_env, dtype=np.float32)
            print_vis_env(self.posterior_vis_env, title='self.posterior_vis_env:', num_indents=num_indents + 2)
            print_aux_env(self.posterior_aux_env, title='self.posterior_aux_env:', num_indents=num_indents + 2)

            # determine if our prediction was correct
            bad_prediction = self.find_changes(num_indents=num_indents + 1)

            # if the condition was incorrect, update the knowledge
            if bad_prediction or (self.goal_type == 'New Action' and not self.action_plan):
                self.create_condition(action, '1', num_indents=num_indents + 1)

            # self.print_mind(prior=False)

            pprint('input captured. duration: %s' % (datetime.now() - start_time),
                new_line_start=True, draw_line=True)

    def create_model(self, from_model_index, num_indents=0):

        # creates a model and puts it at the end of the self.models list

        # for the 1st model
        if from_model_index < 0:

            pprint('creating a model from this environment ...',
                num_indents=num_indents, new_line_start=True)
            start_time = datetime.now()

            # create the model
            self.models = [Model(vis_env=self.prior_vis_env, aux_env=self.prior_aux_env)]
            self.models[0].print_model(title='Model 0:', vis_env=True, aux_env=True,
                vis_count_heap=True, compare=True, focus=True, best_condition=True, num_indents=num_indents + 1,
                new_line_start=True)

            # add any new inputs to the visual and non-visual global sets
            pprint('adding any new inputs to the visual and auxiliary global sets',
                num_indents=num_indents + 1, new_line_start=True)
            self.vis_global_set.update(set(self.prior_vis_env.flatten()))
            self.aux_global_set.update(set(self.prior_aux_env))

            self.print_global_sets(num_indents=num_indents + 1)

            focus_heap = copy.deepcopy(self.models[0].vis_count_heap)

            if self.focus_global_set:
                while focus_heap and self.models[0].focus_value == None:
                    if focus_heap[0][1] in self.focus_global_set:
                        self.models[0].focus_value = focus_heap[0][1]
                    else:
                        heapq.heappop(focus_heap)

                if self.models[0].focus_value == None:
                    not_focus_heap = copy.deepcopy(self.models[0].vis_count_heap)
                    while not_focus_heap and self.models[0].focus_value == None:
                        if not_focus_heap[0][1] not in self.not_focus_global_set:
                            self.models[0].focus_value = not_focus_heap[0][1]
                        else:
                            heapq.heappop(not_focus_heap)

            if self.models[0].focus_value == None:
                self.models[0].focus_value = self.models[0].vis_count_heap[0][1]

        else:  # for the rest of the models

            pprint('creating a model from model %s ...' % from_model_index,
                num_indents=num_indents, new_line_start=True)
            start_time = datetime.now()

            # put a copy of the current model at the end of the list of models
            self.models.append(
                Model(prev_model=self.models[from_model_index],
                      prev_model_index=from_model_index))

        pprint('updating self.current_model_index', num_indents=num_indents + 1,
            new_line_start=True)
        pprint('from:\t\t\t%s' % self.current_model_index, num_indents=num_indents + 2)
        pprint('to:  \t\t\t%s' % (len(self.models) - 1), num_indents=num_indents + 2)

        pprint('model created. duration: %s' % (datetime.now() - start_time),
            num_indents=num_indents, new_line_start=True, draw_line=True)
        return len(self.models) - 1

    def set_goal(self, goal_type, num_indents=0):

        # picks a random condition from a random action
        # grabs any other values that changed in that condition
        # it finds a value in a random condition in its knowledge
        # sets that value (or a value from its memory of all the values its ever seen)
        # to its goal value
        #
        # what is a condition
        #    a condition is inside the knowledge it is any memory of an event happening
        #    capture of the state of the world prior to some event happening

        self.goal_action = None
        self.goal_output = None
        self.goal_source = {
            'value': None,
            'x': None,  # x of goal value relative to focus value
            'y': None,  # y of goal value relative to focus value
            'i': None  # i is for if the goal_source is an auxiliary input
        }
        self.goal_condition = None
        self.goal_value = None

        pprint('setting a goal ...',
            num_indents=num_indents, new_line_start=True)
        start_time = datetime.now()

        goal_found = False
        model = self.models[self.current_model_index]
        no_conditions = False

        # pick a random action
        pprint('picking a random action/output ...', num_indents=num_indents + 1,
            new_line_start=True)
        action_index = random.choice(range(len(self.action_space)))
        self.goal_action = self.action_space[action_index]

        # pick a random output
        # # right now self.goal_output is inevitably going to be 1
        action_output = self.action_output_list[action_index]
        output_range = range(action_output[0], action_output[1], action_output[2])
        self.goal_output = str(random.choice(output_range))
        pprint('self.goal_action = %s' % self.goal_action, num_indents=num_indents + 2)
        pprint('self.goal_output = %s' % self.goal_output, num_indents=num_indents + 2)

        pprint('goal_type: %s' % self.goal_type,
            num_indents=num_indents + 1, new_line_start=True)

        if self.goal_type == 'Random':

            pprint('searching for knowledge of this action/output',
                num_indents=num_indents + 1, new_line_start=True, draw_line=False)

            # see if there's knowledge of this random action/output
            try:

                # knowledge_found will be the list of all the focus values
                # for that action/output pair
                path = str(self.goal_action) + '/' + str(self.goal_output)
                knowledge_found = copy.deepcopy(self.knowledge[path])
                knowledge_prune = []

                pprint('knowledge found.', num_indents=num_indents + 2)
                # set self.focus_pos to the pos of a focus_value in the current model
                model = self.models[self.current_model_index]  # current model

                # prune all knowledge found whose focus_value is not in model.vis_env_count_list
                pprint('Pruning found knowledge:', num_indents=num_indents + 2)
                for knowledge_focus in knowledge_found:
                    if knowledge_focus[0] != 'A':
                        if float(knowledge_focus) not in model.vis_count_list:
                            pprint('focus value ' + str(knowledge_focus) + ' not in visual count', num_indents=num_indents + 3)
                            knowledge_prune.append(knowledge_focus)

                for val in knowledge_prune:
                    knowledge_found.remove(val)

                knowledge_prune = []

                # prune all knowledge found whose focus value does not change and does not have /vis_ref
                for knowledge_focus in knowledge_found:
                    keep = False
                    for check_condition in self.knowledge[path + '/' + str(knowledge_focus)]:
                        try:
                            found_vis_ref = self.knowledge[path + '/' + str(knowledge_focus) + '/' + str(check_condition) + '/vis_ref']
                            for x, y, prior_val, _ in found_vis_ref:
                                try:
                                    if model.vis_count[prior_val]:
                                        keep = True
                                        break
                                except KeyError:
                                    pass
                        except KeyError:
                            pass
                    if not keep:
                        pprint('focus value ' + str(knowledge_focus) + ' no vis_ref in any condition data', num_indents=num_indents + 3)
                        knowledge_prune.append(knowledge_focus)

                for val in knowledge_prune:
                    if len(knowledge_found) > 1:
                        knowledge_found.remove(val)
                    else:
                        no_conditions = True

                # set model.focus_value to a random focus value in knowledge_found
                pprint('selecting a random focus_value from the usable knowledge:', num_indents=num_indents + 2)
                if knowledge_found:
                    model.focus_value = random.choice(knowledge_found)
                else:
                    raise KeyError

                # flag if focus value is aux, set aux variable,
                # and cast focus_value to float
                model.focus_value_is_aux = model.focus_value[0] == 'A'
                if not model.focus_value_is_aux:
                    # (x, y) position of a model.focus_value in the
                    # list of positions for that value in the model
                    model.focus_pos = model.vis_count_pos[float(model.focus_value)][0]
                model.focus_value = float(model.focus_value[1:]) if \
                    model.focus_value_is_aux else float(model.focus_value)
                self.goal_focus_value = copy.deepcopy(model.focus_value)
                self.print_focus_value(num_indents=4)
                pprint('flag model.focus_value_is_aux:\t%s' %
                    model.focus_value_is_aux, num_indents=num_indents + 2)

                # choose a random goal condition
                pprint('selecting a random goal_condition from the knowledge:',
                    num_indents=num_indents + 2, new_line_start=True)
                #self.goal_condition = random.choice(
                    #self.knowledge[path + '/' + str(model.focus_value)])
                if not no_conditions:
                    check_conditions = copy.deepcopy(self.knowledge[path + '/' + str(model.focus_value)])
                    self.goal_condition = random.choice(check_conditions)
                    while check_conditions:
                        try:
                            found_vis_ref = self.knowledge[path + '/' + str(model.focus_value) + '/' + str(self.goal_condition) + '/vis_ref']
                            found = False
                            for x, y, prior_val, _ in found_vis_ref:
                                try:
                                    if model.vis_count[prior_val]:
                                        found = True
                                        break
                                except:
                                    pass
                            if found:
                                break
                            else:
                                check_conditions.remove(self.goal_condition)
                                self.goal_condition = random.choice(check_conditions)
                        except KeyError:
                            check_conditions.remove(self.goal_condition)
                            self.goal_condition = random.choice(check_conditions)
                    if not check_conditions:
                        no_conditions = True
                        self.goal_condition = None
                self.print_goal_condition(num_indents=4)
                self.goal_type = self.goal_type_default

            except KeyError:
                pprint('we have no knowledge of this action/output', num_indents=num_indents + 2)
                self.goal_type = 'New Action'  # do an action we've not done before
                goal_found = True
                pprint('goal_type reset to:\t%s' % self.goal_type, num_indents=num_indents + 2)

        if self.goal_type == 'Predict':
            goal_found = True

        if self.goal_type == 'Observe':
            goal_found = True

        fv = str(model.focus_value) if model.focus_value else ''
        gc = str(self.goal_condition) if self.goal_condition else ''
        path = str(self.goal_action) + '/' + str(self.goal_output) \
             + '/' + fv + '/' + gc
        # fv and gc are used because: TypeError: must be str, not NoneType
        # when using model.focus_value and self.goal_condition directly

        if not goal_found and not no_conditions:
            try:
                pprint('searching for goal_source knowledge at: ' + path + '/vis_ref',
                    num_indents=num_indents + 1, new_line_start=True)

                while True:
                    x, y, prior_val, _ = random.choice(self.knowledge[path + '/vis_ref'])
                    try:
                        if model.vis_count[prior_val]:
                            self.goal_source = {
                                'value': prior_val,
                                'x': x,
                                'y': y,
                                'i': None
                            }
                            self.goal_value = 3.0 #force airis to chase batteries
                            #self.goal_value = prior_val if goal_type == 'Fixed' else \
                                #random.sample(self.vis_global_set, 1)[0]
                            goal_found = True
                            pprint('knowledge found, goal_source set to:', num_indents=num_indents + 2)
                            self.print_goal_source(num_indents=num_indents + 3)
                            break
                    except KeyError:
                        pass
            except KeyError:
                pprint('knowledge not found', num_indents=num_indents + 2)
                # pass

        if not goal_found and not no_conditions:
            try:
                pprint('searching for goal_source knowledge at: ' + path + '/aux_ref',
                    num_indents=num_indents + 1, new_line_start=True)
                i, val = random.choice(self.knowledge[path + '/aux_ref'])
                self.goal_source = {
                    'value': val,
                    'x': None,
                    'y': None,
                    'i': i
                }
                self.goal_value = val if self.goal_type == 'Fixed' else \
                    random.sample(self.aux_global_set, 1)[0]
                goal_found = True
                pprint('knowledge found, goal_source set to:', num_indents=num_indents + 2)
                self.print_goal_source(num_indents=num_indents + 3)
            except KeyError:
                pprint('knowledge not found', num_indents=num_indents + 2)
                # pass
        if not no_conditions:
            pprint('goal set. duration: %s' % (datetime.now() - start_time),
                num_indents=num_indents, new_line_start=True, draw_line=True)

    def make_plan(self, action, num_indents=0):

        # tbd when goal_type is not New Action

        pprint('making a plan to achieve the goal ...',
            num_indents=num_indents, new_line_start=True)
        start_time = datetime.now()

        pprint('goal_type: %s' % self.goal_type,
            num_indents=num_indents + 1, new_line_start=True)

        # how many steps are in the plan
        plan_depth = 0
        worst_condition = []
        new_condition = []

        if self.goal_type == 'Random' and self.goal_value != None:

            # set the current model's compare field
            self.compare_model(self.current_model_index, num_indents=num_indents + 1)

            model = self.models[self.current_model_index]  # get current model
            model.depth = 0
            # how far away that model is from the goal state, and its index
            # use this heap to generate more models on as we go
            base_model_heap = [(model.compare, self.current_model_index)]

            # a way to see if a model has already been generated
            # model_set = {model}
            # make sure you don't generate the same sequence of models over and over again in an infinite loop
            # if we modeled something and we model it again and it has the same result, then we discard that model
            model_set = {np.array_str(model.vis_env) + np.array_str(model.aux_env)}

            # flag if we've reached the goal
            print('Current Goal: ')
            print(self.goal_source,'where value =',self.goal_value)
            goal_reached = False
            print('Initial focus value', model.focus_value)
            print('Initial Compare: ', model.compare)
            if model.compare == 0:
                self.predict(self.goal_action, self.goal_output, num_indents=num_indents + 1)
                self.action_plan.append((self.goal_action, self.goal_output, self.current_model_index))
                goal_reached = True

            if model.compare == 999999:
                goal_reached = True

            while not goal_reached and base_model_heap and plan_depth <= self.action_plan_depth_limit:

                base_model = heapq.heappop(base_model_heap)[1]
                plan_depth += 1
                pprint (str(plan_depth) + ' / ' + str(self.action_plan_depth_limit), num_indents=num_indents + 1)
                for action_index, try_action in enumerate(self.action_space):
                    if not goal_reached:
                        for try_output in range(self.action_output_list[action_index][0], self.action_output_list[action_index][1], self.action_output_list[action_index][2]):
                            self.current_model_index = base_model
                            model = self.models[self.current_model_index]
                            hold_depth = model.depth
                            pprint('base model depth: '+str(model.depth), num_indents=num_indents + 1)
                            self.predict(try_action, try_output, num_indents=num_indents + 1)
                            if model.best_condition_id:
                                worst_dif = int(copy.deepcopy(model.best_condition_dif))
                                worst_id = int(copy.deepcopy(model.best_condition_id))
                                prev_model = model
                                model = self.models[self.current_model_index]
                                model.depth = hold_depth + 1
                                self.compare_model(self.current_model_index, num_indents=num_indents + 1)

                                if model.compare != 999999:
                                    worst_condition.append((worst_dif, model.previous_model_index, worst_id, model.compare, try_action, try_output, 999999, prev_model.focus_value, self.current_model_index))

                                pprint('This model\'s (' + str(self.current_model_index) + ') depth: '+str(model.depth), num_indents=num_indents + 1)
                                pprint('This model\'s (' + str(self.current_model_index) + ') compare: '+str(model.compare), num_indents=num_indents + 1)
                                model_env = np.array_str(model.vis_env) \
                                          + np.array_str(model.aux_env)
                                if model_env not in model_set:
                                    heapq.heappush(base_model_heap, (model.compare + model.depth, self.current_model_index))
                                    model_set.add(model_env)
                                if model.compare == 0:
                                    pprint('model compare Exception', num_indents=num_indents + 1)
                                    self.predict(self.goal_action,self.goal_output, num_indents=num_indents + 1)
                                    if model.best_condition_id:
                                        source = self.current_model_index
                                        model = self.models[source]
                                    else:
                                        source = self.models[self.current_model_index].previous_model_index
                                        self.action_plan.append((self.goal_action, self.goal_output, source))
                                        model = self.models[source]
                                    while model.previous_model_index != None:
                                        self.action_plan.append((model.previous_action, model.previous_output, source))
                                        source = model.previous_model_index
                                        model = self.models[source]  # model.previous is an index
                                    goal_reached = True
                                    break
                            elif model.best_condition_id == None:  # if we don't have knowledge of this try_action
                                source = self.models[self.current_model_index].previous_model_index
                                new_condition.append((999999, self.current_model_index, None, self.models[source].compare , try_action, try_output, 999999, self.models[source].focus_value, self.current_model_index))
                    else:
                        pprint('PLAN MADE!', num_indents=num_indents + 1)
                        break

            # if no successful plan can be found, make a plan to try the least accurate prediction
            if (plan_depth > self.action_plan_depth_limit or not self.action_plan) and not goal_reached:
                if model.compare != 0:
                    print('Insufficient knowledge to achieve: ')
                    print(self.goal_source,'where value =',self.goal_value)
                    if plan_depth > self.action_plan_depth_limit:
                        self.action_plan_depth_limit += 5
                        print('Increasing plan depth to ',str(self.action_plan_depth_limit))

                    worst_condition.extend(new_condition)

                    for i, (dif, index, id, compare, act, out, raw, focus, current) in enumerate(worst_condition):
                        if id != None:
                            raw_dif = 0
                            path = str(act) + '/' + str(out) + '/' + str(focus) + '/' + str(id) + '/'
                            condition_data_array = self.knowledge[path + 'vis_data']
                            condition_aux_data_array = self.knowledge[path + 'aux_data']
                            raw_dif = np.sum(array_dif(self.models[index].vis_env, condition_data_array))
                            raw_dif += np.sum(array_dif(self.models[index].aux_env, condition_aux_data_array))
                            worst_condition[i] = (dif, index, id, compare, act, out, raw_dif, focus, current)

                    worst_condition_prune = copy.deepcopy(worst_condition)

                    worst_condition_check = copy.deepcopy(worst_condition)

                    for dif, index, id, compare, act, out, raw, focus, current in worst_condition_prune:
                        check_worst = (str(self.models[index].vis_env)+str(self.models[index].aux_env), act, out, raw)
                        if check_worst in self.worst_set:
                            pprint('deleting duplicate worst_condition: ('+str(dif)+','+str(index)+','+str(act)+','+str(out)+','+str(raw)+')', num_indents=num_indents + 1)
                            #print('deleting duplicate worst_condition: ('+str(dif)+','+str(index)+','+str(act)+','+str(out)+','+str(raw)+')')
                            worst_condition.remove((dif, index, id, compare, act, out, raw, focus, current))

                    worst_condition = [i for i in worst_condition if i[3] == min(worst_condition, key=itemgetter(3))[3]]

                    worst_condition_prune = [i for i in worst_condition if i[0] > 0]

                    if worst_condition_prune:
                        worst_condition = worst_condition_prune

                    worst_condition_prune = [i for i in worst_condition if i[6] != 0]
                    if worst_condition_prune:
                        worst_condition = worst_condition_prune
                    worst_condition = [i for i in worst_condition if i[6] == min(worst_condition, key=itemgetter(6))[6]]

                    # search through all models to find the one with the highest best_condition_dif
                    # if we cant figure out how to achieve our goal
                    # then instead, do whatever action we're the least confident about to see what action to do
                    if worst_condition:
                        pprint('worst_condition: '+str(worst_condition), num_indents=num_indents + 1)
                        print('Trying the closest thing I can think of...')
                        print('worst_condition: ', worst_condition)
                        worst_index = worst_condition.index(min(worst_condition, key=itemgetter(3)))
                        worst_index = worst_condition.index(max(worst_condition, key=itemgetter(0)))
                        self.store_worst = (str(self.models[worst_condition[worst_index][1]].vis_env)+str(self.models[worst_condition[worst_index][1]].aux_env), worst_condition[worst_index][4], worst_condition[worst_index][5], worst_condition[worst_index][6])
                        self.store_worst_index = worst_condition[worst_index][1]
                        self.current_model_index = worst_condition[worst_index][1]
                        if worst_condition[worst_index][0] == 0:
                            print('I think I\'ve tried \''+str(worst_condition[worst_index][4])+'\' under these conditions before.')
                            self.action_plan.append((worst_condition[worst_index][4], worst_condition[worst_index][5], worst_condition[worst_index][8]))
                        elif worst_condition[worst_index][0] == 999999:
                            pprint('New Action Exception', num_indents=num_indents + 1)
                            print('I don\'t know what will happen when I \''+str(worst_condition[worst_index][4])+'\' under these conditions...')
                            self.action_plan.append((worst_condition[worst_index][4], worst_condition[worst_index][5], worst_condition[worst_index][8]))
                            self.current_model_index = self.models[self.current_model_index].previous_model_index
                        elif 0 < worst_condition[worst_index][0] < 999999:
                            print('I\'m not sure about trying \''+str(worst_condition[worst_index][4])+'\' under these conditions...')
                            self.action_plan.append((worst_condition[worst_index][4], worst_condition[worst_index][5], worst_condition[worst_index][8]))
                        pprint('Cannot determine how to achieve goal.', num_indents=num_indents + 1)
                        pprint('Attempting worst_condition: '+str(worst_condition[worst_index]), num_indents=num_indents + 1)

                        if self.current_model_index != None:
                            model = self.models[self.current_model_index]
                            while model.previous_model_index != None:
                                self.action_plan.append((model.previous_action, model.previous_output, self.current_model_index))
                                self.current_model_index = model.previous_model_index
                                model = self.models[self.current_model_index]

                        print('Action plan: ',self.action_plan)

                    else:
                        pprint('Cannot determine how to achieve goal.', num_indents=num_indents + 1)
                        pprint('No more worst_condition\'s left to try.', num_indents=num_indents + 1)
                        #pprint('Clearing worst_set:', num_indents=num_indents)
                        #self.worst_set.clear()
                        #print('Clearing worst_set')
                        pprint('Abandoning goal.', num_indents=num_indents + 1)
                        print('No more worst_conditions? Check ',worst_condition_check)

        elif self.goal_type == 'New Action':

            pprint('since the goal type is New Action', num_indents=num_indents + 2)
            pprint('just append the randomly determined action/output', num_indents=num_indents + 2)
            pprint('to the plan, along with self.current_model_index', num_indents=num_indents + 2)
            self.action_plan.append((self.goal_action, self.goal_output, 0))

        elif self.goal_type == 'Predict':
            pprint ('Making a prediction...', num_indents=num_indents + 1)
            for action_index, try_action in enumerate(self.action_space):
                for try_output in range(self.action_output_list[action_index][0], self.action_output_list[action_index][1], self.action_output_list[action_index][2]):
                    self.predict(try_action, try_output, num_indents=num_indents + 1)
                    self.action_plan.append((try_action, try_output, self.current_model_index))
                    pprint ('Plan: '+str(self.action_plan), num_indents=num_indents + 1)

        elif self.goal_type == 'Observe':
            pprint ('Observing...', num_indents=num_indents + 1)
            self.predict(action, 1, num_indents=num_indents + 1)
            self.action_plan.append((action, 1, self.current_model_index))
            pprint ('Observed action: '+str(self.action_plan), num_indents=num_indents + 1)

        pprint('self.action_plan:\t%s' % self.action_plan,
            num_indents=num_indents + 1, new_line_start=True)

        pprint('plan made. duration: %s' % (datetime.now() - start_time),
            num_indents=num_indents, new_line_start=True, draw_line=True)

    def compare_model(self, model_index, num_indents=0):

        # set the specified model's compare field to the distance
        # from the predicted goal value's pos to the closest actual goal value

        pprint('compare_model: setting the specified model\'s compare field',
            num_indents=num_indents, new_line_start=True, draw_line=False)
        pprint('to the distance from the predicted goal value\'s pos to the',
            num_indents=num_indents)
        pprint('closest actual goal value ...',
            num_indents=num_indents)
        start_time = datetime.now()

        best_compare = None
        compare = None
        model = self.models[model_index]
        vis_env = copy.deepcopy(model.vis_env)

        fv = model.focus_value
        try:
            if model.vis_count[fv]:
                for fx, fy in model.vis_count_pos[fv]:
                    gx, gy = fx + self.goal_source['x'], fy + self.goal_source['y']
                    pprint('gx, gy: '+str(gx)+','+str(gy), num_indents=num_indents)
                    if not 0 <= gx < len(vis_env) or not 0 <= gy < len(vis_env[0]):
                        compare = 999999

                    # edges of the vis_env
                    vis_top = len(vis_env[0]) - 1
                    vis_bottom = 0
                    vis_left = 0
                    vis_right = len(vis_env) - 1

                    # max_d = maximum distance from the focus value to an edge of the vis_env
                    # max_d is used so the search terminates when the whole vis_env has been searched
                    max_d = max([
                        abs(vis_top - gy),
                        abs(vis_bottom - gy),
                        abs(vis_left - gx),
                        abs(vis_right - gx)
                    ])

                    def next_search_border(env, cx, cy, d):

                        # next_search_border returns a list of tuples:
                        # [(value, (x, y)), ...]
                        # where each tuple provides the value and position
                        # of inputs in the env for the inputs of that env
                        # that form a square border around the center (cx, cy).
                        # d is the number of inputs from the focus value
                        # to the center of any of the border's edges.

                        def get_edge(env, inbounds,
                                    start_x, end_x, only_x,
                                    start_y, end_y, only_y,
                                    horizontal=False,
                                    vertical=False):

                            # get_edge returns a list of tuples for the top
                            # bottom, left, or right edge of the border (inclusive)
                            # If the edge is completely outside the env, [] is returned.
                            # If part of the edge is outside the env, those parts outside
                            # are excluded from the list returned. If the whole edge is
                            # inside the env, the whole edge is returned.

                            return list(map(
                                lambda x, y: (env[x][y], (x, y)),
                                list(range(start_x, end_x + 1)) if horizontal else [only_x] * (end_y - start_y + 1),
                                list(range(start_y, end_y + 1)) if vertical else [only_y] * (end_x - start_x + 1)
                            )) if inbounds else []

                        # edges of the square search border positions
                        sqr_top = cy + d
                        sqr_bottom = cy - d
                        sqr_left = cx - d
                        sqr_right = cx + d

                        # lists of values and positions of each edge of the border
                        top_row = get_edge(
                            env, sqr_top <= vis_top,
                            sqr_left if sqr_left > vis_left else vis_left,
                            sqr_right if sqr_right < vis_right else vis_right, None,
                            None, None, sqr_top,
                            horizontal=True)
                        bottom_row = get_edge(
                            env, sqr_bottom >= vis_bottom,
                            sqr_left if sqr_left > vis_left else vis_left,
                            sqr_right if sqr_right < vis_right else vis_right, None,
                            None, None, sqr_bottom,
                            horizontal=True)
                        left_row = get_edge(
                            env, sqr_left >= vis_left,
                            None, None, sqr_left,
                            sqr_bottom if sqr_bottom > vis_bottom else vis_bottom,
                            sqr_top if sqr_top < vis_top else vis_top, None,
                            vertical=True)
                        right_row = get_edge(
                            env, sqr_right <= vis_right,
                            None, None, sqr_right,
                            sqr_bottom if sqr_bottom > vis_bottom else vis_bottom,
                            sqr_top if sqr_top < vis_top else vis_top, None,
                            vertical=True)

                        # set is used to remove duplicates
                        return set(top_row + bottom_row + left_row + right_row)

                    if 0 <= gx < len(vis_env) and 0 <= gy < len(vis_env[0]):
                        if vis_env[gx][gy] == self.goal_value:
                            best_compare = 0

                        pprint('the current goal value\'s position satisfies the knowledge condition.',
                            num_indents=num_indents + 1, new_line_start=True, draw_line=False)

                    if compare == None:

                        pprint('the current goal value\'s position does not satisfy the knowledge condition.',
                            num_indents=num_indents + 1, new_line_start=True, draw_line=False)
                        pprint('using an expanding square search of the model\'s vis_env',
                            num_indents=num_indents + 1)
                        pprint('to find the closest goal value ...', num_indents=num_indents + 1)

                        d = 1  # d = distance from focus value
                        while True:

                            # stop searching if the closest possible goal value has been found
                            if compare and d > compare:
                                break

                            # stop searching if there is guaranteed to be no more border
                            # because we have reached the final edge of the vis_env
                            if d > max_d:
                                break

                            # get the current square border and increment its
                            # distance for the next border
                            border = next_search_border(vis_env, gx, gy, d)
                            d += 1

                            # if no border was found, we've reached the final edge
                            if not border:
                                break

                            for val, (x, y) in border:

                                # if this value of the model is the goal value
                                if val == self.goal_value:

                                    # distance = number of sub-symbolic inputs from the
                                    # the goal_source's position to the current position
                                    distance = abs(gx - x) + abs(gy - y)

                                    # update compare if there's no compare value
                                    # or this value is closer
                                    compare = distance if not compare or \
                                        distance < compare else compare

                                    #if not 0 <= x - gx <= len(vis_env) or not 0 <= y - gy <= len(vis_env[0]):
                                        #compare = 999999

                    # set the model's compare field to the number
                    # of moves to the closest goal
                    if best_compare == None or compare < best_compare:
                        best_compare = compare

        except:
            pass

        if best_compare == None:
            best_compare = 999999

        model.compare = best_compare

        pprint('goal value%sfound. model.compare set to: %s. duration: %s' %
            (' ' if model.compare != None else ' not ', model.compare, (datetime.now() - start_time)),
            num_indents=num_indents, new_line_start=True, draw_line=True)

    def predict(self, action, output, num_indents=0):

        # to set the model to the posterior based on the
        # past knowledge of an experience closest to the
        # current environment

        pprint('making a prediction for action: %s ...' % action, num_indents=num_indents, new_line_start=True)
        start_time = datetime.now()

        # get the difference between memory and
        # what we're currently looking at
        model = self.models[self.current_model_index]
        model.best_conditions = []

        # action/output/focus_value/condition_id
        path = str(action) + '/' + str(output)
        pprint('path = ' + path, num_indents=num_indents + 1)

        model_heap = copy.deepcopy(model.vis_count_heap)
        condition_candidate_data = {}
        condition_candidate = []

        while model_heap:
            _, focus_val = heapq.heappop(model_heap)

            try:
                if str(focus_val) in self.knowledge[path]:
                    pprint('focus_value for current prediction = ' + str(focus_val), num_indents=num_indents + 1)

                    try:
                        base_diff = None
                        condition_heap = []
                        heapq.heapify(condition_heap)

                        for check_condition in self.knowledge[path + '/' + str(focus_val)]:
                            # action, output, model_index, focus_val, condition_id, base_diff, num_indents
                            result = self.compare_conditions(action, output, self.current_model_index, focus_val, check_condition, base_diff, None, num_indents=num_indents + 1)
                            if result:
                                heapq.heappush(condition_heap, result)
                            base_diff = condition_heap[0][0]

                        # (best_condition_dif, focus_value, condition_id, (posx or auxindex, posy), path)
                        model.best_conditions = [condition_heap[0]]

                    except KeyError:
                        pprint('Knowledge')

                if model.best_conditions:
                    base_condition = str(model.best_conditions[0])
                    for val in self.knowledge['cond/'+base_condition]:
                        try:
                            if model.vis_count[val]:
                                for ref_data in [item for item in self.knowledge[str(focus_val)+'/'+base_condition+'/'+'vis_ref'] if item[2] == val]:
                                    results = self.compare_conditions(action, output, self.current_model_index, val, ref_data[4], None, condition_candidate_data, num_indents=num_indents + 1)
                                    for result in results:
                                        condition_candidate_data[str(result[1])+'/'+str(result[3][0])+','+str(result[3][1])] = result
                                        if str(result[1])+'/'+str(result[3][0])+','+str(result[3][1]) not in condition_candidate:
                                            condition_candidate.append(str(result[1])+'/'+str(result[3][0])+','+str(result[3][1]))
                        except KeyError:
                            pass

            except KeyError:
                pprint('no known values to predict')

        # get the path of the prior focus value in the knowledge
        path = str(action) + '/' + str(output) + '/' +  \
               str(model.focus_value) + '/' + str(model.best_condition_id)

        # put a copy of the current model at the end of the list of models
        self.current_model_index = self.create_model(self.current_model_index, num_indents=num_indents + 1)

        # if we found a condition
        if model.best_condition_id:

            pprint('best_condition_id: ' + str(model.best_condition_id),
                num_indents=num_indents + 1, new_line_start=True)

            self.models[self.current_model_index].source_condition_path = model.best_condition_path
            model = self.models[self.current_model_index]
            focus_found = False

            pprint('new model initial focus_pos: ' + str(model.focus_pos),
                num_indents=num_indents + 1, new_line_start=True)
            model.previous_action = action
            model.previous_output = output

            is_aux = str(model.focus_value)

            if is_aux[0] == 'A':
                predicted_posterior_value = self.knowledge[path + '/posterior_val']
                model.update_aux_value(predicted_posterior_value, model.focus_index)

            else:
                predicted_posterior_val = self.knowledge[path + '/posterior_val']
                model.update_vis_value(predicted_posterior_val, model.focus_pos)

            try:
                predict_vis_ref = self.knowledge[path + '/vis_ref']

            except KeyError:
                predict_vis_ref = []

            if model.focus_pos:
                fx, fy = copy.deepcopy(model.focus_pos)
            for dx, dy, prior_val, posterior_val, change_condition_id in predict_vis_ref:
                x, y = fx + dx, fy + dy
                if 0 <= x < len(self.prior_vis_env) and 0 <= y < len(self.prior_vis_env[0]):
                    model.update_vis_value(posterior_val, (x, y), focus_value=model.focus_value)
                    if float(posterior_val) == model.focus_value:
                        model.focus_pos = (x, y)
                        focus_found = True
            if model.focus_pos:
                pprint('new model predicted focus_pos: ' + str(model.focus_pos),
                    num_indents=num_indents + 1, new_line_start=True)

            try:
                predict_aux_ref = self.knowledge[path + '/aux_ref']

            except KeyError:
                predict_aux_ref = []

            for i, _, prior_val, posterior_val, change_condition_id in predict_aux_ref:
                model.update_aux_value(posterior_val, i)

            # Update focus value if previous models focus value no longer exists
            if not focus_found:
                focus_heap = copy.deepcopy(model.vis_count_heap)
                count_pos = copy.deepcopy(model.vis_count_pos)

                if self.focus_global_set:
                    while focus_heap and not focus_found:
                        if focus_heap[0][1] in self.focus_global_set:
                            model.focus_value = focus_heap[0][1]
                            model.focus_pos = count_pos[model.focus_value][0]
                            focus_found = True
                        else:
                            heapq.heappop(focus_heap)

            try:
                if self.knowledge[model.source_condition_path + 'rel_abs'] == -1:
                    pprint('Changing Model to ABS',
                        num_indents=num_indents + 1, new_line_start=True)
                    model = self.models[self.current_model_index]
                    model.initialize_from_env(
                        self.knowledge[model.source_condition_path + 'post_vis_data'],
                        self.knowledge[model.source_condition_path + 'post_aux_data'])

                    focus_heap = copy.deepcopy(model.vis_count_heap)
                    count_pos = copy.deepcopy(model.vis_count_pos)
                    focus_found = False

                    if self.focus_global_set:
                        while focus_heap and not focus_found:
                            if focus_heap[0][1] in self.focus_global_set:
                                model.focus_value = focus_heap[0][1]
                                model.focus_pos = count_pos[model.focus_value][0]
                                focus_found = True
                            else:
                                heapq.heappop(focus_heap)
            except:
                pass

        else:
            pprint('No matching condition found.',
                num_indents=num_indents + 1, new_line_start=True)
            dest = self.models[self.current_model_index]
            dest.focus_value = model.focus_value
            dest.focus_value_is_aux = model.focus_value_is_aux
            dest.focus_pos = model.focus_pos
            dest.focus_index = model.focus_index
            model = self.models[self.current_model_index]

        pprint('visual prediction: ' + str(model.predicted_vis_change),
            num_indents=num_indents + 1, new_line_start=True)
        pprint('auxiliary prediction: ' + str(model.predicted_aux_change),
            num_indents=num_indents + 1)
        pprint('prediction made. duration: %s' % (datetime.now() - start_time),
            num_indents=1, new_line_start=True, draw_line=True)

    def find_changes(self, num_indents=0):

        # find_out if the current model's predicted posterior
        # is different than the actual posterior, save any
        # differences (changes) in:
        # self.vis_change_list
        # self.aux_change_list
        # and return a boolean flagging if there was a difference at all

        pprint('determining if our prediction was correct ...',
            num_indents=num_indents, new_line_start=True)
        start_time = datetime.now()

        pprint('self.current_model_index = %d' % self.current_model_index,
            num_indents=num_indents + 1, new_line_start=True)
        model = self.models[self.current_model_index]  # current model
        vis_change_found = False
        aux_change_found = False
        vis_abs_found = False
        aux_abs_found = False
        abs_source = False
        vis_prior_found = True
        aux_prior_found = True

        # resetting self.vis_change_list and self.aux_change_list
        self.vis_change_list = []
        self.aux_change_list = []

        # get difference between the current vis env and the current model
        # (the current model is modeling the vis env prior to the action)
        pprint('getting the difference between the current model\'s',
            num_indents=num_indents + 1, new_line_start=True)
        pprint('predicted vis env and the actual posterior vis env', num_indents=num_indents + 1)
        vis_change_array = array_dif(
            self.posterior_vis_env,
            model.vis_env)
        print_vis_env(model.vis_env, title='Predicted Visual Env:', num_indents=num_indents + 2)
        print_vis_env(self.posterior_vis_env, title='Actual Visual Env:', num_indents=num_indents + 2)
        print_vis_env(vis_change_array, title='Visual Difference:', num_indents=num_indents + 2)

        # get the (x, y) locations of the changes
        pprint('getting the (x, y) locations of the vis differences',
            num_indents=num_indents + 1, new_line_start=True)
        change_x, change_y = np.nonzero(vis_change_array)
        vis_change_found = len(change_x) > 0  # flag if any visual changes were found
        pprint('x pos of changes from prediction:\t%s' % change_x, num_indents=num_indents + 2)
        pprint('y pos of changes from prediction:\t%s' % change_y, num_indents=num_indents + 2)

        if vis_change_found:
            # Check to see if it's an absolute change
            try:
                if self.knowledge[model.source_condition_path + 'rel_abs'] != 1:
                    vis_abs_array = array_dif(
                        self.knowledge[model.source_condition_path + 'post_vis_data'],
                        self.posterior_vis_env)

                    abs_x, abs_y = np.nonzero(vis_abs_array)
                    vis_abs_found = len(abs_x) == 0

                    if vis_abs_found:
                        vis_abs_array = array_dif(
                            self.knowledge[model.source_condition_path + 'vis_data'],
                            self.prior_vis_env)

                        abs_x, abs_y = np.nonzero(vis_abs_array)
                        vis_abs_found = len(abs_x) != 0

                    if vis_abs_found:
                        if self.knowledge[model.source_condition_path + 'rel_abs'] == -1:
                            abs_source = True
            except:
                pass

            if not vis_abs_found:
                try:
                    vis_check_found = True
                    pprint('checking ABS 1', num_indents=num_indents + 1)
                    if self.knowledge[model.source_condition_path + 'rel_abs'] == -1:

                        check = self.create_model(model.previous_model_index, num_indents=num_indents + 1)
                        path = model.source_condition_path
                        check_model = self.models[check]

                        is_aux = str(check_model.focus_value)

                        pprint('checking ABS 2', num_indents=num_indents + 1)

                        if is_aux[0] == 'A':
                            predicted_posterior_value = self.knowledge[path + 'posterior_val']
                            check_model.update_aux_value(predicted_posterior_value, check_model.focus_index)

                        else:
                            predicted_posterior_val = self.knowledge[path + 'posterior_val']
                            check_model.update_vis_value(predicted_posterior_val, check_model.focus_pos)

                        pprint('checking ABS 3', num_indents=num_indents + 2)

                        try:
                            predict_vis_ref = self.knowledge[path + 'vis_ref']

                        except KeyError:
                            predict_vis_ref = []

                        pprint('checking ABS 4 '+str(predict_vis_ref), num_indents=num_indents + 1)

                        if check_model.focus_pos:
                            cfx, cfy = copy.deepcopy(check_model.focus_pos)

                        pprint('checking ABS 5 '+str(cfx)+'/'+str(cfy), num_indents=num_indents + 1)

                        for cdx, cdy, prior_val, posterior_val, change_condition_id in predict_vis_ref:
                            x, y = cfx + cdx, cfy + cdy
                            if 0 <= x < len(self.prior_vis_env) and 0 <= y < len(self.prior_vis_env[0]):
                                check_model.update_vis_value(posterior_val, (x, y), focus_value=check_model.focus_value)

                        try:
                            predict_aux_ref = self.knowledge[path + 'aux_ref']

                        except KeyError:
                            predict_aux_ref = []

                        pprint('checking ABS 6 '+str(predict_aux_ref), num_indents=num_indents + 1)

                        for i, _, prior_val, posterior_val, change_condition_id in predict_aux_ref:
                            check_model.update_aux_value(posterior_val, i)

                        vis_check_array = array_dif(
                            self.posterior_vis_env,
                            check_model.vis_env)

                        check_x, check_y = np.nonzero(vis_check_array)
                        vis_check_found = len(check_x) > 0  # flag if any visual changes were found
                except:
                    pprint('checking ABS except', num_indents=num_indents + 1)
                    vis_check_found = True

                if vis_check_found:
                    pprint('getting the difference between the previous vis env\'s',
                        num_indents=num_indents + 1, new_line_start=True)
                    pprint('and the actual posterior vis env', num_indents=num_indents + 1)
                    vis_prior_array = array_dif(
                        self.posterior_vis_env,
                        self.prior_vis_env)
                    print_vis_env(self.prior_vis_env, title='Predicted Visual Env:', num_indents=num_indents + 2)
                    print_vis_env(self.posterior_vis_env, title='Actual Visual Env:', num_indents=num_indents + 2)
                    print_vis_env(vis_change_array, title='Visual Difference:', num_indents=num_indents + 2)
                    change_x, change_y = np.nonzero(vis_prior_array)
                    vis_prior_found = len(change_x) > 0
                    pprint('x pos of changes from prior to post:\t%s' % change_x, num_indents=num_indents + 2)
                    pprint('y pos of changes from prior to post:\t%s' % change_y, num_indents=num_indents + 2)

                    # iterate over the changes in the visual environment
                    pprint('appending differences to self.vis_change_list:',
                        num_indents=num_indents + 1, new_line_start=True)
                    pprint('key: [(x, y, prior_val, actual_posterior_val, change_condition_id), ...]',
                        num_indents=num_indents + 1)
                    for x, y in zip(change_x, change_y):
                        prior_val = self.prior_vis_env[x][y]
                        posterior_val = self.posterior_vis_env[x][y]
                        change_data = (x, y, prior_val, posterior_val, -1)
                        self.vis_change_list.append(copy.deepcopy(change_data))
                else:
                    pprint ('NOT ABS', num_indents=num_indents + 1, new_line_start=True)
                    self.knowledge[model.source_condition_path + 'rel_abs'] = 1
                    vis_change_found = False
                    self.action_plan = []

            else:
                vis_change_found = False

        pprint('Actual Visual Change List:   \t\t%s' % self.vis_change_list,
            num_indents=num_indents + 2)

        # do all the same stuff for the aux env
        pprint('getting the difference between the current model\'s', num_indents=num_indents + 1,
            new_line_start=True)
        pprint('predicted aux env and the actual posterior aux env', num_indents=num_indents + 1)
        aux_change_array = array_dif(
            self.posterior_aux_env,
            model.aux_env)
        print_aux_env(model.aux_env, title='Predicted Auxiliary Env:', num_indents=num_indents + 2)
        print_aux_env(self.posterior_aux_env, title='Actual Auxiliary Env:', num_indents=num_indents + 2)
        print_aux_env(aux_change_array, title='Auxiliary Difference:', num_indents=num_indents + 2)

        pprint('getting the indexes of the aux differences',
            num_indents=num_indents + 1, new_line_start=True)
        aux_change_index, = np.nonzero(aux_change_array)
        aux_change_found = len(aux_change_index) > 0
        pprint('indexes of changes:\t\t%s' % aux_change_index, num_indents=num_indents + 2)

        pprint('appending differences to self.aux_change_list',
            num_indents=num_indents + 1, new_line_start=True)
        pprint('key: [(index, _, prior_val, actual_posterior_val, change_condition_id), ...]',
            num_indents=num_indents + 1)
        pprint('aux_change_list = '+str(aux_change_index),
            num_indents=num_indents + 1)

        if aux_change_found:
            if not vis_change_found:
                try:
                    aux_abs_array = array_dif(
                        self.knowledge[model.source_condition_path + 'post_aux_data'],
                        self.posterior_aux_env)

                    abs_index, = np.nonzero(aux_abs_array)
                    aux_abs_found = len(abs_index) == 0

                    if aux_abs_found:
                        aux_abs_array = array_dif(
                            self.knowledge[model.source_condition_path + 'aux_data'],
                            self.prior_aux_env)

                        abs_index, = np.nonzero(aux_abs_array)
                        aux_abs_found = len(abs_x) != 0

                    if aux_abs_found:
                        if self.knowledge[model.source_condition_path + 'rel_abs'] == -1:
                            abs_source = True
                except:
                    pass

            if not aux_abs_found:
                for i in aux_change_index:
                    prior_val = self.prior_aux_env[i]
                    posterior_val = self.posterior_aux_env[i]
                    change_data = (i, -1, prior_val, posterior_val, -1)
                    self.aux_change_index = i
                    self.aux_change_list.append(copy.deepcopy(change_data))

        if not aux_abs_found and not aux_change_found:

            aux_prior_array = array_dif(
                self.posterior_aux_env,
                self.prior_aux_env)

            aux_prior_index, = np.nonzero(aux_prior_array)
            aux_prior_found = len(aux_prior_index) > 0

            for i in aux_prior_index:
                prior_val = self.prior_aux_env[i]
                posterior_val = self.posterior_aux_env[i]
                change_data = (i, -1, prior_val, posterior_val, -1)
                self.aux_change_index = i
                self.aux_change_list.append(copy.deepcopy(change_data))

        pprint('Actual Auxiliary Change List:\t\t%s' % self.aux_change_list,
            num_indents=num_indents + 2)

        # include real values of all predicted aux changes
        if aux_change_found and not abs_source:
            pprint('appending prediction to self.aux_change_list:',
                num_indents=num_indents + 1, new_line_start=True)
            for i, prior_val, posterior_val, change_condition_id in model.predicted_aux_change:
                if not [index for index in self.aux_change_list if index[0] == i]:
                    self.aux_change_list.append((i, -1, prior_val, posterior_val, change_condition_id))

            for x, y, prior_val, _, change_condition_id in model.predicted_vis_change:
                if not [pos for pos in self.vis_change_list if pos[0] == x and pos[1] == y]:
                    prior_val = self.prior_vis_env[x][y]
                    posterior_val = self.posterior_vis_env[x][y]
                    change_data = (x, y, prior_val, posterior_val, -1)
                    self.vis_change_list.append(copy.deepcopy(change_data))

        # include real values of all predicted changes if there's an unpredicted change but no difference in the env
        if vis_change_found and vis_check_found and not abs_source:
            pprint('appending prediction to self.vis_change_list:',
                num_indents=num_indents + 1, new_line_start=True)
            for x, y, prior_val, _, change_condition_id in model.predicted_vis_change:
                if not [pos for pos in self.vis_change_list if pos[0] == x and pos[1] == y]:
                    prior_val = self.prior_vis_env[x][y]
                    posterior_val = self.posterior_vis_env[x][y]
                    change_data = (x, y, prior_val, posterior_val, -1)
                    self.vis_change_list.append(copy.deepcopy(change_data))

            for i, prior_val, posterior_val, change_condition_id in model.predicted_aux_change:
                if not [index for index in self.aux_change_list if index[0] == i]:
                    self.aux_change_list.append((i, -1, prior_val, posterior_val, change_condition_id))

        if vis_abs_found or aux_abs_found:
            try:
                self.knowledge[model.source_condition_path + 'rel_abs'] = -1
                vis_change_found = False
                self.action_plan = []
            except:
                pass

        pprint('Actual + Predicted Visual Change List:   \t\t%s' % self.vis_change_list,
            num_indents=num_indents + 2)
        pprint('Actual + Predicted Auxiliary Change List:\t\t%s' % self.aux_change_list,
            num_indents=num_indents + 2)

        # return if ANY changes were found
        pprint('differences were%sfound, prediction %s. duration: %s' %
            ((' ' if (vis_change_found or aux_change_found) else ' not '),
            ('incorrect' if (vis_change_found or aux_change_found) else 'correct'),
            (datetime.now() - start_time)),
            num_indents=num_indents, new_line_start=True, draw_line=True)

        return vis_change_found or aux_change_found

    def create_condition(self, last_action, last_output, num_indents=0):

        # storing memory of prior env associated w/
        # actual changes that happened in the posterior

        if self.goal_type == 'New Action':
            print('This is a new Action')
            pprint('This is a New Action.',
                num_indents=num_indents + 1, new_line_start=True)
        else:
            print('This is not the outcome I predicted')

        pprint('creating condition ...', num_indents=num_indents, new_line_start=True)
        start_time = datetime.now()
        print('Saving new knowledge ...')

        condition_focus_value = None

        # increment the condition id
        self.condition_id += 1
        self.print_condition_id(num_indents=num_indents + 1, new_line_start=True)

        # clear the action plan
        self.action_plan = []

        # if there were visual differences or there was a New Action (without changes)
        if self.vis_change_list or (self.goal_type == 'New Action' and not self.aux_change_list):
            # get the data for the prior_vis_env
            self.vis_env_count, self.vis_env_count_list, vis_env_heap, vis_env_pos = \
                get_counts(self.prior_vis_env)

            no_focus_vis_env_heap = copy.deepcopy(vis_env_heap)

            # find the focus value of the prior visual environment
            # (focus value is the least frequent value that changed in
            #  the posterior, but were looking in the prior)
            # and set self.posterior_focus_value to the actual posterior value
            pprint('setting self.posterior_focus_value to the actual posterior value',
                num_indents=num_indents + 1, new_line_start=True, draw_line=False)

            while vis_env_heap and not condition_focus_value:
                _, least_frequent_val = heapq.heappop(vis_env_heap)

                # if the 'nothing' action was done, and there's no change
                # in the environment, or if it does the 'up' action below
                # a wall, and there's no change in the environment, we
                # want to store that lack of change in the knowledge,
                # but since there's no change_lists
                if self.goal_type == 'New Action' and not self.vis_change_list:
                    if least_frequent_val in self.focus_global_set:
                        condition_focus_value = least_frequent_val
                        self.vis_change_index = None
                        self.posterior_focus_value = least_frequent_val
                        x, y = vis_env_pos[least_frequent_val]
                        self.goal_type = self.goal_type_default
                        break

                # if something DID change in the environment, this
                # for loop will properly set:
                #    condition_focus_value
                #    self.vis_change_data
                #    self.posterior_focus_value
                for change_index, (x, y, prior_val, posterior_val, change_condition_id) \
                in enumerate(self.vis_change_list):
                    if prior_val == least_frequent_val and prior_val in self.focus_global_set:
                        condition_focus_value = prior_val
                        self.vis_change_index = change_index
                        self.posterior_focus_value = posterior_val
                        for _, _, not_focus, _, _ in self.vis_change_list:
                            if not_focus != prior_val:
                                self.not_focus_global_set.add(not_focus)
                        break

            if not condition_focus_value and len(self.aux_change_list) == 0:
                pprint('potential focus values not found in focus_global_set', num_indents=num_indents + 1)
                pprint('choosing one and adding it to the set', num_indents=num_indents + 1)

                while no_focus_vis_env_heap and not condition_focus_value:
                    _, least_frequent_val = heapq.heappop(no_focus_vis_env_heap)

                    if self.vis_change_list:
                        for change_index, (x, y, prior_val, posterior_val, change_condition_id) \
                        in enumerate(self.vis_change_list):
                            if prior_val == least_frequent_val and prior_val not in self.not_focus_global_set:
                                condition_focus_value = prior_val
                                self.vis_change_index = change_index
                                self.posterior_focus_value = posterior_val
                                self.focus_global_set.add(least_frequent_val)
                                for _, _, not_focus, _, _ in self.vis_change_list:
                                    if not_focus != prior_val:
                                        self.not_focus_global_set.add(not_focus)
                                break

                    elif least_frequent_val not in self.not_focus_global_set:
                        condition_focus_value = least_frequent_val
                        self.vis_change_index = None
                        self.posterior_focus_value = least_frequent_val
                        x, y = vis_env_pos[least_frequent_val]
                        self.focus_global_set.add(least_frequent_val)

            if condition_focus_value:
                pprint('self.posterior_focus_value     %s' % self.posterior_focus_value, num_indents=num_indents + 2)
                pprint('self.vis_change_index          %s' % self.vis_change_index, num_indents=num_indents + 2)

                pprint('Focus Set: '+str(self.focus_global_set), num_indents=num_indents + 1)
                pprint('Not Focus Set: '+str(self.not_focus_global_set), num_indents=num_indents + 1)

                self.store_condition(last_action, last_output, '',
                                        condition_focus_value,
                                        focus_x=x, focus_y=y,
                                        num_indents=num_indents + 1)

        # the visual prediction was correct
        if self.aux_change_list and not self.vis_change_list:

            focus_index, _, condition_focus_value, self.posterior_focus_value, change_condition_id = \
            self.aux_change_list[0]

            pprint('self.aux_change_list     %s' % self.aux_change_list, num_indents=num_indents + 2)

            self.store_condition(last_action, last_output, 'A',
                                 condition_focus_value, focus_index=focus_index,
                                 num_indents=num_indents + 1)

        self.goal_type = self.goal_type_default

        pprint('condition created. duration: %s' % (datetime.now() - start_time),
            num_indents=num_indents, new_line_start=True, draw_line=True)

    def store_condition(self, action, output, A, condition_focus_value,
                        focus_x=None, focus_y=None, focus_index=None, update=False, num_indents=0):

        # store the condition in the knowledge's tree

        start_time = datetime.now()

        pprint('Updating Knowledge:', num_indents=num_indents, new_line_start=True)

        action = str(action)
        output = str(output)

        if action not in self.knowledge['action set']:
            self.knowledge['action set'].append(action)

        try:  # AIRIS has knowledge of the action AND output
            self.knowledge[action].index(output)
        except KeyError:  # AIRIS has no knowledge of the action
            self.knowledge[action] = [output]
        except ValueError:  # AIRIS has knowledge of the action, but not of the output
            self.knowledge[action].append(output)

        ao_path = action + '/' + output
        if self.vis_change_list:
            change_list = self.vis_change_list
        elif self.aux_change_list:
            change_list = self.aux_change_list
        else:
            change_list = []

        for i, (x, y, prior_val, posterior_val, change_condition_id) in enumerate(change_list):
            condition_focus_value = prior_val

            if change_list is self.aux_change_list:
                index = x

            # action/output/focus_value/condition_id
            path = ao_path
            if change_condition_id == -1:
                change_condition_id = self.knowledge['last condition id']
                self.knowledge['last condition id'] += 1

            change_condition_id = str(change_condition_id)

            A = str(A)
            condition_focus_value = str(condition_focus_value)
            try:
                self.knowledge[path].index(A + condition_focus_value)
            except KeyError:
                self.knowledge[path] = [A + condition_focus_value]
            except ValueError:
                self.knowledge[path].append(A + condition_focus_value)

            path += '/' + A + condition_focus_value
            try:
                self.knowledge[path].index(change_condition_id)
            except KeyError:
                self.knowledge[path] = [change_condition_id]
            except ValueError:
                self.knowledge[path].append(change_condition_id)

            # cond/condition_id/focus_value
            try:
                self.knowledge['cond/'+change_condition_id].index(A+condition_focus_value)
            except KeyError:
                self.knowledge['cond/'+change_condition_id] = [A+condition_focus_value]
            except ValueError:
                self.knowledge['cond/'+change_condition_id].append(A+condition_focus_value)

            # focus_value/condition_id/[data]
            path = A + condition_focus_value
            if path not in self.knowledge['focus set']:
                self.knowledge['focus set'].append(path)

            try:
                self.knowledge[path].index(change_condition_id)
            except KeyError:
                self.knowledge[path] = [change_condition_id]
            except ValueError:
                self.knowledge[path].append(change_condition_id)

            path += '/' + change_condition_id + '/'
            self.knowledge[path + 'posterior_val'] = posterior_val

            if A == '':
                self.knowledge[path + 'focus_x'] = x
                self.knowledge[path + 'focus_y'] = y
            else:
                self.knowledge[path + 'focus_i'] = index

            self.knowledge[path + 'vis_data'] = copy.deepcopy(self.prior_vis_env)
            self.knowledge[path + 'aux_data'] = copy.deepcopy(self.prior_aux_env)

            self.knowledge[path + 'post_vis_data'] = copy.deepcopy(self.posterior_vis_env)
            self.knowledge[path + 'post_aux_data'] = copy.deepcopy(self.posterior_aux_env)

            self.knowledge[path + 'rel_abs'] = 0

            # /action_cause
            try:
                action_cause_temp = ""
                if self.knowledge[path + 'action_cause'] == action:
                    action_cause_temp = action
                self.knowledge[path + 'action_cause'] = action_cause_temp
            except KeyError:
                self.knowledge[path + 'action_cause'] = action

            # /vis_ref
            for ref_i, (ref_x, ref_y, ref_prior_val, ref_posterior_val, ref_change_condition_id) in enumerate(self.vis_change_list):
                if ref_i != self.vis_change_index:
                    dx = ref_x - focus_x
                    dy = ref_y - focus_y
                    vis_ref_data = (dx, dy, ref_prior_val, ref_posterior_val, ref_change_condition_id)
                    try:
                        self.knowledge[path + 'vis_ref'].index(vis_ref_data)
                    except ValueError:
                        self.knowledge[path + 'vis_ref'].append(vis_ref_data)
                    except KeyError:
                        self.knowledge[path + 'vis_ref'] = [vis_ref_data]

            # /vis_cause
            try:
                vis_cause_temp = []
                for cause_i, (cause_x, cause_y, cause_prior_val, cause_posterior_val, cause_change_condition_id) in enumerate(self.vis_change_list):
                    if cause_i != self.vis_change_index:
                        dx = cause_x - focus_x
                        dy = cause_y - focus_y
                        vis_ref_data = (dx, dy, cause_prior_val, cause_posterior_val, cause_change_condition_id)
                        if vis_ref_data in self.knowledge[path + 'vis_cause']:
                            vis_cause_temp.append(vis_ref_data)
                self.knowledge[path + 'vis_cause'] = vis_cause_temp
            except KeyError:
                for cause_i, (cause_x, cause_y, cause_prior_val, cause_posterior_val, cause_change_condition_id) in enumerate(self.vis_change_list):
                    if cause_i != self.vis_change_index:
                        dx = cause_x - focus_x
                        dy = cause_y - focus_y
                        vis_ref_data = (dx, dy, cause_prior_val, cause_posterior_val, cause_change_condition_id)
                        try:
                            self.knowledge[path + 'vis_cause'].append(vis_ref_data)
                        except KeyError:
                            self.knowledge[path + 'vis_cause'] = [vis_ref_data]

            # /vis_prev_cause
            try:
                vis_prev_cause_temp = []
                for prev_cause_i, (prev_cause_x, prev_cause_y, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id) in enumerate(self.vis_change_list_prev):
                    dx = prev_cause_x - focus_x
                    dy = prev_cause_y - focus_y
                    vis_ref_data = (dx, dy, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id)
                    if vis_ref_data in self.knowledge[path + 'vis_prev_cause']:
                        vis_prev_cause_temp.append(vis_ref_data)
                self.knowledge[path + 'vis_prev_cause'] = vis_prev_cause_temp
            except KeyError:
                for prev_cause_i, (prev_cause_x, prev_cause_y, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id) in enumerate(self.vis_change_list_prev):
                    dx = prev_cause_x - focus_x
                    dy = prev_cause_y - focus_y
                    vis_ref_data = (dx, dy, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id)
                    try:
                        self.knowledge[path + 'vis_prev_cause'].append(vis_ref_data)
                    except KeyError:
                        self.knowledge[path + 'vis_prev_cause'] = [vis_ref_data]
                
            # /aux_ref
            for ref_i, _, ref_prior_val, ref_posterior_val, ref_change_condition_id in self.aux_change_list:
                # if there's vis change data, store ALL the data
                if ref_i != focus_index or self.vis_change_list:
                    aux_ref_data = (ref_i, ref_prior_val, ref_posterior_val, ref_change_condition_id)
                    try:
                        self.knowledge[path + 'aux_ref'].append(aux_ref_data)
                    except KeyError:
                        self.knowledge[path + 'aux_ref'] = [aux_ref_data]

            # /aux_cause
            try:
                aux_cause_temp = []
                for cause_i, _, cause_prior_val, cause_posterior_val, cause_change_condition_id in self.aux_change_list:
                    # if there's vis change data, store ALL the data
                    if cause_i != focus_index or self.vis_change_list:
                        aux_ref_data = (cause_i, cause_prior_val, cause_posterior_val, cause_change_condition_id)
                        if aux_ref_data in self.knowledge[path + 'aux_cause']:
                            aux_cause_temp.append(aux_ref_data)
                self.knowledge[path + 'aux_cause'] = aux_cause_temp
            except KeyError:
                for cause_i, _, cause_prior_val, cause_posterior_val, cause_change_condition_id in self.aux_change_list:
                    # if there's vis change data, store ALL the data
                    if cause_i != focus_index or self.vis_change_list:
                        aux_ref_data = (cause_i, cause_prior_val, cause_posterior_val, cause_change_condition_id)
                        try:
                            self.knowledge[path + 'aux_cause'].append(aux_ref_data)
                        except KeyError:
                            self.knowledge[path + 'aux_cause'] = [aux_ref_data]

            # /aux_prev_cause
            try:
                aux_prev_cause_temp = []
                for prev_cause_i, _, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id in self.aux_change_list_prev:
                    aux_ref_data = (prev_cause_i, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id)
                    if aux_ref_data in self.knowledge[path + 'aux_prev_cause']:
                        aux_prev_cause_temp.append(aux_ref_data)
                self.knowledge[path + 'aux_prev_cause'] = aux_prev_cause_temp
            except KeyError:
                for prev_cause_i, _, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id in self.aux_change_list_prev:
                    aux_ref_data = (prev_cause_i, prev_cause_prior_val, prev_cause_posterior_val, prev_cause_change_condition_id)
                    try:
                        self.knowledge[path + 'aux_prev_cause'].append(aux_ref_data)
                    except KeyError:
                        self.knowledge[path + 'aux_prev_cause'] = [aux_ref_data]

            self.save_knowledge()

        else:
            pprint('not updating knowledge, no condition_focus_value',
                num_indents=num_indents, new_line_start=True)

        self.print_knowledge(num_indents=num_indents + 1, new_line_start=True)

        pprint('update complete. duration: %s' % (datetime.now() - start_time),
            num_indents=num_indents, new_line_start=True, draw_line=True)

        self.vis_change_list_prev = self.vis_change_list
        self.aux_change_list_prev = self.aux_change_list

    def compare_conditions(self, action, output, model_index, focus_value, condition_id, base_diff, condition_candidate_data, num_indents=0):

        # get the best condition
        pprint('getting the difference between memory and what we\'re currently looking at',
            num_indents=num_indents + 1, new_line_start=True)

        model = self.models[model_index]
        vis_model = copy.deepcopy(model.vis_env)
        aux_model = copy.deepcopy(model.aux_env)
        pprint(str(action), num_indents=num_indents + 1)
        pprint('model_index = %s' % model_index, num_indents=num_indents + 1)
        # action/output/focus_value/condition_id
        path = str(action) + '/' + str(output)
        pprint('path = ' + path, num_indents=num_indents + 1)
        pprint('focus_value = ' + str(focus_value), num_indents=num_indents + 1)
        data_path = str(focus_value) + '/' + str(condition_id) + '/'
        return_data = []

        if str(focus_value)[0] != 'A':
            for focus_x, focus_y in model.vis_count_pos[focus_value]:
                condition_dif = 0
                if condition_candidate_data:
                    try:
                        base_diff = condition_candidate_data[str(focus_value) + '/' + str(focus_x) + ',' + str(focus_y)][0]
                    except KeyError:
                        base_diff = None

                try:
                    if self.knowledge[data_path + 'vis_cause']:
                        cause_heap = copy.deepcopy(model.vis_count_heap)
                        while cause_heap:
                            cause_val = heapq.heappop(cause_heap)
                            for dx, dy, prior_val, _, _ in [item for item in self.knowledge[data_path + 'vis_cause'] if item[2] == cause_val]:
                                x, y = focus_x + dx, focus_y + dy
                                if 0 <= x < len(vis_model) and 0 <= y < len(vis_model[0]):
                                    if vis_model[x][y] != prior_val:
                                        condition_dif += abs(vis_model[x][y] - prior_val)

                                if base_diff is not None:
                                    if condition_dif > base_diff:
                                        break

                            if base_diff is not None:
                                if condition_dif > base_diff:
                                    break

                    else:
                        condition_data_array = self.knowledge[data_path + 'vis_data']
                        condition_aux_data_array = self.knowledge[data_path + 'aux_data']

                        condition_dif = np.sum(array_dif(vis_model, condition_data_array))
                        condition_dif += np.sum(array_dif(aux_model, condition_aux_data_array))

                except KeyError:
                    print ('Error: Missing vis_cause data for ', condition_id)
                    raise Exception

                try:
                    for i, _, prior_val, _, _ in self.knowledge[data_path + 'aux_cause']:
                        if i < len(aux_model):
                            if aux_model[i] != prior_val:
                                condition_dif += abs(aux_model[i] - prior_val)
                except KeyError:
                    print ('Error: Missing aux_cause data for ', condition_id)
                    raise Exception

                if not self.knowledge[data_path + 'action_cause'] == action:
                    condition_dif += 1

                for item in self.knowledge[data_path + 'vis_prev_cause']:
                    if item not in self.vis_change_list_prev:
                        condition_dif += 1

                if base_diff is not None:
                    if condition_dif < base_diff:
                        return_data.append((condition_dif, focus_value, condition_id, (focus_x, focus_y), data_path))
                    elif condition_dif == base_diff:
                        if condition_candidate_data[str(focus_value) + '/' + str(focus_x) + ',' + str(focus_y)][2] < condition_id:
                            return_data.append((condition_dif, focus_value, condition_id, (focus_x, focus_y), data_path))
                else:
                    return_data.append((condition_dif, focus_value, condition_id, (focus_x, focus_y), data_path))

        else:
            pprint('Aux focus_value = ' + str(focus_value), num_indents=num_indents + 1)
            condition_dif = 0
            try:
                for ind, _, prior_val, _, _ in self.knowledge[data_path + 'aux_cause']:
                    if aux_model[ind] != prior_val:
                        condition_dif += abs(aux_model[ind] - prior_val)

                    if base_diff:
                        if condition_dif > base_diff:
                            return None

                if not self.knowledge[data_path + 'vis_cause']:
                    condition_data_array = self.knowledge[data_path + 'vis_data']
                    condition_aux_data_array = self.knowledge[data_path + 'aux_data']

                    condition_dif = np.sum(array_dif(vis_model, condition_data_array))
                    condition_dif += np.sum(array_dif(aux_model, condition_aux_data_array))

            except KeyError:
                print('Error: Missing vis_cause data for ', condition_id)
                raise Exception

            try:
                for i, _, prior_val, _, _ in self.knowledge[data_path + 'aux_cause']:
                    if i < len(aux_model):
                        if aux_model[i] != prior_val:
                            condition_dif += abs(aux_model[i] - prior_val)
            except KeyError:
                print('Error: Missing aux_cause data for ', condition_id)
                raise Exception

            if not self.knowledge[data_path + 'action_cause'] == action:
                condition_dif += 1

            return_data = (condition_dif, focus_value, condition_id, (focus_index, None), data_path)

        # (best_condition_dif, focus_value, condition_id, (posx or auxindex, posy), path)
        return return_data

    def save_knowledge(self):
        # Save
        np.save('Knowledge.npy', self.knowledge)
        with open('Knowledge.json', 'w') as File:
            File.write(str(self.knowledge))

    def load_knowledge(self):
        # Load
        self.knowledge = np.load('Knowledge.npy').item()
