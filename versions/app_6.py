"""
1. Added animated splash
2. Made text box and send button rounded
3. Changed the color scheme sligtly
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime as dt
from PIL import Image, ImageTk, ImageSequence

#--Defaults--
purple = "#c180f0"
pink = "#f2a2e4"
darkgray = "#1A1A1E"
dfont = ("Cambria", 16)
tfont = ("Cambria", 13)

#--Main Window--
root = tk.Tk()
root.title("Clouds")
root.geometry("1280x800")
root.configure(bg=darkgray)
root.attributes("-zoomed", True)

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
    splash.configure(bg=darkgray)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    gif_path = "SplashAnimated.gif"
    target_w, target_h = 512, 512

    try:
        pil_img = Image.open(gif_path)
    except Exception:
        # Fallback centered blank 512x512
        x = (screen_w // 2) - (target_w // 2)
        y = (screen_h // 2) - (target_h // 2)
        splash.geometry(f"{target_w}x{target_h}+{x}+{y}")
        label = tk.Label(splash, bg=darkgray)
        label.pack(fill="both", expand=True)
        splash.after(2000, lambda: (splash.destroy(), root.deiconify()))
        return

    # Extract frames and durations, scale to 512x512
    frames = []
    durations = []
    for frame in ImageSequence.Iterator(pil_img):
        f = frame.convert("RGBA").resize((target_w, target_h), Image.LANCZOS)
        frames.append(ImageTk.PhotoImage(f))
        durations.append(frame.info.get("duration", 100))  # ms

    # center window at 512x512
    x = (screen_w // 2) - (target_w // 2)
    y = (screen_h // 2) - (target_h // 2)
    splash.geometry(f"{target_w}x{target_h}+{x}+{y}")

    label = tk.Label(splash, bg=darkgray)
    label.place(relx=0.5, rely=0.5, anchor="center", width=target_w, height=target_h)

    start_ms = int(dt.now().timestamp() * 1000)
    total_duration = 2000

    def animate(i=0):
        label.config(image=frames[i])
        label.image = frames[i]
        elapsed = int(dt.now().timestamp() * 1000) - start_ms
        if elapsed >= total_duration:
            splash.destroy()
            root.deiconify()
            return
        delay = durations[i] if durations[i] > 0 else 100
        remaining = total_duration - elapsed
        splash.after(min(delay, remaining), lambda: animate((i + 1) % len(frames)))

    animate()

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

# Rounded entry using Canvas with no visible border (pure rounded corners)
entry_w = 1020
entry_h = 54
corner = 18
rbg = "#222327"

rounded_canvas = tk.Canvas(right_frame, width=entry_w, height=entry_h, bg=darkgray, highlightthickness=0)
rounded_canvas.grid(row=0, column=0, padx=5, pady=8)

def _round_rect(c, x1, y1, x2, y2, r, **kwargs):
    c.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style="pieslice", outline="", fill=kwargs.get("fill"))
    c.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style="pieslice", outline="", fill=kwargs.get("fill"))
    c.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="pieslice", outline="", fill=kwargs.get("fill"))
    c.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="pieslice", outline="", fill=kwargs.get("fill"))
    c.create_rectangle(x1+r, y1, x2-r, y2, outline="", fill=kwargs.get("fill"))
    c.create_rectangle(x1, y1+r, x2, y2-r, outline="", fill=kwargs.get("fill"))

_round_rect(rounded_canvas, 0, 0, entry_w, entry_h, corner, fill=rbg)

textbox = tk.Entry(right_frame, font=dfont, bd=0, fg="#E0E0E0", bg=rbg, insertbackground=pink, relief="flat", highlightthickness=0)
textbox.place(in_=rounded_canvas, x=16, y=8, width=entry_w-32, height=entry_h-16)
textbox.bind("<Return>", lambda event: sendmessage())
textbox.focus_set()

# Create rounded send button matching text box color
btn_w = 54
btn_h = 54
btn_corner = 18

send_canvas = tk.Canvas(right_frame, width=btn_w, height=btn_h, bg=darkgray, highlightthickness=0)
send_canvas.grid(row=0, column=1, padx=(6,12), pady=8)

_round_rect(send_canvas, 0, 0, btn_w, btn_h, btn_corner, fill=rbg)

def on_send_click(event=None):
    sendmessage()

send_label = tk.Label(send_canvas, text=">", font=dfont, fg=purple, bg=rbg)
send_label.place(relx=0.5, rely=0.5, anchor="center")
send_canvas.bind("<Button-1>", lambda e: on_send_click())

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
