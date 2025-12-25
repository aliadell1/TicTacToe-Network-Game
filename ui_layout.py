import tkinter as tk
from tkinter import messagebox
import itertools 
import threading
import subprocess
import shutil
import sys
import os
import platform
import cv2


# --- TRY IMPORTING VIDEO LIBRARIES ---
try:
    from PIL import Image, ImageTk
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    print("Warning: Libraries missing. Video will be skipped.")

# --- LIGHT THEME ---
THEME = {
    "bg": "#ffffff", "fg": "#2c3e50", "btn_bg": "#ecf0f1",    
    "btn_fg": "#2c3e50", "btn_hover": "#bdc3c7", 
    "x_color": "#2980b9", "o_color": "#c0392b", "win_bg": "#27ae60"     
}

class GameUI:
    def __init__(self, root, on_click_callback, on_invite_callback, on_connect_callback):
        self.root = root
        self.on_click_callback = on_click_callback
        self.on_invite_callback = on_invite_callback
        self.on_connect_callback = on_connect_callback
        
        self.root.title("Tic Tac Toe")
        self.root.geometry("400x700")
        self.root.configure(bg=THEME["bg"])
        
        self.setup_layout()
        self.play_sound("welcome")

    def play_sound(self, sound_name):
        def _run():
            file_name = f"{sound_name}.wav"
            if platform.system() == "Linux":
                if os.path.exists(file_name): os.system(f"aplay -q {file_name}")
            elif platform.system() == "Windows":
                try:
                    import winsound
                    if os.path.exists(file_name): winsound.PlaySound(file_name, winsound.SND_FILENAME)
                except: pass
        threading.Thread(target=_run, daemon=True).start()

    def setup_layout(self):
        tk.Label(self.root, text="TIC TAC TOE", font=("Montserrat", 28, "bold"), 
                 bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(60, 20))
        
        self.status_label = tk.Label(self.root, text="Welcome", font=("Segoe UI", 16, "bold"), 
                                     bg=THEME["bg"], fg="black")
        self.status_label.pack(pady=(10, 40))
        self.animate_rainbow()

        self.menu_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.menu_frame.pack(pady=20, padx=60, fill="x") 
        
        def make_btn(text, cmd):
            def cmd_with_sound():
                self.play_sound("click")
                cmd()     
            btn = tk.Button(self.menu_frame, text=text, command=cmd_with_sound,
                             bg=THEME["btn_bg"], fg=THEME["btn_fg"], 
                             activebackground=THEME["btn_hover"],
                             font=("Segoe UI", 12), borderwidth=0, padx=20, pady=15)
            btn.pack(side=tk.TOP, fill="x", pady=25) 
            return btn

        make_btn("Local Game", lambda: self.on_connect_callback("LOCAL"))
        make_btn("Connect Online", lambda: self.on_connect_callback("ONLINE"))

        self.lobby_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.listbox = tk.Listbox(self.lobby_frame, width=30, height=8, 
                                  bg=THEME["btn_bg"], fg=THEME["btn_fg"], 
                                  borderwidth=0, highlightthickness=0,
                                  selectbackground=THEME["x_color"])
        self.listbox.pack(pady=20)
        
        tk.Button(self.lobby_frame, text="Invite Selected", 
                  command=lambda: [self.play_sound("click"), self.trigger_invite()], 
                  bg=THEME["fg"], fg="white", font=("Segoe UI", 10, "bold"),
                  padx=20, pady=10, borderwidth=0).pack(pady=20)

        self.board_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.buttons = []
        for i in range(9):
            def on_board_click(idx=i):
                self.play_sound("click")
                self.on_click_callback(idx)

            btn = tk.Button(self.board_frame, text="", font=("Verdana", 24, "bold"), 
                            width=4, height=2, bg=THEME["btn_bg"], fg="black",
                            borderwidth=0, 
                            command=on_board_click)
            btn.grid(row=i//3, column=i%3, padx=10, pady=10) 
            self.buttons.append(btn)

    def animate_rainbow(self):
        colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6"]
        if not hasattr(self, 'rainbow_cycle'):
            self.rainbow_cycle = itertools.cycle(colors)
        next_color = next(self.rainbow_cycle)
        self.status_label.config(fg=next_color)
        self.root.after(200, self.animate_rainbow)

    def trigger_invite(self):
        selection = self.listbox.curselection()
        if selection:
            target = self.listbox.get(selection[0])
            self.on_invite_callback(target)

    def update_board(self, index, symbol):
        color = THEME["x_color"] if symbol == "X" else THEME["o_color"]
        self.buttons[index].config(text=symbol, fg=color)

    def highlight_win(self, indices):
        for idx in indices:
            self.buttons[idx].config(bg=THEME["win_bg"], fg="white")

    def reset_board_visuals(self):
        for btn in self.buttons:
            btn.config(text="", bg=THEME["btn_bg"], state=tk.NORMAL)

    def show_lobby(self):
        self.menu_frame.pack_forget()
        self.lobby_frame.pack(pady=10)
        self.board_frame.pack_forget()

    def show_game(self):
        self.menu_frame.pack_forget()
        self.lobby_frame.pack_forget()
        self.board_frame.pack()

    def update_list(self, players):
        self.listbox.delete(0, tk.END)
        for p in players:
            self.listbox.insert(tk.END, p)
    
        # [UPDATED] POPUP WITH EMBEDDED VIDEO SUPPORT
    # [UPDATED] POPUP: Handles Video + Audio Sync Internally
    def create_popup(self, title, message, mode="INFO", callback=None, video_file=None):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        
        # Increase height if showing video
        if video_file and VIDEO_AVAILABLE:
            popup.geometry("350x500") 
        else:
            popup.geometry("350x250")
            
        popup.configure(bg=THEME["bg"])
        popup.resizable(False, False)
        
        # Center popup
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 100
        popup.geometry(f"+{x}+{y}")

        # Helper: Play wav or fall back to external players for mp4 audio
        def play_media_audio(video_file):
            def _run():
                wav_path = f"{video_file}.wav"
                mp4_path = f"{video_file}.mp4"

                # 1) Prefer a separate wav file (keeps existing behavior)
                if os.path.exists(wav_path):
                    try:
                        self.play_sound(video_file)
                        return
                    except Exception as e:
                        print(f"play_sound fallback error: {e}")

                # 2) If mp4 exists, try external players for audio-only playback
                if os.path.exists(mp4_path):
                    players = [
                        ("mpv", ["mpv", "--no-video", mp4_path]),
                        ("ffplay", ["ffplay", "-nodisp", "-autoexit", mp4_path]),
                        ("cvlc", ["cvlc", "--play-and-exit", mp4_path]),
                        ("xdg-open", ["xdg-open", mp4_path])
                    ]

                    for exe, cmd in players:
                        if shutil.which(cmd[0]):
                            try:
                                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                return
                            except Exception as e:
                                print(f"Failed to launch {exe}: {e}")

                    # If none available, print helpful message
                    print("No external media player found (mpv/ffplay/cvlc/xdg-open). Install one to hear audio from mp4 files.")
                else:
                    print(f"No audio file or media found for {video_file}")

            threading.Thread(target=_run, daemon=True).start()

        # attach helper to instance so it can be used elsewhere if needed
        self.play_media_audio = play_media_audio

        # --- 1. HANDLE VIDEO & AUDIO SYNC ---
        if video_file:
            # A. Play the Sound (Audio Track) or fallback to external player
            # This looks for "win.wav", "lose.wav", or the audio track inside "win.mp4"
            try:
                self.play_media_audio(video_file)
            except Exception as e:
                print(f"play_media_audio error: {e}")

            # B. Play the Video (Visual Track) or show helpful diagnostics
            vid_path = f"{video_file}.mp4"
            if not VIDEO_AVAILABLE:
                tk.Label(popup, text="Video libraries not installed.", bg=THEME["bg"], fg="#a00").pack(pady=10)
                tk.Label(popup, text="Install: pip install opencv-python Pillow", bg=THEME["bg"], fg="#555").pack(pady=(0,6))

                # Show diagnostic info to help troubleshoot interpreter mismatch
                try:
                    cv_status = ""
                    try:
                        import cv2 as _cv
                        cv_status = f"cv2 OK ({_cv.__version__})"
                    except Exception as _e:
                        cv_status = f"cv2 Missing: {_e}"

                    pil_status = ""
                    try:
                        import PIL as _pil
                        pil_status = f"PIL OK ({_pil.__version__})"
                    except Exception as _e:
                        pil_status = f"PIL Missing: {_e}"

                    tk.Label(popup, text=f"Python: {sys.executable}", bg=THEME["bg"], fg="#555").pack(pady=(4,0))
                    tk.Label(popup, text=cv_status, bg=THEME["bg"], fg="#555").pack()
                    tk.Label(popup, text=pil_status, bg=THEME["bg"], fg="#555").pack(pady=(0,8))
                except Exception:
                    pass
            else:
                try:
                    if not os.path.exists(vid_path):
                        tk.Label(popup, text=f"Video file not found: {vid_path}", bg=THEME["bg"], fg="#a00").pack(pady=10)
                    else:
                        video_lbl = tk.Label(popup, bg="black")
                        video_lbl.pack(pady=10, fill="both", expand=True)

                        cap = cv2.VideoCapture(vid_path)
                        if not cap.isOpened():
                            cap.release()
                            tk.Label(popup, text=f"Unable to open video: {vid_path}", bg=THEME["bg"], fg="#a00").pack(pady=10)
                        else:
                            def stream_video():
                                try:
                                    ret, frame = cap.read()
                                    if ret:
                                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        frame = cv2.resize(frame, (320, 240))
                                        img = Image.fromarray(frame)
                                        imgtk = ImageTk.PhotoImage(image=img)

                                        if video_lbl.winfo_exists():
                                            video_lbl.config(image=imgtk)
                                            video_lbl.image = imgtk
                                            video_lbl.after(30, stream_video)
                                        else:
                                            cap.release()
                                    else:
                                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
                                        stream_video()
                                except Exception as e:
                                    print(f"Video stream error: {e}")
                                    try: cap.release()
                                    except: pass

                            stream_video()
                except Exception as e:
                    print(f"Video playback setup error: {e}")
                    tk.Label(popup, text="Video playback failed (check console).", bg=THEME["bg"], fg="#a00").pack(pady=10)

        # --- 2. STANDARD CONTENT ---
        tk.Label(popup, text=title, font=("Montserrat", 16, "bold"), 
                bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(10, 5))
        
        tk.Label(popup, text=message, font=("Segoe UI", 11), wraplength=300,
                bg=THEME["bg"], fg="#555").pack(pady=5)

        # Input & Buttons (Unchanged)
        entry_var = tk.StringVar()
        if mode == "INPUT":
            entry = tk.Entry(popup, textvariable=entry_var, font=("Segoe UI", 12), 
                            bg=THEME["btn_bg"], fg="black", bd=0, highlightthickness=1)
            entry.pack(pady=15, padx=40, ipady=5, fill="x")
            entry.focus()

        def style_btn(txt, cmd, color=THEME["btn_bg"], txt_color=THEME["btn_fg"]):
            tk.Button(popup, text=txt, command=cmd, bg=color, fg=txt_color,
                    font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=8).pack(pady=10)

        if mode == "INFO":
            style_btn("OK", lambda: [popup.destroy(), callback() if callback else None])
        elif mode == "INPUT":
            def submit():
                if entry_var.get():
                    popup.destroy()
                    if callback: callback(entry_var.get())
            style_btn("Confirm", submit, THEME["x_color"], "white")
        elif mode == "YESNO":
            btn_frame = tk.Frame(popup, bg=THEME["bg"])
            btn_frame.pack(pady=20)
            tk.Button(btn_frame, text="Accept", bg=THEME["win_bg"], fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=8, command=lambda: [popup.destroy(), callback(True)]).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Decline", bg=THEME["o_color"], fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=8, command=lambda: [popup.destroy(), callback(False)]).pack(side=tk.LEFT, padx=10)