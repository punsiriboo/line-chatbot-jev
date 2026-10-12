import asyncio
import os

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from linebot.v3.messaging import TextMessage

load_dotenv()

if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

APP_NAME = "beat_coffee"
MODEL = "gemini-2.5-flash"

session_service = InMemorySessionService()
agent = Agent(
    model=MODEL,
    name="beat_coffee_agent",
    description="พนักงานร้านกาแฟ BEAT COFFEE",
    instruction=(
        "คุณเป็นพนักงานร้านกาแฟ BEAT COFFEE ตอบลูกค้าเป็นภาษาไทย สั้น เป็นกันเอง\n"
        "ข้อเท็จจริงของร้าน: มีสาขากรุงเทพฯ และสุรินทร์ เปิดทุกวัน 08:00-18:00 น. "
        "โปรโมชั่นคือซื้อ 2 แก้วลด 10% "
        "สะสมครบ 10 แก้วรับเครื่องดื่มฟรี 1 แก้ว "
        "ชำระเงินสด พร้อมเพย์ หรือบัตร สั่งในแชทนี้แล้วรับที่ร้านหรือจัดส่งได้ "
        "เมนูมีเอสเพรสโซ อเมริกาโน่ ลาเต้ คาปูชิโน่ และมอคค่า"
    ),
)
runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def _session_for(user_id):
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=user_id,
    )
    if session is not None:
        return session
    return await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=user_id,
    )


async def _reply(user_message, user_id):
    session = await _session_for(user_id)
    content = Content(role="user", parts=[Part(text=user_message)])
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                return text
    return user_message


def get_agent_response(user_message, user_id):
    """Reply with the BEAT COFFEE agent. One in-memory session per LINE user."""
    user_id = user_id or "line-user"
    text = asyncio.run(_reply(user_message, user_id))
    return [TextMessage(text=text)]
