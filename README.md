# LINE Chatbot BEAT COFFEE

The LINE bot for BEAT COFFEE receives webhook messages and asks Jev to classify the intent. When the message matches a store topic, the bot replies with a Flex Message. Otherwise it sends the question to the ADK agent.

## How it works

1. LINE sends a webhook to the `callback` function in `main.py`.
2. Text messages are sent to Jev (`jev-latest`) to choose an intent.
3. If confidence is at least 0.55 and that intent has a Flex file, the bot sends the card from `flex_messages/`.
4. If the intent is `other` or confidence is below the threshold, the question goes to the ADK agent.
5. Images are described in Thai by Gemini. PDF files are summarized in Thai by Gemini.

## Intents

| Intent | Example question | Flex file |
| --- | --- | --- |
| `view_menu` | Can I see the menu? | `flex_messages/view_menu.json` |
| `store_hours` | What time do you open? | `flex_messages/store_hours.json` |
| `promotion` | Any promotions? | `flex_messages/promotion.json` |
| `location` | Where is the shop? | `flex_messages/location.json` |
| `contact` | How do I contact the shop? | `flex_messages/contact.json` |
| `payment` | How can I pay? | `flex_messages/payment.json` |
| `delivery` | How do you deliver? | `flex_messages/delivery.json` |
| `order` | How do I order? | `flex_messages/order.json` |
| `complaint` | How do I file a complaint? | `flex_messages/complaint.json` |
| `feedback` | How do I send feedback? | `flex_messages/feedback.json` |
| `other` | Anything else | No Flex file. Sent to the ADK agent. |

The confidence threshold is `CONFIDENCE_THRESHOLD` in `jev_intent.py`.

## Setup

Copy the example file and fill in the real values. Do not commit `.env`.

```bash
cp .env.example .env
```

| Variable | Purpose |
| --- | --- |
| `LINE_CHANNEL_ACCESS_TOKEN` | Reply to LINE messages |
| `LINE_CHANNEL_SECRET` | Verify the webhook signature |
| `JEV_API_KEY` | TypeSafe key for intent detection. The key starts with `apikey_` |
| `GEMINI_API_KEY` | Key for the ADK agent, image descriptions, and PDF summaries |

In the LINE Developers Console, set the Webhook URL to this function and turn on Use webhook.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install functions-framework python-dotenv line-bot-sdk google-adk google-genai pillow typesafe-sdk
functions-framework --target=callback --debug --port=8080
```

Then point the LINE webhook at a URL that can reach this machine.

## Main files

| File | Role |
| --- | --- |
| `main.py` | Receives the webhook and chooses how to reply |
| `jev_intent.py` | Calls Jev to classify the intent |
| `flex_messages/` | Flex cards for each intent. `main.py` loads these files when replying |
| `adk_agent.py` | ADK agent for questions that have no Flex card |
| `gemini.py` | Describes images and summarizes PDFs |
