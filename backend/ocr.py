import os
import io
import json
import re
import time
from PIL import Image, ImageOps, ImageEnhance
from google import genai
from google.genai import types

PROMPT = """You are extracting every patient record from a page of a handwritten Thai/English veterinary clinic logbook.

FIELD ORDER (each row must have all these fields):
0. date      — the date header written above this row (e.g. "14 ม.ค. 2569", "12 ม.ค. 2569").
               IMPORTANT: a single page can have MULTIPLE date headers at different vertical positions.
               Each row inherits the date of the nearest header written above it on the page.
               If a new date header appears mid-page, all rows below it get that new date.
               Preserve the date exactly as handwritten. If no date header is visible above a row, use "".
1. no        — far-left, the row/patient number
2. name      — owner's name, usually Thai script
3. pet       — pet's name, Thai or English
4. type      — animal type abbreviation: Ct=cat, Dg=dog, Rb=rabbit, Bd=bird, or full Thai/English word
5. opd       — OPD or HN number, typically 3-5 digits
6. description — the WIDEST column in the centre-right area; contains services, medicines, diagnoses in Thai and English (e.g. "FLU วัคซีน (1.5)", "ตรวจ + RXC", "Raboon + ยาถ่าย")
7. price     — numeric amount on the right side (digits only, no ฿ or baht)
8. note      — far-right, often blank or has a circled/highlighted remark

RULES:
- Return ONLY a valid JSON array. No explanation, no markdown fences, no trailing text.
- One JSON object per patient row.
- Extract EVERY row visible on the page — pages typically have 20-35 rows. Do not stop early.
- Preserve Thai text exactly as handwritten. Do not transliterate or translate.
- If a row has 1-2 indented continuation lines below it, those lines belong to that patient's description — append them with a space.
- Ignore crossed-out or struck-through text.
- Ignore the page header row (column labels) and grand-total lines at the bottom.
- Date header lines are NOT patient rows — extract them only as the "date" field of subsequent rows.
- If a field is truly illegible, use "".

OUTPUT FORMAT (example with two dates on one page):
[
  {"date":"12 ม.ค. 2569","no":"1","name":"สมชาย ใจดี","pet":"มิ้ว","type":"Ct","opd":"1234","description":"ตรวจ + วัคซีน Raboon (1 dose) ยาถ่าย","price":"350","note":""},
  {"date":"12 ม.ค. 2569","no":"2","name":"วันดี","pet":"โกลเด้น","type":"Dg","opd":"5678","description":"FLU วัคซีน (2.5 kg) + RXC ยาแก้อักเสบ","price":"480","note":""},
  {"date":"13 ม.ค. 2569","no":"1","name":"John","pet":"Buddy","type":"Dog","opd":"9012","description":"Vaccination FLU + Bordetella","price":"200","note":""}
]"""


def _prepare_image(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Auto-levels: normalise the brightness range (removes washed-out / dark look)
    img = ImageOps.autocontrast(img, cutoff=1)
    # Sharpen text edges
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    # Additional contrast punch after auto-levels
    img = ImageEnhance.Contrast(img).enhance(1.5)
    # Keep full resolution up to 3000px on longest side to preserve small Thai characters
    max_side = 3000
    if max(img.size) > max_side:
        ratio = max_side / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _parse_json(text: str) -> list:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []


def list_models(api_key: str) -> list[dict]:
    client = genai.Client(api_key=api_key)
    results = []
    for m in client.models.list():
        name = getattr(m, "name", "") or ""
        model_id = name.split("/")[-1] if "/" in name else name
        if not model_id:
            continue
        if "gemini" not in model_id.lower():
            continue
        methods = getattr(m, "supported_generation_methods", []) or []
        if methods and "generateContent" not in methods:
            continue
        display_name = getattr(m, "display_name", model_id) or model_id
        results.append({"id": model_id, "display": f"{model_id}  ({display_name})"})
    results.sort(key=lambda x: x["id"])
    return results


def extract_rows(image_bytes: bytes, api_key: str = "", model: str = "gemini-2.5-pro-preview-03-25") -> list[dict]:
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("Gemini API key not provided. Enter it in the app or set GEMINI_API_KEY env var.")

    prepared = _prepare_image(image_bytes)
    client = genai.Client(api_key=key)

    # Enable thinking for Gemini 2.5 models — significantly improves accuracy on
    # complex structured extraction tasks like dense handwritten tables
    config = None
    if "2.5" in model:
        config = types.GenerateContentConfig(
            temperature=0,
            thinking_config=types.ThinkingConfig(thinking_budget=2048),
        )
    else:
        config = types.GenerateContentConfig(temperature=0)

    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=prepared, mime_type="image/jpeg"),
                    PROMPT,
                ],
                config=config,
            )
            break
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = 15 * (attempt + 1)
                time.sleep(wait)
                continue
            raise
    else:
        raise last_error

    rows = _parse_json(response.text)

    keys = ["date", "no", "name", "pet", "type", "opd", "description", "price", "note"]
    clean = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        clean.append({k: str(row.get(k, "") or "").strip() for k in keys})
    return clean
