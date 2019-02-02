from airis_stable import AIRIS

# Environment Setup
# For now, the environment has to be a 2D array, but were only going to use 1 of the D's for this example
character_input = [[]]
for x in range(32):
    character_input[0].append(0)

# aux_input is the "label" of the word. It could be anything.
aux_input = []
for x in range(32):
    aux_input.append(0)

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
    for x in range(32):
        aux_input[x] = 0

    # Clear any leftover predictions
    aux_predict = []

    # Get a word from the user
    print("Enter a word:")
    get_word = input()

    # Fill in character_input with the character codes of all of the given word's letters
    for x in range(len(get_word)):
        character_input[0][x] = ord(get_word[x])

    # This line gives AIRIS the word with an empty label (all 0's)
    # AIRIS then tries to predict what the correct label will be
    ai_action, vis_predict, aux_predict = airis.capture_input(character_input, aux_input, 'label', True)

    if aux_predict:
        # Convert the character codes of the predicted label back into characters for display
        display_prediction = ''
        for item in aux_predict:
            display_prediction += chr(item[2])

        print("The AI thinks the label for this word is: ", display_prediction)
    else:
        print("The AI doesn't yet have knowledge")

    # Get the label from the user
    print("What is the label for this word?")
    get_label = input()

    # Fill in aux_input with the character codes of the given label
    for x in range(len(get_label)):
        aux_input[x] = ord(get_label[x])

    # This line gives AIRIS the same word but with the correct label
    # It checks to see if its prediction was correct and updates its knowledge accordingly
    airis.capture_input(character_input, aux_input, 'label', False)
