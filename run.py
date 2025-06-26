import atexit
import logging
import signal
import sys
import threading

from bot.bot import bot_main, bot_shutdown
from shared.log import get_ray_id, log_event


def run_flask():
    from web.backend.app import app

    app.run(debug=True, use_reloader=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Discord bot and/or Flask backend.")
    parser.add_argument("--bot", action="store_true", help="Run Discord bot")
    parser.add_argument("--web", action="store_true", help="Run Flask web backend")
    args = parser.parse_args()

    if args.bot and args.web:
        bot_thread = threading.Thread(target=bot_main)
        web_thread = threading.Thread(target=run_flask)
        bot_thread.start()
        web_thread.start()
        bot_thread.join()
        web_thread.join()
    elif args.bot:
        bot_main()
    elif args.web:
        run_flask()
    else:
        print("Please specify --bot, --web, or both.")


async def handle_exit(*args):
    logging.shutdown()
    await bot_shutdown()  # Ensure the bot is properly shut down
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# At the end of the file, add shutdown log
atexit.register(lambda: log_event("SHUTDOWN", {"event": "SHUTDOWN", "ray_id": get_ray_id()}))
