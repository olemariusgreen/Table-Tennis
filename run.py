"""Start the website:  python run.py

Works from any directory and needs no install or PYTHONPATH, because it puts
this repo's src/ on the path itself.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from table_tennis.server import main

if __name__ == "__main__":
    main()
