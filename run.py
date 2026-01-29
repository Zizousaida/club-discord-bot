import logging
import os
import sys

# Ensure the src directory is on the import path so we can import bot, config, etc.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from bot import create_bot  # noqa: E402
import config  # noqa: E402


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    )

    if not config.DISCORD_TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is not set. Create a .env file based on .env.example and provide your bot token."
        )

    bot = create_bot()
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()


