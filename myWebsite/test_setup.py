"""
Quick test script to verify the setup is working correctly.
Run this with: python test_setup.py
"""

import os
import sys
import yaml

def check_environment():
    """Check that the environment is set up correctly."""
    print("Checking environment...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check required packages
    try:
        import flask
        print(f"Flask version: {flask.__version__}")
    except ImportError:
        print("ERROR: Flask not installed")
        
    try:
        import markdown
        print(f"Markdown version: {markdown.version}")
    except ImportError:
        print("ERROR: Markdown not installed")
    
    try:
        print(f"PyYAML version: {yaml.__version__}")
    except ImportError:
        print("ERROR: PyYAML not installed")
    
    # Check file structure
    required_dirs = [
        'static',
        'static/css',
        'static/js',
        'static/css/blog',
        'templates',
        'templates/blog',
        'templates/dynamic',
        'content/blog/posts',
    ]
    
    print("\nChecking directory structure...")
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ {directory}")
        else:
            print(f"✗ {directory} (missing)")

    # Check for critical files
    required_files = [
        'app.py',
        'templates/base.html',
        'templates/index.html',
        'templates/dynamic/animations.css',
        'static/js/animations.js',
        'static/css/blog/base.css',
    ]
    
    print("\nChecking critical files...")
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (missing)")

if __name__ == "__main__":
    check_environment()
    print("\nTest setup complete. If there are any errors above, please fix them before continuing.")
