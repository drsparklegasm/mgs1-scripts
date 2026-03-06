import ffmpeg
import subprocess, os, tempfile

# Platform-safe temp directory (e.g. /tmp on Unix, C:\Users\...\AppData\Local\Temp on Windows)
_tempDir = tempfile.gettempdir()


def splitVagFile(filename, leftChanFilename, rightChanFilename):
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
        .run(quiet=True)
    )


def convert_stereo_vag_to_wav(left_vag, right_vag, output_wav):
    try:
        left = ffmpeg.input(left_vag, f='vag')
        right = ffmpeg.input(right_vag, f='vag')
        (
            ffmpeg
            .filter([left, right], 'join', inputs=2, channel_layout='stereo')
            .output(output_wav, acodec='pcm_s16le')
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as e:
        print('FFmpeg error:', e.stderr.decode())


def play_with_ffplay(wav_file):
    """Legacy CLI helper — kept for standalone script use only."""
    try:
        subprocess.run(['ffplay', wav_file, '-nodisp', '-autoexit'],
                       check=True)
    except subprocess.SubprocessError as e:
        print(e)


def playVagFile(filename: str, convertOnly: bool = False) -> int:
    """
    Convert (and optionally play) a VAG file.

    When convertOnly=True the WAV is written to the temp directory and this
    function returns 0.  The caller is responsible for playing it.
    When convertOnly=False the WAV is also played via ffplay (CLI use only).

    Returns 0 on success, -1 on error.
    """
    temp_wav  = os.path.join(_tempDir, "mgs_vox_temp.wav")
    temp_l    = os.path.join(_tempDir, "mgs_vox_temp_L.vag")
    temp_r    = os.path.join(_tempDir, "mgs_vox_temp_R.vag")

    with open(filename, 'rb') as f:
        magic = f.read(4)

    if magic == b'VAGp':
        convert_vag_to_wav(filename, temp_wav)
    elif magic == b'VAGi':
        splitVagFile(filename, temp_l, temp_r)
        convert_stereo_vag_to_wav(temp_l, temp_r, temp_wav)
    else:
        print(f'ERROR: Not a valid VAG file. Magic: 0x{magic.hex()} / {magic}')
        return -1

    if not convertOnly:
        play_with_ffplay(temp_wav)

    return 0


def getTempWavPath() -> str:
    """Returns the path where playVagFile writes its output WAV."""
    return os.path.join(_tempDir, "mgs_vox_temp.wav")


def main():
    # TESTING AREA
    convert_stereo_vag_to_wav(
        "workingFiles/vag-examples/testLeft.vag",
        "workingFiles/vag-examples/testRight.vag",
        "workingFiles/vag-examples/newFile.wav"
    )
    play_with_ffplay("workingFiles/vag-examples/newFile.wav")


if __name__ == "__main__":
    main()
