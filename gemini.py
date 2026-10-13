import io
import os

from google import genai
from google.genai import types
from PIL import Image

MODEL = "gemini-2.5-flash"
_client = None


def image_description(message_content):
    """Describe what is in a LINE image. The description is sent to ADK."""
    image_bytes = _as_bytes(message_content)
    response = _get_client().models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=_mime_type(image_bytes)),
            (
                "ดูรูปนี้แล้วบอกเป็นภาษาไทยสั้น ๆ ว่ารูปคืออะไร "
                "บอกเฉพาะสิ่งที่เห็นในรูป ยังไม่ต้องตอบลูกค้า"
            ),
        ],
    )
    return (response.text or "").strip()


def _as_bytes(message_content):
    if isinstance(message_content, (bytes, bytearray)):
        return bytes(message_content)
    if hasattr(message_content, "read"):
        return message_content.read()
    content = getattr(message_content, "content", None)
    if content is not None:
        return bytes(content)
    raise TypeError("LINE image content is not bytes")


def _mime_type(image_bytes):
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            kind = (image.format or "").lower()
    except Exception:
        return "image/jpeg"
    return {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(kind, "image/jpeg")


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client
