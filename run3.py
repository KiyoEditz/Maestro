import mido
import pygame
import pygame.midi
import time
import os

def main():
    # 1. Inisialisasi Pygame MIDI
    pygame.init()
    pygame.midi.init()

    # 2. Tampilkan daftar Port MIDI Output
    print("=== Mencari Perangkat MIDI ===")
    
    count = pygame.midi.get_count()
    outputs = []
    
    if count == 0:
        print("Tidak ada perangkat MIDI terdeteksi!")
        return

    print("Daftar Port ditemukan:")
    for i in range(count):
        info = pygame.midi.get_device_info(i)
        if info[3] == 1:
            name = info[1].decode('utf-8')
            print(f"{i}: {name}")
            outputs.append(i)

    if not outputs:
        print("Tidak ada Port Output ditemukan.")
        return

    # 3. Minta user memilih Port
    try:
        selection_input = input("\nMasukkan NOMOR port HP Anda: ")
        selection = int(selection_input)
        if selection not in outputs:
            print("Nomor tidak valid.")
            return
    except ValueError:
        print("Harap masukkan angka.")
        return

    # 4. Masukkan nama file MIDI
    default_file = "REAoharu.mid"
    user_file = input(f"\nMasukkan nama file MIDI (Default: {default_file}): ")
    file_midi = default_file if user_file.strip() == "" else user_file

    if not os.path.exists(file_midi):
        print(f"ERROR: File '{file_midi}' tidak ditemukan!")
        return

    # 5. Minta user mengatur KECEPATAN
    print("\n--- Pengaturan Kecepatan ---")
    speed_input = input("Masukkan kecepatan (Default 1.0, misal: 1.5 untuk cepat): ")
    try:
        speed = float(speed_input) if speed_input.strip() != "" else 1.0
        speed = max(0.1, speed) # Cegah angka minus atau 0
    except ValueError:
        speed = 1.0

    # 6. Minta user mengatur VOLUME (FITUR BARU)
    print("\n--- Pengaturan Volume ---")
    print("1.0 = Normal | 0.5 = Lebih pelan | 2.0 = Lebih keras")
    volume_input = input("Masukkan pengali volume (Default 1.0): ")
    try:
        volume_scale = float(volume_input) if volume_input.strip() != "" else 1.0
        volume_scale = max(0.0, volume_scale) # Cegah volume minus
    except ValueError:
        volume_scale = 1.0

    try:
        player = pygame.midi.Output(selection)
        mid = mido.MidiFile(file_midi)
        
        print(f"\nMemutar '{file_midi}' | Kecepatan: {speed}x | Volume: {volume_scale}x")
        print("(Tekan Ctrl+C untuk Stop)")
        
        for msg in mid:
            time.sleep(msg.time / speed)
            
            if not msg.is_meta:
                
                # --- PROSES MODIFIKASI VOLUME ---
                # Cek apakah pesan ini adalah perintah menekan nada (note_on) 
                # dan pastikan velocity > 0 (karena velocity 0 biasanya berarti Note Off)
                if msg.type == 'note_on' and msg.velocity > 0:
                    
                    # Kalikan velocity asli dengan pengali volume kita
                    new_velocity = int(msg.velocity * volume_scale)
                    
                    # Pastikan nilai MIDI tidak tembus batas maksimal (127) atau minimal (1)
                    new_velocity = max(1, min(127, new_velocity))
                    
                    # Terapkan volume baru ke dalam pesan
                    msg.velocity = new_velocity
                # --------------------------------
                
                # Ubah pesan yang sudah dimodifikasi kembali ke raw bytes
                raw_bytes = msg.bytes()
                
                if len(raw_bytes) == 3:
                    player.write_short(raw_bytes[0], raw_bytes[1], raw_bytes[2])
                elif len(raw_bytes) == 2:
                    player.write_short(raw_bytes[0], raw_bytes[1])
                elif len(raw_bytes) == 1:
                    player.write_short(raw_bytes[0])

        print("\nSelesai memutar lagu.")

    except KeyboardInterrupt:
        print("\nBerhenti paksa.")
        if 'player' in locals():
            for ch in range(16):
                player.write_short(0xB0 + ch, 123, 0)
                
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        if 'player' in locals():
            del player
        pygame.midi.quit()

if __name__ == "__main__":
    main()