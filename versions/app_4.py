"""
1. Changed Alignment
2. Added space for contacts tab
"""

import tkinter as tk
from datetime import datetime as dt

#--Defaults--
purple = "#c180f0"
pink = "#f2a2e4"
darkgray = "#202020"
dfont = ("Cambria", 13)
tfont = ("Cambria", 11)

#--Functions--

#Show message on screen locally
def sendmessage():
    msg = textbox.get().strip()
    if msg:
        now = dt.now().strftime("%I:%M %p").upper()

        # Create a frame for each message
        msg_frame = tk.Frame(inner_frame)
        msg_frame.pack(pady=2, padx=10, fill="x", anchor="e")

        # Left blank frame
        left_blank = tk.Frame(msg_frame, width=250)
        left_blank.pack(side="left", fill="y")

        # Time label
        time_label = tk.Label(msg_frame, text=now, font=tfont, fg=darkgray)
        time_label.pack(side="left")

        # Message text
        msg_label = tk.Label(
            msg_frame, text=msg, font=dfont,
            wraplength=400, justify="right", anchor="e"
        )
        msg_label.pack(side="left", padx=5)

        textbox.delete(0, tk.END)

        # Update scroll region
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1.0)

# Update scroll region dynamically
def on_configure(event):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))

#--Main Window--
root = tk.Tk()
root.title("Clouds")
root.geometry("800x600")
root.attributes("-zoomed", True)

#--Scrollable Chat Area--
chat_frame = tk.Frame(root)
chat_frame.pack(fill="both", expand=True)

# Canvas + Scrollbar
chat_canvas = tk.Canvas(chat_frame, highlightthickness=0)
scrollbar = tk.Scrollbar(chat_frame, orient="vertical", command=chat_canvas.yview)
chat_canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
chat_canvas.pack(side="left", fill="both", expand=True)

# Inner frame inside canvas
inner_frame = tk.Frame(chat_canvas)
chat_canvas.create_window((0, 0), window=inner_frame, anchor="nw")

inner_frame.bind("<Configure>", on_configure)

#--Input Frame--
input_frame = tk.Frame(root)
input_frame.pack(side="bottom", fill="x")

right_frame = tk.Frame(input_frame)
right_frame.pack(anchor="e")

textbox = tk.Entry(right_frame, font=dfont, width=40, bd=0)
textbox.grid(row=0, column=0, padx=5)
textbox.bind("<Return>", lambda event: sendmessage())
textbox.focus_set()

sendbtn = tk.Button(right_frame, text=">", font=dfont, bd=0, command=sendmessage)
sendbtn.grid(row=0, column=1, padx=5)

root.mainloop()
