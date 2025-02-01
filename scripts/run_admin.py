import streamlit.cli as stcli
import sys
import os

if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        os.path.join(os.path.dirname(__file__), "../src/admin/app.py"),
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    sys.exit(stcli.main()) 