const API_URL = "http://127.0.0.1:8000";

const urlInput = document.getElementById("youtubeUrl");
const extractButton = document.getElementById("extractButton");
const inputError = document.getElementById("inputError");

const progressSection = document.getElementById("progressSection");
const progressBar = document.getElementById("progressBar");
const progressPercent = document.getElementById("progressPercent");
const statusText = document.getElementById("statusText");
const progressDetail = document.getElementById("progressDetail");

const resultSection = document.getElementById("resultSection");
const resultFilename = document.getElementById("resultFilename");
const audioPlayer = document.getElementById("audioPlayer");
const downloadButton = document.getElementById("downloadButton");

let pollTimer = null;

extractButton.addEventListener("click", extractMusic);

urlInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter") {
        extractMusic();
    }

});

function showError(message) {

    inputError.textContent = message;

    inputError.classList.remove("hidden");

}

function clearError() {

    inputError.textContent = "";

    inputError.classList.add("hidden");

}

function resetResult() {

    resultSection.classList.add("hidden");

    audioPlayer.pause();

    audioPlayer.removeAttribute("src");

    downloadButton.removeAttribute("href");

}

async function extractMusic() {

    const url = urlInput.value.trim();

    clearError();

    resetResult();

    if (!url) {

        showError(
            "Please paste a YouTube URL."
        );

        return;
    }

    if (
        !url.includes("youtube.com/") &&
        !url.includes("youtu.be/")
    ) {

        showError(
            "Please enter a valid YouTube URL."
        );

        return;
    }

    extractButton.disabled = true;

    extractButton.textContent = "Starting...";

    progressSection.classList.remove("hidden");

    setProgress(
        5,
        "Starting extraction...",
        "Creating your extraction job."
    );

    try {

        const response = await fetch(
            `${API_URL}/extract`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    url: url
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to start extraction."
            );

        }

        await pollStatus(data.job_id);

    } catch (error) {

        setProgress(
            0,
            "Extraction failed",
            error.message
        );

        showError(error.message);

        extractButton.disabled = false;

        extractButton.textContent =
            "Extract Music";

    }

}

async function pollStatus(jobId) {

    clearTimeout(pollTimer);

    try {

        const response = await fetch(
            `${API_URL}/status/${jobId}`
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to check job status."
            );

        }

        setProgress(
            data.progress || 0,

            humanizeStatus(
                data.status,
                data.message
            ),

            data.message || ""
        );

        if (data.status === "completed") {

            showCompleted(data);

            return;

        }

        if (data.status === "failed") {

            throw new Error(
                data.message ||
                "Music extraction failed."
            );

        }

        pollTimer = setTimeout(
            () => pollStatus(jobId),
            1000
        );

    } catch (error) {

        setProgress(
            0,
            "Extraction failed",
            error.message
        );

        showError(error.message);

        extractButton.disabled = false;

        extractButton.textContent =
            "Extract Music";

    }

}

function setProgress(
    progress,
    status,
    detail
) {

    const value =
        Math.max(
            0,
            Math.min(
                100,
                progress
            )
        );

    progressBar.style.width =
        `${value}%`;

    progressPercent.textContent =
        `${value}%`;

    statusText.textContent =
        status;

    progressDetail.textContent =
        detail;

}

function humanizeStatus(
    status,
    message
) {

    const labels = {

        queued:
            "Queued",

        starting:
            "Starting",

        downloading:
            "Downloading audio",

        downloaded:
            "Audio downloaded",

        separating:
            "Separating vocals",

        converting:
            "Creating MP3",

        completed:
            "Extraction complete"

    };

    return (
        labels[status] ||
        message ||
        "Processing..."
    );

}

function showCompleted(data) {

    setProgress(
        100,
        "Extraction complete!",
        "Your background music is ready."
    );

    resultFilename.textContent =
        data.filename ||
        "background_music.mp3";

    const downloadUrl =
        `${API_URL}${data.download_url}`;

    audioPlayer.src =
        downloadUrl;

    downloadButton.href =
        downloadUrl;

    downloadButton.download =
        data.filename ||
        "background_music.mp3";

    resultSection.classList.remove(
        "hidden"
    );

    extractButton.disabled = false;

    extractButton.textContent =
        "Extract Again";

}
