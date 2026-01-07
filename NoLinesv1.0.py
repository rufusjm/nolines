import tkinter as tk
import random

import geopandas as gpd
from shapely.geometry import Point

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from shapely.geometry import box

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
root.geometry("1800x650")

# set up exit button
button = tk.Button(root, text="EXIT", font=("Cambria", 10, "bold" ), bg="#CF3333", fg="#FFFFFF")
button.pack(anchor="w")
button.config(command=root.destroy)

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

status = tk.Label(root, text="", font=("Arial", 12))
status.pack(pady=8)

fig = Figure(figsize=(9, 6), dpi=100)
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill="both", expand=True)

# -------------------
# Game state
# -------------------
remaining_states = set(states[NAME_COL].tolist())  # or your own list of 50 states
target_state = None


def redraw():
    ax.clear()
    states.plot(ax=ax, color=states["fill"], edgecolor="tan", linewidth=0.5)
    ax.set_axis_off()
    fig.tight_layout()
    canvas.draw_idle()


def choose_new_target():
    """Pick a new random target, update the status label."""
    global target_state

    if not remaining_states:
        target_state = None
        status.config(text="🎉 Well done! You’ve clicked all the states!")
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


# Start game
redraw()
choose_new_target()
canvas.mpl_connect("button_press_event", on_click)

root.mainloop()