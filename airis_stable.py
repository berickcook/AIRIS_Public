import copy
import numpy as np
import heapq
from state import State
from copy import deepcopy
from collections import defaultdict
from operator import itemgetter
import uuid
import time


class AIRIS(object):

    def __init__(self, input_1d, input_2d, action_space):
        self.input_1D = input_1d
        self.input_2D = input_2d
        self.action_space = action_space
        self.given_goal_state = [[], []]
        self.best_state = 0
        self.best_action = None
        self.goal_action = None
        self.current_state = None
        self.states = None
        self.plan_depth = 1000
        self.action_plan = []
        self.round_to = 1
        self.last_change_1D = []
        self.last_change_2D = []
        self.pos_change_2D = []
        self.goal_reached = False
        self.goal_condition = None
        self.time_step = 0
        self.observe_mode = False
        self.idx2D = None
        self.innovate = False
        self.debug = False
        self.last_action = None
        self.knowledge = dict()
        self.applied_rules = set()
        self.applied_rules_loc = set()
        self.applied_exceptions = set()
        self.applied_exceptions_loc = set()
        self.prev_applied_rules = set()
        self.state_history = set()
        self.prev_action = None
        self.error_stop = False
        self.error_counter = 0

    # This function is used to communicate back and forth with an environment. It is called twice by the environment.
    # Once before an action is performed to get the current environment and return the action to perform back to the environment
    # And once after the action is taken to process the changes that occurred
    def capture_input(self, input_1d, input_2d, action, state, prior):

        # If this is the first call to the function from the environment
        if prior:
            starttime = time.time()
            if self.debug: print('\nCURRENT TIME', starttime, '\n')
            self.input_1D = input_1d.copy()
            self.input_2D = deepcopy(input_2d)

            # This creates a dict of all the positions of each value for faster reference than searching the input
            self.idx2D = defaultdict(list)
            for pos, val in np.ndenumerate(self.input_2D):
                self.idx2D[val].append(pos)

            # If there is no action plan to perform or if its in observation mode, initialize the state graph
            if not self.action_plan or self.observe_mode:
                if self.debug: print('base state prev action', self.prev_action)
                self.states = [State(self.input_1D, self.input_2D, self.idx2D, None, 0, 0, self.pos_change_2D, self.prev_action)]

            if self.given_goal_state and not self.observe_mode:
                # If there is no plan, make one, then return the first action
                if not self.action_plan:
                    self.make_plan(self.given_goal_state, False)
                    if self.action_plan:
                        if self.debug: print('planned')
                        if self.debug: print('capture input prior time:', round(time.time() - starttime, 10))
                        return self.action_plan.pop()

                # If there is a plan, return the next action
                else:
                    if self.debug: print('capture input prior time:', round(time.time() - starttime, 10))

                    return self.action_plan.pop()

            else:
                # A catch for a bug in the puzzle game where it can't handle more than one arrow key pressed at the same time
                if action == 'nothing' and self.time_step != 0:
                    if self.debug: print('Nothing event!')
                    raise IndexError
                new_state, predict_rule_2d, predict_rule_1d, uncertainty, exception_uncertainty, exceptions, no_rule_found = self.predict(action, 0, self.time_step)
                if self.debug: print('predict_rule_2d', predict_rule_2d)
                if self.debug: print('predict_rule_1d', predict_rule_1d)
                if self.debug: print('uncertainty', uncertainty)
                if self.debug: print('exception uncertainty', exception_uncertainty)
                if self.debug: print('exceptions', exceptions)
                self.states.append(new_state)
                if self.debug: print('Observed Compare: ', self.compare(self.states[1], self.given_goal_state, False, 1))
                return action, 1

        # If this is the second call to the function from the environment
        else:
            starttime = time.time()
            self.last_change_2D = []
            self.last_change_1D = []
            clear_plan = False
            self.last_action = action
            self.prev_applied_rules = self.applied_rules
            self.applied_rules = set()
            self.applied_rules_loc = set()
            self.applied_exceptions = set()
            self.applied_exceptions_loc = set()
            except_1d_create = False

            # Compare the environment state to the predicted state
            holddif = np.subtract(input_2d, self.states[state].input_2D)
            x2d, y2d = np.nonzero(holddif)

            holddif = np.subtract(input_1d, self.states[state].input_1D)
            hd = np.nonzero(holddif)

            # If there is a discrepancy between the 2D environment and the 2D prediction
            if len(x2d) or len(hd[0]):
                for difi, difx in enumerate(x2d):
                    key = str(difx) + ':' + str(y2d[difi])
                    if self.debug: print('prediction error key', key)
                    rule_data_exists = True
                    # See if there is an existing rule that was applied to the prediction
                    try:
                        rule_data = self.states[state].applied_rules[key]
                        if rule_data[3] is None:
                            raise KeyError
                        else:
                            if rule_data[3][1] == 0:
                                raise KeyError
                    except KeyError:
                        rule_data_exists = False
                        pass
                    # If there is an existing rule, update the rule with a new exception
                    if rule_data_exists:
                        try:
                            if self.debug: print('error rule_data', rule_data)
                            if self.debug: print('pre creating exception')
                            new_except = self.update_rule(rule_data, False, True, key, input_2d, input_1d, state, None, None, None, None)
                            self.applied_exceptions.add(new_except[0])
                            self.applied_exceptions_loc.add((new_except[1], difx, y2d[difi]))
                            if self.debug: print('post creating exception')
                            clear_plan = True
                        except IndexError:
                            if self.debug: print('passing')
                            pass

            # Do the same as above for the 1D data
            for di, data in enumerate(self.states[state].input_1D):
                if input_1d[di] != data:
                    try:
                        for key in self.states[state].applied_rules.keys():
                            rule_data = self.states[state].applied_rules[key]
                            loc_key = key.split(':')
                            loc_x = int(loc_key[0])
                            loc_y = int(loc_key[1])
                            if rule_data[7]:
                                if self.debug: print(rule_data[7])
                                try:
                                    if di in rule_data[7].keys() and input_1d[di] - self.input_1D[di] != rule_data[7][di][0][2]:
                                        new_except = self.update_rule(rule_data, False, True, key, input_2d, input_1d, state, None, None, None, None)
                                        self.applied_exceptions.add(new_except[0])
                                        self.applied_exceptions_loc.add((new_except[1], loc_x, loc_y))
                                        if self.debug: print('created 1d exception')
                                        clear_plan = True
                                        except_1d_create = True
                                except IndexError:
                                    pass
                    except KeyError:
                        pass

            # Check each exception location again to see if the value did not change at all in the environment and create additional exceptions if needed
            for loc_key in self.states[state].applied_exceptions.keys():
                key = loc_key.split(':')
                loc_x = int(key[0])
                loc_y = int(key[1])
                if self.input_2D[loc_x][loc_y] == input_2d[loc_x][loc_y]:
                    exception_data = self.states[state].applied_exceptions[loc_key]
                    if self.debug: print('pre updating exception')
                    new_except = self.update_rule(exception_data, False, True, loc_key, input_2d, input_1d, state, None, None, None, None)
                    self.applied_exceptions.add(new_except[0])
                    self.applied_exceptions_loc.add((new_except[1], loc_x, loc_y))
                    if self.debug: print('post updating exception')

            if input_2d:
                # Compare the previous environment state to the current environment state
                holddif = np.subtract(input_2d, self.input_2D)
                x2d, y2d = np.nonzero(holddif)

                if len(x2d):
                    self.pos_change_2D = []

                for difi, difx in enumerate(x2d):
                    self.pos_change_2D.append((difx, y2d[difi]))

                holddif = np.subtract(input_1d, self.input_1D)
                hd = np.nonzero(holddif)

                if len(x2d) or len(hd[0]):
                    for difi, difx in enumerate(x2d):
                        self.last_change_2D.append([difx, y2d[difi], self.input_2D[difx][y2d[difi]], round(input_2d[difx][y2d[difi]] - self.input_2D[difx][y2d[difi]], self.round_to), input_2d[difx][y2d[difi]]])

                    for di, data in enumerate(input_1d):
                        if self.input_1D[di] != data:
                            self.last_change_1D.append([di, self.input_1D[di], round(data - self.input_1D[di], self.round_to), data])

            if self.debug: print('last change 2D', self.last_change_2D)
            if self.debug: print('last change 1D', self.last_change_1D)
            # If there was a change, create a rule (discarding the new rule if the rule already exists)
            for cox, coy, cod, cord, coad in self.last_change_2D:
                rule_id = str(uuid.uuid4())[:6]
                if input_2d[cox][coy] != self.states[state].input_2D[cox][coy]:
                    clear_plan = True

                new_rule = self.create_rule(action, cox, coy, cod, cord, coad, rule_id, state, self.states[state].prev_state, self.input_1D, input_1d, self.input_2D, input_2d, self.time_step)
                self.applied_rules.add(new_rule)
                self.applied_rules_loc.add((new_rule, cox, coy))
                if self.debug: print('Attempted to create rule', new_rule)

                if self.debug: print('last change 2D item', cox, coy, cod, cord, coad)

            # If there was a rule applied to a location but no change occurred there, then create a "No change" rule
            for loc_key in self.states[state].applied_rules.keys():
                rule_id = str(uuid.uuid4())[:6]
                rule_data = self.states[state].applied_rules[loc_key]
                key = loc_key.split(':')
                loc_x = int(key[0])
                loc_y = int(key[1])
                if rule_data[1] == 'None' and self.input_2D[loc_x][loc_y] - input_2d[loc_x][loc_y] == 0:
                    new_rule = self.create_rule(action, loc_x, loc_y, self.input_2D[loc_x][loc_y], 0, input_2d[loc_x][loc_y], rule_id, state, self.states[state].prev_state, self.input_1D, input_1d, self.input_2D, input_2d, self.time_step)
                    if self.debug: print('No change rule created', new_rule, rule_id)

            if self.debug: print('self.applied_rules: ', self.applied_rules)
            if self.debug: print('self.applied_exceptions: ', self.applied_exceptions)
            if self.debug: print('self.prev_applied_rules: ', self.prev_applied_rules)
            # Update all new rules with relevant data from other new rules
            self.update_rule(None, True, False, None, input_2d, None, None, self.applied_rules, None, self.prev_applied_rules, self.applied_rules_loc)
            # Update all new exceptions with relevant data from other new exceptions
            self.update_rule(None, True, True, None, None, None, None, self.applied_rules, self.applied_exceptions, self.prev_applied_rules, None)

            # Clear the rules / exceptions of irrelevant conditions
            for rule in self.applied_rules_loc:
                self.clean_rule(rule, input_2d)
            for rule in self.applied_exceptions_loc:
                self.clean_rule(rule, input_2d)

            # If this was the last action in the plan, then add the previous state to state_history
            if not self.action_plan:
                if (str(self.input_1D), str(self.input_2D), action) not in self.state_history:
                    if self.debug: print('adding this state with', action)
                    if self.debug: print('full state history addition', ((str(self.input_1D), str(self.input_2D)), action))
                    if self.debug: print('Added to state history', self.time_step, action, self.input_1D, '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                    if self.debug:
                        format_state = deepcopy(self.input_2D)

                        t_format = np.array(format_state).T

                        for r, x in enumerate(t_format):
                            x = ["%.0f" % i for i in x]
                            for i, item in enumerate(x):
                                if item == '0':
                                    x[i] = '  '
                                elif int(item) < 10:
                                    x[i] = ' ' + x[i]
                            if self.debug: print(x, r)
                        if self.debug: print('')
                        if self.debug: print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")

                self.state_history.add(((str(self.input_1D), str(self.input_2D)), action))
                if self.debug: print('state history length ', len(self.state_history))

            # If there was an unxpected change during plan execution, abandon the plan
            if clear_plan:
                self.action_plan = []

            if self.debug: print('Actual state', self.time_step, action, input_1d, '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            if self.debug:
                format_state = deepcopy(input_2d)

                t_format = np.array(format_state).T

                for r, x in enumerate(t_format):
                    x = ["%.0f" % i for i in x]
                    for i, item in enumerate(x):
                        if item == '0':
                            x[i] = '  '
                        elif int(item) < 10:
                            x[i] = ' ' + x[i]
                    if self.debug: print(x, r)
                if self.debug: print('')
                if self.debug: print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")

            if self.debug: print('++++++++++ capture input post time', round(time.time() - starttime, 10))
            self.time_step += 1
            self.prev_action = action

    def make_plan(self, given_goal, generated):
        starttime = time.time()
        self.goal_reached = True

        self.current_state = 0
        self.best_state = 0
        dupes = 0
        compare_diff, best_action, self.goal_reached = self.compare(self.states[0], given_goal, generated, 0)
        if self.debug: print('error goal reached', compare_diff, best_action, self.goal_reached)
        if self.goal_reached:
            self.best_action = best_action
            goal_state, predict_rules_2d, predict_rules_1d, _, _, _, no_rule_found = self.predict(self.best_action, self.best_state, self.states[self.best_state].step + 1)
            if (self.states[self.best_state].hash(), self.best_action) not in self.state_history and not goal_state.anti_goal:
                self.states.append(goal_state)
                self.best_state = len(self.states) - 1
                if self.debug: print('Goal action from base state not in history')
            else:
                self.goal_reached = False
        state_heap = [(0, self.current_state, 0)]
        confidence_heap = []
        state_set = {(self.states[0].hash(), None)}
        depth = 0
        while not self.goal_reached:
            depth += 1

            if state_heap and depth <= self.plan_depth:
                self.current_state = heapq.heappop(state_heap)[1]
            else:
                if depth > self.plan_depth:
                    self.plan_depth += 1000
                    if self.debug: print('Plan limit reached', self.plan_depth)
                    far = sorted(confidence_heap, key=itemgetter(1))
                    find_state = -1
                    while self.states[far[find_state][1]].anti_goal:
                        find_state -= 1
                    self.best_state = far[find_state][1]


                    if self.debug: print('Trying furthest state')
                    format_state = deepcopy(self.states[self.states[self.best_state].prev_state].input_2D)

                    t_format = np.array(format_state).T

                    for r, x in enumerate(t_format):
                        x = ["%.0f" % i for i in x]
                        for i, item in enumerate(x):
                            if item == '0':
                                x[i] = '  '
                            elif int(item) < 10:
                                x[i] = ' ' + x[i]
                        if self.debug: print(x, r)
                    if self.debug: print('')
                    if self.debug: print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")
                else:
                    if self.debug: print('no more states', len(confidence_heap), depth, self.plan_depth)
                    if confidence_heap:
                        if self.debug: print('confidence heap ', confidence_heap)
                        self.best_state = heapq.heappop(confidence_heap)[1]
                        while confidence_heap and (self.states[self.states[self.best_state].prev_state].hash(), self.states[self.best_state].action) in self.state_history:
                            if self.debug: print('confidence heap ', confidence_heap)
                            if self.debug: print('in history ', self.best_state, self.states[self.best_state].prev_state, self.states[self.best_state].action)
                            if self.debug:
                                format_state = deepcopy(self.states[self.states[self.best_state].prev_state].input_2D)

                                t_format = np.array(format_state).T

                                for r, x in enumerate(t_format):
                                    x = ["%.0f" % i for i in x]
                                    for i, item in enumerate(x):
                                        if item == '0':
                                            x[i] = '  '
                                        elif int(item) < 10:
                                            x[i] = ' ' + x[i]
                                    if self.debug: print(x, r)
                                if self.debug: print('')
                                if self.debug: print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")

                            self.best_state = heapq.heappop(confidence_heap)[1]
                        if not confidence_heap:
                            if (self.states[self.states[self.best_state].prev_state].hash(), self.states[self.best_state].action) in self.state_history:
                                if self.debug: print('All unknowns already in history. Resetting history')
                                self.state_history = set()

                            self.plan_depth += 10
                    else:
                        if self.debug: print('no more confidence heap. Increasing plan depth')
                        self.plan_depth += 1
                break

            for act in self.action_space:
                new_state, predict_rules_2d, predict_rules_1d, _, _, _, no_rule_found = self.predict(act, self.current_state, self.states[self.current_state].step + 1)
                check_hash = new_state.hash()
                confidence = 0
                total_predictions = len(predict_rules_2d.keys())

                predict_sum = 0
                for key in predict_rules_2d.keys():
                    predict_sum -= predict_rules_2d[key][0]

                total_exceptions = len(new_state.applied_exceptions)
                exception_sum = 0
                for key in new_state.applied_exceptions.keys():
                    exception_sum -= new_state.applied_exceptions[key][0]

                if total_predictions or total_exceptions:
                    confidence = (predict_sum + exception_sum) / (total_predictions + total_exceptions)

                new_state.confidence = confidence
                if self.debug: print('Confidence of prediction  = ', confidence)

                compare_diff, best_action, _ = self.compare(new_state, given_goal, generated, len(self.states) - 1)

                if check_hash not in state_set:
                    if self.debug: print('not a duplicate state')
                    state_set.add(check_hash)
                    self.states.append(new_state)
                    self.best_state = len(self.states) - 1

                    if compare_diff is not None:
                        if compare_diff == 0:
                            self.goal_reached = True

                    if self.goal_reached and not new_state.anti_goal:
                        if self.debug: print('GOAL REACHED')
                        self.best_state = len(self.states) - 1
                        self.best_action = best_action
                        goal_state, predict_rules_2d, predict_rules_1d, _, _, _, no_rule_found = self.predict(self.best_action, self.best_state, self.states[self.best_state].step + 1)

                        if (self.states[self.best_state].hash(), self.best_action) not in self.state_history and not goal_state.anti_goal:
                            self.states.append(goal_state)
                            self.best_state = len(self.states) - 1
                            if self.debug: print('Goal action not in history, breaking', self.best_state, self.best_action, self.states[self.best_state].action)
                            break
                        else:
                            if self.debug: print('Goal action in history, continuing to plan')
                            if not new_state.anti_goal or confidence != 1:
                                if confidence == 1 and not new_state.anti_goal:
                                    heapq.heappush(state_heap, (new_state.step, len(self.states) - 1, new_state.step))
                                    if self.debug: print('added to state heap 1')
                                if confidence == 1 and no_rule_found:
                                    heapq.heappush(confidence_heap, (0.99, len(self.states) - 1))
                                    if self.debug: print('no rule added to confidence heap')
                                elif confidence != 1:
                                    heapq.heappush(confidence_heap, (confidence, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 1')

                            else:
                                if confidence == 1 and no_rule_found:
                                    heapq.heappush(confidence_heap, (0.99, len(self.states) - 1))

                                    if self.debug: print('no rule added to confidence heap')
                                elif confidence != 1:
                                    heapq.heappush(confidence_heap, (confidence + 1000, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 2')

                            self.goal_reached = False
                    else:
                        if self.goal_reached:
                            self.goal_reached = False
                            if self.debug: print('goal reached in history')
                        if self.debug: print('State not yet predicted, adding')
                        if self.debug: print('heap conditions', new_state.anti_goal, confidence, compare_diff, no_rule_found)
                        if not new_state.anti_goal or confidence != 1:
                            if confidence == 1 and not new_state.anti_goal:
                                if compare_diff is not None:
                                    heapq.heappush(state_heap, (compare_diff + new_state.step, len(self.states) - 1, new_state.step))
                                    if self.debug: print('added to state heap 3')
                                else:
                                    heapq.heappush(state_heap, (new_state.step, len(self.states) - 1, new_state.step))
                                    if self.debug: print('added to state heap 4')
                            if confidence == 1 and no_rule_found:
                                if compare_diff is not None:
                                    heapq.heappush(confidence_heap, (0.99 + compare_diff + 1, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 5')
                                else:
                                    heapq.heappush(confidence_heap, (0.99, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 6')
                                if self.debug: print('no rule added to confidence heap')
                            elif confidence != 1:
                                if compare_diff is not None:
                                    heapq.heappush(confidence_heap, (confidence + compare_diff, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 7')
                                else:
                                    heapq.heappush(confidence_heap, (confidence, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 8')

                        else:
                            if confidence == 1 and no_rule_found:
                                if compare_diff is not None:
                                    heapq.heappush(confidence_heap, (0.99 + compare_diff + 1, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 9')
                                else:
                                    heapq.heappush(confidence_heap, (0.99, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 10')

                                if self.debug: print('no rule added to confidence heap')
                            elif confidence == 1 and new_state.anti_goal:
                                if compare_diff is not None:
                                    heapq.heappush(confidence_heap, (confidence + 6000 + compare_diff, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 13')
                                else:
                                    heapq.heappush(confidence_heap, (confidence + 6000, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 14')
                            elif confidence != 1:
                                if compare_diff is not None:
                                    heapq.heappush(confidence_heap, (confidence + 1000 + compare_diff, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 15')
                                else:
                                    heapq.heappush(confidence_heap, (confidence + 1000, len(self.states) - 1))
                                    if self.debug: print('added to confidence heap 16')

                else:
                    dupes += 1
                    if self.debug: print('State already predicted', new_state.action, self.goal_reached)
                    self.states.append(new_state)
                    if self.debug: print('heap conditions', new_state.anti_goal, confidence, compare_diff)
                    if not new_state.anti_goal or confidence != 1:
                        if confidence == 1 and no_rule_found:
                            if compare_diff is not None:
                                heapq.heappush(confidence_heap, (0.99 + compare_diff + 1, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 17')
                            else:
                                heapq.heappush(confidence_heap, (0.99, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 18')
                            if self.debug: print('no rule added to confidence heap')
                        elif confidence != 1:
                            if compare_diff is not None:
                                heapq.heappush(confidence_heap, (confidence + compare_diff, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 19')
                            else:
                                heapq.heappush(confidence_heap, (confidence, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 20')

                    else:
                        if confidence == 1 and no_rule_found:
                            if compare_diff is not None:
                                heapq.heappush(confidence_heap, (0.99 + compare_diff + 1, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 21')
                            else:
                                heapq.heappush(confidence_heap, (0.99, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 22')
                            if self.debug: print('no rule added to confidence heap')
                        if confidence == 1 and new_state.anti_goal:
                            if compare_diff is not None:
                                heapq.heappush(confidence_heap, (confidence + 6000 + compare_diff, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 23')
                            else:
                                heapq.heappush(confidence_heap, (confidence + 6000, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 24')
                        elif confidence != 1:
                            if compare_diff is not None:
                                heapq.heappush(confidence_heap, (confidence + 1000 + compare_diff, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 25')
                            else:
                                heapq.heappush(confidence_heap, (confidence + 1000, len(self.states) - 1))
                                if self.debug: print('added to confidence heap 26')

            if self.debug: print('planning debug - state heap', len(state_heap), 'conf heap', len(confidence_heap), 'goal reached', self.goal_reached)

        if self.best_state != 0 or (self.goal_reached and self.best_state == 0):
            if self.debug: print('best state', self.best_state)
            self.action_plan = [(self.states[self.best_state].action, self.best_state)]
            prev_state = self.states[self.best_state].prev_state
            current_act = None
            if prev_state > 0:
                current_act = self.states[prev_state].action

            while prev_state > 0:
                self.action_plan.append((current_act, prev_state))
                prev_state = self.states[prev_state].prev_state
                if prev_state > 0:
                    current_act = self.states[prev_state].action

            if self.debug: print('Action Plan: ', self.action_plan)

            for plan in self.action_plan:
                with open('./plan_log/' + str(self.time_step) + '.txt', 'a') as f:
                    f.write(str(self.states[plan[1]].input_2D) + '\n')

                if self.debug: print('plan state', plan[1], self.states[plan[1]].action, self.states[plan[1]].applied_rule_ids, self.states[plan[1]].compare, self.states[plan[1]].anti_goal, self.states[plan[1]].input_1D, self.states[plan[1]].step, self.plan_depth, self.states[plan[1]].confidence, self.states[plan[1]].last_pos_change_2d, '+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
                if self.debug:
                    format_state = deepcopy(self.states[plan[1]].input_2D)

                    t_format = np.array(format_state).T

                    for r, x in enumerate(t_format):
                        x = ["%.0f" % i for i in x]
                        for i, item in enumerate(x):
                            if item == '0':
                                x[i] = '  '
                            elif int(item) < 10:
                                x[i] = ' ' + x[i]
                        if self.debug: print(x, r)
                    if self.debug: print('')
                    if self.debug: print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")

        if self.debug: print('++++++++++ make plan time:', round(time.time() - starttime, 10))
        if self.debug: print('---------- make plan states / dupes:', len(self.states), dupes)

    def predict(self, act, base_state, step):
        starttime = time.time()
        if self.states[base_state].action is None:
            predict_state = State(self.states[base_state].input_1D, self.states[base_state].input_2D, self.states[base_state].input_2D_idx, act, base_state, self.states[base_state].step + 1, self.states[base_state].last_pos_change_2d, self.states[base_state].prev_action)
        else:
            predict_state = State(self.states[base_state].input_1D, self.states[base_state].input_2D, self.states[base_state].input_2D_idx, act, base_state, self.states[base_state].step + 1, self.states[base_state].last_pos_change_2d, self.states[base_state].action)
        state_pos_change_2D = self.states[base_state].last_pos_change_2d
        predict_heap_2d = []
        predict_rule_2d = dict()
        predict_rule_1d = dict()
        exceptions = dict()
        act_found = False
        no_rule_found = False
        no_rule_count = 0

        if len(predict_state.input_2D) > 0:
            check_pos = []
            orig_pos = set()
            check_set = set()
            if state_pos_change_2D:
                if self.debug: print('checking last changed positions')
                check_pos = copy.deepcopy(state_pos_change_2D)
                orig_pos = set(copy.deepcopy(state_pos_change_2D))
                check_set = set(copy.deepcopy(state_pos_change_2D))
            else:
                if self.debug: print('checking all positions')
                for x, vx in enumerate(predict_state.input_2D):
                    for y, vy in enumerate(predict_state.input_2D[x]):
                        check_pos.append((x, y))
                orig_pos = set(copy.deepcopy(check_pos))
                check_set = set(copy.deepcopy(check_pos))

            heapq.heapify(check_pos)

            while len(check_pos):
                pos = heapq.heappop(check_pos)
                if self.debug: print(pos[0], pos[1])
                try:
                    val = predict_state.input_2D[pos[0]][pos[1]]
                except IndexError:
                    continue
                rules = []

                try:
                    rules = self.knowledge['2d/' + str(val)]
                except KeyError:
                    pass

                if len(rules) > 0:
                    if self.debug: print('\npos', pos, val)
                    dix = pos[0]
                    diy = pos[1]

                    for ri, rule in enumerate(rules):
                        match = 0
                        uncertainty = 0
                        abs_pos = False
                        match_count = 0
                        condition_group = self.knowledge['2d/' + str(val) + '/' + str(rule)]
                        exception_heap = []
                        if self.debug: print('checking rule ', rule)

                        if self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/combined']:
                            if self.debug: print('rule combined, skipping')
                            continue

                        try:
                            if str(dix) + ':' + str(diy) in self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/apos'].keys():
                                abs_pos = True
                                if self.debug: print('abs pos found')
                            else:
                                if len(self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/apos'].keys()) != 0:
                                    match_count += 1
                                    if self.debug: print('abs pos not found')
                                    continue
                        except KeyError:
                            pass

                        try:
                            rel_condition_data = self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/inclusions/rel']
                            for ci, condition in enumerate(rel_condition_data):
                                crx, cry, cod, cor = condition
                                if predict_state.input_2D[dix + crx][diy + cry] == cod:
                                    pass
                        except IndexError:
                            continue

                        try:
                            act_data = self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/act'][act]
                            if act_data[0] / act_data[1] == 1:
                                match += 1
                                match_count += 1
                                if self.debug: print('act found', match, match_count)
                                act_found = True

                        except KeyError:
                            if len(self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/act'].keys()) == 0:
                                match += 1
                            match_count += 1
                            if self.debug: print('act not found', match, match_count)
                            continue

                        rel_heap = []
                        rel_data = self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/rel']
                        for rel_key in self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/rel'].keys():
                            heapq.heappush(rel_heap, (-(rel_data[rel_key][0] / rel_data[rel_key][1]), rel_key))

                        change_type = ('rel', rel_heap[0][1])

                        if change_type[1] == 0:
                            match = match_count

                        hold_rel = dict()

                        rel_condition_data = self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/inclusions/rel']

                        for ci, condition in enumerate(rel_condition_data):
                            crx, cry, cod, cor = condition
                            try:
                                if hold_rel[str(dix + crx) + ':' + str(diy + cry)]:
                                    pass
                            except KeyError:
                                hold_rel[str(dix + crx) + ':' + str(diy + cry)] = []

                            try:
                                if self.debug: print('rule', rule, 'condition group', condition_group)
                                if self.debug: print('rel condition data', rel_condition_data)
                                if self.debug: print('CRX', crx, 'CRY', cry, 'COD', cod, 'ACTUAL', predict_state.input_2D[dix + crx][diy + cry])
                                if predict_state.input_2D[dix + crx][diy + cry] == cod:
                                    heapq.heappush(hold_rel[str(dix + crx) + ':' + str(diy + cry)], -1)
                                else:
                                    if cod != 0 and predict_state.input_2D[dix + crx][diy + cry] != 0:
                                        if cod < predict_state.input_2D[dix + crx][diy + cry]:
                                            heapq.heappush(hold_rel[str(dix + crx) + ':' + str(diy + cry)], -(cod / predict_state.input_2D[dix + crx][diy + cry]))
                                        else:
                                            heapq.heappush(hold_rel[str(dix + crx) + ':' + str(diy + cry)], -(predict_state.input_2D[dix + crx][diy + cry] / cod))
                                    else:
                                        heapq.heappush(hold_rel[str(dix + crx) + ':' + str(diy + cry)], 0)

                            except IndexError:
                                heapq.heappush(hold_rel[str(dix + crx) + ':' + str(diy + cry)], 0)

                        for key in hold_rel.keys():
                            if -(hold_rel[key][0]) != 1:
                                match += -(hold_rel[key][0])
                                if hold_rel[key][0] != 0:
                                    uncertainty += -(hold_rel[key][0])
                                else:
                                    uncertainty += 1
                            else:
                                match += 1
                            match_count += 1
                            if self.debug: print('hold rel', match, match_count)

                        predict_rule_1d = dict()
                        try:
                            rule_1d_data = self.knowledge['1d/' + rule]
                            for di in rule_1d_data:
                                predict_rule_1d[di] = []
                                di_heap = []
                                condition_group_1d = self.knowledge['1d/' + str(di) + '/' + str(rule)]
                                oval_data = self.knowledge['1d/' + str(di) + '/' + str(condition_group_1d) + '/oval']
                                oval = predict_state.input_1D[di]
                                try:
                                    check = oval_data[oval]
                                    match += 1
                                    match_count += 1
                                    if self.debug: print('1d found', match, match_count)
                                except KeyError:
                                    for key in oval_data.keys():
                                        if key != 0 and oval != 0:
                                            if key > 0 and oval > 0:
                                                if key < oval:
                                                    heapq.heappush(di_heap, (-(key / oval), key))
                                                else:
                                                    heapq.heappush(di_heap, (-(oval / key), key))
                                            elif key < 0 and oval < 0:
                                                if key > oval:
                                                    heapq.heappush(di_heap, (-(-key / -oval), key))
                                                else:
                                                    heapq.heappush(di_heap, (-(-oval / -key), key))
                                            else:
                                                if oval < 0:
                                                    hold_val = -oval + key
                                                    heapq.heappush(di_heap, (-(key / hold_val), key))
                                                else:
                                                    hold_val = -key + oval
                                                    heapq.heappush(di_heap, (-(oval / hold_val), key))
                                        else:
                                            heapq.heappush(di_heap, (0, key))

                                    if di_heap:
                                        if -(di_heap[0][0]) != 1:
                                            match += -(di_heap[0][0])
                                            if di_heap[0][0] != 0:
                                                uncertainty += -(di_heap[0][0])
                                            else:
                                                uncertainty += 1
                                        else:
                                            match += 1
                                        match_count += 1
                                        if self.debug: print('other 1d', di_heap[0][1], match, match_count)

                                rel_1d_data = self.knowledge['1d/' + str(di) + '/' + str(condition_group_1d) + '/rel']
                                for rel_key in rel_1d_data.keys():
                                    heapq.heappush(predict_rule_1d[di], (-(rel_1d_data[rel_key][0] / rel_1d_data[rel_key][1]), 'rel', rel_key, condition_group_1d, self.states[base_state].input_1D[di]))

                        except KeyError:
                            pass

                        exception_heap = []
                        group_exists = True
                        try:
                            exception_groups = self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/exceptions']
                        except KeyError:
                            group_exists = False

                        if group_exists:
                            for exception_group in exception_groups:
                                exception_match = 0
                                exception_match_count = 0
                                exception_uncertainty = 0

                                exception_act_data = self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/exceptions/' + str(exception_group) + '/act']

                                try:
                                    if exception_act_data[act][0] / exception_act_data[act][1] == 1:
                                        exception_match += 1
                                        exception_match_count += 1
                                        if self.debug: print('ex act found', exception_match, exception_match_count)
                                except KeyError:
                                    if len(exception_act_data.keys()) == 0:
                                        exception_match += 1
                                    exception_match_count += 1
                                    if self.debug: print('ex act not found', exception_match, exception_match_count)

                                hold_except_rel = dict()
                                exception_rel_condition_data = self.knowledge['2d/' + str(val) + '/' + str(condition_group) + '/exceptions/' + str(exception_group) + '/rel']

                                for ci, condition in enumerate(exception_rel_condition_data):
                                    crx, cry, cod, cor = condition

                                    try:
                                        if hold_except_rel[str(dix + crx) + ':' + str(diy + cry)]:
                                            pass
                                    except KeyError:
                                        hold_except_rel[str(dix + crx) + ':' + str(diy + cry)] = []

                                    try:
                                        if predict_state.input_2D[dix + crx][diy + cry] == cod:
                                            heapq.heappush(hold_except_rel[str(dix + crx) + ':' + str(diy + cry)], -1)
                                        else:
                                            if cod != 0 and predict_state.input_2D[dix + crx][diy + cry] != 0:
                                                if cod < predict_state.input_2D[dix + crx][diy + cry]:
                                                    heapq.heappush(hold_except_rel[str(dix + crx) + ':' + str(diy + cry)], -(cod / predict_state.input_2D[dix + crx][diy + cry]))
                                                else:
                                                    heapq.heappush(hold_except_rel[str(dix + crx) + ':' + str(diy + cry)], -(predict_state.input_2D[dix + crx][diy + cry] / cod))
                                            else:
                                                heapq.heappush(hold_except_rel[str(dix + crx) + ':' + str(diy + cry)], 0)
                                    except IndexError:
                                        heapq.heappush(hold_except_rel[str(dix + crx) + ':' + str(diy + cry)], 0)

                                for key in hold_except_rel.keys():
                                    if -(hold_except_rel[key][0]) != 1:
                                        exception_match += -(hold_except_rel[key][0])
                                        if hold_except_rel[key][0] != 0:
                                            exception_uncertainty += -(hold_except_rel[key][0])
                                        else:
                                            exception_uncertainty += 1
                                    else:
                                        exception_match += 1
                                    exception_match_count += 1
                                    if self.debug: print('ex hold_rel', exception_match, exception_match_count)

                                try:
                                    rule_1d_data = self.knowledge['1d/' + rule]
                                    for di in rule_1d_data:
                                        di_heap = []
                                        condition_group_1d = self.knowledge['1d/' + str(di) + '/' + str(rule)]
                                        oval_data = self.knowledge['1d/' + str(di) + '/' + str(condition_group_1d) + '/exceptions/' + str(exception_group) + '/oval']
                                        oval = predict_state.input_1D[di]
                                        try:
                                            check = oval_data[oval]
                                            exception_match += 1
                                            exception_match_count += 1
                                            if self.debug: print('ex 1d found', exception_match, exception_match_count)
                                        except KeyError:
                                            for key in oval_data.keys():
                                                if key != 0 and oval != 0:
                                                    if key > 0 and oval > 0:
                                                        if key < oval:
                                                            heapq.heappush(di_heap, (-(key / oval), key))
                                                        else:
                                                            heapq.heappush(di_heap, (-(oval / key), key))
                                                    elif key < 0 and oval < 0:
                                                        if key > oval:
                                                            heapq.heappush(di_heap, (-(-key / -oval), key))
                                                        else:
                                                            heapq.heappush(di_heap, (-(-oval / -key), key))
                                                    else:
                                                        if oval < 0:
                                                            hold_val = -oval + key
                                                            heapq.heappush(di_heap, (-(key / hold_val), key))
                                                        else:
                                                            hold_val = -key + oval
                                                            heapq.heappush(di_heap, (-(oval / hold_val), key))
                                                else:
                                                    heapq.heappush(di_heap, (0, key))

                                            if di_heap:
                                                if -(di_heap[0][0]) != 1:
                                                    exception_match += -(di_heap[0][0])
                                                    if di_heap[0][0] != 0:
                                                        exception_uncertainty += -(di_heap[0][0])
                                                    else:
                                                        exception_uncertainty += 1
                                                else:
                                                    exception_match += 1
                                                exception_match_count += 1
                                                if self.debug: print('ex 1d other', di_heap[0][1], exception_match, exception_match_count, 'oval data', self.knowledge['1d/' + str(di) + '/' + str(condition_group_1d) + '/exceptions/' + str(exception_group) + '/oval'])

                                except KeyError:
                                    pass

                                if self.debug: print('Exception Data: ', rule, exception_group, -(exception_match / exception_match_count))
                                heapq.heappush(exception_heap, (-(exception_match / exception_match_count), rule, condition_group, exception_group, str(dix) + ':' + str(diy), exception_uncertainty, predict_rule_1d, dix, diy, val))

                        if exception_heap:
                            heapq.heappush(predict_heap_2d, (-(match / match_count), rule, condition_group, change_type, abs_pos, str(dix) + ':' + str(diy), uncertainty, predict_rule_1d, dix, diy, exception_heap[0], val))
                        elif change_type[1] == 0:
                            heapq.heappush(predict_heap_2d, (-(match / match_count), rule, condition_group, change_type, abs_pos, str(dix) + ':' + str(diy), uncertainty, predict_rule_1d, dix, diy, [0], val))
                        else:
                            heapq.heappush(predict_heap_2d, (-(match / match_count), rule, condition_group, change_type, abs_pos, str(dix) + ':' + str(diy), uncertainty, predict_rule_1d, dix, diy, [1], val))
                        if self.debug: print('Rule ID', rule)
                        try:
                            if self.debug: print('exception match', exception_heap[0][0], str(dix) + ':' + str(diy))
                        except IndexError:
                            if self.debug: print('exception match', 'NONE', str(dix) + ':' + str(diy))
                        if self.debug: print('prediction match', -(match / match_count), str(dix) + ':' + str(diy))

                    if not predict_heap_2d:
                        if self.debug: print('no applicable rules found')
                        heapq.heappush(predict_heap_2d, (-0.01, 'None', None, None, None, str(dix) + ':' + str(diy), 0, None, dix, diy, [0], val))

                    try:
                        if self.debug: print('best pre-check exception match', predict_heap_2d[0][10][0], str(dix) + ':' + str(diy), predict_heap_2d[0][1])
                        if self.debug: print('best pre-check prediction match', predict_heap_2d[0][0], str(dix) + ':' + str(diy), predict_heap_2d[0][1])

                        best_result_2d = None

                        while predict_heap_2d[0][3] is not None and predict_heap_2d[0][3][1] == 0:
                            if self.debug: print('best result is a no change rule')
                            best_result_2d = [predict_heap_2d[0]]
                            best_predict = predict_heap_2d[0][0]
                            best_except = predict_heap_2d[0][10][0]
                            heapq.heappop(predict_heap_2d)
                            if not predict_heap_2d:
                                break

                        if predict_heap_2d:
                            if self.debug: print('predict_heap_2d[0][10]', predict_heap_2d[0][10])
                            if predict_heap_2d[0][10][0] != 1:
                                if self.debug: print('exception found', predict_heap_2d[0][10])
                            else:
                                if self.debug: print('no exceptions')
                                best_result_2d = [predict_heap_2d[0]]
                                best_predict = predict_heap_2d[0][0]
                                best_except = predict_heap_2d[0][10][0]
                                heapq.heappop(predict_heap_2d)


                        if predict_heap_2d:
                            if best_result_2d is None:
                                best_result_2d = [predict_heap_2d[0]]
                                best_predict = predict_heap_2d[0][0]
                                best_except = predict_heap_2d[0][10][0]
                                heapq.heappop(predict_heap_2d)
                            try:
                                while predict_heap_2d[0][0] == best_predict and best_except != 1:
                                    if ((predict_heap_2d[0][10][0] > best_except or best_result_2d[0][10][0] == 1) and predict_heap_2d[0][10][0] != 0) or (best_result_2d[0][3] is not None and best_result_2d[0][3][1] == 0):
                                        best_result_2d = [predict_heap_2d[0]]
                                        best_except = predict_heap_2d[0][10][0]
                                        heapq.heappop(predict_heap_2d)
                                    else:
                                        heapq.heappop(predict_heap_2d)
                            except IndexError:
                                pass

                        if self.debug: print('best post-check exception match', best_result_2d[0][10][0], str(dix) + ':' + str(diy), best_result_2d[0][1])
                        if self.debug: print('best post-check prediction match', best_result_2d[0][0], str(dix) + ':' + str(diy), best_result_2d[0][1])

                        if best_result_2d[0][3] is not None and best_result_2d[0][3][1] == 0:
                            no_rule_count += 1

                        if best_result_2d[0][0] >= best_result_2d[0][10][0]:
                            exceptions[str(dix) + ':' + str(diy)] = best_result_2d[0][10]
                        else:
                            predict_rule_2d[str(dix) + ':' + str(diy)] = best_result_2d[0]
                        if self.debug: print('check_pos check', (dix, diy) in orig_pos, best_result_2d[0][2], best_result_2d[0][10][0])
                        if (dix, diy) in orig_pos and best_result_2d[0][2] is not None and best_result_2d[0][10][0] != 0:
                            rel_set_data = self.knowledge['2d/' + str(val) + '/' + str(best_result_2d[0][2]) + '/inclusions/rel_set']
                            for cond in rel_set_data:
                                crx, cry, cod, cor = cond
                                if (dix + crx, diy + cry) not in check_set:
                                    if dix + crx >= 0 and diy + cry >= 0:
                                        try:
                                            check = predict_state.input_2D[dix + crx][diy + cry]
                                            if self.debug: print('check_pos 1 add ', str((dix + crx, diy + cry)))
                                            check_pos.append((dix + crx, diy + cry))
                                            check_set.add((dix + crx, diy + cry))
                                        except IndexError:
                                            pass
                    except IndexError:
                        pass

                    predict_heap_2d = []

                if self.debug: print('check pos', check_pos)
                if self.debug: print('check set', check_set)
                if self.debug: print('orig pos', orig_pos)

        uncertainty = 0
        exception_uncertainty = 0
        used_rules_1d = set()
        mrules_1d = set()
        if predict_rule_2d:
            predict_state.last_pos_change_2d = []
        else:
            predict_state.no_change = True

        for loc_key in predict_rule_2d.keys():
            key = loc_key.split(':')
            loc_x = int(key[0])
            loc_y = int(key[1])
            if predict_rule_2d[loc_key][1] != 'None' and predict_rule_2d[loc_key][3] is not None and predict_rule_2d[loc_key][10][0] != 0:
                predict_state.last_pos_change_2d.append((loc_x, loc_y))

            if predict_rule_2d[loc_key][3] is not None:
                if predict_rule_2d[loc_key][3][0] == 'rel':
                    predict_state.input_2D[loc_x][loc_y] += predict_rule_2d[loc_key][3][1]

            predict_state.applied_rules[loc_key] = predict_rule_2d[loc_key]
            if predict_rule_2d[loc_key][1] != 'None' and predict_rule_2d[loc_key][3] is not None and predict_rule_2d[loc_key][10][0] != 0:
                predict_state.applied_rule_ids.add(predict_rule_2d[loc_key][1])

            uncertainty += predict_rule_2d[loc_key][6]

            if predict_rule_2d[loc_key][3] is not None:
                if not used_rules_1d and predict_rule_2d[loc_key][1] != 'None':
                    used_rules_1d.add(predict_rule_2d[loc_key][1])
                    for mrule in self.knowledge['2d/' + str(predict_rule_2d[loc_key][11]) + '/' + str(predict_rule_2d[loc_key][2]) + '/mrules'].keys():
                        mrules_1d.add(mrule)
                    predict_1d = predict_rule_2d[loc_key][7]
                    if self.debug: print('applied 1d rule', predict_rule_2d[loc_key][1])
                    if self.debug: print('predict_1d', predict_1d)
                    for di_key in predict_1d.keys():
                        try:
                            if predict_1d[di_key][0][1] == 'rel':
                                predict_state.input_1D[di_key] += predict_1d[di_key][0][2]
                                if di_key == 2 and predict_1d[di_key][0][2] < 0:
                                    predict_state.anti_goal = True
                        except IndexError:
                            pass
                elif predict_rule_2d[loc_key][1] not in used_rules_1d and predict_rule_2d[loc_key][1] != 'None':
                    if self.debug: print('used rules 1d', used_rules_1d)
                    if self.debug: print('mrules 1d', mrules_1d)
                    if predict_rule_2d[loc_key][1] not in mrules_1d:
                        used_rules_1d.add(predict_rule_2d[loc_key][1])
                        predict_1d = predict_rule_2d[loc_key][7]
                        if self.debug: print('applied 1d rule', predict_rule_2d[loc_key][1])
                        if self.debug: print('predict_1d', predict_1d)
                        for di_key in predict_1d.keys():
                            try:
                                if predict_1d[di_key][0][1] == 'rel':
                                    predict_state.input_1D[di_key] += predict_1d[di_key][0][2]
                                    if di_key == 2 and predict_1d[di_key][0][2] < 0:
                                        predict_state.anti_goal = True
                            except IndexError:
                                pass
                    for mrule in self.knowledge['2d/' + str(predict_rule_2d[loc_key][11]) + '/' + str(predict_rule_2d[loc_key][2]) + '/mrules'].keys():
                        mrules_1d.add(mrule)

        if self.debug: print('final used rules 1d', used_rules_1d)
        if self.debug: print('final mrules 1d', mrules_1d)

        for loc_key in exceptions.keys():
            exception_uncertainty += exceptions[loc_key][5]
            predict_state.applied_exceptions[loc_key] = exceptions[loc_key]
            predict_state.applied_exception_ids.add(exceptions[loc_key][3])

        predict_state.heap()

        with open('./predict_log/' + str(self.time_step) + '.txt', 'a') as f:
            f.write(str(predict_state.input_2D) + '\n')

        if self.debug: print('Predict state', len(self.states), act, predict_state.input_1D, 'prev state', predict_state.prev_state, predict_state.prev_action, predict_state.anti_goal, predict_state.bad_rules, '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        if self.debug:
            format_state = deepcopy(predict_state.input_2D)

            t_format = np.array(format_state).T

            for r, x in enumerate(t_format):
                x = ["%.0f" % i for i in x]
                for i, item in enumerate(x):
                    if item == '0':
                        x[i] = '  '
                    elif int(item) < 10:
                        x[i] = ' ' + x[i]
                if self.debug: print(x, r)
            if self.debug: print('')
            if self.debug: print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")

        if self.debug: print('predicted state last changes', predict_state.last_pos_change_2d)
        if self.debug: print('predicted changes 2d:', predict_state.change_2D)
        if self.debug: print('predicted changes 1d:', predict_state.change_1D)
        for key in predict_rule_2d.keys():
            if self.debug: print('predict rule 2d', key, predict_rule_2d[key])
            if self.debug: print('exception heap', exception_heap, '\n')
        for di in predict_rule_1d.keys():
            if self.debug: print('predict rule 1d', di, predict_rule_1d[di], '\n')

        if self.debug: print('++++++++++ predict', act, 'time:', round(time.time() - starttime, 10))

        if self.debug: print('no rule check', len(predict_rule_2d.keys()), len(exceptions.keys()), no_rule_count)
        if len(predict_rule_2d.keys()) + len(exceptions.keys()) == no_rule_count:
            if self.debug: print('no_rule_found = True')
            no_rule_found = True

        return predict_state, predict_rule_2d, predict_rule_1d, uncertainty, exception_uncertainty, exceptions, no_rule_found

    def compare(self, compare_state, given_goal, generated, state_num):
        rule_heap = []
        rule_list = []
        change_heap = []
        best_action = None
        check_rules = []
        if given_goal and not generated:
            for gi, goal in enumerate(given_goal):
                if goal:
                    for goal_data in goal:
                        if gi == 0:
                            try:
                                check_rules = self.knowledge['1d/' + str(goal_data[0])]
                            except KeyError:
                                if self.debug: print('compare passing ', '1d/' + str(goal_data[0]))
                                pass
                            if goal_data[1] == '+':
                                for rule in check_rules:
                                    rule_cond_id = self.knowledge['1d/' + str(goal_data[0]) + '/' + rule]
                                    change_heap = []
                                    rel_data = self.knowledge['1d/' + str(goal_data[0]) + '/' + str(rule_cond_id) + '/rel']

                                    for key in rel_data.keys():
                                        heapq.heappush(change_heap, (-(rel_data[key][0] / rel_data[key][1]), 'rel', key, rule))

                                    if change_heap:
                                        if change_heap[0][1] == 'rel':
                                            if change_heap[0][2] > 0:
                                                rule_list.append(change_heap[0][3])

                                if self.debug: print('Compare rule list', rule_list)

                                for rule in rule_list:
                                    val = self.knowledge['2d/' + rule]
                                    if val in compare_state.input_2D_idx.keys():
                                        rule_2d_cond_id = self.knowledge['2d/' + str(val) + '/' + rule]
                                        rel_condition_data = self.knowledge['2d/' + str(val) + '/' + str(rule_2d_cond_id) + '/inclusions/rel']
                                        for key in self.knowledge['2d/' + str(val) + '/' + str(rule_2d_cond_id) + '/act'].keys():
                                            action = key
                                        exception_groups = []

                                        for pos in compare_state.input_2D_idx[val]:
                                            diff = 0
                                            try:
                                                for ci, condition in enumerate(rel_condition_data):
                                                    crx, cry, cod, cor = condition
                                                    if compare_state.input_2D[pos[0] + crx][pos[1] + cry] == cod:
                                                        pass
                                            except IndexError:
                                                if self.debug: print('Index Error, continuing')
                                                continue

                                            if self.debug: print('Compare rel_condition_data', rel_condition_data, rule, val)
                                            for ci, condition in enumerate(rel_condition_data):
                                                rel_diff_heap = []
                                                crx, cry, cod, cor = condition

                                                if self.debug: print('Compare cod', cod)
                                                if cod in compare_state.input_2D_idx.keys():
                                                    if self.debug: print('Compare cod found')
                                                    for rel_pos in compare_state.input_2D_idx[cod]:
                                                        if self.debug: print('Compare rel_pos', rel_pos, pos, crx, cry, abs(rel_pos[0] - (pos[0] + crx)), abs(rel_pos[1] - (pos[1] + cry)))
                                                        heapq.heappush(rel_diff_heap, abs(rel_pos[0] - (pos[0] + crx)) + abs(rel_pos[1] - (pos[1] + cry)))
                                                    if self.debug: print('Compare rel_diff_heap')
                                                    diff += rel_diff_heap[0]
                                                else:
                                                    diff += 1
                                            if self.debug: print('Compare debug ', val, diff, rule, (pos[0], pos[1]), rel_condition_data)
                                            heapq.heappush(rule_heap, (diff, rule, action))

                            if goal_data[1] == '-':
                                for rule in check_rules:
                                    rule_cond_id = self.knowledge['1d/' + str(goal_data[0]) + '/' + rule]
                                    change_heap = []
                                    rel_data = self.knowledge['1d/' + str(goal_data[0]) + '/' + str(rule_cond_id) + '/rel']

                                    for key in rel_data.keys():
                                        heapq.heappush(change_heap, (-(rel_data[key][0] / rel_data[key][1]), 'rel', key, rule))

                                    if change_heap:
                                        if change_heap[0][1] == 'rel':
                                            if change_heap[0][2] < 0:
                                                rule_list.append(change_heap[0][3])

                                if self.debug: print('Compare rule list', rule_list)

                                for rule in rule_list:
                                    val = self.knowledge['2d/' + rule]
                                    if val in compare_state.input_2D_idx.keys():
                                        rule_2d_cond_id = self.knowledge['2d/' + str(val) + '/' + rule]
                                        rel_condition_data = self.knowledge['2d/' + str(val) + '/' + str(rule_2d_cond_id) + '/inclusions/rel']
                                        for key in self.knowledge['2d/' + str(val) + '/' + str(rule_2d_cond_id) + '/act'].keys():
                                            action = key
                                        exception_groups = []

                                        for pos in compare_state.input_2D_idx[val]:
                                            diff = 0
                                            try:
                                                for ci, condition in enumerate(rel_condition_data):
                                                    crx, cry, cod, cor = condition
                                                    if compare_state.input_2D[pos[0] + crx][pos[1] + cry] == cod:
                                                        pass
                                            except IndexError:
                                                if self.debug: print('Index Error, continuing')
                                                continue

                                            if self.debug: print('Compare rel_condition_data', rel_condition_data, rule, val)
                                            for ci, condition in enumerate(rel_condition_data):
                                                rel_diff_heap = []
                                                crx, cry, cod, cor = condition

                                                if self.debug: print('Compare cod', cod)
                                                if cod in compare_state.input_2D_idx.keys():
                                                    if self.debug: print('Compare cod found')
                                                    for rel_pos in compare_state.input_2D_idx[cod]:
                                                        if self.debug: print('Compare rel_pos', rel_pos, pos, crx, cry, abs(rel_pos[0] - (pos[0] + crx)), abs(rel_pos[1] - (pos[1] + cry)))
                                                        heapq.heappush(rel_diff_heap, abs(rel_pos[0] - (pos[0] + crx)) + abs(rel_pos[1] - (pos[1] + cry)))
                                                    if self.debug: print('Compare rel_diff_heap')
                                                    diff += rel_diff_heap[0]
                                                else:
                                                    diff += 1
                                            if self.debug: print('Compare debug ', val, diff, rule, (pos[0], pos[1]), rel_condition_data)
                                            heapq.heappush(rule_heap, (diff, rule, action))

        if generated:
            diff = None
            for pos in compare_state.input_2D_idx[given_goal[1]]:
                check_pos = [pos[0] + given_goal[2][0], pos[1] + given_goal[2][1]]
                for pos_idx in compare_state.input_2D_idx[given_goal[2][2]]:
                    if diff is None or (abs(pos_idx[0] - check_pos[0]) + abs(pos_idx[1] - check_pos[1])) < diff:
                        diff = abs(pos_idx[0] - check_pos[0]) + abs(pos_idx[1] - check_pos[1])

        if rule_heap:
            if self.debug: print('Compare diff:', generated, rule_heap[0][0], rule_heap[0][1], state_num, rule_heap)

            diff = rule_heap[0][0]
            best_rule = rule_heap[0][1]
            best_action = rule_heap[0][2]
        else:
            diff = None
            best_rule = None

        compare_state.compare = diff

        if diff == 0:
            return diff, best_action, True
        else:
            return diff, best_action, False

    def create_rule(self, act, dix, diy, oval, rval, aval, rule_id, state, prev_state, prev_1d, post_1d, prev_2d, post_2d, step):
        is_dupe = False
        new_rule = 'ERROR'
        hold_rules = []
        try:
            hold_rules = self.knowledge['2d/' + str(oval)]
        except KeyError:
            pass

        for rule_group, r_id in enumerate(hold_rules):
            dupe_act = False
            dupe_1d = True
            dupe_1d_rel = True
            dupe_rel = False
            dupe_inc = False
            if self.debug: print('checking rule ', r_id)
            if self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/combined']:
                if self.debug: print('rule is combined, skipping')
                continue

            if act in self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/act'].keys():
                dupe_act = True
            else:
                if self.debug: print('rule is not for this action, skipping')
                continue
            if self.debug: print('checking rval', rval, self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/rel'].keys())
            if rval in self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/rel'].keys():
                dupe_rel = True
            else:
                if self.debug: print('rule does not have the same rval, skipping')
                continue

            if rval != 0:
                rel_count = 0
                rel_total = 0
                rel_set = set()
                for rel_data in self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/inclusions/rel']:
                    rox = rel_data[0]
                    roy = rel_data[1]
                    try:
                        if self.debug: print('checking inclusion', rox, roy, dix, diy, dix + rox, diy + roy, self.input_2D[dix + rox][diy + roy], rel_data[2])
                    except IndexError:
                        if self.debug: print('checking inclusion index error')
                    if (rox, roy) not in rel_set:
                        rel_total += 1
                        rel_set.add((rox, roy))

                    try:
                        if self.input_2D[dix + rox][diy + roy] == rel_data[2]:
                            rel_count += 1
                    except IndexError:
                        pass
                    if self.debug: print('rel_count', rel_count, 'rel_total', rel_total)

                if rel_count == rel_total:
                    dupe_inc = True
                else:
                    if self.debug: print('rule inclusions do not match, skipping', rel_count, rel_total)
                    continue

                count_1d = 0
                total_1d = 0
                for di, val in enumerate(self.input_1D):
                    try:
                        di_group = self.knowledge['1d/' + str(di) + '/' + str(r_id)]
                        found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/oval']
                        total_1d += 1
                        try:
                            found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/oval'][val]
                            if self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/rel'][post_1d[di] - val]:
                                count_1d += 1
                        except KeyError:
                            dupe_1d = False
                    except KeyError:
                        pass

                if total_1d != count_1d:
                    dupe_1d = False
                    is_dupe = False

                if not dupe_1d:
                    count_1d = 0
                    total_1d = 0
                    for di, val in enumerate(self.input_1D):
                        try:
                            di_group = self.knowledge['1d/' + str(di) + '/' + str(r_id)]
                            if self.debug: print('1d/' + str(di) + '/' + str(di_group) + '/rel', self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/rel'], post_1d[di], val)
                            found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/rel']
                            total_1d += 1
                            try:
                                found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/rel'][post_1d[di] - val]
                                count_1d += 1
                            except KeyError:
                                pass
                        except KeyError:
                            pass
                    if total_1d != count_1d:
                        dupe_1d_rel = False
                        is_dupe = False
                        if self.debug: print('not dupe_1d_rel', dupe_1d_rel, dupe_1d)
                        if self.debug: print('total 1d / count 1d', total_1d, count_1d)

                    if dupe_1d_rel:
                        dupe_1d = True
                        if dupe_act and dupe_1d and dupe_inc and dupe_rel:
                            for di, val in enumerate(self.input_1D):
                                di_group = self.knowledge['1d/' + str(di) + '/' + str(r_id)]
                                try:
                                    found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/oval'][val]
                                except KeyError:
                                    self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/oval'] = dict()

                if dupe_act and dupe_1d and dupe_inc and dupe_rel:
                    if self.debug: print('setting is_dupe to true')
                    is_dupe = True
            elif dupe_act and dupe_rel:
                if self.debug: print('rval is 0 so is_dupe is true')
                is_dupe = True

            if self.debug: print('all checks for r_id', r_id, dupe_act, dupe_1d, dupe_inc, dupe_rel, dupe_1d_rel, is_dupe)

            if is_dupe:
                try:
                    data = self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/apos'][str(dix) + ':' + str(diy)]
                    data[0] += 1
                    data[1] += 1
                    self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/apos'][str(dix) + ':' + str(diy)] = data
                except KeyError:
                    if self.debug: print('clearing apos from rule', r_id)
                    self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/apos'] = {}

                for loc_key in self.states[state].applied_rules.keys():
                    key = loc_key.split(':')
                    loc_x = int(key[0])
                    loc_y = int(key[1])

                    check_rule = self.states[state].applied_rules[loc_key][1]
                    if check_rule is not None and self.states[state].applied_rules[loc_key][3] is not None and self.states[state].applied_rules[loc_key][10][0] != 0:
                        cond_group = self.states[state].applied_rules[loc_key][2]
                        check_val = self.states[state].applied_rules[loc_key][11]
                        if self.debug: print('Applied rules at loc ', loc_key, self.states[state].applied_rules[loc_key])
                        if self.input_2D[loc_x][loc_y] == check_val and post_2d[loc_x][loc_y] - check_val in self.knowledge['2d/' + str(check_val) + '/' + str(cond_group) + '/rel'].keys():
                            self.knowledge['2d/' + str(oval) + '/' + str(rule_group) + '/mrules'][check_rule] = [1, 1]

                new_rule = r_id
                break

        if not is_dupe:
            starttime = time.time()
            new_rule = rule_id

            self.knowledge['plan_depth'] = self.plan_depth

            try:
                self.knowledge[act].append(rule_id)
            except KeyError:
                self.knowledge[act] = [rule_id]

            try:
                self.knowledge['2d/' + str(oval)].append(rule_id)
            except KeyError:
                self.knowledge['2d/' + str(oval)] = [rule_id]

            rule_num = str(len(self.knowledge['2d/' + str(oval)]) - 1)

            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/act'] = {act: [1, 1]}
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/rel'] = {rval: [1, 1]}
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/abs'] = {aval: [1, 1]}
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/apos'] = {str(dix) + ':' + str(diy): [1, 1]}
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/oraw'] = [self.input_1D, self.input_2D]
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/lraw'] = [self.input_1D, self.input_2D]
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/id'] = rule_id
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/lstep'] = step
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/rstep'] = {}
            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/combined'] = False
            self.knowledge['2d/' + str(oval) + '/' + str(rule_id)] = len(self.knowledge['2d/' + str(oval)]) - 1

            if rval != 0:
                self.knowledge['2d/' + str(oval) + '/' + rule_num + '/mrules'] = dict()
                for loc_key in self.states[state].applied_rules.keys():
                    key = loc_key.split(':')
                    loc_x = int(key[0])
                    loc_y = int(key[1])

                    check_rule = self.states[state].applied_rules[loc_key][1]
                    if check_rule is not None and self.states[state].applied_rules[loc_key][3] is not None and self.states[state].applied_rules[loc_key][10][0] != 0:
                        cond_group = self.states[state].applied_rules[loc_key][2]
                        check_val = self.states[state].applied_rules[loc_key][11]
                        if self.debug: print('Applied rules at loc ', loc_key, self.states[state].applied_rules[loc_key])
                        if self.input_2D[loc_x][loc_y] == check_val and post_2d[loc_x][loc_y] - check_val in self.knowledge['2d/' + str(check_val) + '/' + str(cond_group) + '/rel'].keys():
                            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/mrules'][check_rule] = [1, 1]

                if self.debug: print('new rule position ', dix, diy)
                for loc_key in self.states[state].applied_rules.keys():
                    key = loc_key.split(':')
                    loc_x = int(key[0])
                    loc_y = int(key[1])

                    check_rule = self.states[state].applied_rules[loc_key][1]
                    if check_rule is not None and self.states[state].applied_rules[loc_key][3] is not None and self.states[state].applied_rules[loc_key][10][0] != 0:
                        cond_group = self.states[state].applied_rules[loc_key][2]
                        check_val = self.states[state].applied_rules[loc_key][11]
                        if self.debug: print('Applied rules at loc ', loc_key, self.states[state].applied_rules[loc_key])
                        if self.debug: print('Adding inclusions from rule ' + str(check_rule), 'val: ' + str(check_val), 'cond_group: ' + str(cond_group))
                        for check_rel in self.knowledge['2d/' + str(check_val) + '/' + str(cond_group) + '/inclusions/rel_set']:
                            if (loc_x + check_rel[0]) - dix != 0 or (loc_y + check_rel[1]) - diy != 0:
                                try:
                                    if ((loc_x + check_rel[0]) - dix, (loc_y + check_rel[1]) - diy, self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])], post_2d[(loc_x + check_rel[0])][(loc_y + check_rel[1])] - self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])]) not in self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel']:
                                        self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'].append(((loc_x + check_rel[0]) - dix, (loc_y + check_rel[1]) - diy, self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])], post_2d[(loc_x + check_rel[0])][(loc_y + check_rel[1])] - self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])]))
                                        if self.debug: print('Added loc: ', dix, diy, loc_x, loc_y, check_rel[0], check_rel[1], self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])])
                                except KeyError:
                                    self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'] = [((loc_x + check_rel[0]) - dix, (loc_y + check_rel[1]) - diy, self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])], post_2d[(loc_x + check_rel[0])][(loc_y + check_rel[1])] - self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])])]
                                    if self.debug: print('Added loc: ', dix, diy, loc_x, loc_y, check_rel[0], check_rel[1], self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])])
                                except IndexError:
                                    if self.debug: print('Location outside view, skipping')
                            else:
                                if self.debug: print('Skipped due to same location as new rule')

                for loc_key in self.states[state].applied_exceptions.keys():
                    key = loc_key.split(':')
                    loc_x = int(key[0])
                    loc_y = int(key[1])
                    exception_data = self.states[state].applied_exceptions[str(loc_x) + ':' + str(loc_y)]
                    check_rule = exception_data[1]
                    cond_group = exception_data[2]
                    check_val = exception_data[9]
                    if self.debug: print('Applied exception at loc ', str(loc_x) + ':' + str(loc_y), exception_data)
                    if self.input_2D[loc_x][loc_y] != post_2d[loc_x][loc_y]:
                        if self.debug: print('Adding inclusions from rule exception ' + str(check_rule), 'val: ' + str(check_val), 'cond_group: ' + str(cond_group))
                        for check_rel in self.knowledge['2d/' + str(check_val) + '/' + str(cond_group) + '/inclusions/rel_set']:
                            if (loc_x + check_rel[0]) - dix != 0 or (loc_y + check_rel[1]) - diy != 0:
                                try:
                                    if ((loc_x + check_rel[0]) - dix, (loc_y + check_rel[1]) - diy, self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])], post_2d[(loc_x + check_rel[0])][(loc_y + check_rel[1])] - self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])]) not in self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel']:
                                        self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'].append(((loc_x + check_rel[0]) - dix, (loc_y + check_rel[1]) - diy, self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])], post_2d[(loc_x + check_rel[0])][(loc_y + check_rel[1])] - self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])]))
                                        if self.debug: print('Added loc: ', dix, diy, loc_x, loc_y, check_rel[0], check_rel[1], self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])])
                                except KeyError:
                                    self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'] = [((loc_x + check_rel[0]) - dix, (loc_y + check_rel[1]) - diy, self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])], post_2d[(loc_x + check_rel[0])][(loc_y + check_rel[1])] - self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])])]
                                    if self.debug: print('Added loc: ', dix, diy, loc_x, loc_y, check_rel[0], check_rel[1], self.input_2D[(loc_x + check_rel[0])][(loc_y + check_rel[1])])
                                except IndexError:
                                    if self.debug: print('Exception location outside view, skipping')
                            else:
                                if self.debug: print('Skipped due to same location as new rule')
                    else:
                        if self.debug: print('Skipped adding inclusions from rule exception due to exception success')

                try:
                    if self.debug: print('pre-added inclusions: ', self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'])
                except KeyError:
                    pass
                for cox, coy, cod, cord, coad in self.last_change_2D:
                    if cox != dix or coy != diy:
                        try:
                            if (cox - dix, coy - diy, cod, cord) not in self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel']:
                                self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'].append((cox - dix, coy - diy, cod, cord))
                        except KeyError:
                            self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'] = [(cox - dix, coy - diy, cod, cord)]

                for item in self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel']:
                    try:
                        self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel_set'].add(item)
                    except KeyError:
                        self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel_set'] = {item}
            else:
                self.knowledge['2d/' + str(oval) + '/' + rule_num + '/mrules'] = dict()
                self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel'] = []
                self.knowledge['2d/' + str(oval) + '/' + rule_num + '/inclusions/rel_set'] = set()

            try:
                if oval not in self.knowledge['2d{']:
                    self.knowledge['2d'].append(oval)
                    self.knowledge['2d{'].add(oval)
            except KeyError:
                self.knowledge['2d'] = [oval]
                self.knowledge['2d{'] = {oval}

            self.knowledge['2d/' + rule_id] = oval

            if rval != 0:
                for di, val in enumerate(prev_1d):
                    try:
                        if rule_id not in self.knowledge['1d{' + str(di)]:
                            self.knowledge['1d/' + str(di)].append(rule_id)
                        self.knowledge['1d{' + str(di)].add(rule_id)
                    except KeyError:
                        self.knowledge['1d/' + str(di)] = [rule_id]
                        self.knowledge['1d{' + str(di)] = {rule_id}

                    rule_num_1d = str(len(self.knowledge['1d/' + str(di)]) - 1)
                    self.knowledge['1d/' + str(di) + '/' + rule_num_1d + '/oval'] = {val: [1, 1]}
                    self.knowledge['1d/' + str(di) + '/' + rule_num_1d + '/rel'] = {post_1d[di] - val: [1, 1]}
                    self.knowledge['1d/' + str(di) + '/' + rule_num_1d + '/abs'] = {post_1d[di]: [1, 1]}
                    self.knowledge['1d/' + str(di) + '/' + str(rule_id)] = rule_num_1d

                    try:
                        self.knowledge['1d/' + rule_id].add(di)
                    except KeyError:
                        self.knowledge['1d/' + rule_id] = {di}

            if self.debug: print('================ create condition', dix, diy, 'time:', round(time.time() - starttime, 10), len(self.knowledge), rule_id)

        if new_rule == 'ERROR':
            if self.debug: print('new rule is ERROR')
            raise Exception
        return new_rule

    def update_rule(self, rule_data, update, exception, loc_key, input_2d, input_1d, state, rules_list, exceptions_list, prules_list, applied_rules):
        if loc_key is not None:
            pos = loc_key.split(':')
            pos[0] = int(pos[0])
            pos[1] = int(pos[1])
            oval = self.input_2D[pos[0]][pos[1]]

        if exception and not update:
            is_dupe = False
            exception_group = None
            try:
                for group in self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions']:
                    dupe_act = False
                    dupe_1d = True
                    dupe_1d_rel = True
                    dupe_rel = False

                    if self.last_action in self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + group + '/act'].keys():
                        dupe_act = True
                    else:
                        continue

                    rel_count = 0
                    rel_total = 0
                    for rel_data in self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + group + '/rel']:
                        rel_total += 1
                        rox = rel_data[0]
                        roy = rel_data[1]

                        try:
                            if self.input_2D[pos[0] + rox][pos[1] + roy] == rel_data[2]:
                                rel_count += 1

                        except IndexError:
                            rel_count += 1

                    if rel_count == rel_total:
                        dupe_rel = True
                    else:
                        continue

                    count_1d = 0
                    total_1d = 0
                    for di, val in enumerate(self.input_1D):
                        try:
                            di_group = self.knowledge['1d/' + str(di) + '/' + str(rule_data[1])]
                            if self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/exceptions/' + group + '/oval']:
                                total_1d += 1
                                try:
                                    found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/exceptions/' + group + '/oval'][val]
                                    count_1d += 1
                                except KeyError:
                                    dupe_1d = False
                                    is_dupe = False
                        except KeyError:
                            dupe_1d = False
                            is_dupe = False

                    if count_1d != total_1d:
                        dupe_1d = False
                        is_dupe = False

                    if not dupe_1d:
                        count_1d = 0
                        total_1d = 0
                        for di, val in enumerate(self.input_1D):
                            try:
                                di_group = self.knowledge['1d/' + str(di) + '/' + str(rule_data[1])]
                                if self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/exceptions/' + group + '/rel']:
                                    total_1d += 1
                                    try:
                                        found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/exceptions/' + group + '/rel'][input_1d[di] - val]
                                        count_1d += 1
                                    except KeyError:
                                        pass
                            except KeyError:
                                pass
                        if count_1d != total_1d:
                            dupe_1d_rel = False
                            is_dupe = False

                        if dupe_1d_rel:
                            dupe_1d = True
                            if dupe_act and dupe_rel:
                                for di, val in enumerate(self.input_1D):
                                    di_group = self.knowledge['1d/' + str(di) + '/' + str(rule_data[1])]
                                    try:
                                        found = self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/exceptions/' + group + '/oval'][val]
                                    except KeyError:
                                        self.knowledge['1d/' + str(di) + '/' + str(di_group) + '/exceptions/' + group + '/oval'] = dict()

                                for loc_key in self.states[state].applied_rules.keys():
                                    key = loc_key.split(':')
                                    loc_x = int(key[0])
                                    loc_y = int(key[1])

                                    check_rule = self.states[state].applied_rules[loc_key][1]
                                    if check_rule is not None and self.states[state].applied_rules[loc_key][3] is not None and self.states[state].applied_rules[loc_key][10][0] != 0:
                                        cond_group = self.states[state].applied_rules[loc_key][2]
                                        check_val = self.states[state].applied_rules[loc_key][11]
                                        if self.debug: print('Applied rules at loc ', loc_key, self.states[state].applied_rules[loc_key])
                                        if self.input_2D[loc_x][loc_y] == check_val and input_2d[loc_x][loc_y] - check_val in self.knowledge['2d/' + str(check_val) + '/' + str(cond_group) + '/rel'].keys():
                                            self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + group + '/mrules'][check_rule] = [1, 1]

                    if dupe_act and dupe_rel and dupe_1d:
                        is_dupe = True
                        exception_group = group
                        break

            except KeyError:
                if self.debug: print('Exception KeyError')

            if not is_dupe:
                exception_group = str(uuid.uuid4())[:6]
                try:
                    self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions'].append(exception_group)
                except KeyError:
                    self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions'] = [exception_group]

                if self.debug: print('creating exception ', exception_group, '2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions')

                self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/act'] = {self.last_action: [1, 1]}
                self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/apos'] = {loc_key: [1, 1]}
                self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/rstep'] = {}
                self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/lstep'] = self.time_step

                self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/mrules'] = dict()
                for loc_key in self.states[state].applied_rules.keys():
                    key = loc_key.split(':')
                    loc_x = int(key[0])
                    loc_y = int(key[1])

                    check_rule = self.states[state].applied_rules[loc_key][1]
                    if check_rule is not None and self.states[state].applied_rules[loc_key][3] is not None and self.states[state].applied_rules[loc_key][10][0] != 0:
                        cond_group = self.states[state].applied_rules[loc_key][2]
                        check_val = self.states[state].applied_rules[loc_key][11]
                        if self.debug: print('Applied rules at loc ', loc_key, self.states[state].applied_rules[loc_key])
                        if self.input_2D[loc_x][loc_y] == check_val and input_2d[loc_x][loc_y] - check_val in self.knowledge['2d/' + str(check_val) + '/' + str(cond_group) + '/rel'].keys():
                            self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/mrules'][check_rule] = [1, 1]
                if self.debug: print(rule_data)
                self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/rel'] = []
                for rel_data in self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/inclusions/rel']:
                    rox = rel_data[0]
                    roy = rel_data[1]
                    rod = self.input_2D[pos[0] + rox][pos[1] + roy]
                    ror = input_2d[pos[0] + rox][pos[1] + roy] - self.input_2D[pos[0] + rox][pos[1] + roy]
                    self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/rel'].append((rox, roy, rod, ror))

                hold_rel = set(self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/rel'])

                if self.debug: print('Exception rel:', self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/rel'], hold_rel, '2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/rel')
                self.knowledge['2d/' + str(oval) + '/' + str(rule_data[2]) + '/exceptions/' + exception_group + '/rel'] = list(hold_rel)

                for di_key, di_val in enumerate(self.input_1D):
                    di_group = self.knowledge['1d/' + str(di_key) + '/' + str(rule_data[1])]
                    try:
                        self.knowledge['1d/' + rule_data[1] + '/' + str(di_group) + '/exceptions/' + exception_group].append(di_key)
                    except KeyError:
                        self.knowledge['1d/' + rule_data[1] + '/' + str(di_group) + '/exceptions/' + exception_group] = [di_key]

                    self.knowledge['1d/' + str(di_key) + '/' + str(di_group) + '/exceptions/' + exception_group + '/oval'] = {di_val: [1, 1]}
                    self.knowledge['1d/' + str(di_key) + '/' + str(di_group) + '/exceptions/' + exception_group + '/rel'] = {input_1d[di_key] - di_val: [1, 1]}

                self.knowledge['2d/exceptions/' + str(exception_group)] = oval
                self.knowledge['2d/exceptions/' + str(exception_group) + '/cond_group'] = rule_data[2]

            if exception_group is not None:
                return exception_group, rule_data[1]
            else:
                if self.debug: print('NONE exception group')
                raise Exception

        if update and not exception:
            for rule_id in rules_list:
                val = self.knowledge['2d/' + str(rule_id)]
                cond_group = self.knowledge['2d/' + str(val) + '/' + str(rule_id)]

                for rule in applied_rules:
                    loc_x = rule[1]
                    loc_y = rule[2]

                    check_rule = rule[0]

                    check_val = self.knowledge['2d/' + str(check_rule)]
                    check_cond_group = self.knowledge['2d/' + str(check_val) + '/' + str(check_rule)]

                    if self.debug: print('Applied rules at loc ', loc_x, loc_y, rule)
                    if self.input_2D[loc_x][loc_y] == check_val and input_2d[loc_x][loc_y] - check_val in self.knowledge['2d/' + str(check_val) + '/' + str(check_cond_group) + '/rel'].keys():
                        self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/mrules'][check_rule] = [1, 1]

                try:
                    if self.debug: print('updating lrules for rule', rule_id, self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'])
                except KeyError:
                    if self.debug: print('updating lrules for rule', rule_id, 'no lrules')
                if prules_list:
                    try:
                        if self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules']:
                            if self.debug: print('updating rule lrules', '2d/' + str(val) + '/' + str(cond_group) + '/lrules', self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'], prules_list, self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'] & prules_list)
                            self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'] = self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'] & prules_list
                    except KeyError:
                        if self.debug: print('updating rule no lrules entry, creating')
                        self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'] = copy.deepcopy(prules_list)
                else:
                    try:
                        if self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules']:
                            if self.debug: print('updating rule no prules, clearing')
                            self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'] = set()
                    except KeyError:
                        if self.debug: print('updating rule no lrules entry, creating')
                        self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'] = copy.deepcopy(prules_list)

        if update and exception:
            for exception_id in exceptions_list:
                val = self.knowledge['2d/exceptions/' + str(exception_id)]
                cond_group = self.knowledge['2d/exceptions/' + str(exception_id) + '/cond_group']
                try:
                    if self.debug: print('updating lrules for exception', exception_id, self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'])
                except KeyError:
                    if self.debug: print('updating lrules for exception', exception_id, 'no rules')
                if prules_list:
                    try:
                        if self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules']:
                            if self.debug: print('updating exception lrules', '2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules', self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'], prules_list, self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'] & prules_list)
                            self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'] = self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'] & prules_list
                    except KeyError:
                        if self.debug: print('updating exception lrules no lrules entry, creating')
                        self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'] = copy.deepcopy(prules_list)
                else:
                    try:
                        if self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules']:
                            if self.debug: print('updating exception no prules, clearing')
                            self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'] = set()
                    except KeyError:
                        if self.debug: print('updating exception lrules no lrules entry, creating')
                        self.knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'] = copy.deepcopy(prules_list)

    def clean_rule(self, source_rule, post_2d):
        source_rule_id = source_rule[0]
        source_val = self.knowledge['2d/' + str(source_rule_id)]
        source_cond_group = self.knowledge['2d/' + str(source_val) + '/' + str(source_rule_id)]
        hold_conditions = copy.deepcopy(self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/inclusions/rel'])
        if self.debug: print('cleaning rule', source_rule_id, hold_conditions)
        self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/inclusions/rel/cleaned'] = True
        for condition in hold_conditions:
            crx, cry, cod, cor = condition
            if cor != 0:
                try:
                    for except_id in self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/exceptions']:
                        is_match = True
                        for i in range(3):
                            source_1d = self.knowledge['1d/' + str(i) + '/' + str(source_rule_id)]
                            try:
                                if self.knowledge['1d/' + str(i) + '/' + str(source_1d) + '/oval'] != self.knowledge['1d/' + str(i) + '/' + str(source_1d) + '/exceptions/' + str(except_id) + '/oval']:
                                    is_match = False
                                if self.knowledge['1d/' + str(i) + '/' + str(source_1d) + '/rel'] != self.knowledge['1d/' + str(i) + '/' + str(source_1d) + '/exceptions/' + str(except_id) + '/rel']:
                                    is_match = False
                            except KeyError:
                                if self.debug: print('clean rule exception mismatch')
                                self.error_stop = True
                        if is_match:
                            hold_except_conditions = copy.deepcopy(self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/exceptions/' + str(except_id) + '/rel'])
                            for exception_cond in hold_except_conditions:
                                erx, ery, eod, eor = exception_cond
                                if crx == erx and cry == ery and cod == eod and self.input_2D[source_rule[1] + crx][source_rule[2] + cry] == cod and post_2d[source_rule[1] + crx][source_rule[2] + cry] == self.input_2D[source_rule[1] + crx][source_rule[2] + cry]:
                                    if self.debug: print('removing condition from inclusions/rel', condition, 'based on', exception_cond)
                                    try:
                                        self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/inclusions/rel/removed'].append(condition)
                                        self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/exceptions/' + str(except_id) + '/rel/removed'].append(exception_cond)
                                    except KeyError:
                                        self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/inclusions/rel/removed'] = [condition]
                                        self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/exceptions/' + str(except_id) + '/rel/removed'] = [exception_cond]
                                    try:
                                        self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/inclusions/rel'].remove(condition)
                                        self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/exceptions/' + str(except_id) + '/rel'].remove(exception_cond)
                                    except ValueError:
                                        pass
                                    if self.debug: print('finished removing using', except_id, hold_except_conditions)
                except KeyError:
                    if self.debug: print('clean_rule keyerror')
                    pass
        if not self.knowledge['2d/' + str(source_val) + '/' + str(source_cond_group) + '/inclusions/rel']:
            self.error_stop = True

    def save_knowledge(self, fname):
        np.save(fname, self.knowledge)
        sorted_keys = list(self.knowledge.keys())
        sorted_keys.sort()

        if self.error_stop:
            raise Exception

    def load_knowledge(self, fname):
        try:
            self.knowledge = np.load(fname, allow_pickle=True).item()
            self.plan_depth = self.knowledge['plan_depth']
        except FileNotFoundError:
            self.knowledge = dict()
