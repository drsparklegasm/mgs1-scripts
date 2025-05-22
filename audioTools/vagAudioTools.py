import os, sys
import ffmpeg
import subprocess

filename = "workingFiles/vag-examples/test.vag"

def splitVagFile(filename, leftChanFilename, rightChanFilename):
    # Check if the file is a VAG file
    with open(filename, 'rb') as f:
        data = f.read()
    header = data[:0x40]
    oldSize = int.from_bytes(header[12:16], 'big')
    newSize = (oldSize // 2).to_bytes(4, 'big')

    leftChannelData = header[16:]
    rightChannelData = header[16:]

    for i in range(0x40, len(data), 0x2000):
        leftChannelData += data[i:i+0x1000]
        rightChannelData += data[i+0x1000:i+0x2000]

    with open(leftChanFilename, 'wb') as f:
        f.write(header[0:12])
        f.write(newSize)
        f.write(leftChannelData)

    with open(rightChanFilename, 'wb') as f:   
        f.write(header[0:12])
        f.write(newSize)
        f.write(rightChannelData)

def convert_vag_to_wav(input_path, output_path):
    (
        ffmpeg
        .input(input_path, f='vag')
        .output(output_path)
        .overwrite_output()
        .run()
    )

def convert_stereo_vag_to_wav(left_vag, right_vag, output_wav):
    # Set inputs separately to obects
    try:
        left = ffmpeg.input(left_vag, f='vag')
        right = ffmpeg.input(right_vag, f='vag')
        ffmpeg.filter([left, right], 'join', inputs=2, channel_layout='stereo').output(output_wav, acodec='pcm_s16le').overwrite_output().run()
    except ffmpeg.Error as e:
        print('FFmpeg error:', e.stderr.decode())


def play_with_ffplay(wav_file):
    try:
        print(subprocess.run(['ffplay', wav_file]))
    except subprocess.SubprocessError as e:
        print(e)


def main():
    # TESTING AREA 
    convert_stereo_vag_to_wav("workingFiles/vag-examples/testLeft.vag", "workingFiles/vag-examples/testRight.vag", "workingFiles/vag-examples/newFile.wav") 
    play_with_ffplay("workingFiles/vag-examples/newFile.wav")

if __name__ == "__main__":
    main()