import tkinter as tk
from datetime import datetime as now

root = tk.Tk()  # window
root.title("Gui Test")
root.geometry("400x300")  # dimensions

# Message display area
chat_frame = tk.Frame(root)
chat_frame.pack(fill="both", expand=True)

# Input area
input_frame = tk.Frame(root)
input_frame.pack(side="bottom", fill="x", pady=6)

entry = tk.Entry(input_frame, font=("Cambria", 14), width=20)  # text box for messages
entry.pack(side="left", padx=5)  # this is where 'side' belongs

def message():
    msg = entry.get().strip()
    if msg:
        time = now.now().strftime("%I:%M %p")  # 12-hour format
        label = tk.Label(chat_frame, text=f"{time} | {msg}")
        label.pack(anchor="w", pady=2)
        entry.delete(0, tk.END)

btn = tk.Button(input_frame, text="Send Message", command=message)
btn.pack(side="left", padx=5)

root.mainloop()
