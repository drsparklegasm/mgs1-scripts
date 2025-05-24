# Subtitle test 2

import json
import time

# Load JSON data
with open('workingFiles/vag-testing.json', 'r') as file:
    dialogue_data = json.load(file)

# Extract dialogues from the nested structure
dialogues = []
for key1, value1 in dialogue_data.items():
    for key2, value2 in value1.items():
        for key3, dialogue in value2.items():
            start_frame = int(dialogue['startFrame'])
            display_frames = int(dialogue['displayFrames'])
            text = dialogue.get('text', '')
            dialogues.append((start_frame, display_frames, text))

# Sort dialogues by start frame
dialogues.sort(key=lambda x: x[0])

# Simulate frame counting and display subtitles
current_frame = 0
while True:
    # Clear the screen (works in Unix-like systems)
    print("\033[H\033[J", end="")

    # Track which dialogues are currently active
    active_dialogues = []

    # Check if there are any dialogues to display at the current frame
    for start_frame, display_frames, text in dialogues:
        if start_frame <= current_frame < start_frame + display_frames:
            active_dialogues.append(text)

    # Print all active dialogues
    for text in active_dialogues:
        print(text)

    # Increment the frame counter
    current_frame += 1

    # Simulate frame rate (30 fps)
    time.sleep(1/30)

    # Break condition to stop the loop after a certain number of frames or other criteria
    if current_frame > 200:  # Adjust this condition as needed
        break
