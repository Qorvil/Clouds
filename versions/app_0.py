import tkinter as tk
from datetime import datetime as now

root = tk.Tk()
root.title("Button")
root.geometry("400x300")

entry = tk.Entry(root, font=("Cambria", 14), width = 20)

def message():
    msg = entry.get().strip()
    if msg:
        time = now.now().strftime("%I:%M  %p")
        label = tk.Label(root, text=f"{time} | {msg}")
        label.pack(anchor="w")

btn = tk.Button(root, text = "Send Message", command=message)

entry.pack(anchor="w")
btn.pack(anchor="w")

root.mainloop()
