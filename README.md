# OPD Extractor — Clinic OCR

A web app that converts photos of handwritten veterinary clinic patient records (Thai + English) into a structured Excel file using Google Gemini Vision AI.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Pro-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## What it does

1. Upload one or more phone photos of handwritten OPD logbook pages
2. Gemini Vision AI reads each page and extracts all patient rows
3. Review and edit the extracted data in an interactive table
4. Download a formatted `.xlsx` Excel file

**Output columns:** `No. | Name | Pet | Type | OPD | Description | Price | Note`

---

## Screenshots

| Upload & Process | Extracted Table |
|---|---|
| Drag-drop photos, select model, click Process | Live editable table, download Excel |

---

## Requirements

- Python 3.10+
- [Google AI Studio API key](https://aistudio.google.com/app/apikey) (billing recommended for best models)

---

## Quick Start (Windows)

```bat
git clone https://github.com/mrkaqz/opdextractor.git
cd opdextractor
start.bat
```

`start.bat` will:
1. Create a Python virtual environment (`venv/`)
2. Install all dependencies
3. Start the server at `http://localhost:8000`

Open your browser to **http://localhost:8000**

---

## Quick Start (Docker)

```bash
docker compose up
```

Then open **http://localhost:8000**

Or with Docker only:
```bash
docker build -t opdextractor .
docker run -p 8000:8000 opdextractor
```

---

## Manual Setup

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Usage

1. Paste your **Gemini API key** in the field
2. Click **🔄 Load Models** to fetch available models for your account
3. Select a model — **`gemini-2.5-pro`** gives the best accuracy for Thai handwriting
4. Drag & drop your logbook photos (JPG/PNG, multiple at once)
5. Click **⚡ Process Photos** — images are processed one at a time with a progress bar
6. Review the extracted table (all cells are editable)
7. Click **⬇️ Download Excel**

---

## Model Recommendations

| Model | Speed | Accuracy | Cost |
|---|---|---|---|
| `gemini-2.5-pro-preview-*` | Slow | ⭐⭐⭐⭐⭐ Best | Medium |
| `gemini-2.5-flash-preview-*` | Fast | ⭐⭐⭐⭐ | Low |
| `gemini-1.5-flash` | Very fast | ⭐⭐⭐ | Very low |

For dense handwritten Thai text, **Gemini 2.5 Pro with Thinking** (enabled automatically) gives the best results.

---

## Project Structure

```
opdextractor/
├── backend/
│   ├── main.py           # FastAPI app (process, export, model-list endpoints)
│   ├── ocr.py            # Gemini Vision image → structured JSON
│   ├── excel_export.py   # openpyxl Excel builder
│   └── requirements.txt
├── frontend/
│   ├── index.html        # Single-page web UI
│   └── style.css
├── Dockerfile
├── docker-compose.yml
├── start.bat             # Windows one-click launcher
└── Book.xlsx             # Output column reference template
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `GET` | `/api/models` | List available Gemini models for the API key |
| `POST` | `/api/process` | Upload image(s), returns extracted JSON rows |
| `POST` | `/api/export` | Accept rows JSON, returns `.xlsx` file |

Headers used:
- `X-Gemini-Key` — your API key
- `X-Gemini-Model` — model ID to use

---

## Privacy

- The API key is **never stored on the server** — sent per-request from the browser
- Uploaded photos are processed in memory and immediately discarded
- Patient data never leaves your machine except for the Gemini API call

---

## License

MIT
