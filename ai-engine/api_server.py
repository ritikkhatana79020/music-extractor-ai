import re
import sys
import uuid
import subprocess
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage for V1
jobs = {}


class ExtractRequest(BaseModel):
    url: str


def update_job(job_id, status, progress, message, **extra):
    jobs[job_id].update(
        {
            "status": status,
            "progress": progress,
            "message": message,
            **extra,
        }
    )


def process_extraction(job_id, url):
    try:
        update_job(
            job_id,
            "starting",
            5,
            "Starting extraction...",
        )

        process = subprocess.Popen(
            [
                sys.executable,
                str(BASE_DIR / "app.py"),
                url,
            ],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_file = None

        for line in process.stdout:
            line = line.strip()

            print(line)

            # YouTube download
            if "Downloading audio" in line:
                update_job(
                    job_id,
                    "downloading",
                    15,
                    "Downloading audio...",
                )

            # Download completed
            elif "Download complete" in line:
                update_job(
                    job_id,
                    "downloaded",
                    30,
                    "Download complete.",
                )

            # Demucs
            elif "MUSIC EXTRACTOR" in line:
                update_job(
                    job_id,
                    "separating",
                    40,
                    "AI is separating vocals from music...",
                )

            # Demucs progress
            match = re.search(
                r"(\d+)%\|",
                line,
            )

            if match:
                percentage = int(match.group(1))

                # Map Demucs 0-100 -> overall 40-85
                overall = 40 + int(
                    percentage * 0.45
                )

                update_job(
                    job_id,
                    "separating",
                    overall,
                    f"Separating vocals... {percentage}%",
                )

            # FFmpeg
            elif "ffmpeg" in line.lower():
                update_job(
                    job_id,
                    "converting",
                    90,
                    "Creating MP3...",
                )

            # Find final output
            match = re.search(
                r"Background music:\s*(.+)",
                line,
            )

            if match:
                output_file = Path(
                    match.group(1).strip()
                )

        return_code = process.wait()

        print(
            f"Extraction process finished with exit code: {return_code}"
        )

        if return_code != 0:
            raise RuntimeError(
                f"Music extraction failed. "
                f"Process exited with code {return_code}. "
                f"Check Railway deployment logs for the detailed error."
            )

        if not output_file or not output_file.exists():
            # Fallback: find newest MP3
            files = sorted(
                OUTPUT_DIR.glob(
                    "*_background_music.mp3"
                ),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

            if files:
                output_file = files[0]

        if not output_file:
            raise RuntimeError(
                "Output music file was not found."
            )

        update_job(
            job_id,
            "completed",
            100,
            "Extraction complete.",
            filename=output_file.name,
            download_url=f"/download/{output_file.name}",
        )

    except Exception as error:
        print(
            f"Job {job_id} failed: {error}"
        )

        update_job(
            job_id,
            "failed",
            0,
            str(error),
        )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "music-extractor-ai",
    }


@app.post("/extract")
def extract(request: ExtractRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="YouTube URL is required.",
        )

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Job created.",
    }

    thread = threading.Thread(
        target=process_extraction,
        args=(job_id, url),
        daemon=True,
    )

    thread.start()

    return {
        "job_id": job_id,
        "status": "queued",
    }


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    return {
        "job_id": job_id,
        **job,
    }


@app.get("/download/{filename}")
def download(filename: str):
    output_file = OUTPUT_DIR / filename

    if not output_file.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return FileResponse(
        output_file,
        media_type="audio/mpeg",
        filename=output_file.name,
    )