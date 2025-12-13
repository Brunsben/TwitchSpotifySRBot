"""Main entry point for the Twitch Spotify Bot."""
import logging
from pathlib import Path

from src.ui import BotGUI
from src.utils import setup_logging
from src.constants import APP_VERSION


def main():
    """Run the application."""
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Use DEBUG level to see all messages during troubleshooting
    setup_logging(
        log_file=log_dir / "bot.log",
        level=logging.DEBUG
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Twitch Spotify Bot v{APP_VERSION}")
    logger.info(f"Log file: {log_dir / 'bot.log'}")
    
    # Create and run GUI
    app = BotGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
