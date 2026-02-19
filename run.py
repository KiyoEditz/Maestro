import mido
import time
from pynput.keyboard import Controller

# --- SETTING ---
NAMA_FILE_MIDI = 'midi_雑魚.mid'  # ganti dengan nama midi
NADA_MIDI_AWAL_UNTUK_A = 60   # Middle C = 60

# --- KEYS MAPPING (DON'T CHANGE IF YOU DON'T KNOW) ---
NOTE_TO_KEY_MAP = {
    0: 'a',   # DO
    1: 'w',   # DO#
    2: 's',   # RE
    3: 'e',   # RE#
    4: 'd',   # MI
    5: 'f',   # FA
    6: 't',   # FA#
    7: 'g',   # SOL
    8: 'y',   # SOL#
    9: 'h',   # LA
    10: 'u',  # LA#
    11: 'j',  # SI
}

KEY_OCTAVE_UP = 'x'
KEY_OCTAVE_DOWN = 'z'

# Inisialisasi controller keyboard
keyboard = Controller()

def main():
    """
    MAIN FUNCTION TO READ FILE, PLAY IT AND HANDLE OCTAVE CHANGES
    """
    try:
        midi_file = mido.MidiFile(NAMA_FILE_MIDI)
        print(f"✅ Berhasil memuat file MIDI: {NAMA_FILE_MIDI}")
    except FileNotFoundError:
        print(f"❌ ERROR: File MIDI tidak ditemukan di '{NAMA_FILE_MIDI}'")
        return
    except Exception as e:
        print(f"❌ Terjadi kesalahan saat memuat file MIDI: {e}")
        return

    print("\nPERSIAPAN SEBELUM MEMULAI:")
    print("1. Buka Perfect Piano di handphone Anda.")
    print("2. Jalankan scrcpy dan pastikan layar handphone tampil.")
    print("3. Atur oktaf di Perfect Piano ke posisi tengah (biasanya default).")
    print("4. KLIK JENDELA SCRCPY untuk membuatnya menjadi jendela aktif.")

    for i in range(5, 0, -1):
        print(f"Memulai dalam {i} detik...", end='\r')
        time.sleep(1)

    print("\n🎶 Memainkan lagu...")

    # Variabel untuk melacak oktaf saat ini di aplikasi
    # Kita asumsikan oktaf awal di aplikasi sesuai dengan NADA_MIDI_AWAL_UNTUK_A
    current_app_octave_start_note = NADA_MIDI_AWAL_UNTUK_A

    try:
        for msg in midi_file.play():
            if msg.type == 'note_on' and msg.velocity > 0:
                note_midi = msg.note

                # --- LOGIKA PENYESUAIAN OKTAF ---
                while note_midi >= current_app_octave_start_note + 12:
                    # Nada terlalu tinggi, naikkan oktaf
                    print("Oktaf naik -> Tekan 'x'")
                    keyboard.press(KEY_OCTAVE_UP)
                    time.sleep(0.05)
                    keyboard.release(KEY_OCTAVE_UP)
                    current_app_octave_start_note += 12
                    time.sleep(0.1) # Beri jeda agar aplikasi tidak lag

                while note_midi < current_app_octave_start_note:
                    # Nada terlalu rendah, turunkan oktaf
                    print("Oktaf turun <- Tekan 'z'")
                    keyboard.press(KEY_OCTAVE_DOWN)
                    time.sleep(0.05)
                    keyboard.release(KEY_OCTAVE_DOWN)
                    current_app_octave_start_note -= 12
                    time.sleep(0.1) # Beri jeda agar aplikasi tidak lag
                
                # --- MEMAINKAN NADA ---
                # Cari tombol yang sesuai setelah oktaf benar
                note_pitch_class = note_midi % 12
                if note_pitch_class in NOTE_TO_KEY_MAP:
                    key_to_press = NOTE_TO_KEY_MAP[note_pitch_class]
                    print(f"Nada: {note_midi} -> Oktaf: {current_app_octave_start_note // 12} -> Tombol: '{key_to_press}'")
                    
                    keyboard.press(key_to_press)
                    # Jeda pelepasan bisa disesuaikan, 0.05 detik biasanya cukup
                    time.sleep(0.05)
                    keyboard.release(key_to_press)
                else:
                    # Seharusnya tidak terjadi jika mapping lengkap
                    print(f"Nada: {note_midi} -> Tidak ada mapping. Dilewati.")

    except KeyboardInterrupt:
        print("\nPlayback dihentikan oleh pengguna.")
    except Exception as e:
        print(f"\nTerjadi kesalahan saat playback: {e}")

    print("✅ Playback selesai.")

if __name__ == "__main__":
    main()