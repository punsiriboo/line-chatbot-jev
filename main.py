import os
from pathlib import Path
import functions_framework
from dotenv import load_dotenv
import base64

from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
)

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
    ShowLoadingAnimationRequest,
    FlexContainer,
    FlexMessage,
)

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]


configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
line_bot_blob_api = MessagingApiBlob(api_client)

from adk_agent import get_agent_response
from gemini import image_description
from jev_intent import CONFIDENCE_THRESHOLD, detect_intent

FLEX_DIR = Path(__file__).resolve().parent / "flex_messages"

_FLEX_FILES = {
    "view_menu": (
        "view_menu.json",
        "BEAT COFFEE เมนูเครื่องดื่ม",
        "นี่คือเมนูเครื่องดื่มของร้านค่ะ",
    ),
    "store_hours": (
        "store_hours.json",
        "ร้านเปิดทุกวัน 08:00 - 18:00 น.",
        "ร้านเปิดทุกวันค่ะ",
    ),
    "promotion": (
        "promotion.json",
        "โปรโมชั่นประจำร้าน ซื้อ 2 แก้ว ลด 10%",
        "ตอนนี้มีโปรโมชั่นแบบนี้ค่ะ",
    ),
    "membership": (
        "membership.json",
        "สะสมครบ 10 แก้ว รับเครื่องดื่มฟรี 1 แก้ว",
        "สะสมครบ 10 แก้ว รับฟรี 1 แก้วค่ะ",
    ),
    "location": (
        "location.json",
        "BEAT COFFEE มีสาขากรุงเทพมหานครและสุรินทร์",
        "เรามีสองสาขาค่ะ",
    ),
    "contact": (
        "contact.json",
        "ติดต่อ BEAT COFFEE ได้ในแชทนี้",
        "ติดต่อร้านได้ตามนี้เลยค่ะ",
    ),
    "payment": (
        "payment.json",
        "ชำระได้ทั้งเงินสด พร้อมเพย์ และบัตร",
        "ชำระเงินได้หลายแบบค่ะ",
    ),
    "delivery": (
        "delivery.json",
        "รับที่ร้านได้เลย หรือให้จัดส่งรอบสาขา",
        "รับที่ร้านหรือให้จัดส่งได้ค่ะ",
    ),
    "order": (
        "order.json",
        "สั่งเครื่องดื่ม BEAT COFFEE ในแชทนี้ได้เลย",
        "สั่งเครื่องดื่มได้ตามนี้ค่ะ",
    ),
    "complaint": (
        "complaint.json",
        "แจ้งปัญหาให้ BEAT COFFEE ได้ในแชทนี้",
        "แจ้งปัญหาได้เลยนะคะ",
    ),
    "feedback": (
        "feedback.json",
        "ส่งคำชมหรือคำแนะนำให้ BEAT COFFEE ได้ในแชทนี้",
        "ส่งข้อเสนอแนะได้เลยนะคะ",
    ),
}


def flex_message_for(intent):
    item = _FLEX_FILES.get(intent)
    if item is None:
        return None
    filename, alt_text, intro = item
    raw = (FLEX_DIR / filename).read_text(encoding="utf-8")
    flex_message = FlexMessage(
        alt_text=alt_text,
        contents=FlexContainer.from_json(raw),
    )
    return [TextMessage(text=intro), flex_message]


@functions_framework.http
def callback(request):
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    print("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )

    return "OK"


def _chat_id(event):
    source = event.source
    source_type = getattr(source, "type", "user")
    if source_type == "group":
        return getattr(source, "group_id", None)
    if source_type == "room":
        return getattr(source, "room_id", None)
    return getattr(source, "user_id", None)


def _show_loading(event):
    chat_id = _chat_id(event)
    if not chat_id:
        return
    try:
        line_bot_api.show_loading_animation(
            ShowLoadingAnimationRequest(chat_id=chat_id, loading_seconds=20)
        )
    except Exception as exc:
        print(f"Loading animation failed: {exc}")


def _adk_messages(user_text, user_id, event):
    # Start loading only for this slow call. A fast Jev reply would land
    # before LINE draws the animation, and then nothing remains to dismiss it.
    _show_loading(event)
    return [TextMessage(text=get_agent_response(user_text, user_id))]


def _messages_for_intent(user_text, result, user_id, event):
    flex_messages = None
    if (
        result is not None
        and result.intent != "other"
        and result.confidence >= CONFIDENCE_THRESHOLD
    ):
        try:
            flex_messages = flex_message_for(result.intent)
        except Exception as exc:
            print(f"Flex reply failed, sending to ADK: {exc}")
    if flex_messages is not None:
        return flex_messages

    print("Sending unmatched text to ADK")
    return _adk_messages(user_text, user_id, event)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text
    user_id = event.source.user_id
    try:
        result = detect_intent(user_text=user_text, user_id=user_id)
        print(
            "Jev intent="
            f"{result.intent} confidence={result.confidence} "
            f"probabilities={result.probabilities}"
        )
    except Exception as exc:
        print(f"Jev intent detection failed: {exc}")
        result = None

    low_confidence = (
        result is None
        or result.intent == "other"
        or result.confidence < CONFIDENCE_THRESHOLD
    )
    if low_confidence:
        print("Jev low confidence, sending to ADK")
        messages = _adk_messages(user_text, user_id, event)
    else:
        try:
            messages = _messages_for_intent(user_text, result, user_id, event)
        except Exception as exc:
            print(f"Text reply failed, sending to ADK: {exc}")
            messages = _adk_messages(user_text, user_id, event)

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages,
        )
    )


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    _show_loading(event)

    try:
        message_content = line_bot_blob_api.get_message_content(message_id=event.message.id)
        reply_text = image_description(message_content)
        if not reply_text:
            raise RuntimeError("Gemini returned an empty image description")
    except Exception as exc:
        print(f"Image reply failed, sending to ADK: {exc}")
        reply_text = get_agent_response("ลูกค้าส่งรูปมา ช่วยตอบสั้นๆ", event.source.user_id)

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text=reply_text),
            ],
        )
    )
