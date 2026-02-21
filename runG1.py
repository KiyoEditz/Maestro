import mido
import pygame
import pygame.midi
import time
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class MidiPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Python MIDI Player")
        self.root.geometry("500x480")
        self.root.resizable(False, False)

        # --- PENGATURAN TEMA (DARK MODE) ---
        self.bg_color = "#2E3440"       # Warna background utama (Gelap)
        self.fg_color = "#D8DEE9"       # Warna teks (Terang)
        self.accent_color = "#88C0D0"   # Warna aksen (Biru muda)
        self.frame_bg = "#3B4252"       # Warna kotak frame
        
        self.root.configure(bg=self.bg_color)
        self.setup_theme()

        # Inisialisasi status
        self.is_playing = False
        self.is_paused = False
        self.player = None
        self.file_path = ""
        self.current_port_id = None

        # Inisialisasi Pygame MIDI
        pygame.init()
        pygame.midi.init()

        # Bangun Antarmuka (UI)
        self.build_ui()

    def setup_theme(self):
        """Mengatur gaya kustom untuk widget (Tombol, Label, Progressbar)"""
        style = ttk.Style()
        style.theme_use('clam') # Gunakan base theme yang mudah dimodifikasi

        # Konfigurasi Label
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure("Frame.TLabel", background=self.frame_bg, foreground=self.fg_color)
        
        # Konfigurasi Tombol
        style.configure("TButton", background=self.frame_bg, foreground=self.fg_color, 
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=5)
        style.map("TButton", background=[("active", self.accent_color), ("disabled", "#4C566A")])

        # Konfigurasi Progressbar
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
        """Mengubah detik menjadi format MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def build_ui(self):
        # Frame utama untuk memberi margin
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(padx=20, pady=15, fill="both", expand=True)

        # 1. Pilih Port
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

        # 2. Pilih File
        ttk.Label(main_frame, text="2. Pilih File MIDI (.mid):").pack(anchor="w", pady=(0, 5))
        
        file_frame = tk.Frame(main_frame, bg=self.frame_bg, padx=10, pady=5)
        file_frame.pack(fill="x", pady=(0, 15))
        
        self.file_label = ttk.Label(file_frame, text="Belum ada file dipilih...", style="Frame.TLabel")
        self.file_label.pack(side="left")
        
        btn_browse = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        btn_browse.pack(side="right")

        # 3. Pengaturan (Kecepatan & Volume)
        settings_frame = tk.Frame(main_frame, bg=self.bg_color)
        settings_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(settings_frame, text="Kecepatan (Tempo):").grid(row=0, column=0, sticky="w", pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_entry = ttk.Spinbox(settings_frame, from_=0.1, to=5.0, increment=0.1, textvariable=self.speed_var, width=8)
        self.speed_entry.grid(row=0, column=1, padx=10)

        ttk.Label(settings_frame, text="Volume (Velocity):").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_entry = ttk.Spinbox(settings_frame, from_=0.1, to=3.0, increment=0.1, textvariable=self.volume_var, width=8)
        self.volume_entry.grid(row=0, column=3, padx=10)

        # 4. Progress Bar & Waktu
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100, style="TProgressbar")
        self.progress_bar.pack(fill="x", pady=(15, 5))

        self.time_label = ttk.Label(main_frame, text="00:00 / 00:00", font=("Consolas", 11))
        self.time_label.pack()

        # 5. Tombol Kontrol (Play, Pause, Stop)
        control_frame = tk.Frame(main_frame, bg=self.bg_color)
        control_frame.pack(pady=20)

        self.btn_play = ttk.Button(control_frame, text="▶ Play", command=self.start_playback, width=10)
        self.btn_play.pack(side="left", padx=5)

        self.btn_pause = ttk.Button(control_frame, text="⏸ Pause", command=self.toggle_pause, state="disabled", width=10)
        self.btn_pause.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_playback, state="disabled", width=10)
        self.btn_stop.pack(side="left", padx=5)

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Pilih File MIDI",
            filetypes=(("MIDI Files", "*.mid *.midi"), ("All Files", "*.*"))
        )
        if filepath:
            self.file_path = filepath
            self.file_label.config(text=os.path.basename(filepath)[:35] + "...") # Potong teks jika terlalu panjang
            
            # Hitung dan tampilkan total waktu saat file dipilih
            try:
                mid = mido.MidiFile(self.file_path)
                total_time = mid.length
                self.time_label.config(text=f"00:00 / {self.format_time(total_time)}")
                self.progress_var.set(0)
            except:
                pass

    def silence_all_notes(self):
        """Mematikan semua suara di 16 channel"""
        if self.player:
            try:
                for ch in range(16):
                    self.player.write_short(0xB0 + ch, 123, 0)
            except:
                pass

    def toggle_pause(self):
        """Fungsi untuk menjeda dan melanjutkan lagu"""
        if not self.is_playing:
            return
            
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.config(text="▶ Resume")
            self.silence_all_notes() # Hentikan suara yang sedang bunyi agar tidak nyangkut
        else:
            self.btn_pause.config(text="⏸ Pause")

    def start_playback(self):
        if not self.file_path:
            messagebox.showwarning("Peringatan", "Pilih file MIDI terlebih dahulu!")
            return
            
        port_selection = self.port_var.get()
        if not port_selection or port_selection == "Tidak ada perangkat MIDI terdeteksi!":
            messagebox.showwarning("Peringatan", "Pilih port MIDI yang valid!")
            return

        # Atur tombol
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
            mid = mido.MidiFile(self.file_path)
            total_time = mid.length
            
            # Reset UI
            self.root.after(0, lambda: self.progress_bar.config(maximum=total_time))
            self.root.after(0, lambda: self.progress_var.set(0))
            
            current_time = 0.0

            for msg in mid:
                # 1. Cek jika Stop ditekan
                if not self.is_playing:
                    break
                
                # 2. Cek jika Pause ditekan (Loop penahan waktu)
                while self.is_paused:
                    time.sleep(0.05)
                    if not self.is_playing: # Jika saat di-pause user menekan Stop
                        break
                
                if not self.is_playing:
                    break

                # 3. Proses Kecepatan
                speed = self.speed_var.get()
                time_to_sleep = (msg.time / speed) if speed > 0 else msg.time
                
                if time_to_sleep > 0:
                    time.sleep(time_to_sleep)
                
                current_time += msg.time # Tambah waktu aktual lagu berjalan

                # Update UI Waktu & Progress Bar (Gunakan root.after agar aman di Thread)
                self.root.after(0, self.update_gui_progress, current_time, total_time)

                # 4. Proses Nada & Volume
                if not msg.is_meta:
                    volume_scale = self.volume_var.get()
                    if msg.type == 'note_on' and msg.velocity > 0:
                        new_vel = int(msg.velocity * volume_scale)
                        msg.velocity = max(1, min(127, new_vel))
                    
                    raw_bytes = msg.bytes()
                    if len(raw_bytes) == 3:
                        self.player.write_short(raw_bytes[0], raw_bytes[1], raw_bytes[2])
                    elif len(raw_bytes) == 2:
                        self.player.write_short(raw_bytes[0], raw_bytes[1])
                    elif len(raw_bytes) == 1:
                        self.player.write_short(raw_bytes[0])

        except Exception as e:
            # 1. Ubah error menjadi teks permanen
            error_msg = str(e) 
            
            # 2. Ikat teks tersebut ke dalam variabel lokal lambda (msg=error_msg)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", f"Terjadi kesalahan:\n{msg}"))
            
        finally:
            self.cleanup_playback()

    def update_gui_progress(self, current_t, total_t):
        """Memperbarui teks waktu dan progress bar di GUI"""
        self.progress_var.set(current_t)
        self.time_label.config(text=f"{self.format_time(current_t)} / {self.format_time(total_t)}")

    def stop_playback(self):
        self.is_playing = False
        self.is_paused = False

    def cleanup_playback(self):
        self.is_playing = False 
        self.silence_all_notes()

        # Kembalikan tampilan GUI ke awal
        self.root.after(0, lambda: self.btn_play.config(state="normal"))
        self.root.after(0, lambda: self.btn_pause.config(state="disabled", text="⏸ Pause"))
        self.root.after(0, lambda: self.btn_stop.config(state="disabled"))
        
        # Reset progress bar jika lagu selesai/di-stop
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