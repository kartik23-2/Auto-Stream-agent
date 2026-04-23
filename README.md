# AutoStream AI Sales Agent

AutoStream AI Sales Agent is a Streamlit-based conversational assistant for product sales support. It answers pricing and policy questions from a local knowledge base, captures high-intent leads, and uses an LLM only to rephrase grounded answers for better readability.

The core goal of this project is reliability: answers should come from known business data in `knowledge_base.json`, not from model hallucinations.

## Table of Contents

- Project Overview
- Key Features
- How It Works
- Project Structure
- Technology Stack
- Setup and Installation
- Configuration
- Running the App
- WhatsApp Webhook Deployment
- Usage Guide
- Testing and Validation
- Troubleshooting
- Security and Privacy Notes
- Current Limitations
- Future Improvements

## Project Overview

This assistant is designed for sales-oriented Q and A workflows:

- Handle common customer questions about plans, pricing, support, and refund policies.
- Detect lead intent and guide the user through lead capture (name, email, platform).
- Persist chat and lead-capture state within a Streamlit session.
- Keep factual accuracy by grounding responses in a local JSON knowledge source.

## Key Features

1. Knowledge-grounded responses
- Business facts are sourced from `knowledge_base.json`.
- Unknown questions return a clear "not available in current knowledge base" response.

2. Controlled LLM usage
- LLM is used for rephrasing only.
- Rephrase prompt explicitly blocks adding new facts, numbers, policies, or features.

3. Graceful degradation
- If API key is missing, quota is exhausted, or model call fails, the app still returns deterministic knowledge-base answers.

4. Lead capture workflow
- Detects purchase intent.
- Collects name, email, and creator platform.
- Stores leads into `leads.csv`.

5. Session-aware chat
- `st.session_state` stores chat history and agent state per browser session.

## How It Works

### Response pipeline

1. User asks a question in Streamlit chat.
2. Agent checks if lead capture mode is active.
3. If not in lead mode, agent detects intent.
4. For pricing/general product questions:
- Build a factual draft from `knowledge_base.json`.
- Send draft to LLM for style-only rewrite.
- If LLM fails, return factual draft directly.
5. For lead intent:
- Start guided lead capture flow.

### Intent groups

- Greeting intent: welcome and guidance message.
- Pricing intent: pricing and plan related responses.
- Lead intent: triggers lead capture sequence.
- General intent: still grounded to knowledge base and optionally rephrased.

## Project Structure

- `app.py`: Streamlit UI and session state handling.
- `agent.py`: Main decision logic, intent detection, KB answer drafting, lead flow.
- `prompt.py`: Prompt templates, including strict rephrasing rules.
- `model.py`: Gemini client wrapper and error-safe LLM call.
- `config.py`: Environment and model configuration.
- `tools.py`: Email validation and CSV lead persistence.
- `knowledge_base.json`: Source-of-truth business data.
- `requirements.txt`: Python dependencies.
- `README.md`: Project documentation.

## Technology Stack

- Python 3.10+
- Streamlit (chat UI)
- Google Gemini SDK (`google-genai`)
- Python Dotenv (`python-dotenv`)
- JSON and CSV for local data persistence

## Setup and Installation

### 1. Clone the repository

Use your normal Git workflow to clone or copy this project.

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

Model name is configured in `config.py` through `MODEL_NAME`.

Example currently used:

```python
MODEL_NAME = 'gemini-2.0-flash'
```

## Running the App

```powershell
streamlit run app.py
```

Optional headless/server mode:

```powershell
python -m streamlit run app.py --server.headless true --server.port 8502
```

After startup, open the shown local URL in your browser.

## WhatsApp Webhook Deployment

To integrate this agent with WhatsApp, use Meta WhatsApp Cloud API with Webhooks. The Streamlit app remains useful for local testing, while webhook endpoints handle real WhatsApp traffic.

### Solution architecture

1. Customer sends a message to your WhatsApp business number.
2. Meta sends webhook event to your backend (`POST /webhook`).
3. Backend extracts sender ID (`wa_id`) and message text.
4. Backend loads conversation state for that sender.
5. Backend calls `run_agent(message_text, state)` from `agent.py`.
6. Backend sends the reply using WhatsApp Graph API.
7. Backend persists updated state and logs.

### Why webhooks are required

- WhatsApp Cloud API is event-driven.
- Incoming messages are pushed by Meta to your webhook URL.
- Without webhooks, your bot cannot receive user messages in real time.

### Integration requirements

#### 1. Meta and WhatsApp setup

- Meta developer account
- WhatsApp Business Account
- WhatsApp app in Meta dashboard
- Phone Number ID
- Permanent access token (recommended for production)
- Webhook verify token

#### 2. Backend requirements

- Python API framework (`FastAPI` or `Flask`)
- Public HTTPS endpoint (required by Meta)
- Request handling for GET/POST webhook methods
- HTTP client for outbound API calls (`requests` or `httpx`)

#### 3. Data and state requirements

- Per-user conversation state keyed by `wa_id`
- Persistent storage (Redis or database)
- Lead storage (database preferred over local CSV for production)

#### 4. Security requirements

- Verify webhook token in `GET /webhook`
- Validate webhook signature (`X-Hub-Signature-256`) for POST events
- Keep secrets in environment variables only
- Use HTTPS and restrict server/network access

#### 5. Reliability requirements

- Logging for all inbound/outbound events
- Retry handling for transient failures
- Monitoring and alerts for webhook/API failures

### Required environment variables

Add these variables for WhatsApp integration:

```env
WHATSAPP_ACCESS_TOKEN=your_permanent_meta_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_GRAPH_API_VERSION=v20.0
```

Existing variable still required:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Webhook endpoints you need

#### `GET /webhook` (verification)

- Read `hub.mode`, `hub.verify_token`, `hub.challenge`.
- If token matches `WHATSAPP_VERIFY_TOKEN`, return `hub.challenge` with HTTP 200.
- Otherwise return HTTP 403.

#### `POST /webhook` (incoming messages)

- Parse inbound event JSON.
- Extract `wa_id` and message body.
- Load sender state from storage.
- Generate response via `run_agent`.
- Save updated sender state.
- Send response text to WhatsApp Graph API.

### Outbound send-message API

Use Graph API endpoint:

`https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages`

Payload type should be `text`, with `to=<wa_id>` and `text.body=<agent_response>`.

### Suggested backend file (new)

Create a new file such as `whatsapp_webhook.py` that wraps webhook behavior around your existing `agent.py` logic.

Pseudo-flow:

```text
POST /webhook
	-> parse event
	-> wa_id, user_text
	-> state = load_state(wa_id)
	-> reply = run_agent(user_text, state)
	-> save_state(wa_id, state)
	-> send_whatsapp_message(wa_id, reply)
```

### Production recommendation

- Keep `agent.py` as the core decision engine.
- Use Redis for session/state continuity across restarts.
- Use PostgreSQL for lead and audit records.
- Deploy webhook service separately from Streamlit UI.
- Keep Streamlit as admin/demo frontend if needed.

### End-to-end checklist

1. Create Meta app and connect WhatsApp Cloud API.
2. Generate and store tokens/IDs in `.env`.
3. Build and deploy webhook backend with HTTPS.
4. Configure webhook URL and verify token in Meta dashboard.
5. Implement sender-state persistence (`wa_id` based).
6. Test message receive, bot response, and lead capture flow.
7. Add logs, retries, and monitoring before production rollout.

## Usage Guide

### Example pricing questions

- What is the basic plan price?
- Tell me pro plan pricing.
- What resolution is available in pro?
- Do you offer AI captions?

### Example policy questions

- What is your refund policy?
- What support is available?

### Example unknown question behavior

If information is not in `knowledge_base.json` (for example yearly billing), expected response is:

"I do not have that information in the current knowledge base."

### Example lead capture flow

1. User: I want pro
2. Bot: asks full name
3. Bot: asks email (validated)
4. Bot: asks creator platform
5. Lead is stored in `leads.csv`

## Testing and Validation

Recommended functional checks:

1. Pricing correctness
- Ask basic and pro pricing questions.

2. Policy correctness
- Ask support and refund questions.

3. Unknown information handling
- Ask for a field not present in KB (for example yearly plan).

4. Lead capture
- Complete full lead flow and verify row appended in `leads.csv`.

5. Fallback behavior
- Temporarily remove/invalid key or hit quota; verify app still gives deterministic KB answer.

## Troubleshooting

### Problem: "Gemini API key is missing"

- Ensure `.env` exists in project root.
- Ensure `GOOGLE_API_KEY` is set correctly.
- Restart Streamlit after updating `.env`.

### Problem: "AI service temporarily unavailable"

- Usually quota/rate limit/network issue.
- App should still provide deterministic KB answer fallback.

### Problem: outdated response behavior after code changes

- Restart Streamlit server to clear stale process state.

### Problem: Unicode symbols display oddly in terminal

- This is typically a terminal encoding issue, not a logic bug.

## Security and Privacy Notes

- Leads are stored in plain CSV (`leads.csv`) for local demo use.
- Do not use this storage approach in production without encryption/access controls.
- Do not commit real API keys to version control.

## Current Limitations

1. Rule-based intent detection
- Uses keyword/regex logic; complex phrasing may require tuning.

2. Local persistence only
- No production database, authentication, or role-based access.

3. Narrow domain knowledge
- Answers are limited to fields in `knowledge_base.json`.

4. No admin console
- No built-in dashboard for leads or KB management.

## Future Improvements

1. Admin-managed knowledge base
- Build UI to edit plans/policies safely.

2. Better intent and retrieval
- Add robust semantic routing while preserving hard grounding rules.

3. Lead management backend
- Move from CSV to a database with audit logging.

4. Observability
- Add structured logs, error metrics, and request tracing.

5. Production hardening
- Add authentication, input sanitization, and deployment configs.

