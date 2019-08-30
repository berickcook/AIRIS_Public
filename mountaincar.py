import argparse
import time
import sys
from airis_aux import AIRIS

import gym
from gym import wrappers, logger


class AIAgent(object):
    """The world's simplest agent!"""
    def __init__(self, action_space):
        self.vis_env = [[0]]
        self.aux_env = [0, 0]
        self.action_space = [0, 1, 2]
        self.action = 0
        self.action_output_list = [
            [1, 2, 1],
            [1, 2, 1],
            [1, 2, 1]
        ]
        self.airis = AIRIS(self.vis_env, self.aux_env, self.action_space, self.action_output_list)
        self.airis.goal_type = 'Fixed'
        self.airis.goal_type_default = 'Fixed'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument('env_id', nargs='?', default='MountainCar-v0', help='Select the environment to run')
    args = parser.parse_args()

    # You can set the level to logger.DEBUG or logger.WARN if you
    # want to change the amount of output.
    logger.set_level(logger.INFO)

    env = gym.make(args.env_id)

    # You provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    outdir = '/tmp/random-agent-results'
    # env = wrappers.Monitor(env, directory=outdir, force=True)
    env.seed(0)
    agent = AIAgent(env.action_space)
    result_data = []
    round_to = 3


    episode_count = 100
    episode_score = 0
    reward = 0
    done = False

    ob = env.reset()
    episode_score = 0
    start_time = time.time()
    best_loc_high = None
    best_loc_low = None
    while True:
        action, _, _ = agent.airis.capture_input([[0]], [round(ob[0], round_to), round(ob[1], round_to)], 0, prior=True)
        if action is None:
            action = 1
            print ('AI took no action')
        ob, reward, done, _ = env.step(action)
        episode_score += reward
        if best_loc_high is None or round(ob[0], round_to) > best_loc_high:
            best_loc_high = round(ob[0], round_to)
        if best_loc_low is None or round(ob[0], round_to) < best_loc_low:
            best_loc_low = round(ob[0], round_to)
        if action is not None:
            agent.airis.capture_input([[0]], [round(ob[0], round_to), round(ob[1], round_to)], action, prior=False)
        print(action, ob, reward, done, episode_score, best_loc_low, best_loc_high, str(time.time()-start_time), agent.airis.knowledge['last condition id'])
        if done:
            print('episode score: ', episode_score)
            result_data.append((episode_score, best_loc_low, best_loc_high))
            break
        # Note there's no env.render() here. But the environment still can open window and
        # render if asked by env.monitor: it calls env.render('rgb_array') to record video.
        # Video is not recorded every episode, see capped_cubic_video_schedule for details.

    with open('MountainCar_3Rounded_NoDupe_FixedGoal_200Depth_Assume_Relative.txt', 'a') as file:
        file.write(str(episode_score)+' | '+str(best_loc_low)+' | '+str(best_loc_high)+' | '+str(time.time() - start_time)+' | '+str(agent.airis.knowledge['last condition id'])+'\n')
    agent.airis.save_knowledge()

    env.close()
