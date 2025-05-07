"""
Basically had LLM generate this from ColdSauce's VAG to WAV converter
https://github.com/ColdSauce/psxsdk/blob/master/tools/vag2wav.c
"""
import struct
import wave

# Constants for VAG and WAV files
SAMPLE_RATE = 22050  # Sample rate for PlayStation ADPCM (VAG)
CHANNELS = 1         # Mono audio
BITS_PER_SAMPLE = 16 # WAV files typically use 16-bit PCM
BLOCK_SIZE = 24      # Each block contains 16 samples and 4 coefficients

# Coefficients for the ADPCM decoding
ADPCM_COEFFICIENTS = [
    (0, 0),
    (60, 0),
    (115, -52),
    (98, -55),
    (122, -60)
]

def adpcm_decode(vag_data):
    pcm_data = []
    s_1, s_2 = 0.0, 0.0
    
    for i in range(0, len(vag_data), BLOCK_SIZE):
        block = vag_data[i:i + BLOCK_SIZE]
        
        # First byte contains the shift factor and predictor number
        predictor_number = (block[0] >> 4) & 0x0F
        shift_factor = block[0] & 0x0F
        
        # Coefficients for the ADPCM decoding
        f1, f2 = ADPCM_COEFFICIENTS[predictor_number]
        
        # Decode each sample in the block
        for j in range(4, BLOCK_SIZE):
            nibble = (block[j // 2] >> ((j % 2) * 4)) & 0x0F
            
            # Sign-extend the 4-bit nibble to a 16-bit signed integer
            if nibble >= 8:
                nibble -= 16
            
            # Calculate the predicted sample value
            predicted_sample = int((f1 * s_1 + f2 * s_2) / 64)
            
            # Add the decoded difference to the predicted sample
            differential_sample = (nibble << shift_factor) + predicted_sample
            
            # Clamp the sample to 16-bit signed integer range
            if differential_sample > 32767:
                differential_sample = 32767
            elif differential_sample < -32768:
                differential_sample = -32768
            
            # Add the sample to the PCM data list
            pcm_data.append(differential_sample)
            
            # Update the previous two samples for the next iteration
            s_2, s_1 = s_1, differential_sample
    
    return pcm_data

def vag_to_wav(vag_file_path, wav_file_path):
    with open(vag_file_path, "rb") as vag_file:
        # Read the VAG header
        vag_name = vag_file.read(4)
        
        if vag_name != b'VAGp':
            print(f"{vag_file_path} is not in VAG format. Aborting.")
            return -1
        
        # Skip the version and other metadata (for simplicity, we assume known structure)
        vag_file.seek(12)
        data_size = struct.unpack(">I", vag_file.read(4))[0]
        
        print(f"Data Size: {data_size} bytes")
        
        # Read the VAG audio data
        vag_data = vag_file.read(data_size - 16)  # Skip header and metadata
        
        # Decode ADPCM to PCM
        pcm_data = adpcm_decode(vag_data)
        
        # Write the WAV file
        with wave.open(wav_file_path, "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(BITS_PER_SAMPLE // 8)
            wav_file.setframerate(SAMPLE_RATE)
            
            # Convert PCM data to bytes and write to the WAV file
            pcm_bytes = struct.pack(f'>{len(pcm_data)}h', *pcm_data)
            wav_file.writeframes(pcm_bytes)
    
    print(f"Converted {vag_file_path} to {wav_file_path}")
    return 0

# Example usage
if __name__ == "__main__":
    vag_file_path = "workingFiles/vag-examples/00042.vag"
    wav_file_path = "workingFiles/vag-examples/00042.wav"
    vag_to_wav(vag_file_path, wav_file_path)
