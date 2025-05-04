import struct

def vag2wav(vag_path, wav_path):
    # Open the VAG file
    with open(vag_path, "rb") as vag:
        # Read the header
        header = vag.read(48)
        if len(header) < 48:
            raise ValueError("Invalid VAG file: Header too short.")
        
        # Check the magic number (VAGp)
        magic_number = header[:4]
        if magic_number != b'VAGp':
            raise ValueError(f"Invalid VAG file: Magic number {magic_number} does not match 'VAGp'.")
        
        # Extract data_size
        data_size = struct.unpack(">I", header[12:16])[0]
        
        # Prepare the WAV header
        wav_header = (
            b'RIFF' + struct.pack("<I", 36 + data_size * 4) +  # ChunkSize
            b'WAVEfmt ' + struct.pack("<I", 16) +             # Subchunk1Size (PCM)
            struct.pack("<H", 1) +                            # AudioFormat (PCM = 1)
            struct.pack("<H", 1) +                            # NumChannels (mono)
            struct.pack("<I", 22050) +                         # SampleRate (default for VAG is 22050 Hz)
            struct.pack("<I", 44100) +                         # ByteRate (SampleRate * NumChannels * BitsPerSample / 8)
            struct.pack("<H", 2) +                            # BlockAlign (NumChannels * BitsPerSample / 8)
            struct.pack("<H", 16) +                           # BitsPerSample
            b'data' + struct.pack("<I", data_size * 4)         # Subchunk2Size
        )
        
        # Open the WAV file for writing
        with open(wav_path, "wb") as pcm:
            pcm.write(wav_header)
            
            # Predictors and shift factors
            f = [
                [0.0, 0.0],
                [60.0 / 64.0, 0.0],
                [115.0 / 64.0, -52.0 / 64.0],
                [98.0 / 64.0, -55.0 / 64.0],
                [122.0 / 64.0, -60.0 / 64.0]
            ]
            
            s_1 = 0.0
            s_2 = 0.0
            
            samples = [0] * 28
            
            # Process each block
            while vag.tell() < (data_size + 48):
                predict_nr = struct.unpack("B", vag.read(1))[0]
                shift_factor = predict_nr & 0xf
                predict_nr >>= 4
                flags = struct.unpack("B", vag.read(1))[0]  # flags
                
                if flags == 7:
                    break
                
                for i in range(0, 28, 2):
                    d = struct.unpack("B", vag.read(1))[0]
                    s = (d & 0xf) << 12
                    if s & 0x8000:
                        s |= 0xffff0000
                    samples[i] = int(s >> shift_factor)
                    
                    s = (d & 0xf0) << 8
                    if s & 0x80000:
                        s |= 0xffff0000
                    samples[i + 1] = int(s >> shift_factor)
                
                for i in range(28):
                    samples[i] += s_1 * f[predict_nr][0] + s_2 * f[predict_nr][1]
                    s_2 = s_1
                    s_1 = samples[i]
                    
                    # Clamp to 16-bit signed integer range
                    sample_value = max(-32768, min(32767, int(samples[i] + 0.5)))
                    pcm.write(struct.pack("<h", sample_value))

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python vag2wav.py <input.vag> <output.wav>")
        sys.exit(1)
    
    vag_path = sys.argv[1]
    wav_path = sys.argv[2]
    vag2wav(vag_path, wav_path)
