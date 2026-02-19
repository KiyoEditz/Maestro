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
        # info format: (interf, name, input, output, opened)
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

    # 4. Masukkan nama file MIDI (PERBAIKAN DI SINI)
    # Default ke REAoharu.mid jika user langsung tekan Enter
    default_file = "REAoharu.mid"
    user_file = input(f"Masukkan nama file MIDI (Default: {default_file}): ")
    
    # Jika user input kosong, pakai default
    if user_file.strip() == "":
        file_midi = default_file
    else:
        file_midi = user_file

    # Cek apakah file benar-benar ada sebelum lanjut
    if not os.path.exists(file_midi):
        print(f"ERROR: File '{file_midi}' tidak ditemukan di folder ini!")
        print("Pastikan nama file benar dan berakhiran .mid")
        return

    try:
        # Buka koneksi ke Port MIDI HP
        player = pygame.midi.Output(selection)
        
        mid = mido.MidiFile(file_midi)
        
        print(f"\nMemutar '{file_midi}'... (Tekan Ctrl+C untuk Stop)")
        
        # Loop membaca setiap pesan dalam file MIDI
        for msg in mid.play():
            
            # Konversi pesan Mido ke format raw MIDI untuk Pygame
            # PERBAIKAN LOGIKA: Menangani semua tipe pesan MIDI (Pitch bend, control change, dll)
            
            if not msg.is_meta: # Abaikan pesan meta (seperti lirik/tempo text)
                raw_bytes = msg.bytes()
                
                # Pygame midi write_short hanya menerima maksimal 3 byte
                if len(raw_bytes) == 3:
                    player.write_short(raw_bytes[0], raw_bytes[1], raw_bytes[2])
                elif len(raw_bytes) == 2:
                    player.write_short(raw_bytes[0], raw_bytes[1])
                elif len(raw_bytes) == 1:
                    player.write_short(raw_bytes[0])

        print("\nSelesai memutar lagu.")

    except KeyboardInterrupt:
        print("\nBerhenti paksa.")
        # Panic button: matikan semua suara
        if 'player' in locals():
            # Mengirim All Notes Off ke 16 channel (agar tidak ada suara 'nyangkut')
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