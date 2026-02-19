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
        self.root.title("Python MIDI Player")
        self.root.geometry("450x350")
        self.root.resizable(False, False)

        # Inisialisasi status
        self.is_playing = False
        self.player = None
        self.file_path = ""
        self.current_port_id = None

        # Inisialisasi Pygame MIDI
        pygame.init()
        pygame.midi.init()

        # Bangun Antarmuka (UI)
        self.build_ui()

    def get_midi_ports(self):
        """Mencari semua port MIDI output yang tersedia"""
        count = pygame.midi.get_count()
        ports = {}
        for i in range(count):
            info = pygame.midi.get_device_info(i)
            # info[3] adalah flag output
            if info[3] == 1:
                name = info[1].decode('utf-8')
                ports[f"{i}: {name}"] = i
        return ports

    def build_ui(self):
        # --- Bagian Pemilihan Port ---
        ttk.Label(self.root, text="1. Pilih Port MIDI Output:").pack(pady=(15, 5), padx=20, anchor="w")
        self.ports_dict = self.get_midi_ports()
        
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(self.root, textvariable=self.port_var, state="readonly", width=45)
        self.port_dropdown['values'] = list(self.ports_dict.keys())
        self.port_dropdown.pack(padx=20)
        
        if self.ports_dict:
            self.port_dropdown.current(0) # Set default ke port pertama
        else:
            self.port_dropdown.set("Tidak ada perangkat MIDI terdeteksi!")

        # --- Bagian Pemilihan File ---
        ttk.Label(self.root, text="2. Pilih File MIDI (.mid):").pack(pady=(15, 5), padx=20, anchor="w")
        
        file_frame = tk.Frame(self.root)
        file_frame.pack(padx=20, fill="x")
        
        self.file_label = ttk.Label(file_frame, text="Belum ada file dipilih", foreground="gray", width=35)
        self.file_label.pack(side="left")
        
        btn_browse = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        btn_browse.pack(side="right")

        # --- Bagian Pengaturan Kecepatan & Volume ---
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=20, padx=20, fill="x")

        # Kecepatan
        ttk.Label(settings_frame, text="Kecepatan (Tempo):").grid(row=0, column=0, sticky="w")
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_entry = ttk.Spinbox(settings_frame, from_=0.1, to=5.0, increment=0.1, textvariable=self.speed_var, width=8)
        self.speed_entry.grid(row=0, column=1, padx=10)

        # Volume
        ttk.Label(settings_frame, text="Volume (Velocity):").grid(row=1, column=0, sticky="w", pady=10)
        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_entry = ttk.Spinbox(settings_frame, from_=0.1, to=3.0, increment=0.1, textvariable=self.volume_var, width=8)
        self.volume_entry.grid(row=1, column=1, padx=10)

        # --- Tombol Kontrol (Play/Stop) ---
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        self.btn_play = ttk.Button(control_frame, text="▶ Play", command=self.start_playback)
        self.btn_play.pack(side="left", padx=10)

        self.btn_stop = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_playback, state="disabled")
        self.btn_stop.pack(side="left", padx=10)

    def browse_file(self):
        """Membuka dialog untuk memilih file MIDI"""
        filepath = filedialog.askopenfilename(
            title="Pilih File MIDI",
            filetypes=(("MIDI Files", "*.mid *.midi"), ("All Files", "*.*"))
        )
        if filepath:
            self.file_path = filepath
            # Menampilkan nama file saja (bukan path lengkap) agar rapi
            self.file_label.config(text=os.path.basename(filepath), foreground="black")

    def start_playback(self):
        """Memulai lagu dan mengatur koneksi agar tetap menyala"""
        if not self.file_path:
            messagebox.showwarning("Peringatan", "Pilih file MIDI terlebih dahulu!")
            return
            
        port_selection = self.port_var.get()
        if not port_selection or port_selection == "Tidak ada perangkat MIDI terdeteksi!":
            messagebox.showwarning("Peringatan", "Pilih port MIDI yang valid!")
            return

        # Ubah tampilan tombol
        self.btn_play.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.is_playing = True

        # Ambil ID Port dari dictionary
        port_id = self.ports_dict[port_selection]

        # Buka port HANYA JIKA belum dibuka atau user mengganti port di dropdown
        if self.player is None or getattr(self, 'current_port_id', None) != port_id:
            if self.player:
                self.player.close() # Tutup port lama HANYA jika user memilih port yang berbeda
            try:
                self.player = pygame.midi.Output(port_id)
                self.current_port_id = port_id # Simpan ID port yang sedang menyala
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka port: {e}")
                self.cleanup_playback()
                return

        # Jalankan fungsi pemutaran di Thread terpisah
        threading.Thread(target=self.play_midi_thread, daemon=True).start()

    def play_midi_thread(self):
        """Fungsi utama yang memutar lagu (berjalan di background)"""
        try:
            mid = mido.MidiFile(self.file_path)
            speed = self.speed_var.get()
            volume_scale = self.volume_var.get()

            # Proses membaca pesan MIDI
            for msg in mid:
                # Cek jika tombol Stop ditekan
                if not self.is_playing:
                    break
                
                # Jeda waktu dengan pengaturan kecepatan
                time.sleep((msg.time / speed) if speed > 0 else msg.time)
                
                if not msg.is_meta:
                    # Proses Modifikasi Volume (Velocity)
                    if msg.type == 'note_on' and msg.velocity > 0:
                        new_vel = int(msg.velocity * volume_scale)
                        msg.velocity = max(1, min(127, new_vel))
                    
                    # Kirim ke perangkat MIDI
                    raw_bytes = msg.bytes()
                    if len(raw_bytes) == 3:
                        self.player.write_short(raw_bytes[0], raw_bytes[1], raw_bytes[2])
                    elif len(raw_bytes) == 2:
                        self.player.write_short(raw_bytes[0], raw_bytes[1])
                    elif len(raw_bytes) == 1:
                        self.player.write_short(raw_bytes[0])

        except Exception as e:
            # Gunakan root.after untuk menampilkan pop up error dari dalam thread
            self.root.after(0, lambda: messagebox.showerror("Error", f"Terjadi kesalahan:\n{e}"))
        finally:
            self.cleanup_playback()

    def stop_playback(self):
        """Memicu penghentian lagu"""
        self.is_playing = False

    def cleanup_playback(self):
        """Menghentikan nada nyangkut TANPA menutup koneksi port"""
        self.is_playing = False 
        
        if self.player:
            try:
                # Hanya matikan suaranya saja (All Notes Off)
                for ch in range(16):
                    self.player.write_short(0xB0 + ch, 123, 0)
            except Exception as e:
                print(f"Error mematikan suara: {e}")

        # Kembalikan tampilan GUI ke awal
        self.root.after(0, lambda: self.btn_play.config(state="normal"))
        self.root.after(0, lambda: self.btn_stop.config(state="disabled"))

    def on_closing(self):
        """Menutup port secara permanen saat aplikasi disilang (X)"""
        self.is_playing = False
        time.sleep(0.1) # Beri waktu thread berhenti sebentar
        
        if self.player:
            try:
                for ch in range(16):
                    self.player.write_short(0xB0 + ch, 123, 0)
                self.player.close()
            except:
                pass
            
        pygame.midi.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiPlayerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing) # Tangkap event saat window ditutup
    root.mainloop()