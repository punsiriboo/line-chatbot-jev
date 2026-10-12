import os
from dataclasses import dataclass

from typesafe_sdk import Choice, TypeSafeClient

MODEL = "jev-latest"
CONFIDENCE_THRESHOLD = 0.55
REQUEST_TIMEOUT_SECONDS = 10

INTENT_CRITERIA = {
    "view_menu": "อยากดูเมนูหรือถามว่ามีเครื่องดื่มอะไรบ้าง เช่น ขอดูเมนูหน่อย, มีเครื่องดื่มอะไรบ้าง",
    "store_hours": "ถามเวลาเปิดหรือปิดร้าน เช่น ร้านเปิดกี่โมง, วันนี้ปิดกี่โมง",
    "promotion": "ถามโปรโมชั่นหรือส่วนลด เช่น มีโปรอะไรบ้าง, ตอนนี้มีส่วนลดไหม",
    "membership": "ถามการสะสมแต้ม สะสมแก้ว หรือเครื่องดื่มฟรีจากการสะสม เช่น สะสมแต้มยังไง, สะสมครบ 10 ฟรีไหม",
    "location": "ถามตำแหน่งร้าน เช่น ร้านอยู่ที่ไหน, ร้านอยู่ที่กรุงเทพมหานครหรือสุรินทร์",
    "contact": "ถามวิธีติดต่อร้าน เช่น วิธีติดต่อร้าน, วิธีติดต่อร้านกาแฟ BEAT COFFEE",
    "payment": "ถามวิธีชำระเงิน เช่น วิธีชำระเงิน, วิธีชำระเงินกาแฟ BEAT COFFEE",
    "delivery": "ถามวิธีส่งสินค้า เช่น วิธีส่งสินค้า, วิธีส่งสินค้า BEAT COFFEE",
    "order": "ถามวิธีสั่งสินค้า เช่น วิธีสั่งสินค้า, วิธีสั่งสินค้า BEAT COFFEE",
    "complaint": "ถามวิธีร้องทุกข์ เช่น วิธีร้องทุกข์, วิธีร้องทุกข์ BEAT COFFEE",
    "feedback": "ถามวิธีส่งข้อคิดเห็น เช่น วิธีส่งข้อคิดเห็น, วิธีส่งข้อคิดเห็น BEAT COFFEE",
    "other": "คำถามอื่นที่ไม่ใช่เมนู เวลาเปิดร้าน โปรโมชั่น การสะสมแต้ม ที่ตั้งร้าน การติดต่อ การชำระเงิน การจัดส่ง การสั่งซื้อ การร้องเรียน หรือข้อเสนอแนะ",
}

client = TypeSafeClient(
    api_key=os.environ["JEV_API_KEY"],
    model=MODEL,
    timeout=REQUEST_TIMEOUT_SECONDS,
)


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float


def detect_intent(user_text):
    """Classify a LINE text message with Jev and return the chosen intent."""
    result = client.system_one(
        state={
            "channel": "line",
            "message": user_text,
        },
        questions={
            "intent": Choice(
                instructions=(
                    "เลือก intent ที่ตรงกับข้อความลูกค้าของร้านกาแฟ BEAT COFFEE มากที่สุด "
                    "ถ้าไม่เข้า intent ที่มีอยู่ ให้เลือก other"
                ),
                criteria=INTENT_CRITERIA,
            )
        },
    )
    answer = result.choices.get("intent")
    if answer is None or answer.choice not in INTENT_CRITERIA:
        return IntentResult(intent="other", confidence=0.0)

    intent = answer.choice

    return IntentResult(
        intent=intent,
        confidence=float(answer.confidence or 0),
    )
