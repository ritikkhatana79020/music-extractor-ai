import sys
from pathlib import Path

from youtube_downloader import download_audio
from extractor import extract_music


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print('python app.py "<youtube_url>"')
        sys.exit(1)

    url = sys.argv[1]

    print("\n" + "=" * 60)
    print("              MUSIC EXTRACTOR AI")
    print("=" * 60)

    try:
        # Step 1: Download YouTube audio
        downloaded_file = download_audio(url)

        # Step 2: Separate background music
        output_file = extract_music(downloaded_file)

        print("\n" + "=" * 60)
        print("              🎵 COMPLETE")
        print("=" * 60)
        print(f"Background music:")
        print(output_file)

    except Exception as error:
        print("\n" + "=" * 60)
        print("              ❌ ERROR")
        print("=" * 60)
        print(error)

        sys.exit(1)


if __name__ == "__main__":
    main()