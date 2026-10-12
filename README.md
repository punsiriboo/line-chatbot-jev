# Intent-based LINE Chatbot with JEV

![Intent-based LINE Chatbot with JEV](images/title.png)

BEAT COFFEE answers LINE messages by intent. Jev classifies each text message. A confident store intent gets a short Thai line plus a Flex Message. Anything else goes to the ADK agent.

## Flow

1. LINE posts the webhook to `callback` in `main.py`.
2. Text is sent to Jev (`jev-latest`) through the TypeSafe SDK. Jev picks one intent from `INTENT_CRITERIA`.
3. If the intent is a store topic and confidence is at least `0.55`, the bot sends the intro text and the Flex card in `flex_messages/`. This path does not show a loading animation, because the reply returns too quickly for LINE to clear one.
4. If Jev returns `other`, confidence is below the threshold, or the call fails, the bot shows a loading animation and sends the same text to the ADK agent. The reply dismisses the animation.
5. The agent keeps one in-memory session per LINE user id.
6. Images are described in Thai by Gemini. If that fails, the question goes to the ADK agent.

## Intents

| Intent | Example | Reply |
| --- | --- | --- |
| `view_menu` | ขอดูเมนูหน่อย | `flex_messages/view_menu.json` |
| `store_hours` | ร้านเปิดกี่โมง | `flex_messages/store_hours.json` |
| `promotion` | มีโปรอะไรบ้าง | `flex_messages/promotion.json` |
| `membership` | สะสมแต้มยังไง | `flex_messages/membership.json` |
| `location` | ร้านอยู่ที่ไหน | `flex_messages/location.json` |
| `contact` | ติดต่อร้านยังไง | `flex_messages/contact.json` |
| `payment` | จ่ายเงินยังไง | `flex_messages/payment.json` |
| `delivery` | ส่งไหม | `flex_messages/delivery.json` |
| `order` | สั่งยังไง | `flex_messages/order.json` |
| `complaint` | อยากแจ้งปัญหา | `flex_messages/complaint.json` |
| `feedback` | อยากให้คำแนะนำ | `flex_messages/feedback.json` |
| `other` | Anything else | ADK agent, no Flex card |

`CONFIDENCE_THRESHOLD` lives in `jev_intent.py`.

## Setup

```bash
cp .env.example .env
```

Do not commit `.env`.

| Variable | Purpose |
| --- | --- |
| `LINE_CHANNEL_ACCESS_TOKEN` | Reply on LINE |
| `LINE_CHANNEL_SECRET` | Verify `X-Line-Signature` |
| `JEV_API_KEY` | TypeSafe key for Jev. It starts with `apikey_` |
| `GEMINI_API_KEY` | Used by the ADK agent. Copied to `GOOGLE_API_KEY` when that variable is empty |

In the LINE Developers console, set the webhook URL to the Cloud Run service root and enable **Use webhook**.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
functions-framework --target=callback --debug --port=8080
```

Point the LINE webhook at a public URL that reaches this process.

## Deploy

`deploy.sh` deploys to Cloud Run in `asia-southeast1` on project `data-beat-labs`. It reads `.env` into a temporary env file and does not upload `.env` itself.

## Files

| File | Role |
| --- | --- |
| `main.py` | Webhook, loading animation, and reply routing |
| `jev_intent.py` | Jev intent classification |
| `flex_messages/` | One Flex card per store intent |
| `adk_agent.py` | ADK agent for unmatched text and failed image replies |
| `gemini.py` | Describes images before the ADK fallback |
| `deploy.sh` | Cloud Run deploy |
