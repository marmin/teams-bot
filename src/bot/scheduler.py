import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

_scheduler = None
_loop = None  # the aiohttp loop we capture at startup


def start_scheduler(loop: asyncio.AbstractEventLoop):
    """
    Start the APScheduler bound to the given event loop.
    """
    global _scheduler, _loop
    _loop = loop

    if _scheduler is None:
        _scheduler = AsyncIOScheduler(event_loop=loop)  # bind to this loop
        _scheduler.start()
        logging.info(f"[SCHED] started (loop id={id(loop)})")

def schedule_in_minutes(n_minutes, coro_func, *args, **kwargs):
    run_time = datetime.now() + timedelta(minutes=n_minutes)
    logging.info(f"[SCHED] job scheduled for {run_time.isoformat()} (in {n_minutes} min)")

    def _job_wrapper():
        # Ensure the coroutine runs on the aiohttp loop even if APScheduler calls from another thread
        asyncio.run_coroutine_threadsafe(coro_func(*args, **kwargs), _loop)

    _scheduler.add_job(_job_wrapper, "date", run_date=run_time, misfire_grace_time=120, coalesce=True)
