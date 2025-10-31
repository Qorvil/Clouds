# clouds_chat_custom_scroll.py
"""
1. Optimistic message removal fixed
2. Rounded text box inside canvas
3. Thin pink scrollbar (like original)
4. Fixed sending messages and arrow key scrolling
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime as dt
from PIL import Image, ImageTk, ImageSequence
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import threading

# -- Config: REPLACE these with your values --
FIREBASE_API_KEY = "AIzaSyCp7EQTjE5PIPFqzY-dIwkgTwFUDBWt6mM"
SERVICE_ACCOUNT_PATH = "backend/clouds-service-account.json"
PROJECT_ID = "clouds-188cc"
STORAGE_BUCKET = f"{PROJECT_ID}.appspot.com"
CHANNEL_ID = "general"
# ------------------------------------------------

# -- Defaults --
purple = "#c180f0"
pink = "#f2a2e4"
darkgray = "#1A1A1E"
dfont = ("Cambria", 16)
tfont = ("Cambria", 13)

app_state = {}
optimistic_frames = {}

# Initialize Firebase Admin
def init_firebase_admin():
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'storageBucket': STORAGE_BUCKET})
        print("firebase-admin initialized")
    except Exception as e:
        print("firebase-admin init error:", e)

threading.Thread(target=init_firebase_admin, daemon=True).start()

# Tkinter root
root = tk.Tk()
root.title("Clouds")
root.geometry("1280x800")
root.configure(bg=darkgray)
try:
    root.attributes("-zoomed", True)
except Exception:
    pass

# Firebase Auth
def signup_email_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

def signin_email_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

def prompt_auth():
    choice = messagebox.askquestion("Sign in", "Do you have an account?")
    if choice == "yes":
        email = simpledialog.askstring("Sign in", "Email:")
        pwd = simpledialog.askstring("Sign in", "Password:", show="*")
        if not email or not pwd: return prompt_auth()
        res = signin_email_password(email, pwd)
        if "idToken" in res:
            app_state['idToken'] = res['idToken']
            app_state['uid'] = res['localId']
            app_state['email'] = email
            messagebox.showinfo("Signed in", f"Signed in as {email}")
        else:
            messagebox.showerror("Sign-in error", res.get("error", {}).get("message", str(res)))
            return prompt_auth()
    else:
        email = simpledialog.askstring("Sign up", "Email:")
        pwd = simpledialog.askstring("Sign up", "Password:", show="*")
        if not email or not pwd: return prompt_auth()
        res = signup_email_password(email, pwd)
        if "idToken" in res:
            app_state['idToken'] = res['idToken']
            app_state['uid'] = res['localId']
            app_state['email'] = email
            messagebox.showinfo("Signed up", f"Account created: {email}")
        else:
            messagebox.showerror("Sign-up error", res.get("error", {}).get("message", str(res)))
            return prompt_auth()

# Firestore client
db = None
def init_db_client():
    global db
    try:
        db = firestore.client()
        print("Firestore client ready")
    except Exception as e:
        print("Firestore init error:", e)
threading.Thread(target=init_db_client, daemon=True).start()

# --- Message Rendering ---
def render_message_widget(data, color=pink, tempId=None):
    now = dt.utcnow().strftime("%I:%M %p").upper()
    mf = tk.Frame(inner_frame, bg=darkgray)
    mf.pack(pady=2, padx=10, fill="x", anchor="e")
    left_blank = tk.Frame(mf, bg=darkgray, width=250)
    left_blank.pack(side="left", fill="y")
    time_label = tk.Label(mf, text=now if not data.get('createdAt') else now,
                          font=tfont, fg="#888", bg=darkgray)
    time_label.pack(side="left")
    msg_label = tk.Label(mf, text=data.get('text',''), font=dfont,
                         wraplength=1000, justify="left", anchor="w",
                         fg=color, bg=darkgray, padx=10, pady=5)
    msg_label.pack(side="left", padx=5)
    if tempId:
        mf.tempId = tempId
    return mf

rendered_message_ids = set()

# --- Send message ---
def sendmessage(event=None):
    if not app_state.get('idToken'):
        messagebox.showwarning("Not signed in", "Please sign in first.")
        prompt_auth()
        return

    msg = textbox.get().strip()
    if not msg:
        return

    decoded = {'uid': app_state.get('uid')}
    if not decoded:
        messagebox.showerror("Auth error", "Session expired. Please sign in again.")
        app_state.clear()
        prompt_auth()
        return

    temp_id = f"temp-{dt.now().timestamp()}"
    frame = render_message_widget({'text': msg, 'userId': decoded['uid']}, color="#888", tempId=temp_id)
    optimistic_frames[temp_id] = frame

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)
    textbox.delete(0, tk.END)

    # Push to Firestore
    def push_to_firestore():
        try:
            doc_ref = db.collection('channels').document(CHANNEL_ID).collection('messages').document()
            doc = {
                'messageId': doc_ref.id,
                'tempId': temp_id,
                'userId': decoded['uid'],
                'text': msg,
                'createdAt': firestore.SERVER_TIMESTAMP
            }
            doc_ref.set(doc)
        except Exception as e:
            print("Send error:", e)
            if temp_id in optimistic_frames:
                optimistic_frames[temp_id].destroy()
                del optimistic_frames[temp_id]

    threading.Thread(target=push_to_firestore, daemon=True).start()

# --- Splashscreen ---
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
        splash.destroy()
        root.deiconify()
        root.after(100, prompt_auth)
        return
    frames = []
    durations = []
    for frame in ImageSequence.Iterator(pil_img):
        f = frame.convert("RGBA").resize((target_w, target_h), Image.LANCZOS)
        frames.append(ImageTk.PhotoImage(f))
        durations.append(frame.info.get("duration", 100))
    x = (screen_w // 2) - (target_w // 2)
    y = (screen_h // 2) - (target_h // 2)
    splash.geometry(f"{target_w}x{target_h}+{x}+{y}")
    label = tk.Label(splash, bg=darkgray)
    label.place(relx=0.5, rely=0.5, anchor="center", width=target_w, height=target_h)
    start_ms = int(dt.now().timestamp() * 1000)
    total_duration = 1200
    def animate(i=0):
        label.config(image=frames[i])
        label.image = frames[i]
        elapsed = int(dt.now().timestamp() * 1000) - start_ms
        if elapsed >= total_duration:
            splash.destroy()
            root.deiconify()
            root.after(100, prompt_auth)
            return
        delay = durations[i] if durations[i] > 0 else 100
        remaining = total_duration - elapsed
        splash.after(min(delay, remaining), lambda: animate((i + 1) % len(frames)))
    animate()

splashscreen()

# --- Chat UI & Scrollbar ---
chat_frame = tk.Frame(root, bg=darkgray)
chat_frame.pack(fill="both", expand=True)

chat_canvas = tk.Canvas(chat_frame, highlightthickness=0, bg=darkgray)
chat_canvas.pack(side="left", fill="both", expand=True)

# Thin pink scrollbar like original
style = ttk.Style(root)
style.theme_use("clam")
style.configure("NoArrows.Vertical.TScrollbar",
                troughcolor=darkgray,
                background=pink,
                bordercolor=darkgray,
                lightcolor=darkgray,
                darkcolor=purple,
                arrowsize=0,
                width=6)

scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=chat_canvas.yview,
                          style="NoArrows.Vertical.TScrollbar")
scrollbar.pack(side="right", fill="y")
chat_canvas.configure(yscrollcommand=scrollbar.set)

inner_frame = tk.Frame(chat_canvas, bg=darkgray)
window_id = chat_canvas.create_window((0,0), window=inner_frame, anchor="nw")

def _resize_inner(event):
    chat_canvas.itemconfig(window_id, width=event.width)
chat_canvas.bind("<Configure>", _resize_inner)

def toggle_scrollbar():
    if inner_frame.winfo_height() > chat_canvas.winfo_height():
        if not scrollbar.winfo_ismapped():
            scrollbar.pack(side="right", fill="y")
    else:
        scrollbar.pack_forget()

def on_configure(event=None):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
    toggle_scrollbar()
inner_frame.bind("<Configure>", on_configure)

# Arrow key scrolling
def on_key_press(event):
    if event.keysym in ("Down", "Up", "Next", "Prior"):
        delta = {"Down":1, "Up":-1, "Next":10, "Prior":-10}[event.keysym]
        chat_canvas.yview_scroll(delta, "units")
root.bind_all("<Down>", on_key_press)
root.bind_all("<Up>", on_key_press)
root.bind_all("<Next>", on_key_press)
root.bind_all("<Prior>", on_key_press)

# --- Input UI ---
input_frame = tk.Frame(root, bg=darkgray)
input_frame.pack(side="bottom", fill="x")
right_frame = tk.Frame(input_frame, bg=darkgray)
right_frame.pack(anchor="e")

# Rounded text box
entry_w, entry_h, corner, rbg = 1020, 54, 18, "#222327"
rounded_canvas = tk.Canvas(right_frame, width=entry_w, height=entry_h, bg=darkgray, highlightthickness=0)
rounded_canvas.grid(row=0, column=0, padx=5, pady=8)

def _round_rect(c, x1, y1, x2, y2, r, **kwargs):
    c.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style="pieslice",
                 outline="", fill=kwargs.get("fill"))
    c.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style="pieslice",
                 outline="", fill=kwargs.get("fill"))
    c.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="pieslice",
                 outline="", fill=kwargs.get("fill"))
    c.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="pieslice",
                 outline="", fill=kwargs.get("fill"))
    c.create_rectangle(x1+r, y1, x2-r, y2, outline="", fill=kwargs.get("fill"))
    c.create_rectangle(x1, y1+r, x2, y2-r, outline="", fill=kwargs.get("fill"))

_round_rect(rounded_canvas, 0, 0, entry_w, entry_h, corner, fill=rbg)

textbox = tk.Entry(rounded_canvas, font=dfont, bd=0, fg="#E0E0E0",
                   bg=rbg, insertbackground=pink, relief="flat", highlightthickness=0)
textbox.place(x=8, y=8, width=entry_w-16, height=entry_h-16)
textbox.bind("<Return>", sendmessage)

# Send button
btn_w, btn_h, btn_corner = 54, 54, 18
send_canvas = tk.Canvas(right_frame, width=btn_w, height=btn_h, bg=darkgray, highlightthickness=0)
send_canvas.grid(row=0, column=1, padx=(6,12), pady=8)
_round_rect(send_canvas, 0, 0, btn_w, btn_h, btn_corner, fill=rbg)
send_label = tk.Label(send_canvas, text=">", font=dfont, fg=purple, bg=rbg)
send_label.place(relx=0.5, rely=0.5, anchor="center")
send_canvas.bind("<Button-1>", sendmessage)

# Firestore listener
def refresh_messages():
    if db is None: return
    try:
        docs = db.collection('channels').document(CHANNEL_ID).collection('messages').order_by('createdAt').stream()
        for d in docs:
            data = d.to_dict()
            if data['messageId'] not in rendered_message_ids:
                for temp_id, frame in list(optimistic_frames.items()):
                    if getattr(frame, "tempId", None) == data.get("tempId"):
                        frame.destroy()
                        del optimistic_frames[temp_id]
                        break
                render_message_widget(data)
                rendered_message_ids.add(data['messageId'])
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1.0)
    except Exception as e:
        print("refresh_messages error:", e)

def attach_listener():
    if db is None: return
    query = db.collection('channels').document(CHANNEL_ID).collection('messages').order_by('createdAt')
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                data = change.document.to_dict()
                if data['messageId'] not in rendered_message_ids:
                    for temp_id, frame in list(optimistic_frames.items()):
                        if getattr(frame, "tempId", None) == data.get("tempId"):
                            frame.destroy()
                            del optimistic_frames[temp_id]
                            break
                    render_message_widget(data)
                    rendered_message_ids.add(data['messageId'])
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1.0)
    query.on_snapshot(on_snapshot)

root.after(2000, attach_listener)
root.after(2500, refresh_messages)
root.mainloop()
