from airis_stable import AIRIS

# Environment Setup
# For now, the environment has to be a 2D array, but were only going to use 1 of the D's for this example
character_input = [[]]
for x in range(32):
    character_input[0].append(0)

# aux_input is the encoded "label" of the word. It could be anything. Like 0 for noun, 1 for verb, or whatever.
# -1 is effectively null
aux_input = [-1]

# A list of actions that the AI can perform. Only one in this case.
action_space = ['label']

# action_output_list = output range of each action [min, max(exclusive), increment size]
# in this example, the output will always be 1
# this is really only useful for analog outputs like a joystick
action_output_list = [
    [1, 2, 1]
]

# AI Setup
airis = AIRIS(character_input, aux_input, action_space, action_output_list)
# we're only using AIRIS to make predictions in this example. No action planning is used.
airis.goal_type = 'Predict'
airis.goal_type_default = 'Predict'

while True:

    # First reset all inputs to 0
    for x in range(32):
        character_input[0][x] = 0
    aux_input[0] = -1

    aux_predict = []

    # Get a word from the user
    print("Enter a word:")
    get_word = input()

    # Fill in character_input with the character codes of all of the given word's letters
    for x in range(len(get_word)):
        character_input[0][x] = ord(get_word[x])

    # This line gives AIRIS the word with a -1 label (effectively, no label)
    # AIRIS then tries to predict what the correct label will be
    ai_action, vis_predict, aux_predict = airis.capture_input(character_input, [-1], 'label', True)

    if aux_predict:
        print("The AI thinks the label for this word is: ", int(aux_predict[0][2]))
    else:
        print("The AI doesn't yet have knowledge")

    # Get the integer label from the user
    # (Soon you will be able to give it any kind of label, like a string. Working on it...)
    print("What integer label is this word?")
    get_label = input()
    while True:
        try:
            int(get_label)
            aux_input[0] = get_label
            break
        except:
            print('Invalid entry. label must be an integer')
            get_label = input()

    # This line gives AIRIS the same word but with the correct label
    # It checks to see if its prediction was correct and updates its knowledge accordingly
    airis.capture_input(character_input, aux_input, 'label', False)
