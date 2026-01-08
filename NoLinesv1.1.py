import tkinter as tk
import random

import geopandas as gpd
from shapely.geometry import Point

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from shapely.geometry import box

import time
import json
import os

HIGHSCORE_FILE = "highscore.json"

# -------------------
# Load shapefile
# -------------------
states = gpd.read_file(r"C:\Users\rufus\Downloads\cb_2018_us_state_20m\cb_2018_us_state_20m.shp")

# Remove Puerto Rico and Washington DC
states = states[states["STUSPS"] != "PR"]
states = states[states["STUSPS"] != "DC"]

#crop to include the contiguous US, Alaska, and Hawaii
bbox = box(-170, 18, -65, 72)
states = states.to_crs("EPSG:4326")
states = states.clip(bbox)

NAME_COL = "NAME"
if NAME_COL not in states.columns:
    raise ValueError(f"Can't find '{NAME_COL}' column. Columns are: {list(states.columns)}")

# Starting colours
states["fill"] = "tan"

# Spatial index for fast click detection
sindex = states.sindex

# -------------------
# Tkinter UI
# -------------------
root = tk.Tk()
root.title("nolines")
root.state("zoomed")

# set up exit button
button = tk.Button(root, text="EXIT", font=("Cambria", 10, "bold" ), bg="#CF3333", fg="#FFFFFF")
button.pack(anchor="w")
button.config(command=root.destroy)

# title label
label = tk.Label(root,
                 text="nolines",
                 font=("Cambria", 25, "bold", "italic"),
                 fg="#FFFFFF",                    # text color
                 bg="black",                 # background color
                 highlightbackground="tan",# highlight border color
                 highlightthickness=6,
                 relief="sunken",              # raised appearance
                 bd=4,
                 padx=10,
                 pady=5
                 )
label.pack(pady=20)


def action_button_clicked():
    if game_running:
        restart_game()
    else:
        press_start()

# action button
action_button = tk.Button(
    root,
    text="START",
    font=("Cambria", 10, "bold"),
    bg="#4E59FC",
    fg="white",
    padx=10,
    pady=5,
    command=action_button_clicked)
action_button.pack(pady=6)


# timer label
timer_label = tk.Label(root, text="Time: 0.0s", font=("Cambria", 12))
timer_label.pack(pady=4)

#  high score label
highscore_label = tk.Label(root, font=("Cambria", 8))
highscore_label.pack(pady=4)

# status label
status = tk.Label(root, text="", font=("Cambria", 12))
status.pack(pady=8)

fig = Figure(figsize=(9, 6), dpi=100)
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill="both", expand=True)

# -------------------
# Game state
# -------------------

game_running = False
start_time = None
timer_running = False


remaining_states = set(states[NAME_COL].tolist())  # or your own list of 50 states
target_state = None


def redraw():
    ax.clear()
    states.plot(ax=ax, color=states["fill"], edgecolor="tan", linewidth=0.5)
    ax.set_axis_off()
    fig.tight_layout()
    canvas.draw_idle()

def press_start():
    global game_running, start_time, timer_running

    if game_running:
        return

    game_running = True

    # turn into restart button
    action_button.config(text="RESTART", bg="#009714", command=restart_game)

    # start timer
    start_time = time.time()
    timer_running = True
    update_stopwatch()

    # choose first target
    choose_new_target()

def restart_game():
    global game_running, timer_running, start_time, target_state, remaining_states

    # Stop everything
    game_running = False
    timer_running = False
    start_time = None
    target_state = None

    # Reset remaining states
    remaining_states = set(states[NAME_COL].tolist())

    # Reset map colours
    states["fill"] = "tan"
    redraw()

    # Reset UI
    timer_label.config(text="Time: 0.0s")
    status.config(text="")

    # Start fresh immediately
    press_start()

def update_stopwatch():
    if not timer_running:
        return
    elapsed = time.time() - start_time
    timer_label.config(text=f"Time: {elapsed:.1f}s")
    root.after(100, update_stopwatch)  # update every 0.1s


def choose_new_target():
    """Pick a new random target, update the status label."""
    global target_state, game_running, timer_running, best_time

    if not remaining_states:
        game_running = False
        target_state = None
        timer_running = False
        final_time = time.time() - start_time
        status.config(text=f"🎉 Well done! You’ve clicked all the states!", font="Cambria")
        if best_time is None or final_time < best_time:
            best_time = final_time
            save_high_score(best_time)
            update_highscore_label()
            timer_label.config(text=f"Time: {final_time:.1f}s — NEW HIGH SCORE!")
        else:
            timer_label.config(text=f"Time: {final_time:.1f}s")
        return
    
    

    target_state = random.choice(list(remaining_states))
    status.config(text=f"Click on: {target_state}  ({len(remaining_states)} left)")


def state_clicked(x, y):
    """Return the NAME of the state covering the click point, else None."""
    pt = Point(x, y)

    # candidates via spatial index (bounding box filter)
    candidate_idx = list(sindex.intersection(pt.bounds))
    if not candidate_idx:
        return None

    candidates = states.iloc[candidate_idx]

    # covers() handles boundary clicks better than contains()
    hits = candidates[candidates.covers(pt)]
    if hits.empty:
        return None

    return hits.iloc[0][NAME_COL]


def highlight_state_by_name(name, colour="lightgreen"):
    """Colour a state (by NAME) and redraw."""
    mask = states[NAME_COL].str.lower() == name.lower()
    if mask.any():
        states.loc[mask, "fill"] = colour


def on_click(event):
    global target_state

    #do nothing if game not running
    if not game_running:
        return

    # ignore clicks outside axes
    if event.inaxes != ax or event.xdata is None or event.ydata is None:
        return

    if target_state is None:
        return  # game finished / no target

    clicked_name = state_clicked(event.xdata, event.ydata)

    if clicked_name is None:
        status.config(text=f"Missed! You clicked outside. Try again: {target_state}")
        return

    if clicked_name.lower() == target_state.lower():
        # Correct click
        highlight_state_by_name(clicked_name, "lightgreen")
        redraw()

        remaining_states.remove(target_state)
        choose_new_target()
    else:
        # Wrong state clicked
        status.config(text=f"Oops — you clicked {clicked_name}. Try again: {target_state}")

def load_high_score():
    if not os.path.exists(HIGHSCORE_FILE):
        return None  # no high score yet
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("best_time_seconds")
    except (json.JSONDecodeError, OSError):
        return None

def save_high_score(best_time_seconds: float):
    data = {"best_time_seconds": best_time_seconds}
    with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_highscore_label():
    if best_time is None:
        highscore_label.config(text="Best time: —")
    else:
        highscore_label.config(text=f"Best time: {best_time:.1f}s")



# Start game
redraw()
best_time = load_high_score()
update_highscore_label()
canvas.mpl_connect("button_press_event", on_click)

root.mainloop()