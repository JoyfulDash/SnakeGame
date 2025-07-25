#!/usr/bin/env python3
# To-Do:
# Ensure powerup don't spawn in the beginning
# Ensure when pause, powerup timer stops

import pygame, random, sys, os, requests, time, subprocess

# Global variables
music_muted = False
sound_effects_enabled = True
paused_option = 0
pause_menu_options = ["Resume", "Toggle Sound Effects", "Toggle Music", "Main Menu"]
last_powerup_time = 0 #track last spawn/hide time in milliseconds
slow_effect_active = False
slow_effect_start_time = 0
fps = 30
normal_fps = fps # to keep track of normal speed
active_powerup = None
new_all_time_high_score = False
pygame.init()

menu_options = ["Play", "Leaderboard", "Update Game", "Credits", "Exit"]
selected_option = 0
state = "Menu"
input_name = ""
name_enter_active = False
new_high_score = False
cellsize = 20
width, height = 600, 400
separator_y = 40
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")

Black = (0, 0, 0)
Green = (50, 205, 50)
Red = (255, 0, 0)
White = (255, 255, 255)

# Food types: color and score value
food_types = [
    {"color": (255, 0, 0), "score": 50},      # Red
    {"color": (255, 165, 0), "score": 30},    # Orange
    {"color": ((255, 255, 0)), "score": 60}    # Yellow
]

#powerups
powerups = {
    "cyan": {
        "rect": pygame.Rect(-100, -100, cellsize, cellsize),
        "color": (0, 255, 255),  # Cyan
        "score": 0,
        "duration": 7000,
        "active": False,
        "effect": "slow"  # example effect, if any
    },
    "pink": {
        "rect": pygame.Rect(-100, -100, cellsize, cellsize),
        "color": (255, 105, 180),  # Pink
        "score": 0,
        "duration": 7000,
        "active": False,
        "effect": "bonus_points"
    },
    "purple": {
        "rect": pygame.Rect(-100, -100, cellsize, cellsize),
        "color": (128, 0, 128),  # Purple
        "score": 0,
        "duration": 7000,
        "active": False,
        "effect": "shrink"
    }
}

# Initialize current food type index
current_food_type = random.choice(food_types)

player = pygame.Rect(300, separator_y + 200, cellsize, cellsize)
snake = [player.copy()]
velocity = cellsize
direction = "right"
next_direction = direction
speed_level = 1

food = pygame.Rect(
    random.randint(0, (width - cellsize) // cellsize) * cellsize,
    random.randint(0, (height - separator_y) // cellsize - 1) * cellsize + separator_y,
    cellsize, cellsize
)
current_food_type = random.choice(food_types)

CLOCK = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
fps = 10
score = 0

def update_speed():
    global fps
    fps = 10 + (score // 1000) * 2

def reset_game():
    global snake, player, direction, next_direction, food, score
    player = pygame.Rect(300, separator_y + 200, cellsize, cellsize)
    snake = [player.copy()]
    direction = "right"
    next_direction = direction
    spawn_food()
    score = 0

    # Reset powerups
    for key in powerups:
        powerups[key]["active"] = False
        powerups[key]["rect"].x = -100  # Move off screen
    active_powerup = None

    # Reset slow effect and FPS
    slow_effect_active = False
    fps = normal_fps = 10  # or your default fps

FIREBASE_DB_URL = "https://snake-game-leaderboard-31464-default-rtdb.firebaseio.com/"

def load_leaderboard():
    try:
        res = requests.get(f"{FIREBASE_DB_URL}/scores.json")
        if res.status_code == 200 and res.json():
            data = res.json()
            entries = [(v["name"], v["score"]) for v in data.values()]
            return sorted(entries, key=lambda x: x[1], reverse=True)[:8]
    except Exception as e:
        print("Failed to load leaderboard:", e)
    return []

def update_leaderboard(name, new_score):
    leaderboard = load_leaderboard()
    if len(leaderboard) < 8 or new_score > leaderboard[-1][1]:
        try:
            data = {"name": name, "score": new_score}
            requests.post(f"{FIREBASE_DB_URL}/scores.json", json=data)
        except Exception as e:
            print("Failed to update leaderboard:", e)
            save_pending_score(name, new_score) #save locally if network fails
            show_message("Network error! Score saved locally.")
# Function to save pending score locally
def save_pending_score(name, score):
    try:
        with open("pending_score.txt", "a") as file:
            file.write(f"{name},{score}\n")
    except Exception as e:
        print("Failed to save pending score:", e)

def sync_pending_scores():
    if not os.path.exists("pending_score.txt"):
        return
    try:
        with open("pending_score.txt", "r") as file:
            lines = file.readlines()
        os.remove("pending_score.txt")  # Clear the file after reading
        for line in lines:
            name, score = line.strip().split(",")
            update_leaderboard(name, int(score)) #retry upload
    except Exception as e:
        print("Failed to sync pending scores:", e)

def show_message(message, duration=2000):
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # semi-transparent background
    screen.blit(overlay, (0, 0))

    message_text = font.render(message, True, White)
    screen.blit(
        message_text,
        (width // 2 - message_text.get_width() // 2, height // 2)
    )
    pygame.display.update()
    pygame.time.delay(duration)

def check_high_score(new_score):
    leaderboard = load_leaderboard()
    return len(leaderboard) < 8 or new_score > leaderboard[-1][1]

def get_highest_score():
    leaderboard = load_leaderboard()
    if leaderboard:
        return max(score for _, score in leaderboard)
    return 0

highest_score = get_highest_score()

pygame.mixer.init()

base_dir = os.path.dirname(os.path.abspath(__file__))
background_music_path = os.path.join(base_dir, "background.wav")
eat_sound = pygame.mixer.Sound(os.path.join(base_dir, "eat.wav"))
death_sound = pygame.mixer.Sound(os.path.join(base_dir, "death.wav"))
highscore_sound = pygame.mixer.Sound(os.path.join(base_dir, "highscore.wav"))

pygame.mixer.music.load(background_music_path)
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# Sync pending scores at the start
sync_pending_scores()

running = True
game_over = False

# Zoom-in animation function for Game Over text
def game_over_zoom_in_animation():
    base_font = pygame.font.SysFont(None, 60)
    max_size = 100
    min_size = 20
    steps = 15
    for step in range(steps):
        size = min_size + (max_size - min_size) * (step / (steps - 1))
        font_zoom = pygame.font.SysFont(None, int(size))
        text = font_zoom.render("Game Over", True, Red)
        screen.fill(Black)
        screen.blit(text, (width // 2 - text.get_width() // 2, height // 2 - text.get_height() // 2))
        pygame.display.update()
        pygame.time.delay(50)

# Add a flag attribute to remember if animation ran
game_over_zoom_in_animation.done = False

# Function to draw the game state
def draw_game():
    screen.fill(Black)

    # Draw horizontal line near top (e.g., 70 px from top)
    line_color = White
    pygame.draw.line(screen, White, (0, separator_y), (width, separator_y), 1)

    # Draw food BELOW the line (offset y by separator_y)
    food_rect_below = food
    pygame.draw.rect(screen, current_food_type["color"], food_rect_below)

    # Draw snake BELOW the line
    for segment in snake:
        # Only draw segment if fully visible inside vertical bounds
        if separator_y <= segment.y <= height - cellsize:
            pygame.draw.rect(screen, Green, segment)
    
    pygame.draw.rect(screen, current_food_type["color"], food)

    # Draw powerups BELOW the line
    for powerup in powerups.values():
        if powerup["active"]:
            pygame.draw.rect(screen, powerup["color"], powerup["rect"])

def update_game():
    global state
    state = "Updating"

    repo_dir = os.path.dirname(os.path.abspath(__file__))

    screen.fill(Black)
    text = font.render("Updating...", True, White)
    screen.blit(text, (width // 2 - text.get_width() // 2, height // 2))
    pygame.display.update()

    try:
        print("Changing directory to:", repo_dir)
        os.chdir(repo_dir)

        # Step 1: Hard reset any local changes
        subprocess.run(["git", "reset", "--hard"], check=True)

        # Step 2: Fetch latest from origin
        subprocess.run(["git", "fetch", "origin"], check=True)

        # Step 3: Hard reset to origin/main
        result = subprocess.run(["git", "reset", "--hard", "origin/main"], capture_output=True, text=True)
        print("Git stdout:", result.stdout)
        print("Git stderr:", result.stderr)

        output = result.stdout.strip()
        pygame.time.delay(1000)

        screen.fill(Black)
        update_result = "Game is already up to date." if "HEAD is now at" in output else "Update successful!"
        text = font.render(update_result, True, White)
        screen.blit(text, (width // 2 - text.get_width() // 2, height // 2))
        pygame.display.update()

        pygame.time.delay(2000)

        # ✅ Make the game script executable BEFORE restarting
        game_file = os.path.join(repo_dir, "gameSnake.py")
        try:
            subprocess.run(["chmod", "+x", game_file], check=True)
            print(f"chmod +x succeeded for {game_file}")
        except subprocess.CalledProcessError as chmod_error:
            print(f"chmod +x failed for {game_file}: {chmod_error}")
        except Exception as e:
            print(f"Unexpected error while setting executable permission: {e}")

        # ✅ Now restart the script
        os.execv(sys.executable, ['python'] + [os.path.abspath(__file__)])

    except Exception as e:
        error_text = font.render("Update failed!", True, Red)
        screen.fill(Black)
        screen.blit(error_text, (width // 2 - error_text.get_width() // 2, height // 2))
        pygame.display.update()
        print(f"Update error: {e}")
        pygame.time.delay(2000)
        state = "Menu"


#define mouse click handling
def handle_mouse_click(x, y):
    global state, selected_option, paused_option, music_muted, sound_effects_enabled, running, input_name, new_high_score, esc_rect
    if state == "Menu":
        for i, option in enumerate(menu_options):
            text = font.render(option, True, White)
            rect = text.get_rect(center=(width // 2, 150 + i * 40 + text.get_height() // 2))
            if rect.collidepoint(x, y):
                selected = option
                if selected == "Play":
                    state = "Playing"
                    reset_game()
                elif selected == "Leaderboard":
                    state = "Leaderboard"
                elif selected == "Update Game":
                    update_game()
                elif selected == "Credits":
                    state = "Credits"
                elif selected == "Exit":
                    running = False

    elif state == "Paused":
        #render pause menu options
        for i, option in enumerate(pause_menu_options):
            text = pygame.font.SysFont(None, 36).render(option, True, White)
            rect = text.get_rect(center=(width // 2, 150 + i * 40 + text.get_height() // 2))
            screen.blit(text, rect)

            #handle clicks
            if rect.collidepoint(x, y):
                paused_option = i
                if option == "Resume":
                    for i in range(3, 0, -1):
                        draw_game()  # Draw current game scene

                        #create a semi-transparent pause menu
                        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, 150))  # Semi-transparent black
                        screen.blit(overlay, (0, 0))

                        countdown = font.render(str(i), True, White)
                        screen.blit(countdown, (width // 2 - countdown.get_width() // 2, height // 2))
                        pygame.display.update()
                        pygame.time.delay(1000)
                    state = "Playing"
                elif option == "Toggle Sound Effects":
                    sound_effects_enabled = not sound_effects_enabled
                elif option == "Toggle Music":
                    music_muted = not music_muted
                    pygame.mixer.music.set_volume(0 if music_muted else 0.5)
                elif option == "Main Menu":
                    reset_game()
                    state = "Menu"
                    game_over_zoom_in_animation.done = False

    elif state == "Leaderboard" or state == "Credits" or state == "GameOver" or state == "Leaderboard":
        # ESC/Back to menu
        esc_text = pygame.font.SysFont(None, 24).render("Press ESC to Return", True, Red)
        esc_rect = esc_text.get_rect(center=(width // 2, height - 40))
        if esc_rect.collidepoint(x, y):
            state = "Menu"

    elif state == "EnterName":
        esc_text = pygame.font.SysFont(None, 24).render("Press ESC to Return", True, Red)
        esc_rect = esc_text.get_rect(center=(width // 2, height - 40))
        if esc_rect.collidepoint(x, y):
            input_name = ""
            new_high_score = False
            state = "Menu"

#spawn powerup
def spawn_powerup():
    global active_powerup, last_powerup_time
    active_powerup_key = random.choice(list(powerups.keys()))  # Pick a key string
    active_powerup = powerups[active_powerup_key]             # Get the powerup dict
    active_powerup["rect"].x = random.randint(0, (width - cellsize) // cellsize) * cellsize
    active_powerup["rect"].y = random.randint(0, (height - separator_y) // cellsize - 1) * cellsize + separator_y
    active_powerup["spawn_time"] = pygame.time.get_ticks()
    active_powerup["active"] = True
    last_powerup_time = active_powerup["spawn_time"]

def spawn_food():
    food.x = random.randint(0, (width - cellsize) // cellsize) * cellsize
    food.y = random.randint(0, (height - separator_y) // cellsize - 1) * cellsize + separator_y

#main game loop
while running:
    current_time = pygame.time.get_ticks()

    # Restore speed if slow effect duration is over
    if slow_effect_active and current_time - slow_effect_start_time >= 10000: # 10 seconds
        fps = normal_fps
        slow_effect_active = False

    CLOCK.tick(fps)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            mouse_x, mouse_y = event.pos
            handle_mouse_click(mouse_x, mouse_y)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and state != "EnterName":
                if state in ("Playing", "GameOver"):
                    reset_game()
                    state = "Menu"
                    game_over = False
                    game_over_zoom_in_animation.done = False
                elif state == "Leaderboard":
                    pass
                elif state == "Credits":
                    pass
                else:
                    running = False
            if event.key == pygame.K_m and state not in ("EnterName",):
                music_muted = not music_muted
                pygame.mixer.music.set_volume(0 if music_muted else 0.5)

            if state == "Menu":
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN or event.key == 1073741912:
                    selected = menu_options[selected_option]
                    if selected == "Play":
                        state = "Playing"
                        reset_game()
                        game_over = False
                        game_over_zoom_in_animation.done = False
                    elif selected == "Leaderboard":
                        state = "Leaderboard"
                    elif selected == "Update Game":
                        update_game()
                    elif selected == "Credits":
                        state = "Credits"
                    elif selected == "Exit":
                        running = False

            elif state == "Playing":
                if event.key == pygame.K_LEFT and direction != "right":
                    next_direction = "left"
                elif event.key == pygame.K_RIGHT and direction != "left":
                    next_direction = "right"
                elif event.key == pygame.K_UP and direction != "down":
                    next_direction = "up"
                elif event.key == pygame.K_DOWN and direction != "up":
                    next_direction = "down"
                elif event.key == pygame.K_p:
                    state = "Paused"

            elif state == "Paused":
                if event.key == pygame.K_UP:
                    paused_option = (paused_option - 1) % len(pause_menu_options)
                elif event.key == pygame.K_DOWN:
                    paused_option = (paused_option + 1) % len(pause_menu_options)
                elif event.key == pygame.K_RETURN or event.key == 1073741912:
                    selected = pause_menu_options[paused_option]
                    if selected == "Resume":
                        for i in range (3, 0, -1):

                            draw_game()  # Draw current game scene

                            #create a semi-transparent pause menu
                            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                            overlay.fill((0, 0, 0, 150))  # Semi-transparent black
                            screen.blit(overlay, (0, 0))

                            countdown = font.render(str(i), True, White)
                            screen.blit(countdown, (width // 2 - countdown.get_width() // 2, height // 2))
                            pygame.display.update()
                            pygame.time.delay(1000)
                        state = "Playing"
                    elif selected == "Toggle Sound Effects":
                        sound_effects_enabled = not sound_effects_enabled
                    elif selected == "Toggle Music":
                        music_muted = not music_muted
                        pygame.mixer.music.set_volume(0 if music_muted else 0.5)
                    elif selected == "Main Menu":
                        reset_game()
                        state = "Menu"
                        game_over_zoom_in_animation.done = False

            elif state == "Credits" and event.key == pygame.K_ESCAPE:
                state = "Menu"

            elif state == "Leaderboard" and event.key == pygame.K_ESCAPE:
                state = "Menu"
            elif state == "GameOver" and event.key == pygame.K_ESCAPE:
                if new_high_score:
                    input_name = ""
                    new_high_score = False
                    state = "EnterName"
                else:
                    reset_game()
                    state = "Menu"
                    game_over_zoom_in_animation.done = False

            elif state == "GameOver" and event.key == pygame.K_SPACE:
                reset_game()
                state = "Playing"
                game_over = False
                game_over_zoom_in_animation.done = False

            elif state == "EnterName":
                if (event.key == pygame.K_RETURN or event.key == 1073741912) and input_name:
                    update_leaderboard(input_name, score)
                    input_name = ""
                    new_high_score = False
                    highest_score = get_highest_score()
                    state = "Leaderboard"
                elif event.key == pygame.K_BACKSPACE:
                    input_name = input_name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    input_name = ""
                    new_high_score = False
                    state = "Menu"
                else:
                    if len(input_name) < 10:
                        char = event.unicode
                        if char.isalnum() or char in " _-":
                            input_name += char

    if state == "Playing" and not game_over:
        direction = next_direction

        if direction == "left":
            new_head = player.move(-velocity, 0)
        elif direction == "right":
            new_head = player.move(velocity, 0)
        elif direction == "up":
            new_head = player.move(0, -velocity)
        elif direction == "down":
            new_head = player.move(0, velocity)

        new_head.x %= width
        if new_head.y < separator_y:
            new_head.y = height - cellsize
        elif new_head.y >= height:
            new_head.y = separator_y
        # else: new_head stays the same if within bounds

        snake.insert(0, new_head)

        if new_head in snake[1:]:
            if sound_effects_enabled:
                death_sound.play()

            game_over = True

            leaderboard = load_leaderboard()
            highest_score = get_highest_score()
            is_new_high_score = check_high_score(score)
            new_all_time_high_score = score > highest_score

            scores = [s for _, s in leaderboard]
            is_new_high_score = check_high_score(score)
            new_all_time_high_score = score > highest_score

            if is_new_high_score:
                new_high_score = True
                state = "EnterName"
                input_name = ""
            else:
                state = "GameOver"
                game_over_zoom_in_animation.done = False  # Let it run once inside GameOver state

            game_over = True

        if new_head.colliderect(food):
            if sound_effects_enabled:
                eat_sound.play()
            score += current_food_type["score"]
            food.x = random.randint(0, (width - cellsize) // cellsize) * cellsize
            food.y = random.randint(0, (height - separator_y - cellsize) // cellsize) * cellsize + separator_y
            current_food_type = random.choice(food_types)
            
            # check if score is a new high score to play sound
            if score > highest_score and not new_all_time_high_score:
                if sound_effects_enabled:
                    highscore_sound.play()
                new_all_time_high_score = True
                highest_score = score

        else:
            snake.pop()

        player = new_head

        current_time = pygame.time.get_ticks()

        if (not active_powerup or not active_powerup["active"]) and current_time - last_powerup_time >= 120000:
            spawn_powerup()
            last_powerup_time = current_time

        if active_powerup and active_powerup["active"] and current_time - active_powerup["spawn_time"] > active_powerup["duration"]:
            active_powerup["active"] = False
            active_powerup["rect"].x = -100
            last_powerup_time = current_time

        if active_powerup and active_powerup["active"] and player.colliderect(active_powerup["rect"]):
            active_powerup["active"] = False
            active_powerup["rect"].x = -100
            if sound_effects_enabled:
                eat_sound.play()

            if active_powerup["effect"] == "slow" and not slow_effect_active:
                normal_fps = fps
                fps = max(5, fps // 2)
                slow_effect_active = True
                slow_effect_start_time = current_time

            elif active_powerup["effect"] == "bonus_points":
                score += 150  # Plus 150 points
            
            elif active_powerup["effect"] == "shrink":
                shrink_amount = max(1, len(snake) // 3)  # remove 1/3 or at least 1 segment
                for _ in range(shrink_amount):
                    if len(snake) > 1:
                        snake.pop()

    screen.fill(Black)

    # State rendering
    if state == "Menu":
        title = font.render("Snake ", True, Green)
        screen.blit(title, (width // 2 - title.get_width() // 2, 50))
        for i, option in enumerate(menu_options):
            color = Red if i == selected_option else White
            text = font.render(option, True, color)
            screen.blit(text, (width // 2 - text.get_width() // 2, 150 + i * 40))

    elif state == "Credits":
        title = font.render("Credits", True, Green)
        screen.blit(title, (width // 2 - title.get_width() // 2, 50))
        credit = pygame.font.SysFont(None, 32).render("Thanks for playing!", True, Red)
        screen.blit(credit, (width // 2 - credit.get_width() // 2, height // 2))
        #ESC clickable return
        esc_text = pygame.font.SysFont(None, 24).render("Press ESC to Return", True, Red)
        esc_rect = esc_text.get_rect(center=(width // 2, height - 40))
        screen.blit(esc_text, esc_rect)

    elif state == "Paused":
        pause_title = font.render("Game Paused", True, Green)
        screen.blit(pause_title, (width // 2 - pause_title.get_width() // 2, 50))

        for i, option in enumerate(pause_menu_options):
            label = option
            if option == "Toggle Sound Effects":
                label += f" ({'On' if sound_effects_enabled else 'Off'})"
            if option == "Toggle Music":
                label += f" ({'Off' if music_muted else 'On'})"
            color = Red if i == paused_option else White
            text = pygame.font.SysFont(None, 36).render(label, True, color)
            screen.blit(text, (width // 2 - text.get_width() // 2, 150 + i * 40))

    elif state == "Playing":
        draw_game()

        # Draw powerups if active
        for key, pwr in powerups.items():
            if pwr["active"]:
                pygame.draw.rect(screen, pwr["color"], pwr["rect"])

        # Create a smaller font for scores (size 24)
        score_font = pygame.font.SysFont(None, 24)

        # Draw current score
        score_text = score_font.render(f"Score: {score}", True, White)
        screen.blit(score_text, (10, 20))  # Adjust Y if needed

        # Draw high score
        high_score_text = score_font.render(f"High Score: {highest_score}", True, Green)
        screen.blit(high_score_text, (10, 2))


        mute_status = pygame.font.SysFont(None, 24).render("Muted" if music_muted else "Press M to Mute", True, White)
        screen.blit(mute_status, (width - mute_status.get_width() - 10, 2))
        pause_status = pygame.font.SysFont(None, 24).render("Press P to Pause", True, White)
        screen.blit(pause_status, (width - pause_status.get_width() - 10, 20))
        quit_msg = pygame.font.SysFont(None, 24).render("Press Q for Main Menu", True, White)
        screen.blit(quit_msg, (width // 2 - quit_msg.get_width() // 2, 10))

    elif state == "GameOver":
        # Run zoom-in animation once
        if not game_over_zoom_in_animation.done:
            game_over_zoom_in_animation.done = True
            game_over_zoom_in_animation()

        # Draw "Game Over" in red at fixed size near the top
        game_over_font = pygame.font.SysFont(None, 60)
        go_text = game_over_font.render("Game Over", True, Red)
        screen.blit(go_text, (width // 2 - go_text.get_width() // 2, 50))
        score_text = font.render(f"Score: {score}", True, White)
        screen.blit(score_text, (width // 2 - score_text.get_width() // 2, height // 2 - score_text.get_height() // 2))
        
        #ESC clickable return
        esc_text = pygame.font.SysFont(None, 24).render("Press ESC to Return", True, Red)
        esc_rect = esc_text.get_rect(center=(width // 2, height - 40))
        screen.blit(esc_text, esc_rect)

        # Draw "Press PSACE to play again" message
        space_text = pygame.font.SysFont(None, 24).render("Press SPACE to Play Again", True, White)
        space_rect = space_text.get_rect(center=(width // 2, height - 70))
        screen.blit(space_text, space_rect)

    elif state == "Leaderboard":
        title = font.render("Leaderboard", True, Green)
        screen.blit(title, (width // 2 - title.get_width() // 2, 20))
        leaderboard = load_leaderboard()
        for i, (name, sc) in enumerate(leaderboard):
            entry_text = pygame.font.SysFont(None, 28).render(f"{i+1}. {name}: {sc}", True, White)
            screen.blit(entry_text, (width // 2 - entry_text.get_width() // 2, 70 + i * 30))

        #ESC clickable return
        esc_text = pygame.font.SysFont(None, 24).render("Press ESC to Return", True, Red)
        esc_rect = esc_text.get_rect(center=(width // 2, height - 40))
        screen.blit(esc_text, esc_rect)

    elif state == "EnterName":
        if new_all_time_high_score:
            prompt_text = "New All-Time Score! Enter your name:"
            prompt_color = Red
        else:
            prompt_text = "New High Score! Enter your name:"
            prompt_color = Green  # fallback color if Red is only for all-time high

        # Render the prompt (now using the corrected string and color)
        prompt = font.render(prompt_text, True, prompt_color)
        screen.blit(prompt, (width // 2 - prompt.get_width() // 2, 100))

        # Blinking cursor logic
        cursor_char = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else ""
        name_with_cursor = input_name + cursor_char
        name_surface = font.render(name_with_cursor, True, White)
        screen.blit(name_surface, (width // 2 - name_surface.get_width() // 2, 150))

        # Draw ESC message only (no click detection here)
        esc_text = pygame.font.SysFont(None, 24).render("Press ESC to Return", True, Red)
        esc_rect = esc_text.get_rect(center=(width // 2, height - 40))
        screen.blit(esc_text, esc_rect)

    pygame.display.update()

pygame.quit()
