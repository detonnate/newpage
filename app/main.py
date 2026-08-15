from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.rag_service import LocalRAG

app = FastAPI(title="Newpage Docs Q&A", version="1.0.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
rag = LocalRAG(docs_dir="sample_docs")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def healthcheck():
    return {
        "status": "ok",
        "documents": len(rag.documents),
        "chunks": len(rag.chunks),
        "ai_provider": rag.ai_provider,
        "model": rag.gemini_model if rag.llm else None,
    }


@app.get("/api/documents")
async def list_documents():
    return {"documents": [{"name": doc["name"], "path": doc["path"]} for doc in rag.documents]}


@app.get("/api/demo-documents")
async def list_demo_documents():
    if not rag.docs_dir.exists():
        return {"documents": []}
    return {
        "documents": [
            {"name": file.name}
            for file in sorted(rag.docs_dir.iterdir())
            if file.is_file()
        ]
    }


@app.post("/api/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    added = []
    uploaded_docs = []
    for file in files:
        if not file.filename:
            continue
        file_bytes = await file.read()
        if file.filename.lower().endswith(".pdf"):
            try:
                from io import BytesIO
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(file_bytes))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                text = ""
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
        if not text.strip():
            continue
        uploaded_docs.append({"name": file.filename, "text": text})
        added.append(file.filename)
    if uploaded_docs:
        rag.replace_documents(uploaded_docs)
    return {"status": "ok", "added": added}


@app.post("/api/query")
async def query(payload: dict):
    question = (payload or {}).get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="A question is required.")
    result = rag.answer(question)
    return result


@app.post("/api/brief")
async def generate_brief():
    result = rag.generate_brief()
    if not result:
        detail = rag.ai_error_message() or "Gemini AI mode is unavailable. Set GEMINI_API_KEY or GOOGLE_API_KEY and use a supported Gemini model."
        raise HTTPException(status_code=503, detail=detail)
    return result


@app.post("/api/load-demo")
async def load_demo(payload: dict | None = None):
    rag.documents = []
    rag.chunks = []
    selected_documents = (payload or {}).get("documents")
    rag._load_default_documents(selected_documents)
    return {"status": "ok", "documents": [doc["name"] for doc in rag.documents]}
