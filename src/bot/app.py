# src/bot/app.py
import os, logging
import re
from aiohttp import web
from botbuilder.core import TurnContext, ActivityHandler, MessageFactory
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity
from botframework.connector.auth import ClaimsIdentity
from .llm_hf import HFLLM
import asyncio
from urllib.parse import urlsplit, urlunsplit


from .storage import upsert_conversation_reference, conversation_refs
from .scheduler import start_scheduler, schedule_in_minutes


logging.basicConfig(level=logging.INFO)

APP_ID = os.getenv("MicrosoftAppId", "")
APP_PASSWORD = os.getenv("MicrosoftAppPassword", "")
PORT = int(os.getenv("PORT", "3978"))

class ChatBot(ActivityHandler):
    def __init__(self):
        self.llm = HFLLM()

    async def on_turn(self, turn_context: TurnContext):
        upsert_conversation_reference(turn_context)  # for proactive reminders
        return await super().on_turn(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        user_id = upsert_conversation_reference(turn_context)
        logging.info("[REF] stored conversation ref for user=%s", user_id)

        text = (turn_context.activity.text or "").strip()

        # Reminder: "remind in 5 minutes: take a break"
        pattern = r"""
         ^\s*remind(?:er)?        # 'remind' or 'reminder'
        (?:\s+me)?               # optional 'me'
        (?:\s+in)?\s*            # optional 'in'
        (?P<num>\d+)             # minutes number
        \s*(?:m|min|mins|minute|minutes)?  # optional unit
        (?:\s*[:\-]\s*(?P<msg>.+))?        # optional ': message' or '- message'
        \s*$
        """
        m = re.match(pattern, text, flags=re.X)
        if m:
            n = int(m.group("num")); 
            msg = (m.group("msg") or f"{n} minute(s) have passed.").strip()
            user_id = upsert_conversation_reference(turn_context)
            print(f"[REM] scheduling user_id={user_id}, msg={msg!r}")


            async def _send_reminder(user_id: str, message: str):
                ref = conversation_refs.get(user_id)
                print(f"[REM] firing user_id={user_id}, have_ref={bool(ref)}")
                if not ref: 
                    return
                async def logic(ctx: TurnContext):
                    await ctx.send_activity(f"Reminder: {message}")

                try:
                    anon = ClaimsIdentity({}, "anonymous")
                    await ADAPTER.continue_conversation(ref, logic, claims_identity=anon)
                    print("[REM] continue_conversation OK")
                except Exception as e:
                    print("[REM] continue_conversation ERROR:", e)

            schedule_in_minutes(n, _send_reminder, user_id, msg)
            return await turn_context.send_activity(f"Okay! I'll remind you in {n} minute(s).")

        # Echo command
        if text.lower().startswith("echo "):
            return await turn_context.send_activity(MessageFactory.text(text[5:].strip()))

        # LLM fallback
        reply = await self.llm.generate(text)
        await turn_context.send_activity(MessageFactory.text(reply))

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)
BOT = ChatBot()

async def on_error(context: TurnContext, error: Exception):
    logging.exception(error)
    await context.send_activity("Oops, something went wrong.")
ADAPTER.on_turn_error = on_error

routes = web.RouteTableDef()

def _rewrite_service_url(url: str) -> str:
    """If the serviceUrl uses localhost, point it to the host so the container can reach it."""
    try:
        u = urlsplit(url)
        if u.hostname in ("localhost", "127.0.0.1"):
            host_override = os.getenv("PLAYGROUND_HOST", "host.docker.internal")
            netloc = f"{host_override}:{u.port}" if u.port else host_override
            return urlunsplit((u.scheme, netloc, u.path, u.query, u.fragment))
    except Exception:
        pass
    return url

@routes.post("/api/messages")
async def messages(req: web.Request):
    if "application/json" not in req.headers.get("Content-Type", ""):
        return web.Response(status=415)
    body = await req.json()

    su = body.get("serviceUrl")
    new_su = _rewrite_service_url(su) if su else su
    if new_su and new_su != su:
        print(f"[NET] Rewriting serviceUrl {su} -> {new_su}")
        body["serviceUrl"] = new_su


    print("INBOUND channel:", body.get("channelId"), "| type:", body.get("type"), "| text:", body.get("text"))


    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")
    async def aux_logic(turn_context: TurnContext):
        await BOT.on_turn(turn_context)
    await ADAPTER.process_activity(activity, auth_header, aux_logic)
    return web.Response(status=201)

@routes.get("/healthz")
async def health(_):
    return web.json_response({"ok": True})


APP = web.Application()
APP.add_routes(routes)

async def _on_startup(app: web.Application):
    loop = asyncio.get_running_loop()
    start_scheduler(loop)

APP.on_startup.append(_on_startup)


def main():
    #start_scheduler()
    app = web.Application()
    app.add_routes(routes)
    web.run_app(APP, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
