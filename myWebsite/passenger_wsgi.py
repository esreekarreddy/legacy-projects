import sys
import os

# Use system Python directly
INTERP = "/usr/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add the directory of the app to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask application
from app import app as application
