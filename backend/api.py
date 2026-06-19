from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from controller import analyze_uploaded_voice
from input_validator import analyze_voice_sample

app = FastAPI(title="VocaSense API")

# Define the origins (URLs) allowed to access your API
origins = [
    "http://localhost:5173",  # Web link from Vite
    "http://127.0.0.1:5173",  # Vite via loopback IP
    "http://127.0.0.1:5500",  # Common for VS Code Live Server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/data")
async def get_data():
    return {"message": "Success!"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/voice/validate")
async def validate_voice_sample(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="No audio file was uploaded.")

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()
    if "wav" not in content_type and not filename.endswith(".wav"):
        raise HTTPException(
            status_code=415,
            detail="Please upload WAV audio. The frontend converts recordings to WAV before calling this API.",
        )

    try:
        return analyze_voice_sample(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/voice/analyze")
async def analyze_voice(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="No audio file was uploaded.")

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()
    if "wav" not in content_type and not filename.endswith(".wav"):
        raise HTTPException(
            status_code=415,
            detail="Please upload WAV audio. The frontend converts recordings to WAV before calling this API.",
        )

    try:
        return analyze_uploaded_voice(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
