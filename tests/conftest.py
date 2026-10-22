import os
import sys
from pathlib import Path

ROX_TOOL_DIR = Path(__file__).resolve().parent.parent
os.chdir(ROX_TOOL_DIR)

SRC = ROX_TOOL_DIR / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
