import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from backend.ocr import extract_rows, list_models
from backend.excel_export import build_excel

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="Clinic OCR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = FRONTEND_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/style.css")
async def style():
    css_path = FRONTEND_DIR / "style.css"
    if not css_path.exists():
        return Response(content="", media_type="text/css")
    return Response(content=css_path.read_text(encoding="utf-8"), media_type="text/css")


@app.get("/api/models")
async def get_models(x_gemini_key: str = Header(default="")):
    if not x_gemini_key:
        raise HTTPException(status_code=400, detail="API key required.")
    try:
        models = list_models(x_gemini_key)
        if not models:
            raise HTTPException(status_code=404, detail="No generative models found for this API key.")
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/process")
async def process_images(
    files: List[UploadFile] = File(...),
    x_gemini_key: str = Header(default=""),
    x_gemini_model: str = Header(default="gemini-2.5-pro-preview-03-25"),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    all_rows: list[dict] = []
    errors: list[str] = []

    for upload in files:
        try:
            image_bytes = await upload.read()
            rows = extract_rows(image_bytes, api_key=x_gemini_key, model=x_gemini_model)
            all_rows.extend(rows)
        except Exception as e:
            errors.append(f"{upload.filename}: {str(e)}")

    return {
        "rows": all_rows,
        "total": len(all_rows),
        "errors": errors,
    }


class ExportRequest(BaseModel):
    rows: list[dict]


@app.post("/api/export")
async def export_excel(req: ExportRequest):
    if not req.rows:
        raise HTTPException(status_code=400, detail="No rows to export.")
    xlsx_bytes = build_excel(req.rows)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=clinic_records.xlsx"},
    )
