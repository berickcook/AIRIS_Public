import numpy as np
import heapq
import re
from numba import vectorize
from constants import *

# cleaner way to print things
def pprint(string='', indent=DEFAULT_INDENT, num_indents=0,
           new_line_start=False, new_line_end=False, draw_line=DEFAULT_DRAW_LINE):

    if DEBUG_WITH_CONSOLE:

        total_indent0 = ''.join([indent] * num_indents)
        total_indent1 = ''.join([indent] * (num_indents + 1))

        if new_line_start:
            print(total_indent1 if draw_line else total_indent0)

        print(total_indent0 + string)

        if new_line_end:
            print(total_indent1 if draw_line else total_indent0)

    if DEBUG_WITH_LOGFILE:

        f = open(DEBUG_LOGFILE_PATH, 'a')

        new_indent = '\t'

        total_indent0 = ''.join([new_indent] * num_indents)
        total_indent1 = ''.join([new_indent] * (num_indents + 1))

        if new_line_start:
            f.write((total_indent1 if draw_line else total_indent0) + '\n')

        # all these regex's are to make tabs in the string properly
        # asdfasdf is to make sure there's no false positives
        # when replacing the indent
        indent2 = re.sub('\|', 'asdfasdf', indent)
        string = re.sub(indent2, new_indent, re.sub('\|', 'asdfasdf', string))
        f.write(total_indent0 + string + '\n')

        if new_line_end:
            f.write((total_indent1 if draw_line else total_indent0) + '\n')

        f.close()

# pretty prints the 2d numpy array env
def print_vis_env(env, title=None, indent=DEFAULT_INDENT, num_indents=0,
                  new_line_start=False, new_line_end=False,
                  draw_line=DEFAULT_DRAW_LINE):

    if title:
        pprint(title, indent=indent, num_indents=num_indents,
            new_line_start=new_line_start, draw_line=draw_line)

    pprint(
        re.sub('\[|\]', ' ',
            re.sub('0', '.',
                re.sub('\n', ('\n' + ''.join([indent] * num_indents)),
                    np.array_str(
                        np.swapaxes(
                            env.astype(int), 0, 1
                        )
                    )
                )
            )
        ),
        indent=indent, num_indents=num_indents,
        new_line_end=new_line_end, draw_line=draw_line
    )

# pretty prints the 1d numpy array env
def print_aux_env(env, title=None, indent=DEFAULT_INDENT, num_indents=0,
                  new_line_start=False, new_line_end=False,
                  draw_line=DEFAULT_DRAW_LINE):

    if title:
        pprint(title, indent=indent, num_indents=num_indents,
            new_line_start=new_line_start, draw_line=draw_line)

    pprint('  ' + np.array_str(env.astype(int)),
           indent=indent, num_indents=num_indents,
           new_line_end=new_line_end,
           draw_line=draw_line)

# get vis_env_count, vis_env_count_list, vis_env_heap
# args:
# vis_env: 2d numpy array of the visual environment
# returns:
# (vis_env_count, vis_env_count_list, vis_env_heap)
#    vis_env_count: dictionary of frequence count of unique values in the vis_env
#    vis_env_count_list: set of all unique values in the vis_env
#    vis_env_heap: min heap of all unique values in the vis_env sorted by frequency count
def get_counts(vis_env):

    # fill vis_env_count with the frequency of input values in this vis_env
    # and append any never seen before values
    vis_env_count = {}
    vis_env_pos = {}
    for pos, val in np.ndenumerate(vis_env):
        try:
            vis_env_count[val] += 1
            vis_env_pos[val] = pos
        except KeyError:
            vis_env_count[val] = 1
            vis_env_pos[val] = pos

    # fill and self.vis_count_list with the values never seen before
    vis_env_count_list = set(vis_env_count)

    # put them in a min heap by frequency count
    vis_env_heap = []
    heapq.heapify(vis_env_heap)
    for val, count in vis_env_count.items():
        heapq.heappush(vis_env_heap, (count, val))

    return vis_env_count, vis_env_count_list, vis_env_heap, vis_env_pos


# function to return the difference between two numpy arrays,
# a and b, using parallel processing to do it faster
@vectorize(['float32(float32, float32)'], target="parallel")
def array_dif(a, b):
    return abs(a - b)
