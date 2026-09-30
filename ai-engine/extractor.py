import os
import re
import sys
import subprocess
from pathlib import Path

def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename[:150]


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
DEMUCS_DEVICE = os.getenv("DEMUCS_DEVICE", "cpu")

def run_command(command):
    print("\nRunning:")
    print(" ".join(command))
    print()

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError("Audio processing failed.")


def extract_music(input_file):
    input_file = Path(input_file).resolve()

    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_file}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

    print("=" * 50)
    print("       MUSIC EXTRACTOR")
    print("=" * 50)
    print(f"Input: {input_file.name}")

    # Demucs output directory
    demucs_output = TEMP_DIR / "separated"

    # Separate vocals from the rest of the audio
    run_command([
        sys.executable,
        "-m",
        "demucs",
        "--two-stems=vocals",
        "-d",
        DEMUCS_DEVICE,
        "-o",
        str(demucs_output),
        str(input_file)
    ])

    # Demucs creates:
    # separated/htdemucs/<filename>/no_vocals.wav
    model_dir = demucs_output / "htdemucs"
    track_dir = model_dir / input_file.stem
    music_file = track_dir / "no_vocals.wav"

    if not music_file.exists():
        raise FileNotFoundError(
            f"Demucs output was not found: {music_file}"
        )

    safe_name = sanitize_filename(input_file.stem)
    output_file = OUTPUT_DIR / f"{safe_name}_background_music.mp3"
    # Convert WAV to MP3
    run_command([
        "ffmpeg",
        "-y",
        "-i",
        str(music_file),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "320k",
        str(output_file)
    ])

    print("\n" + "=" * 50)
    print("       EXTRACTION COMPLETE")
    print("=" * 50)
    print(f"Background music: {output_file}")
    print()

    return output_file


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage:")
        print("python extractor.py <audio_or_video_file>")
        sys.exit(1)

    try:
        extract_music(sys.argv[1])
    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)
