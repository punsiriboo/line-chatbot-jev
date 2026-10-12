import os

from typesafe_sdk import Choice, TypeSafeClient

CONFIDENCE_THRESHOLD = 0.55

INTENT_CRITERIA = {
    "view_menu": "อยากดูเมนูหรือถามว่ามีเครื่องดื่มอะไรบ้าง เช่น ขอดูเมนูหน่อย, มีเครื่องดื่มอะไรบ้าง",
    "store_hours": "ถามเวลาเปิดหรือปิดร้าน เช่น ร้านเปิดกี่โมง, วันนี้ปิดกี่โมง",
    "promotion": "ถามโปรโมชั่น ส่วนลด หรือการสะสมแต้ม เช่น มีโปรอะไรบ้าง, ตอนนี้มีส่วนลดไหม, สะสมครบ 10 ฟรีไหม",
    "location": "ถามตำแหน่งร้าน เช่น ร้านอยู่ที่ไหน, ร้านอยู่ที่กรุงเทพมหานครหรือสุรินทร์",
    "contact": "ถามวิธีติดต่อร้าน เช่น วิธีติดต่อร้าน, โทรศัพท์ร้าน",
    "other": "คำถามอื่นที่ไม่ใช่เมนู เวลาเปิดร้าน โปรโมชั่น การสะสมแต้ม ที่ตั้งร้าน หรือการติดต่อ",
}

client = TypeSafeClient(api_key=os.environ["JEV_API_KEY"], model="jev-latest")

def detect_intent_with_jev(user_text):
    """Classify a LINE text message with Jev and return (intent, confidence)."""
    result = client.system_one(
        state={"channel": "line", "message": user_text},
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
    return answer.choice, float(answer.confidence or 0)
