"""Compatibility entry: same arguments as autovideo.py sua."""
import runpy
import sys
from pathlib import Path
sys.argv.insert(1,'sua')
runpy.run_path(str(Path(__file__).resolve().parents[3]/'autovideo.py'),run_name='__main__')
