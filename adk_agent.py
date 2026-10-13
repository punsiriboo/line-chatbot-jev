import asyncio

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai.types import Content, Part
from linebot.v3.messaging import TextMessage

load_dotenv()

APP_NAME = "beat_coffee"
session_service = InMemorySessionService()
runner = Runner(
    app_name=APP_NAME,
    session_service=session_service,
    agent=Agent(
        model="gemini-3.5-flash",
        name="beat_coffee_agent",
        description="พนักงานร้านกาแฟ BEAT COFFEE",
        instruction=(
            "คุณเป็นพนักงานร้านกาแฟ BEAT COFFEE ตอบลูกค้าเป็นภาษาไทย สั้น เป็นกันเอง\n"
            "ข้อเท็จจริงของร้าน: มีสาขากรุงเทพฯ และสุรินทร์ เปิดทุกวัน 08:00-18:00 น. "
            "โปรโมชั่นคือซื้อ 2 แก้วลด 10% "
            "สะสมครบ 10 แก้วรับเครื่องดื่มฟรี 1 แก้ว "
            "ชำระเงินสด พร้อมเพย์ หรือบัตร สั่งในแชทนี้แล้วรับที่ร้านหรือจัดส่งได้ "
            "เมนูมีเอสเพรสโซ อเมริกาโน่ ลาเต้ คาปูชิโน่ และมอคค่า\n"
            "ถ้าคำถามอยู่นอกข้อเท็จจริงของร้าน ให้ใช้ Google Search แล้วตอบสั้นจากผลค้นหา"
        ),
        tools=[google_search],
    ),
)


async def _reply(user_message, user_id):
    ids = {"app_name": APP_NAME, "user_id": user_id, "session_id": user_id}
    session = await session_service.get_session(**ids) or await session_service.create_session(**ids)
    message = Content(role="user", parts=[Part(text=user_message)])
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=message):
        if not event.is_final_response() or not event.content or not event.content.parts:
            continue
        text = event.content.parts[0].text
        if text:
            return text
    return user_message


def get_agent_response(user_message, user_id):
    text = asyncio.run(_reply(user_message, user_id or "line-user"))
    return [TextMessage(text=text)]
