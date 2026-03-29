from pathlib import Path

from config import settings


PROJECT_ROOT=Path(settings.BASE_DIR)
NODE_ANALYZER_DIR = PROJECT_ROOT / "js_analyzer"
NODE_ANALYZER_SCRIPT = NODE_ANALYZER_DIR / "analyze.js"