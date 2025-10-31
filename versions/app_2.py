import tkinter as tk
from datetime import datetime as now

root = tk.Tk()
root.title("Clouds Messenger")
root.geometry("400x300")

# Chat area (top)
chat_frame = tk.Frame(root)
chat_frame.pack(fill="both", expand=True)

# Input area (bottom)
input_frame = tk.Frame(root)
input_frame.pack(side="bottom", fill="x", pady=6)

entry = tk.Entry(input_frame, font=("Cambria", 14), width=24)
entry.pack(side="left", padx=8, pady=4, expand=True, fill="x")
entry.focus_set()

def message():
    msg = entry.get().strip()
    if not msg:
        return
    time = now.now().strftime("%I:%M %p")
    label = tk.Label(chat_frame, text=f"{time} | {msg}", anchor="w", justify="left")
    label.pack(anchor="w", padx=10, pady=2)
    entry.delete(0, tk.END)
    entry.focus_set()

btn = tk.Button(input_frame, text="Send Message", command=message)
btn.pack(side="left", padx=6, pady=4)

entry.bind("<Return>", lambda event: message())

root.mainloop()
