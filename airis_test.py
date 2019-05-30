from airis_stable import AIRIS


class Test(object):

    def __init__(self):

        self.vis_env = [[0, 0, 0, 0]]
        self.aux_env = []
        self.action_space = [0, 1]
        self.action = 0
        self.action_output_list = [
            [1, 2, 1],
            [1, 2, 1]
        ]
        self.airis = AIRIS(self.vis_env, self.aux_env, self.action_space, self.action_output_list)

    def update(self):
        self.action, _, _ = self.airis.capture_input(self.vis_env, self.aux_env, 0, prior=True)

        print(self.action)

        if self.action == 0:
            # self.aux_env[1] -= 1
            self.vis_env[0][1] -= 1
        else:
            # self.aux_env[1] += 1
            self.vis_env[0][1] += 1

        self.airis.capture_input(self.vis_env, self.aux_env, 0, prior=False)


if __name__ == '__main__':

    test = Test()

    while True:
        test.update()
        interrupt = input()
