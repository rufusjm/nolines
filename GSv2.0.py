import tkinter as tk

us_states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
             "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
             "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
             "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
             "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
             "Wisconsin", "Wyoming"]

#set up window
window = tk.Tk()
window.geometry("500x300")
window.title("Guess States v2.0")
label = tk.Label(window, text="guess states?", font=("Cambria", 25, "bold"))
label.pack(pady=20)

label2 = tk.Label(window, text="Welcome to the US States Guessing Game!", font=("Cambria", 10))
label2.pack()

label3 = tk.Label(window, text="Guess a US state: ", font=("Cambria", 10))
label3.pack()


# work with user input
def show_text(event=None):  
    answer = myEntry.get()
    myEntry.delete(0, tk.END)
    if answer.title() in us_states:
        us_states.remove(answer.title())
        if len(us_states) == 0:
            label2.destroy()
            label3.destroy()
            myEntry.destroy()
            label4.config(text="Congratulations! You've guessed all the states!")
        else:
            label4.config(text="Correct! Remaining states to guess: {}".format(len(us_states)))
    else:
        label4.config(text="Incorrect or already guessed. Try again.")


# set up entry box
myEntry = tk.Entry(window, font=("Cambria", 10))
myEntry.pack(pady=10)

# trigger function when Enter key is pressed
myEntry.bind("<Return>", show_text) 

# set up output label
label4 = tk.Label(window, text="", font=("Cambria", 10))
label4.pack(pady=10)

# set up exit button
button = tk.Button(window, text="EXIT", font=("Cambria", 10))
button.pack(pady=5)
button.config(command=window.destroy)

window.mainloop()

