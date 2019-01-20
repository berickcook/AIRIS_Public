# AIRIS - Public Release

AIRIS is an Artificial General Intelligence (AGI) project that combines aspects of Reinforcement Learning (RL) with more traditional symbolic techniques (GOFAI).

[See http://airis-ai.com for videos and additional information.](http://airis-ai.com)

Requires Python 3.x

See "requirements.txt" for additional required packages

###### This is the Cognitive Architecture of AIRIS 
![AIRIS Cognitive Architecture](https://airisai.files.wordpress.com/2019/01/airis-cognitive-architecture-3.png)

# Example Tests

Included in the stable release are 2 test environments: 

## puzzle_game_driver.py 
A grid-world puzzle game with various obstacles. The goal is to collect all batteries in a level. 

![Puzzle Game Level](https://airisai.files.wordpress.com/2019/01/puzzle-game-level.png)

[Gif of AIRIS Completing a puzzle](https://airisai.files.wordpress.com/2018/03/level.gif)

###### puzzle_game_driver.py additional controls

To enable "view plan" mode, hold the Up Arrow on your keyboard until the console says "Awaiting plan approval..."

You can then use the Left and Right arrow keys to step through each action the AI is planning to perform, and what it expects the result to be.

Press the Space Bar on your keyboard to "approve" the plan and allow the AI to continue.

To disable "view plan" mode, hold the Down Arrow

###### Note: "view plan" mode not fully tested and may cause instabilities!

## mnist_driver2.py
Number recognition using the MNIST hand-written character dataset

![MNIST Character](https://airisai.files.wordpress.com/2018/03/sprite0_4.png)
