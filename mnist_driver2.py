import pygame
import time, sys, os
import array
import numpy as np
from pygame.locals import QUIT, KEYDOWN
from constants import *
from airis_old import AIRIS
import struct
import matplotlib.pyplot as plt

''' NOTES:

        Original database: http://yann.lecun.com/exdb/mnist/

    '''

class PyGameView(object):

    '''
        PyGameView controls the display
    '''

    def __init__(self, model):

        self.model = model
        self.screen = pygame.display.set_mode(MNIST_SCREEN_SIZE) # a pygame screen
        self.surface = pygame.Surface(MNIST_SCREEN_SIZE) # a pygame surface is the thing you draw on
        self.show_view = True # toggle display
        self.dir_path = os.path.dirname(os.path.realpath(__file__))

        self.setup_mnist_image()
        self.setup_image_count()
        self.draw_keyboard_controls()
        self.draw_keyboard_settings()
        self.setup_current_accuracy_text()

    def draw(self):

        # draw image and data
        i = model.current_image_index
        self.draw_mnist_image(model.current_data[i][0])
        self.draw_image_count()
        self.draw_current_accuracy_text(i)

        # update display
        pygame.display.update()

    # these functions draw the image and image count
    def setup_mnist_image(self):

        sp = MNIST_IMAGE_START
        s = MNIST_PIXEL_SIZE

        # draw border of histogram
        pygame.draw.rect(self.surface, pygame.Color('white'),
            (sp[0], sp[1], MNIST_IMAGE_SIZE[0], MNIST_IMAGE_SIZE[1]), 3)
    def draw_mnist_image(self, image):

        sp = MNIST_IMAGE_START
        s = MNIST_PIXEL_SIZE

        # draw pixels of mnist image
        for x in range(MNIST_IMAGE_GRID[0]):
            for y in range(MNIST_IMAGE_GRID[1]):
                pixel_value = image[MNIST_IMAGE_GRID[0]*y+x]
                pixel_color = [pixel_value, pixel_value, pixel_value]
                pygame.draw.rect( \
                    self.surface, \
                    pixel_color, \
                    [sp[0] + x*s[0], sp[1] + y*s[1], s[0], s[1]] \
                )
    def setup_image_count(self):
        self.draw_text('Image', MNIST_IMAGE_START[0], \
            MNIST_IMAGE_START[1] + MNIST_IMAGE_SIZE[1] + 10, 20)
        self.draw_text('out of  %d' % len(model.current_data), MNIST_IMAGE_START[0], \
            MNIST_IMAGE_START[1] + MNIST_IMAGE_SIZE[1] + 30, 20)
    def draw_image_count(self):

        # draw current image count
        i = model.current_image_index + 1
        i_x = MNIST_IMAGE_START[0] + 45 # i_x is the x location
        i_y = MNIST_IMAGE_START[0] + MNIST_IMAGE_SIZE[1] + 10 # i_y is the y location
        self.draw_text(str(i), i_x, i_y, 20)

        # draw current percent complete
        perc = 100*float(i)/len(model.current_data)
        perc_x = MNIST_IMAGE_START[0] # perc_x is the x location
        perc_y = MNIST_IMAGE_START[0] + MNIST_IMAGE_SIZE[1] + 50 # perc_y is the y location
        self.draw_text('%.1f %%' % perc, perc_x, perc_y, 20)

    # these functions show the accuracy over time
    def setup_current_accuracy_text(self):
        text = 'Current Accuracy'
        self.draw_text(text, \
            MNIST_IMAGE_START[0], \
            MNIST_IMAGE_START[1] + MNIST_IMAGE_SIZE[1] + 130, \
            20)
    def draw_current_accuracy_text(self, i):
        if self.model.accuracy_log != []:
            current_accuracy = '%.4f %%' % (100*self.model.accuracy_log[i-1])
            self.draw_text(current_accuracy, \
                MNIST_IMAGE_START[0] + 120, \
                MNIST_IMAGE_START[1] + MNIST_IMAGE_SIZE[1] + 130, \
                20)
    def plot_accuracy_log(self):

        fig = plt.figure()
        plt.plot(self.model.accuracy_log)
        plt.title('Training Accuracy')
        plt.xlabel('Sample Number')
        plt.ylabel('Accuracy %')
        plt.show()
        # fig.savefig('training_accuracy.jpg')

    # these functions draw the key board controls and current
    def draw_keyboard_controls(self):

        # draw control key
        for n, line in enumerate(MNIST_CONTROL_KEY):
            self.draw_text(line, \
                MNIST_IMAGE_START[0] + MNIST_IMAGE_SIZE[0] + 50, \
                MNIST_IMAGE_START[1] + 14*n, 20)
    def draw_keyboard_settings(self):
        controller = self.model.controller
        settings = [
            'AIRIS' if model.airis_controlled else 'Manual',
            'Playing' if not controller.paused else 'Paused',
            'Yes' if controller.render_gui else 'No'
        ]

        # draw control settings
        for n, line in enumerate(settings):
            self.draw_text(line, \
                MNIST_IMAGE_START[0] + MNIST_IMAGE_SIZE[0] + 270, \
                MNIST_IMAGE_START[1] + 13 + 14*n, 20)

    def draw_text(self, text, x, y, size, \
        text_color = (100, 100, 100), \
        background_color = (0, 0, 0)):

        # make text
        basicfont = pygame.font.SysFont(None, size)
        text_render = basicfont.render(text, True, text_color)
        text_width = text_render.get_width()
        text_height = text_render.get_height()

        # draw background
        pygame.draw.rect(self.surface, background_color, \
            [x, y, text_width+50, text_height])

        # draw text
        self.surface.blit(text_render, (x, y))

class Model(object):

    def __init__(self, controller, airis_controlled, data_to_use):

        # window parameters / drawing
        self.show = True # show current model
        self.controller = controller

        # get mnist data set
        print('\ncollecting mnist data ...')
        start_time = time.time()
        get_all_data = False
        self.mnist_training = self.get_mnist_data( \
            './images/mnist/train-images-idx3-ubyte', \
            './images/mnist/train-labels-idx1-ubyte', \
            60000, all_data=get_all_data, n=60)
        self.mnist_testing = self.get_mnist_data( \
            './images/mnist/t10k-images-idx3-ubyte', \
            './images/mnist/t10k-labels-idx1-ubyte', \
            10000, all_data=get_all_data, n=10)
        print('data collected: %.3f seconds\n' % (time.time() - start_time))

        # setup data structure to track prediction results
        self.setup_test(data_to_use)

        # AGI setup
        self.screen_input = []
        for x in range(MNIST_IMAGE_GRID[0]):
            self.screen_input.append([])
            for y in range(MNIST_IMAGE_GRID[1]):
                self.screen_input[x].append(0.0)
        self.aux_input = [-1]
        action_space = ['reveal']
        #action_output_list = output range of each action [min, max, increment size]
        action_output_list = [
            [1, 2, 1]
        ]
        self.airis = AIRIS(self.screen_input, self.aux_input, action_space, action_output_list)
        self.airis_controlled = airis_controlled
        self.airis.goal_type = 'Predict'
        self.airis.goal_type_default = 'Predict'

    # this function updates the model
    def update(self, controller):

        # make prediction

        if not self.prediction and self.airis_controlled:

            # give unlabeled image environment to airis and get label prediction from airis
            self.current_environment(False)
            _, _, aux_predict = self.airis.capture_input(self.screen_input, self.aux_input, 'reveal', True)

            if aux_predict:
                print('I think this is a ', aux_predict[0][2])
                self.prediction = aux_predict[0][2]
            else:
                print('I don\'t know what this is...')
                self.prediction = -1

            # give labeled image to airis
            self.current_environment(True)
            self.airis.capture_input(self.screen_input, self.aux_input, 'reveal', False)

            if self.aux_input[0] == self.prediction:
                print('I was right!')
            else:
                print('I was wrong...')

        if self.prediction == None and not self.airis_controlled:

            self.prediction = self.controller.prediction

        # if the user or airis has made a prediction
        if self.prediction != None:

            # get prediction and then reset it
            prediction = int(self.prediction)
            self.prediction = None
            self.controller.prediction = None

            # get current image and label
            current_image = self.current_data[self.current_image_index]
            label = current_image[1]

            # update prediction results if its correct or incorrect
            # and save accuracy to accuracy log
            self.update_accuracy(prediction, label)
            # self.print_results()

            # get next image
            self.current_image_index += 1

        return self.current_image_index != len(self.current_data)

    def current_environment(self, give_label):
        current_image = self.current_data[self.current_image_index]
        image, label = current_image
        for x in range(MNIST_IMAGE_GRID[0]):
            for y in range(MNIST_IMAGE_GRID[1]):
                pixel_value = image[MNIST_IMAGE_GRID[0]*y+x]
                self.screen_input[x][y] = pixel_value

        if give_label:
            self.aux_input[0] = label
        else:
            self.aux_input[0] = -1

    # these functions handle prediction accuracy
    def setup_test(self, data_to_use):

        if data_to_use == 'train':
            self.current_data = self.mnist_training
            self.current_log = MNIST_TRAINING_ACCURACY_LOG
            self.clear_file(MNIST_TRAINING_ACCURACY_LOG)
        elif data_to_use == 'test':
            self.current_data = self.mnist_testing
            self.current_log = MNIST_TESTING_ACCURACY_LOG
            self.clear_file(MNIST_TESTING_ACCURACY_LOG)
        else:
            print('ERROR: invalid arguement to setup_test function')
            pygame.quit()
            sys.exit()
        self.current_image_index = 0

        self.prediction = None
        self.results = {
            '0':{'correct':0, 'total':0, 'accuracy':0.00},
            '1':{'correct':0, 'total':0, 'accuracy':0.00},
            '2':{'correct':0, 'total':0, 'accuracy':0.00},
            '3':{'correct':0, 'total':0, 'accuracy':0.00},
            '4':{'correct':0, 'total':0, 'accuracy':0.00},
            '5':{'correct':0, 'total':0, 'accuracy':0.00},
            '6':{'correct':0, 'total':0, 'accuracy':0.00},
            '7':{'correct':0, 'total':0, 'accuracy':0.00},
            '8':{'correct':0, 'total':0, 'accuracy':0.00},
            '9':{'correct':0, 'total':0, 'accuracy':0.00},
            'total':{'correct':0, 'total':0, 'accuracy':0.00}
        }
        self.accuracy_log = []
    def update_accuracy(self, prediction, label):

        if prediction == label:
            self.results[str(label)]['correct'] += 1
            self.results['total']['correct'] += 1

        self.results[str(label)]['total'] += 1
        self.results['total']['total'] += 1

        self.results[str(label)]['accuracy'] = \
            float(self.results[str(label)]['correct']) / self.results[str(label)]['total']
        self.results['total']['accuracy'] = \
            float(self.results['total']['correct']) / self.results['total']['total']

        self.accuracy_log.append(self.results['total']['accuracy'])

        self.write_accuracy(self.current_log)
    def print_results(self):
        for k, v in self.results.items():
            print('%s:\t%s' % (k, v))

    # these functions gets the mnist data
    def get_mnist_data(self, imgf, labelf, N, all_data=False, n=20):
        if all_data:
            return self.get_all_data(imgf, labelf, N)
        else:
            return self.get_some_data(imgf, labelf, N, n)
    def get_all_data(self, imgf, labelf, N):
        # https://pjreddie.com/projects/mnist-in-csv/
        # gets the first n samples from the file
        f = open(imgf, "rb")
        l = open(labelf, "rb")
        f.read(16)
        l.read(8)
        data = []
        for i in range(N):
            label = [ord(l.read(1))][0]
            image = []
            for j in range(28*28):
                image.append(ord(f.read(1)))
            # self.print_mnist_image(image[1:])
            data.append((image, label))
        return data
    def get_some_data(self, imgf, labelf, N, n=20):
        # https://pjreddie.com/projects/mnist-in-csv/
        # set 'all_data' to True if you want all N samples
        # if 'all_data' is set to False, this function returns
        # n samples of each digit are required

        f = open(imgf, "rb")
        l = open(labelf, "rb")

        f.read(16)
        l.read(8)
        data = []
        num_of_each_digit = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0}
        # key = digit, value = number of samples of that digit

        for i in range(N):
            label = [ord(l.read(1))][0]
            image = []
            for j in range(28*28):
                image.append(ord(f.read(1)))
            # self.print_mnist_image(image[1:])
            if num_of_each_digit[label] >= n:
                continue
            else:
                data.append((image, label))
                num_of_each_digit[label] += 1
            # exit data gathering if we've got everything we need
            leave = True
            for val in num_of_each_digit.values():
                if val < n:
                    leave = False
                    break
            if leave: break

        return data

    def print_mnist_image(self, image):
        image_numbers = ''
        for y in range(MNIST_IMAGE_GRID[1]):
            row = ''
            for x in range(MNIST_IMAGE_GRID[0]):
                row += ('%d   ' % image[MNIST_IMAGE_GRID[0]*y+x])[:4]
            image_numbers += (row + '\n')
        print(image_numbers)

    def write_accuracy(self, filename):

        f = open(filename, 'a')
        f.write(str(self.results['total']['accuracy'])+'\n')
        f.close()
    def clear_file(self, filename):

        open(filename, 'w').close()

class PyGameKeyboardController(object):

    def __init__(self):

        self.paused = False
        self.prediction = None
        self.render_gui = True
        self.just_disabled_gui = False

    def handle_event(self, event):

        if event.type != KEYDOWN:
            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = pygame.mouse.get_pos()
                print('mouse position = (%d,%d)' % (mouse_pos[0], mouse_pos[1]))

                if event.button == 4:
                    # print('mouse wheel scroll up')
                    pass
                elif event.button == 5:
                    # print('mouse wheel scroll down')
                    pass
                elif event.button == 1:
                    # print('mouse left click')
                    pass
                elif event.button == 3:
                    pass
                    # print('mouse right click')
                else:
                    pass
                    # print('event.button = %d' % event.button)

        elif event.key == pygame.K_SPACE:
            if model.airis_controlled:
                self.paused = not self.paused
            # only able to pause/play for manual control
            view.draw_keyboard_settings()

        elif event.key == pygame.K_a:
            model.airis_controlled = not model.airis_controlled
            if not model.airis_controlled:
                self.paused = False
            # only able to pause/play for manual control
            view.draw_keyboard_settings()

        elif event.key == pygame.K_r:
            self.render_gui = not self.render_gui
            if not self.render_gui:
                self.just_disabled_gui = True
            view.draw_keyboard_settings()

        elif event.key == pygame.K_UP:
            # print('up arrow')
            pass
        elif event.key == pygame.K_DOWN:
            # print('down arrow')
            pass
        elif event.key == pygame.K_LEFT:
            # print('left arrow')
            pass
        elif event.key == pygame.K_RIGHT:
            # print('right arrow')
            pass

        elif event.key == pygame.K_0:
            # print('0')
            self.prediction = '0'
        elif event.key == pygame.K_1:
            # print('1')
            self.prediction = '1'
        elif event.key == pygame.K_2:
            # print('2')
            self.prediction = '2'
        elif event.key == pygame.K_3:
            # print('3')
            self.prediction = '3'
        elif event.key == pygame.K_4:
            # print('4')
            self.prediction = '4'
        elif event.key == pygame.K_5:
            # print('5')
            self.prediction = '5'
        elif event.key == pygame.K_6:
            # print('6')
            self.prediction = '6'
        elif event.key == pygame.K_7:
            # print('7')
            self.prediction = '7'
        elif event.key == pygame.K_8:
            # print('8')
            self.prediction = '8'
        elif event.key == pygame.K_9:
            # print('9')
            self.prediction = '9'
        else: pass

        # another way to do it, gets keys currently pressed
        keys = pygame.key.get_pressed()  # checking pressed keys
        if keys[pygame.K_UP]:
            pass # etc. ...

if __name__ == '__main__':

    # pygame setup
    airis_controlled = True
    pygame.init()
    controller = PyGameKeyboardController()
    model = Model(controller, airis_controlled, 'train')
    view = PyGameView(model)

    # training
    start_time = time.time()
    training = True
    pygame.display.set_caption('training AIRIS ...'+str(id(pygame)))
    while training:

        # handle user input
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            else:
                controller.handle_event(event)

        # update the model
        if not controller.paused:
            training = model.update(controller)

        # display the view
        if training and (controller.render_gui or controller.just_disabled_gui):
            controller.just_disabled_gui = False
            view.draw()
            view.screen.blit(view.surface, (0,0))
            pygame.display.update()
            #time.sleep(1.0) # control frame rate (in seconds)

    print('training complete: %.3f seconds\n' % (time.time() - start_time))

    testing = True
    start_time = time.time()
    model.setup_test('test')
    view = PyGameView(model)
    pygame.display.set_caption('testing AIRIS ...'+str(id(pygame)))
    while testing:

        # handle user input
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            else:
                controller.handle_event(event)

        # update the model
        if not controller.paused:
            testing = model.update(controller)

        # display the view
        if testing and (controller.render_gui or controller.just_disabled_gui):
            controller.just_disabled_gui = False
            view.draw()
            view.screen.blit(view.surface, (0,0))
            pygame.display.update()
            #time.sleep(1.0) # control frame rate (in seconds)

    print('testing complete: %.3f seconds\n' % (time.time() - start_time))

    print('Accuracy = %.4f %%\n' % (100 * model.results['total']['accuracy']))

    model.airis.save_knowledge()

    pygame.quit()
    sys.exit()
