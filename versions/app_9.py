# app.py
# Full updated Clouds chat app with:
# - "Uploading <file name>..." optimistic status
# - 10 MB per-file size limit enforced

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime as dt
from PIL import Image, ImageTk, ImageSequence
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import threading
import dropbox
import hashlib  # for custom colors lol

# -- Config --
FIREBASE_API_KEY = "AIzaSyCp7EQTjE5PIPFqzY-dIwkgTwFUDBWt6mM"
SERVICE_ACCOUNT_PATH = "backend/clouds-service-account.json"
PROJECT_ID = "clouds-188cc"
STORAGE_BUCKET = f"{PROJECT_ID}.appspot.com"
CHANNEL_ID = "general"
DROPBOX_TOKEN = "sl.u.AGHozdZcOVj381P2D_FuAZ-T_EZFn9XEXmgo0X58ffe89xPgiFkaEe6cTmtNN-Z6EhdwHpbn4JM3tPkbUHjhrPux8iskoLoNiasbA5JKUpwa8jOY-YpDO-6fyIYJC-FJG4ASxG7qsxcFv4NMIixDC9TqujJVS_kHtQJNYaENLjOkU-di5L1y_e_GMGhZKCNmn9MNWFYNz78V_YnqACU4FcSKwrUV404mC2YV5rFVp9_4zqwaqqdh1MnBBn8vKKb0lbBTSnFAMpxjFLLLdUQZOoBvEUsgbQFbZpzDCvdWJJCqokG95qYZnAATD26DAUstMgtQm1WI1g8_1wG1wA8JkQNnv4GP6Q6FMRmPUoG9WAdEMu2DauwH8xnns66AZZeFxhmsDg0TwKc-ad8_7G0H6UL9T0mZryFR8oM7SZC-wPfAJ9QiRn9G1Pa_3J18sGuooLcZDFJ04F23u3YceZF15ZEZ7OvEdCAXU5ycEgky1swmXjov5-PfJMay96WyqzCIU2kURW_9zPaLIXFeUujJ2uvlyXiGCtfMUsz8jfxEXrlXq9h0bqd_s4rS0mcH0LZB7pIz0X1EsrrVyTRkz8dAK7g2yTr3LuEjoeojjfX-NoyJ9IDpEAamN-LbH8reTS-QVytkpRqqZHLL6iFo6pwd9sgPJ5gzq8Sw_2NyXDqKo52WAI7w69k8c_mIM-27T3bGK3KV3XiiWlCC_5OShA0033ww0AMwsg14lqrOseaolk01eXdChsqx-PStWO7H8p1tGGGc0comBFEb1BxT_AVBYjpj3PlF9opYDaSH-ziTaG6QfsBi-_WP_Kth12lbv3RusBFHYRogEyfNe2H4vfY1JrQWht8RVF5LBHybI_8s2AD-X0NEfm5XLkWRtyO8q4ZGE9I4aboukhjF4lvCTMejN7GETjCc2dFb1eiLYN2tHa-8JsXaoNluNQv7L3VS2QBFkeYmv9WIT0dMHTMxHhFH6I7kLx0zU2IDYQs_9KdwnTyHpW6PK7hTIKk1w9GDGmaMSbLVs2yUUGVMYzb9OqPtSrHw8NsMKI8ZrWl1BGLcoynzBJKgom-wso5bNVHDT84u54yyhAJb73-YV5wdsBzXbD4uqxb9SNxrt7CWaMlyPJrvZLTEHb21n6kFnZnQmNq9DFDU4K4Ax57VIlsLRUAHH67slVu7PRRgGz_pww0nV6bn7z8GNRo5_sHH9h8qIWR6HE5QJB2vQcJ6QwpjLv7d_pqUq8SeaLGElmch0zf6O9ji3wN7z3HK6gzZiVQUd66Xwx8oXlUW53HY5_Qfo9oV0GgEukYydzEP7PnW-erDTXttypyyTO-fJBqQdzSJH9Yt1tmvC0brqghoyYbEWZ_1riX7OAYUCQN279KOTKxMbNa4TArNDf5GjWkgQLb0snM_NeWgmLR_vapAiQO30l33cCZsku6SyVKGDRINaePty0NmSw"


# --- DEFAULTS ---
purple = "#c180f0"
pink = "#f2a2e4"
darkgray = "#1A1A1E"
dfont = ("Cambria", 16)
tfont = ("Cambria", 13)

# Expanded palette
USER_COLORS = [
    "#FFD700", "#F2A2E4", "#FFFFFF", "#00FF00", "#FF4D4D", "#87CEFA",
    "#FFA500", "#ADFF2F", "#40E0D0", "#FF69B4", "#8A2BE2", "#00CED1"
]

def get_color_for_username(username: str) -> str:
    """Return consistent color per username."""
    if not username:
        return "#CCCCCC"
    h = int(hashlib.sha256(username.encode()).hexdigest(), 16)
    return USER_COLORS[h % len(USER_COLORS)]

# --- ---

app_state = {}
optimistic_frames = {}
rendered_message_ids = set()

# --- Firebase ---
def init_firebase_admin():
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'storageBucket': STORAGE_BUCKET})
        print("firebase-admin initialized")
    except Exception as e:
        print("firebase-admin init error:", e)
threading.Thread(target=init_firebase_admin, daemon=True).start()

def signup_email_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

def signin_email_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

# --- Tkinter root ---
root = tk.Tk()
root.title("Clouds")
root.geometry("1280x800")
root.configure(bg=darkgray)
try: root.attributes("-zoomed", True)
except: pass
root.withdraw()

# --- Splashscreen ---
def splashscreen(callback_after_splash=None):
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg=darkgray)
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    gif_path = "SplashAnimated.gif"
    target_w, target_h = 512, 512
    try: pil_img = Image.open(gif_path)
    except Exception:
        splash.destroy()
        if callback_after_splash: callback_after_splash()
        return
    frames = []
    durations = []
    for frame in ImageSequence.Iterator(pil_img):
        f = frame.convert("RGBA").resize((target_w, target_h), Image.LANCZOS)
        frames.append(ImageTk.PhotoImage(f))
        durations.append(frame.info.get("duration", 100))
    x = (screen_w//2)-(target_w//2)
    y = (screen_h//2)-(target_h//2)
    splash.geometry(f"{target_w}x{target_h}+{x}+{y}")
    label = tk.Label(splash, bg=darkgray)
    label.place(relx=0.5, rely=0.5, anchor="center", width=target_w, height=target_h)
    start_ms = int(dt.now().timestamp()*1000)
    total_duration = 1200
    def animate(i=0):
        label.config(image=frames[i])
        label.image = frames[i]
        elapsed = int(dt.now().timestamp()*1000)-start_ms
        if elapsed>=total_duration:
            splash.destroy()
            if callback_after_splash: callback_after_splash()
            return
        delay = durations[i] if durations[i]>0 else 100
        remaining = total_duration - elapsed
        splash.after(min(delay, remaining), lambda: animate((i+1)%len(frames)))
    animate()

# --- Auth ---

def prompt_auth():
    auth_win = tk.Toplevel(root)
    auth_win.title("Accounts")
    auth_win.geometry("400x520")  # taller window
    auth_win.configure(bg=darkgray)
    auth_win.resizable(False, False)
    auth_win.grab_set()

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

    tk.Label(auth_win, text="Sign in / Sign up", font=dfont, fg=pink, bg=darkgray).pack(pady=15)
    entry_bg = "#222327"
    entry_w, entry_h, corner = int(340*1.02), int(220*1.02), 20
    canvas = tk.Canvas(auth_win, width=entry_w, height=entry_h, bg=darkgray, highlightthickness=0)
    canvas.pack(pady=10)
    _round_rect(canvas, 0,0,entry_w,entry_h,corner, fill=entry_bg)

    # Username
    tk.Label(canvas, text="Username:", bg=entry_bg, fg="#E0E0E0", font=tfont).place(x=10, y=10)
    username_entry = tk.Entry(canvas, bg=entry_bg, fg="#E0E0E0", bd=0, insertbackground=pink, font=tfont)
    username_entry.place(x=10, y=35, width=entry_w-20, height=30)

    # Email
    tk.Label(canvas, text="Email:", bg=entry_bg, fg="#E0E0E0", font=tfont).place(x=10, y=85)
    email_entry = tk.Entry(canvas, bg=entry_bg, fg="#E0E0E0", bd=0, insertbackground=pink, font=tfont)
    email_entry.place(x=10, y=110, width=entry_w-20, height=30)

    # Password
    tk.Label(canvas, text="Password:", bg=entry_bg, fg="#E0E0E0", font=tfont).place(x=10, y=160)
    pwd_entry = tk.Entry(canvas, bg=entry_bg, fg="#E0E0E0", bd=0, insertbackground=pink, font=tfont, show="*")
    pwd_entry.place(x=10, y=185, width=entry_w-20, height=30)

    error_label = tk.Label(auth_win, text="", fg="red", bg=darkgray, font=tfont)
    error_label.pack(pady=5)
    btn_frame = tk.Frame(auth_win, bg=darkgray)
    btn_frame.pack(pady=15)

    btn_w, btn_h, btn_corner = 120, 45, 15
    def format_error_code(code:str)->str:
        return code.replace("_"," ").capitalize()

    def do_signin():
        username=username_entry.get().strip()
        email=email_entry.get().strip()
        pwd=pwd_entry.get().strip()
        if not username or not email or not pwd: return
        res=signin_email_password(email,pwd)
        if "idToken" in res:
            app_state['idToken']=res['idToken']
            app_state['uid']=res['localId']
            app_state['email']=email
            app_state['username']=username
            auth_win.destroy()
            root.deiconify()
        else:
            raw_code=res.get("error",{}).get("message",str(res))
            error_label.config(text=format_error_code(raw_code))

    def do_signup():
        username=username_entry.get().strip()
        email=email_entry.get().strip()
        pwd=pwd_entry.get().strip()
        if not username or not email or not pwd: return

        # Check username uniqueness
        users_ref = db.collection('users')
        existing = users_ref.where('username', '==', username).get()
        if existing:
            error_label.config(text="Username already taken")
            return

        res=signup_email_password(email,pwd)
        if "idToken" in res:
            app_state['idToken']=res['idToken']
            app_state['uid']=res['localId']
            app_state['email']=email
            app_state['username']=username

            # Save username tied to UID
            users_ref.document(app_state['uid']).set({'username': username, 'email': email})

            auth_win.destroy()
            root.deiconify()
        else:
            raw_code=res.get("error",{}).get("message",str(res))
            error_label.config(text=format_error_code(raw_code))

    # Sign in button
    signin_canvas = tk.Canvas(btn_frame,width=btn_w,height=btn_h,bg=darkgray,highlightthickness=0)
    signin_canvas.pack(side="left",padx=15)
    _round_rect(signin_canvas,0,0,btn_w,btn_h,btn_corner,fill=purple)
    signin_label = tk.Label(signin_canvas,text="Sign in",fg="white",bg=purple,font=tfont)
    signin_label.place(relx=0.5,rely=0.5,anchor="center")
    signin_canvas.bind("<Button-1>",lambda e: do_signin()); signin_label.bind("<Button-1>",lambda e: do_signin())

    # Sign up button
    signup_canvas = tk.Canvas(btn_frame,width=btn_w,height=btn_h,bg=darkgray,highlightthickness=0)
    signup_canvas.pack(side="left",padx=15)
    _round_rect(signup_canvas,0,0,btn_w,btn_h,btn_corner,fill=pink)
    signup_label = tk.Label(signup_canvas,text="Sign up",fg="white",bg=pink,font=tfont)
    signup_label.place(relx=0.5,rely=0.5,anchor="center")
    signup_canvas.bind("<Button-1>",lambda e: do_signup()); signup_label.bind("<Button-1>",lambda e: do_signup())


splashscreen(callback_after_splash=prompt_auth)

# --- Firestore ---
db=None
def init_db_client():
    global db
    try: db=firestore.client(); print("Firestore client ready")
    except Exception as e: print("Firestore init error:", e)
threading.Thread(target=init_db_client, daemon=True).start()


# --- UID > username cache ---
uid_username_map = {}  # global cache

# --- Attach button ---
uid_username_map = {}  # cache UID -> username

def get_username_from_uid(uid):
    if uid in uid_username_map:
        return uid_username_map[uid]
    try:
        doc = db.collection('users').document(uid).get()
        if doc.exists:
            username = doc.to_dict().get('username', uid)
            uid_username_map[uid] = username
            return username
    except:
        pass
    return uid  # fallback UID if username unknown



# --- Left Sidebar (User List) ---
sidebar_width = 300
sidebar_frame = tk.Frame(root, bg="#111", width=sidebar_width)
sidebar_frame.pack(side="left", fill="y")

# User list canvas & scrollbar
sidebar_canvas = tk.Canvas(sidebar_frame, bg="#111", highlightthickness=0)
sidebar_scrollbar = ttk.Scrollbar(sidebar_frame, orient="vertical", command=sidebar_canvas.yview)
sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
sidebar_scrollbar.pack(side="right", fill="y")
sidebar_canvas.pack(side="left", fill="both", expand=True)

sidebar_inner = tk.Frame(sidebar_canvas, bg="#111")
window_id_sb = sidebar_canvas.create_window((0,0), window=sidebar_inner, anchor="nw")

def _resize_sidebar(event):
    sidebar_canvas.itemconfig(window_id_sb, width=event.width)
sidebar_canvas.bind("<Configure>", _resize_sidebar)
def _on_configure_sidebar(event):
    sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
sidebar_inner.bind("<Configure>", _on_configure_sidebar)

# --- Dropbox ---
dbx=dropbox.Dropbox(DROPBOX_TOKEN)

# --- Chat UI ---
chat_frame=tk.Frame(root,bg=darkgray); chat_frame.pack(fill="both",expand=True)
chat_canvas=tk.Canvas(chat_frame,highlightthickness=0,bg=darkgray); chat_canvas.pack(side="left",fill="both",expand=True)
style=ttk.Style(root); style.theme_use("clam")
style.configure("NoArrows.Vertical.TScrollbar", troughcolor=darkgray, background=pink, bordercolor=darkgray,
                lightcolor=darkgray, darkcolor=purple, arrowsize=0, width=6)
scrollbar=ttk.Scrollbar(chat_frame,orient="vertical",command=chat_canvas.yview,style="NoArrows.Vertical.TScrollbar")
scrollbar.pack(side="right",fill="y")
chat_canvas.configure(yscrollcommand=scrollbar.set)
inner_frame=tk.Frame(chat_canvas,bg=darkgray)
window_id=chat_canvas.create_window((0,0),window=inner_frame,anchor="nw")
def _resize_inner(event): chat_canvas.itemconfig(window_id,width=event.width)
chat_canvas.bind("<Configure>",_resize_inner)
def toggle_scrollbar():
    if inner_frame.winfo_height()>chat_canvas.winfo_height(): scrollbar.pack(side="right",fill="y")
    else: scrollbar.pack_forget()
def on_configure(event=None):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
    toggle_scrollbar()
inner_frame.bind("<Configure>",on_configure)
def on_key_press(event):
    if event.keysym in ("Down","Up","Next","Prior"):
        delta={"Down":1,"Up":-1,"Next":10,"Prior":-10}[event.keysym]
        chat_canvas.yview_scroll(delta,"units")
root.bind_all("<Down>",on_key_press)
root.bind_all("<Up>",on_key_press)
root.bind_all("<Next>",on_key_press)
root.bind_all("<Prior>",on_key_press)

# --- Input UI ---
input_frame=tk.Frame(root,bg=darkgray); input_frame.pack(side="bottom",fill="x")
right_frame=tk.Frame(input_frame,bg=darkgray); right_frame.pack(anchor="e")
entry_w, entry_h, corner, rbg = 1020, 54, 18, "#222327"
rounded_canvas=tk.Canvas(right_frame,width=entry_w,height=entry_h,bg=darkgray,highlightthickness=0)
rounded_canvas.grid(row=0,column=1,padx=5,pady=8)
def _round_rect(c,x1,y1,x2,y2,r,**kwargs):
    c.create_arc(x1,y1,x1+2*r,y1+2*r,start=90,extent=90,style="pieslice",outline="",fill=kwargs.get("fill"))
    c.create_arc(x2-2*r,y1,x2,y1+2*r,start=0,extent=90,style="pieslice",outline="",fill=kwargs.get("fill"))
    c.create_arc(x1,y2-2*r,x1+2*r,y2,start=180,extent=90,style="pieslice",outline="",fill=kwargs.get("fill"))
    c.create_arc(x2-2*r,y2-2*r,x2,y2,start=270,extent=90,style="pieslice",outline="",fill=kwargs.get("fill"))
    c.create_rectangle(x1+r,y1,x2-r,y2,outline="",fill=kwargs.get("fill"))
    c.create_rectangle(x1,y1+r,x2,y2-r,outline="",fill=kwargs.get("fill"))
_round_rect(rounded_canvas,0,0,entry_w,entry_h,corner,fill=rbg)
textbox=tk.Entry(rounded_canvas,font=dfont,bd=0,fg="#E0E0E0",bg=rbg,insertbackground=pink,relief="flat",highlightthickness=0)
textbox.place(x=8,y=8,width=entry_w-16,height=entry_h-16)
textbox.bind("<Return>", lambda e: sendmessage())  # ENTER key bound

btn_w, btn_h, btn_corner = 54, 54, 18
send_canvas=tk.Canvas(right_frame,width=btn_w,height=btn_h,bg=darkgray,highlightthickness=0)
send_canvas.grid(row=0,column=2,padx=(6,12),pady=8)
_round_rect(send_canvas,0,0,btn_w,btn_h,btn_corner,fill=rbg)
user_color = get_color_for_username(app_state.get('username', ''))
send_label = tk.Label(send_canvas, text=">", font=dfont, fg=user_color, bg=rbg)
send_label.place(relx=0.5,rely=0.5,anchor="center")

# --- Attach button ---
attach_canvas=tk.Canvas(right_frame,width=54,height=54,bg=darkgray,highlightthickness=0)
attach_canvas.grid(row=0,column=0,padx=(12,5),pady=8)
_round_rect(attach_canvas,0,0,54,54,btn_corner,fill=rbg)
attach_label = tk.Label(attach_canvas, text="+", font=dfont, fg=user_color, bg=rbg)
attach_label.place(relx=0.5,rely=0.5,anchor="center")

# --- Functions ---
def render_message_widget(data, color=None, tempId=None):
    now = dt.utcnow().strftime("%I:%M %p").upper()
    mf = tk.Frame(inner_frame, bg=darkgray)
    mf.pack(pady=2, padx=10, fill="x", anchor="e")
    left_blank = tk.Frame(mf, bg=darkgray, width=250)
    left_blank.pack(side="left", fill="y")

    username = data.get('username') or "unknown"
    if color is None:
        color = get_color_for_username(username)

    tk.Label(mf, text=username, font=tfont, fg=color, bg=darkgray).pack(side="right", padx=5)

    # Check if it's a file
    if 'filePath' in data:
        file_path = data['filePath'].lower()
        if file_path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            try:
                _, res = dbx.files_download(file_path)
                img = Image.open(res.raw)
                img.thumbnail((400, 400))
                img_tk = ImageTk.PhotoImage(img)
                lbl = tk.Label(mf, image=img_tk, bg=darkgray)
                lbl.image = img_tk
                lbl.pack(side="left", padx=5, pady=5)
            except Exception as e:
                lbl = tk.Label(mf, text=f"[File] {data['text'].replace('[File] ', '')}",
                               font=dfont, fg=color, bg=darkgray, padx=10, pady=5)
                lbl.pack(side="left")
        else:
            lbl = tk.Label(mf, text=f"[File] {data['text'].replace('[File] ', '')}",
                           font=dfont, fg=color, bg=darkgray, padx=10, pady=5)
            lbl.pack(side="left")

        def download_file():
            save_path = filedialog.asksaveasfilename(initialfile=data['text'].replace('[File] ', ''))
            if not save_path: return
            try:
                _, res = dbx.files_download(data['filePath'])
                with open(save_path, "wb") as f: f.write(res.content)
            except Exception as e:
                messagebox.showerror("Download error", str(e))
        tk.Button(mf, text="↓", command=download_file, bg=darkgray, fg=color).pack(side="left", padx=5)

    else:
        lbl = tk.Label(mf, text=data.get('text',''), font=dfont, wraplength=1000, justify="left", anchor="w",
                       fg=color, bg=darkgray, padx=10, pady=5)
        lbl.pack(side="left", padx=5)

    if tempId is None:
        tempId = data.get("tempId")
    if tempId:
        mf.tempId = tempId

    return mf



def sendmessage(event=None):
    if not app_state.get('idToken'):
        messagebox.showwarning("Not signed in", "Please sign in first.")
        prompt_auth()
        return

    if not selected_user:
        messagebox.showwarning("Select user", "Please select a user to chat with.")
        return

    msg = textbox.get().strip()
    if not msg:
        return

    temp_id = f"temp-{int(dt.now().timestamp()*1000)}"

    # Render gray optimistic message
    frame = render_message_widget(
        {'text': msg, 'userId': app_state.get('uid'), 'username': app_state.get('username')},
        color="#888",  # gray for optimistic
        tempId=temp_id
    )
    optimistic_frames[temp_id] = frame

    # Scroll to bottom and clear input
    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)
    textbox.delete(0, tk.END)

    def push_to_firestore():
        try:
            doc_ref = db.collection('channels').document(CHANNEL_ID).collection('messages').document()
            doc_ref.set({
                'messageId': doc_ref.id,
                'tempId': temp_id,  # <--- must include for listener
                'userId': app_state.get('uid'),
                'userEmail': app_state.get('email'),
                'username': app_state.get('username'),
                'text': msg,
                'recipientId': selected_user,
                'createdAt': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print("Send error:", e)
            # Remove optimistic frame on failure
            if temp_id in optimistic_frames:
                f = optimistic_frames.pop(temp_id)
                f.destroy()

    threading.Thread(target=push_to_firestore, daemon=True).start()


def attach_file(event=None):
    if not app_state.get("idToken"):
        prompt_auth()
        return

    if not selected_user:
        messagebox.showwarning("Select user", "Please select a user to chat with.")
        return

    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    try:
        if os.path.getsize(file_path) > 10 * 1024 * 1024:
            messagebox.showwarning("File too large", "Maximum file size is 10 MB.")
            return
    except Exception as e:
        print("Could not determine file size:", e)

    ext = file_path.split(".")[-1]
    sender = app_state['username']
    receiver = get_username_from_uid(selected_user)
    file_name = f"{sender}_{receiver}.{ext}"  # Auto-named
    temp_id = f"temp-{int(dt.now().timestamp()*1000)}"

    # Optimistic frame
    frame = tk.Frame(inner_frame, bg=darkgray)
    frame.pack(pady=2, padx=10, fill="x", anchor="e")
    tk.Frame(frame, bg=darkgray, width=250).pack(side="left", fill="y")
    status_lbl = tk.Label(frame, text=f"Uploading {file_name}...", font=dfont,
                          fg="#888", bg=darkgray, padx=10, pady=5)
    status_lbl.pack(side="left")
    frame.tempId = temp_id
    optimistic_frames[temp_id] = frame

    def upload_and_save():
        try:
            with open(file_path, "rb") as f:
                dbx.files_upload(f.read(), f"/{file_name}", mode=dropbox.files.WriteMode.overwrite)

            doc_ref = db.collection('channels').document(CHANNEL_ID).collection('messages').document()
            doc_ref.set({
                'messageId': doc_ref.id,
                'tempId': temp_id,
                'userId': app_state['uid'],
                'userEmail': app_state['email'],
                'username': app_state['username'],
                'text': f"[File] {file_name}",
                'filePath': f"/{file_name}",
                'recipientId': selected_user,
                'createdAt': firestore.SERVER_TIMESTAMP
            })

            optimistic_frames.pop(temp_id, None)
            try: frame.destroy()
            except: pass

        except Exception as e:
            print("File send error:", e)
            try:
                status_lbl.config(text=f"Upload failed: {file_name}", fg="red")
            except: pass
            try:
                optimistic_frames.pop(temp_id, None)
                frame.destroy()
            except: pass

    threading.Thread(target=upload_and_save, daemon=True).start()



attach_canvas.bind("<Button-1>",attach_file)
attach_label.bind("<Button-1>",attach_file)
send_canvas.bind("<Button-1>",sendmessage)
send_label.bind("<Button-1>",sendmessage)

# --- Firestore listener ---
# --- Unified Firestore listener ---
listener_attached = False

def attach_listener():
    global listener_attached
    if listener_attached or db is None:
        if db is None:
            root.after(500, attach_listener)
        return

    listener_attached = True

    query = db.collection('channels').document(CHANNEL_ID)\
              .collection('messages').order_by('createdAt')

    def on_snapshot(col_snapshot, changes, read_time):
        def tk_update():
            if not selected_user:
                return

            # --- Clear all optimistic messages before any render ---
            for f in list(optimistic_frames.values()):
                try:
                    f.destroy()
                except:
                    pass
            optimistic_frames.clear()

            for change in changes:
                if change.type.name != 'ADDED':
                    continue

                data = change.document.to_dict()
                msg_id = data['messageId']
                if msg_id in rendered_message_ids:
                    continue

                # Only messages between current user and selected user
                if set([data.get('userId'), data.get('recipientId')]) != set([app_state['uid'], selected_user]):
                    continue

                render_message_widget(data)
                rendered_message_ids.add(msg_id)

            chat_canvas.update_idletasks()
            chat_canvas.yview_moveto(1.0)

        root.after(0, tk_update)

    query.on_snapshot(on_snapshot)

user_widgets = {}
selected_user = None

def render_user(username, uid):
    # Skip self
    if uid == app_state.get('uid'):
        return

    if uid in user_widgets:
        return

    def select_user():
        global selected_user
        selected_user = uid
        load_conversation(uid)
        for u, w in user_widgets.items():
            w.config(bg="#111")
        user_widgets[uid].config(bg="#333")

    frame = tk.Frame(sidebar_inner, bg="#111", pady=5)
    frame.pack(fill="x")
    lbl = tk.Label(frame, text=username, fg="white", bg="#111", font=tfont, anchor="w")
    lbl.pack(fill="x", padx=10)
    lbl.bind("<Button-1>", lambda e: select_user())
    user_widgets[uid] = frame


def fetch_users():
    if db is None:
        root.after(500, fetch_users)
        return
    users = db.collection('users').get()
    for u in users:
        data = u.to_dict()
        if data['email'] != app_state.get('email'):
            render_user(data['username'], u.id)


def load_conversation(uid):
    # Clear current messages
    for widget in inner_frame.winfo_children():
        widget.destroy()
    rendered_message_ids.clear()
    if not uid:
        return

    query = db.collection('channels').document(CHANNEL_ID)\
              .collection('messages')\
              .order_by('createdAt')

    def on_snapshot(col_snapshot, changes, read_time):
        def tk_update():
            # --- Clear all optimistic messages before rendering ---
            for f in list(optimistic_frames.values()):
                try:
                    f.destroy()
                except:
                    pass
            optimistic_frames.clear()

            for change in changes:
                if change.type.name != 'ADDED':
                    continue

                data = change.document.to_dict()
                msg_id = data['messageId']
                if msg_id in rendered_message_ids:
                    continue

                # Only messages between current user and selected user
                if 'filePath' in data:
                    fname = data['filePath'].split("/")[-1]
                    # Expect pattern sender_receiver.ext
                    name_part = fname.rsplit(".", 1)[0]  # remove extension
                    expected_patterns = [
                        f"{app_state['username']}_{get_username_from_uid(uid)}",
                        f"{get_username_from_uid(uid)}_{app_state['username']}"
                    ]
                    if name_part not in expected_patterns:
                        continue
                else:
                    if set([data.get('userId'), data.get('recipientId')]) != set([app_state['uid'], uid]):
                        continue

                render_message_widget(data)
                rendered_message_ids.add(msg_id)

            chat_canvas.update_idletasks()
            chat_canvas.yview_moveto(1.0)

        root.after(0, tk_update)

    query.on_snapshot(on_snapshot)

root.after(3000, fetch_users)


root.after(2000,attach_listener)
root.mainloop()
