import pygame
import json

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Dialogue Display")

# Load JSON data
with open('workingfiles/vag-testing.json', 'r') as file:
    dialogue_data = json.load(file)

# Font for displaying text
font = pygame.font.Font(None, 36)
fps = 30
clock = pygame.time.Clock()

# Function to draw text on the screen
def draw_text(text, x, y):
    surface = font.render(text, True, (255, 255, 255))
    screen.blit(surface, (x, y))

# Main loop
running = True
current_frame = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Clear the screen
    screen.fill((0, 0, 0))
    
    # Determine which dialogue to show based on current frame
    for key1, value1 in dialogue_data.items():
        for key2, value2 in value1.items():
            for key3, dialogue in value2.items():
                start_frame = int(dialogue['startFrame'])
                display_frames = int(dialogue['displayFrames'])
                
                if start_frame <= current_frame < (start_frame + display_frames):
                    draw_text(dialogue['text'], 100, 100)
    
    # Update the screen
    pygame.display.flip()
    
    # Increment frame and control the frame rate
    current_frame += 1
    clock.tick(fps)

# Quit Pygame
pygame.quit()
