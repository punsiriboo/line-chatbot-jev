import os
from pathlib import Path
import functions_framework
from dotenv import load_dotenv

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
from jev_intent import CONFIDENCE_THRESHOLD, detect_intent_with_jev

FLEX_DIR = Path(__file__).resolve().parent / "flex_messages"

_FLEX_FILES_MAPPING = {
    "view_menu": ("view_menu.json", "BEAT COFFEE มีเมนูเครื่องดื่มดังนี้ค่ะ"),
    "store_hours": ("store_hours.json", "ร้านเปิดทุกวัน 08:00 - 18:00 น."),
    "promotion": ("promotion.json", "ซื้อ 2 แก้วลด 10% และสะสมครบ 10 แก้วฟรี 1 แก้ว"),
    "location": ("location.json", "BEAT COFFEE มีสาขากรุงเทพมหานครและสุรินทร์"),
    "contact": ("contact.json", "ติดต่อ BEAT COFFEE ได้ในแชทนี้"),
}


def flex_message_for_intent(intent):
    item = _FLEX_FILES_MAPPING.get(intent)
    if item is None:
        return None
    filename, text = item
    raw = (FLEX_DIR / filename).read_text(encoding="utf-8")
    flex_message = FlexMessage(
        alt_text=text,
        contents=FlexContainer.from_json(raw),
    )
    return [TextMessage(text=text), flex_message]


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


def _show_loading(event):
    chat_id = event.source.user_id

    if not chat_id:
        return
    try:
        line_bot_api.show_loading_animation(
            ShowLoadingAnimationRequest(chat_id=chat_id)
        )
    except Exception as exc:
        print(f"Loading animation failed: {exc}")


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text
    user_id = event.source.user_id


    intent, confidence = detect_intent_with_jev(user_text)
    known_intent = intent != "other"
    high_confidence = confidence >= CONFIDENCE_THRESHOLD
    if known_intent and high_confidence:
        messages = flex_message_for_intent(intent)
    else:
        _show_loading(event)
        messages = get_agent_response(user_text, user_id)

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
        messages = [TextMessage(text=reply_text)]
    except Exception as exc:
        print(f"Image reply failed, sending to ADK: {exc}")
        messages = get_agent_response("ลูกค้าส่งรูปมา ช่วยตอบสั้นๆ", event.source.user_id)

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages,
        )
    )
