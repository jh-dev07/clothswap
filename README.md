# CoverSwap clothing swap: Android Java + Python API

Separate clothing-swap application; the previously delivered offline face app is unchanged.
Frontend: Java, Gradle 6.1.1, AGP 4.0.2, JDK8, compile/target SDK29, Build Tools29.0.3, minSDK24.
Backend: original CoverSwap commit 99c43fd773a567a56212b2efdbc934b158215d48.

## Server setup

Use Python3.12 and an NVIDIA CUDA environment. The original project recommends 8GB VRAM for CatVTON.
Actual generation latency and memory requirements have not been measured for this service.

From server/:

    python setup_backend.py
    python -m venv .venv

Activate the virtual environment (Windows: .venv\Scripts\activate; Linux: source .venv/bin/activate), then:

    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
    pip install -r backend/requirements.txt
    pip install -r requirements.txt

Choose a PyTorch CUDA wheel appropriate for the server driver if cu128 is unsuitable.
Copy the ORIGINAL PC project's complete weights/ and third_party/CatVTON/ directories into
server/backend/weights/ and server/backend/third_party/CatVTON/ respectively. Reuse the working
PC installation to retain its exact model files and CatVTON code. Models are not in this ZIP.
The repository model downloader is also available in backend/scripts/download_models.py;
it fetches models for other features too. Existing PC weights avoid that unnecessary download.

The backend root must be on PYTHONPATH before starting the API:

Linux:

    export PYTHONPATH="$PWD/backend"
    uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1

Windows PowerShell:

    $env:PYTHONPATH = "$PWD\backend"
    uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1

Run these commands from server/. Health: GET /health. Interactive API documentation: /docs.
Models load lazily during processing; health reports process readiness, not model validation.
Use exactly one worker for one GPU. A lock serializes detector/generation work; this prototype
uses synchronous long-running requests and has no persistent queue or recovery after disconnect.

## Android

Open android/ in Android Studio4.0.2 or another IDE supporting AGP4.0.2. Set Gradle JDK8.
Install SDK29 and Build Tools29.0.3. Run gradlew.bat assembleDebug (Windows) or ./gradlew assembleDebug.
No ML weights are needed in Android; all AI runs in the service.

Enter the server URL at the top of the app. Android Studio emulator: http://10.0.2.2:8000.
Physical phones: use the server's reachable LAN address, such as http://192.168.1.20:8000.
LDPlayer host addressing depends on its network configuration; use an address reachable from it.
Allow the API port through the server firewall on your trusted network.

Select person photo and garment photo, detect people, select a numbered person from the list,
choose category/settings, then swap. Boxes are shown as coordinates in the selection list.
The default is 30 steps, seed42, guidance4.0, 576x768 processing. High resolution uses 768x1024.
The server composites the generated clothing back into the full-size photo using upstream logic.
Save exports PNG through Android's document picker. Local image uploads are limited to12MB;
server images are limited to16 megapixels. Detection and swap use the same unchanged target image.

The app transmits photos to the configured service. Cleartext HTTP is enabled for LAN development.
There is no authentication in this prototype: deploy it on a trusted private network only.
Before public hosting add HTTPS, authentication, request-body limits at a reverse proxy, and a
bounded job queue. Base64 JSON expands transfer size; it was chosen to keep the client dependency-free.
The app allows up to15 minutes for generation. These settings do not guarantee completion time.

## API

POST /detect: JSON {"photo":"BASE64_IMAGE"}
Returns {"people":[{"index":0,"label":"Person 1","box":[x1,y1,x2,y2]}]}.

POST /swap: JSON with photo, garment (both base64), person (zero-based index), category
(upper_body/lower_body/dress), steps (1–60), seed, guidance (0–10), high_resolution (boolean).
Returns {"image":"BASE64_PNG","mime":"image/png"}.
Errors use HTTP status codes and FastAPI JSON details. The same image is detected again for swap;
no person masks or photos are stored between requests. No upload history is persisted by this API.

## Validation and limitations

Python sources passed syntax compilation. Android Java source passed javac against Android SDK29
with JDK8. No APK build, Android installation test, HTTP integration test, or GPU model inference
was executed for this delivery. Treat it as an implementation ready for integration testing, not
a verified production deployment. Upstream Python dependencies are not all version-pinned, so use
an existing working PC virtual environment where possible and freeze it after validating deployment.
The server imports CoverSwapPipeline unchanged, which also imports face-related Python packages;
installing the upstream requirements is intentional even though only clothing endpoints are exposed.

Original model and application licensing restrictions still apply. Upstream README permits personal/
offline application use; pretrained models have separate terms. See the original repository and
CatVTON upstream terms before commercial deployment.
