"""
1. Changed theme
2. Changed text and text box size
3. Made arrow keys scroll
4. Made scroll bar only visible when needed
5. Added splash screen
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime as dt

#--Defaults--
purple = "#c180f0"
pink = "#f2a2e4"
darkgray = "#202020"
dfont = ("Cambria", 15)
tfont = ("Cambria", 13)

#--Functions--

def sendmessage():
    msg = textbox.get().strip()
    if msg:
        now = dt.now().strftime("%I:%M %p").upper()

        msg_frame = tk.Frame(inner_frame, bg=darkgray)
        msg_frame.pack(pady=2, padx=10, fill="x", anchor="e")

        left_blank = tk.Frame(msg_frame, bg=darkgray, width=250)
        left_blank.pack(side="left", fill="y")

        time_label = tk.Label(msg_frame, text=now, font=tfont, fg="#888", bg=darkgray)
        time_label.pack(side="left")

        msg_label = tk.Label(
            msg_frame, text=msg, font=dfont,
            wraplength=1000, justify="left", anchor="w",
            fg=pink, bg=darkgray, padx=10, pady=5
        )
        msg_label.pack(side="left", padx=5)

        textbox.delete(0, tk.END)
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1.0)
        toggle_scrollbar()

def on_configure(event):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
    toggle_scrollbar()

def splashscreen():
    root.withdraw()
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w // 2) - (512 // 2)
    y = (screen_h // 2) - (512 // 2)
    splash.geometry(f"512x512+{x}+{y}")

    splash_img = tk.PhotoImage(file="splash.png")
    label = tk.Label(splash, image=splash_img, bg=darkgray)
    label.image = splash_img
    label.pack(fill="both", expand=True)
    splash.after(2000, lambda: (splash.destroy(), root.deiconify()))

def toggle_scrollbar():
    canvas_height = chat_canvas.winfo_height()
    inner_height = inner_frame.winfo_height()
    if inner_height > canvas_height:
        if not scrollbar.winfo_ismapped():
            scrollbar.pack(side="right", fill="y")
    else:
        if scrollbar.winfo_ismapped():
            scrollbar.pack_forget()

def _on_mousewheel(event):
    if event.num == 5 or event.delta < 0:
        chat_canvas.yview_scroll(1, "units")
    elif event.num == 4 or event.delta > 0:
        chat_canvas.yview_scroll(-1, "units")

def _bind_mousewheel(widget):
    widget.bind("<Enter>", lambda e: _bind_to_mousewheel())
    widget.bind("<Leave>", lambda e: _unbind_from_mousewheel())

def _bind_to_mousewheel():
    if root.tk.call('tk', 'windowingsystem') == 'aqua':
        chat_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    else:
        chat_canvas.bind_all("<Button-4>", _on_mousewheel)
        chat_canvas.bind_all("<Button-5>", _on_mousewheel)
        chat_canvas.bind_all("<MouseWheel>", _on_mousewheel)

def _unbind_from_mousewheel():
    if root.tk.call('tk', 'windowingsystem') == 'aqua':
        chat_canvas.unbind_all("<MouseWheel>")
    else:
        chat_canvas.unbind_all("<Button-4>")
        chat_canvas.unbind_all("<Button-5>")
        chat_canvas.unbind_all("<MouseWheel>")

#--Main Window--
root = tk.Tk()
root.title("Clouds")
root.geometry("800x600")
root.configure(bg=darkgray)
root.attributes("-zoomed", True)

# Modern Scrollbar
style = ttk.Style(root)
style.theme_use("clam")
style.configure("NoArrows.Vertical.TScrollbar",
                troughcolor=darkgray,
                background=purple,
                bordercolor=darkgray,
                lightcolor=darkgray,
                darkcolor=purple,
                arrowsize=0)


splashscreen()

chat_frame = tk.Frame(root, bg=darkgray)
chat_frame.pack(fill="both", expand=True)

chat_canvas = tk.Canvas(chat_frame, highlightthickness=0, bg=darkgray)
scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=chat_canvas.yview, style="NoArrows.Vertical.TScrollbar")
chat_canvas.configure(yscrollcommand=scrollbar.set)

chat_canvas.pack(side="left", fill="both", expand=True)

# -- Inner Frame --
inner_frame = tk.Frame(chat_canvas, bg=darkgray)
window_id = chat_canvas.create_window((0, 0), window=inner_frame, anchor="nw")

def _resize_inner(event):
    chat_canvas.itemconfig(window_id, width=event.width)

chat_canvas.bind("<Configure>", _resize_inner)
inner_frame.bind("<Configure>", on_configure)

input_frame = tk.Frame(root, bg=darkgray)
input_frame.pack(side="bottom", fill="x")

right_frame = tk.Frame(input_frame, bg=darkgray)
right_frame.pack(anchor="e")

textbox = tk.Entry(right_frame, font=dfont, width=100, bd=0, fg="#E0E0E0", bg=darkgray, insertbackground=pink)
textbox.grid(row=0, column=0, padx=5, ipady=3)
textbox.bind("<Return>", lambda event: sendmessage())
textbox.focus_set()

sendbtn = tk.Button(
    right_frame, text=">", font=dfont, fg=purple, bg=darkgray,
    activebackground=darkgray, activeforeground=purple,
    relief="flat", bd=0, highlightthickness=0, highlightbackground=darkgray,
    command=sendmessage
)
sendbtn.grid(row=0, column=1, padx=5)

_bind_mousewheel(chat_canvas)

# -- Scroll with Arrow Keys --
def on_key_press(event):
    if event.keysym == "Down":
        chat_canvas.yview_scroll(1, "units")
    elif event.keysym == "Up":
        chat_canvas.yview_scroll(-1, "units")
    elif event.keysym == "Next":
        chat_canvas.yview_scroll(1, "pages")
    elif event.keysym == "Prior":
        chat_canvas.yview_scroll(-1, "pages")

root.bind_all("<Down>", on_key_press)
root.bind_all("<Up>", on_key_press)
root.bind_all("<Next>", on_key_press)
root.bind_all("<Prior>", on_key_press)

root.mainloop()
