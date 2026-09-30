import re
import sys
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)


def sanitize_filename(filename):
    """
    Convert a YouTube title into a filesystem-safe filename.
    """
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()

    # Prevent extremely long filenames
    filename = filename[:150]

    return filename


def download_audio(url):
    print("=" * 50)
    print("       YOUTUBE AUDIO DOWNLOADER")
    print("=" * 50)

    # First get the video title
    title_command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--print",
        "%(title)s",
        "--skip-download",
        url
    ]

    result = subprocess.run(
        title_command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError("Could not retrieve YouTube video information.")

    title = result.stdout.strip()
    safe_title = sanitize_filename(title)

    output_file = TEMP_DIR / f"{safe_title}.wav"

    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "-f",
        "bestaudio/best",
        "-x",
        "--audio-format",
        "wav",
        "-o",
        str(output_file),
        url
    ]

    print(f"\nVideo: {title}")
    print(f"Output: {output_file.name}")
    print("\nDownloading audio...\n")

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError("YouTube download failed.")

    if not output_file.exists():
        raise FileNotFoundError(
            f"Downloaded audio file was not found: {output_file}"
        )

    print("\nDownload complete:")
    print(output_file)

    return output_file


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage:")
        print('python youtube_downloader.py "<youtube_url>"')
        sys.exit(1)

    try:
        download_audio(sys.argv[1])
    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)