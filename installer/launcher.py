"""SIM AT Command Tool - Launcher for PyInstaller exe.
Starts Flask server and opens browser automatically."""

import sys
import os
import threading
import webbrowser
import socket
import multiprocessing


def get_free_port(preferred=8083):
    """Check if preferred port is available, otherwise find a free one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', preferred))
            return preferred
        except OSError:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]


def open_browser(port):
    """Open browser after a short delay to let Flask start."""
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://127.0.0.1:{port}')


def main():
    # When running as PyInstaller bundle, adjust paths
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Add src to path so Flask app can import modules
    src_dir = os.path.join(base_dir, 'src')
    sys.path.insert(0, src_dir)

    # Change working directory to src for template resolution
    os.chdir(src_dir)

    port = get_free_port(8083)

    # Import Flask app after path setup
    from app import app

    # Frozen 환경에서 Flask template 경로를 명시적으로 지정
    template_dir = os.path.join(src_dir, 'templates')
    app.template_folder = template_dir

    print()
    print('  +========================================+')
    print('  |  SIM AT Command Tool -- Web UI          |')
    print('  +========================================+')
    print()
    print(f'  [START] http://127.0.0.1:{port}')
    print()

    # Open browser in background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start Flask (no debug/reloader in frozen mode)
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
