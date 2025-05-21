import sys
from cli import main_cli
from gui import main_gui

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If there are arguments, assume CLI usage
        main_cli()
    else:
        # Otherwise, launch GUI
        main_gui()
