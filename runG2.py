import mido
import pygame
import pygame.midi
import time
import os
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class MidiPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Python MIDI Player")
        self.root.geometry("500x480")
        self.root.resizable(False, False)

        self.set_high_priority()

        # --- PENGATURAN TEMA (DARK MODE) ---
        self.bg_color = "#2E3440"       
        self.fg_color = "#D8DEE9"       
        self.accent_color = "#88C0D0"   
        self.frame_bg = "#3B4252"       
        
        self.root.configure(bg=self.bg_color)
        self.setup_theme()

        self.is_playing = False
        self.is_paused = False
        self.player = None
        self.file_path = ""
        self.current_port_id = None

        pygame.init()
        pygame.midi.init()
        self.build_ui()

    def set_high_priority(self):
        try:
            if sys.platform == 'win32':
                ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080)
        except Exception:
            pass

    def setup_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure("Frame.TLabel", background=self.frame_bg, foreground=self.fg_color)
        style.configure("TButton", background=self.frame_bg, foreground=self.fg_color, 
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=5)
        style.map("TButton", background=[("active", self.accent_color), ("disabled", "#4C566A")])
        style.configure("TProgressbar", thickness=15, troughcolor=self.frame_bg, 
                        background=self.accent_color, bordercolor=self.bg_color)

    def get_midi_ports(self):
        count = pygame.midi.get_count()
        ports = {}
        for i in range(count):
            info = pygame.midi.get_device_info(i)
            if info[3] == 1:
                name = info[1].decode('utf-8')
                ports[f"{i}: {name}"] = i
        return ports

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def build_ui(self):
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(padx=20, pady=15, fill="both", expand=True)

        ttk.Label(main_frame, text="1. Pilih Port MIDI Output:").pack(anchor="w", pady=(0, 5))
        self.ports_dict = self.get_midi_ports()
        
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(main_frame, textvariable=self.port_var, state="readonly", width=50)
        self.port_dropdown['values'] = list(self.ports_dict.keys())
        self.port_dropdown.pack(fill="x", pady=(0, 15))
        
        if self.ports_dict:
            self.port_dropdown.current(0)
        else:
            self.port_dropdown.set("Tidak ada perangkat MIDI terdeteksi!")

        ttk.Label(main_frame, text="2. Pilih File MIDI (.mid):").pack(anchor="w", pady=(0, 5))
        
        file_frame = tk.Frame(main_frame, bg=self.frame_bg, padx=10, pady=5)
        file_frame.pack(fill="x", pady=(0, 15))
        
        self.file_label = ttk.Label(file_frame, text="Belum ada file dipilih...", style="Frame.TLabel")
        self.file_label.pack(side="left")
        
        btn_browse = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        btn_browse.pack(side="right")

        settings_frame = tk.Frame(main_frame, bg=self.bg_color)
        settings_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(settings_frame, text="Kecepatan:").grid(row=0, column=0, sticky="w", pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_entry = ttk.Spinbox(settings_frame, from_=0.1, to=5.0, increment=0.1, textvariable=self.speed_var, width=8)
        self.speed_entry.grid(row=0, column=1, padx=10)

        ttk.Label(settings_frame, text="Volume:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_entry = ttk.Spinbox(settings_frame, from_=0.1, to=3.0, increment=0.1, textvariable=self.volume_var, width=8)
        self.volume_entry.grid(row=0, column=3, padx=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100, style="TProgressbar")
        self.progress_bar.pack(fill="x", pady=(15, 5))

        self.time_label = ttk.Label(main_frame, text="00:00 / 00:00", font=("Consolas", 11))
        self.time_label.pack()

        control_frame = tk.Frame(main_frame, bg=self.bg_color)
        control_frame.pack(pady=20)

        self.btn_play = ttk.Button(control_frame, text="▶ Play", command=self.start_playback, width=10)
        self.btn_play.pack(side="left", padx=5)

        self.btn_pause = ttk.Button(control_frame, text="⏸ Pause", command=self.toggle_pause, state="disabled", width=10)
        self.btn_pause.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_playback, state="disabled", width=10)
        self.btn_stop.pack(side="left", padx=5)

        ttk.Label(main_frame, text="I don't think this is an upgrade, because this is losing some quality.\nthe melody seems to be boring and flat. but its add more compatibility \non error midi file").pack(anchor="w", pady=(0, 5))

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Pilih File MIDI",
            filetypes=(("MIDI Files", "*.mid *.midi"), ("All Files", "*.*"))
        )
        if filepath:
            self.file_path = filepath
            self.file_label.config(text=os.path.basename(filepath)[:35] + "...") 
            
            try:
                # PERBAIKAN 1: Tambahkan clip=True saat membaca durasi file
                mid = mido.MidiFile(self.file_path, clip=True)
                total_time = mid.length
                self.time_label.config(text=f"00:00 / {self.format_time(total_time)}")
                self.progress_var.set(0)
            except:
                pass

    def silence_all_notes(self):
        if self.player:
            try:
                for ch in range(16):
                    self.player.write_short(0xB0 + ch, 123, 0)
            except:
                pass

    def toggle_pause(self):
        if not self.is_playing:
            return
            
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.config(text="▶ Resume")
            self.silence_all_notes()
        else:
            self.btn_pause.config(text="⏸ Pause")

    def precise_sleep(self, duration):
        target_time = time.perf_counter() + duration
        while True:
            current_time = time.perf_counter()
            if current_time >= target_time:
                break
            
            if target_time - current_time > 0.002:
                time.sleep(0.001) 
            else:
                pass 

    def start_playback(self):
        if not self.file_path:
            messagebox.showwarning("Peringatan", "Pilih file MIDI terlebih dahulu!")
            return
            
        port_selection = self.port_var.get()
        if not port_selection or port_selection == "Tidak ada perangkat MIDI terdeteksi!":
            messagebox.showwarning("Peringatan", "Pilih port MIDI yang valid!")
            return

        self.btn_play.config(state="disabled")
        self.btn_pause.config(state="normal", text="⏸ Pause")
        self.btn_stop.config(state="normal")
        
        self.is_playing = True
        self.is_paused = False

        port_id = self.ports_dict[port_selection]

        if self.player is None or getattr(self, 'current_port_id', None) != port_id:
            if self.player:
                self.player.close() 
            try:
                self.player = pygame.midi.Output(port_id)
                self.current_port_id = port_id 
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka port: {e}")
                self.cleanup_playback()
                return

        threading.Thread(target=self.play_midi_thread, daemon=True).start()

    def play_midi_thread(self):
        try:
            # PERBAIKAN 2: Tambahkan clip=True saat memutar lagunya. Ini akan memaksa data korup menjadi aman!
            mid = mido.MidiFile(self.file_path, clip=True)
            total_time = mid.length
            
            self.root.after(0, lambda: self.progress_bar.config(maximum=total_time))
            self.root.after(0, lambda: self.progress_var.set(0))
            
            current_time = 0.0
            last_ui_update = 0.0

            for msg in mid:
                if not self.is_playing:
                    break
                
                while self.is_paused:
                    time.sleep(0.05)
                    if not self.is_playing: 
                        break
                
                if not self.is_playing:
                    break

                speed = self.speed_var.get()
                time_to_sleep = (msg.time / speed) if speed > 0 else msg.time
                
                if time_to_sleep > 0:
                    self.precise_sleep(time_to_sleep)
                
                current_time += msg.time 

                if current_time - last_ui_update > 0.1:
                    self.root.after(0, self.update_gui_progress, current_time, total_time)
                    last_ui_update = current_time

                if not msg.is_meta:
                    if msg.type == 'sysex':
                        continue
                        
                    volume_scale = self.volume_var.get()
                    if msg.type == 'note_on' and msg.velocity > 0:
                        new_vel = int(msg.velocity * volume_scale)
                        msg.velocity = max(1, min(127, new_vel))
                    
                    try:
                        raw_bytes = msg.bytes()
                        if len(raw_bytes) > 0:
                            status_byte = raw_bytes[0]
                            
                            if len(raw_bytes) == 3:
                                data1 = raw_bytes[1] & 0x7F
                                data2 = raw_bytes[2] & 0x7F
                                self.player.write_short(status_byte, data1, data2)
                            elif len(raw_bytes) == 2:
                                data1 = raw_bytes[1] & 0x7F
                                self.player.write_short(status_byte, data1)
                            elif len(raw_bytes) == 1:
                                self.player.write_short(status_byte)
                    except Exception:
                        pass 

            if self.is_playing:
                self.root.after(0, self.update_gui_progress, total_time, total_time)

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", f"Terjadi kesalahan:\n{msg}"))
        finally:
            self.cleanup_playback()

    def update_gui_progress(self, current_t, total_t):
        self.progress_var.set(current_t)
        self.time_label.config(text=f"{self.format_time(current_t)} / {self.format_time(total_t)}")

    def stop_playback(self):
        self.is_playing = False
        self.is_paused = False

    def cleanup_playback(self):
        self.is_playing = False 
        self.silence_all_notes()

        self.root.after(0, lambda: self.btn_play.config(state="normal"))
        self.root.after(0, lambda: self.btn_pause.config(state="disabled", text="⏸ Pause"))
        self.root.after(0, lambda: self.btn_stop.config(state="disabled"))
        
        self.root.after(0, lambda: self.progress_var.set(0))
        total_time_str = self.time_label.cget("text").split("/")[-1].strip() if "/" in self.time_label.cget("text") else "00:00"
        self.root.after(0, lambda: self.time_label.config(text=f"00:00 / {total_time_str}"))

    def on_closing(self):
        self.is_playing = False
        self.is_paused = False
        time.sleep(0.1) 
        
        if self.player:
            self.silence_all_notes()
            try:
                self.player.close()
            except:
                pass
            
        pygame.midi.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiPlayerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()