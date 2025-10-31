import tkinter as tk #FUCKING GUI
from datetime import datetime as dt
import time

#--Additional Defaults--
purple="#c180f0"
pink ="#f2a2e4"
darkgray = "#202020"
dfont = ("Cambria", 13)
tfont = ("Cambria", 11)

#--Functions--
def sendmessage():
    msg = textbox.get().strip()
    if msg:
        now = dt.now().strftime("%I:%M %P").upper()

        msg_frame = tk.Frame(chat_frame)
        msg_frame.pack(pady=2, padx=10, fill="x")


        msg_frame.columnconfigure(0, weight=1)
        msg_frame.columnconfigure(1, weight=0)

        time_label = tk.Label(msg_frame, text=now, font=tfont, anchor="e", width=8, fg="gray")
        time_label.grid(row=0, column=1, sticky="e")

        msg_label = tk.Label(msg_frame, text=msg, font=dfont, wraplength=400, justify="right", anchor="e")
        msg_label.grid(row=0, column=0, sticky="ew", padx=(0, 5))


        textbox.delete(0, tk.END)

#--Main Window--
root = tk.Tk()
root.title("Clouds")
root.geometry("800x600")

#--Frame for Chat Window--
chat_frame = tk.Frame(root)
chat_frame.pack(fill="both", expand=True)

#--Frame for Text Box and Send Button--
input_frame = tk.Frame(root)
input_frame.pack(side="bottom",fill="x")

#--Centering Container--
right_frame = tk.Frame(input_frame)
right_frame.pack(anchor="e")

#--Text Box--
textbox = tk.Entry(right_frame, font=dfont, width=40, bd=0)
textbox.grid(row=0, column=0, padx=5)
textbox.bind("<Return>", lambda event: sendmessage())
textbox.focus_set()

#--Send Button--
sendbtn = tk.Button(right_frame, text=">", font=dfont, bd=0, command=sendmessage)
sendbtn.grid(row=0, column=1, padx=5)

root.mainloop()
