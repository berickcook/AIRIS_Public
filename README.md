# AIRIS - Public Release

AIRIS is an Artificial General Intelligence (AGI) project that combines aspects of Reinforcement Learning (RL) with more traditional symbolic techniques (GOFAI).

[See http://airis-ai.com for videos and additional information.](http://airis-ai.com)

Requires Python 3.x

See "requirements.txt" for additional required packages

###### The Cognitive Architecture of AIRIS 
![AIRIS Cognitive Architecture](https://airisai.files.wordpress.com/2019/01/airis-cognitive-architecture-3.png)

# Example Tests

Included in the stable release are 3 test environments.

Simply run either puzzle_game_driver.py / mnist_driver2.py / or basic_example.py

## puzzle_game_driver.py 
A grid-world puzzle game with various obstacles. The goal is to collect all batteries in a level. 

![Puzzle Game Level](https://airisai.files.wordpress.com/2019/01/puzzle-game-level.png)

[Gif of AIRIS Completing the puzzle](https://airisai.files.wordpress.com/2018/03/level.gif)

###### puzzle_game_driver.py additional controls

To enable "view plan" mode, hold the Up Arrow on your keyboard until the console says "Awaiting plan approval..."

You can then use the Left and Right arrow keys to step through each action the AI is planning to perform, and what it expects the result to be.

Press the Space Bar on your keyboard to "approve" the plan and allow the AI to continue.

To disable "view plan" mode, hold the Down Arrow

###### Note: "view plan" mode not fully tested and may cause instabilities!

## mnist_driver2.py
Number recognition using the MNIST hand-written character dataset

![MNIST Character](https://airisai.files.wordpress.com/2018/03/sprite0_4.png)

## basic_example.py

This is intended to be a simple usage example. It will ask for a word, then ask what the label of that word is. It will try to predict what the label is for new words.

```
Enter a word:
  Robert
The AI doesn't yet have knowledge
What is the label for this word?
  Name
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
  House
The AI thinks the label for this word is:  Name
What is the label for this word?
  Location
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
  Bill
The AI thinks the label for this word is:  Location
What is the label for this word?
  Name
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
  Bob
The AI thinks the label for this word is:  Name
What is the label for this word?
  Name
Enter a word:
  Building
The AI thinks the label for this word is:  Name
What is the label for this word?
  Location
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
  Home
The AI thinks the label for this word is:  Name
What is the label for this word?
  Location
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
  Housing
The AI thinks the label for this word is:  Location
What is the label for this word?
  Location
Enter a word:
  Apartment
The AI thinks the label for this word is:  Location
What is the label for this word?
  Location
Enter a word:
  John
The AI thinks the label for this word is:  Location
What is the label for this word?
  Name
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
  Jim
The AI thinks the label for this word is:  Location
What is the label for this word?
  Name
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
  James
The AI thinks the label for this word is:  Location
What is the label for this word?
    Name
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
    Joe
The AI thinks the label for this word is:  Name
What is the label for this word?
    Name
Enter a word:
    Studio
The AI thinks the label for this word is:  Name
What is the label for this word?
    Location
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
    Studio Apartment
The AI thinks the label for this word is:  Location
What is the label for this word?
    Location
Enter a word:
    Office
The AI thinks the label for this word is:  Name
What is the label for this word?
    Location
This is not the outcome I predicted
Saving new knowledge ...
Enter a word:
    Office Building
The AI thinks the label for this word is:  Location
What is the label for this word?
    Location
Enter a word:
```

## Special Thanks to Lucius Dickerson for helping to teach me Python, fixing my newbie mistakes, and for porting the test environments!
