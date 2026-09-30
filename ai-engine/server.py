from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Music Extractor AI",
    version="1.0.0"
)


class ExtractRequest(BaseModel):
    url: str


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Music Extractor AI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 80px auto;
                padding: 20px;
                background: #f5f5f5;
            }

            .container {
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 5px 25px rgba(0,0,0,0.08);
            }

            h1 {
                margin-bottom: 10px;
            }

            input {
                width: 100%;
                padding: 14px;
                margin-top: 20px;
                box-sizing: border-box;
                border: 1px solid #ccc;
                border-radius: 8px;
                font-size: 16px;
            }

            button {
                margin-top: 15px;
                padding: 14px 25px;
                border: none;
                border-radius: 8px;
                background: #111;
                color: white;
                font-size: 16px;
                cursor: pointer;
            }

            button:disabled {
                background: #999;
            }

            #status {
                margin-top: 25px;
                white-space: pre-line;
            }

            .success {
                color: green;
            }

            .error {
                color: red;
            }
        </style>
    </head>

    <body>

        <div class="container">

            <h1>🎵 Music Extractor AI</h1>

            <p>
                Extract background music from a video.
            </p>

            <input
                id="url"
                type="text"
                placeholder="Paste YouTube URL here..."
            />

            <button id="extractBtn" onclick="extractMusic()">
                Extract Music
            </button>

            <div id="status"></div>

        </div>

        <script>

            async function extractMusic() {

                const url = document.getElementById("url").value;
                const button = document.getElementById("extractBtn");
                const status = document.getElementById("status");

                if (!url) {
                    status.innerHTML =
                        '<span class="error">Please enter a YouTube URL.</span>';
                    return;
                }

                button.disabled = true;

                status.innerText =
                    "⏳ Processing...\\n\\n" +
                    "This may take a little while.";

                try {

                    const response = await fetch("/extract", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            url: url
                        })
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(data.detail || "Extraction failed.");
                    }

                    status.innerHTML =
                        '<span class="success">' +
                        '✅ Extraction complete!<br><br>' +
                        '🎵 ' + data.filename +
                        '<br><br>' +
                        '<a href="' + data.download_url + '" download>' +
                        'Download Background Music' +
                        '</a>' +
                        '</span>';

                } catch (error) {

                    status.innerHTML =
                        '<span class="error">' +
                        '❌ ' + error.message +
                        '</span>';

                } finally {

                    button.disabled = false;

                }
            }

        </script>

    </body>
    </html>
    """


@app.post("/extract")
def extract(request: ExtractRequest):

    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="YouTube URL is required."
        )

    try:

        # Run our existing application.
        result = subprocess.run(
            [
                sys.executable,
                "app.py",
                url
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr or result.stdout or "Extraction failed."
            )

        output_dir = BASE_DIR / "output"

        files = sorted(
            output_dir.glob("*_background_music.mp3"),
            key=lambda file: file.stat().st_mtime,
            reverse=True
        )

        if not files:
            raise RuntimeError(
                "Extraction completed but output file was not found."
            )

        output_file = files[0]

        return {
            "success": True,
            "filename": output_file.name,
            "download_url": f"/download/{output_file.name}"
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


from fastapi.responses import FileResponse


@app.get("/download/{filename}")
def download(filename: str):

    output_file = BASE_DIR / "output" / filename

    if not output_file.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found."
        )

    return FileResponse(
        output_file,
        media_type="audio/mpeg",
        filename=output_file.name
    )