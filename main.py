import sys
import os
import requests
from parser import parse_args
from net import (
    fetch_databox, download_file, extract_cookie_value,
    check_upload_permission, upload_file, delete_file
)

# Global mapping: stores file info (path, neid, path_type) by index number
pan_files = {}


def get_cookie_via_webview(width, height):
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QUrl
    from PyQt5.QtWebEngineWidgets import QWebEngineView

    app = QApplication(sys.argv)
    view = QWebEngineView()
    target_url = "https://pan.hit.edu.cn/"
    cookie = None

    def on_load_finished(ok):
        nonlocal cookie
        if not ok:
            return
        current_url = view.url().toString()
        if current_url.startswith(target_url):
            view.page().runJavaScript("document.cookie",
                                      lambda js_cookie: callback(js_cookie))

    def callback(js_cookie):
        nonlocal cookie
        cookie = js_cookie.strip()
        app.quit()

    view.loadFinished.connect(on_load_finished)
    view.load(QUrl(
        "https://ids.hit.edu.cn/authserver/login?"
        "service=https://pan.hit.edu.cn/custom-sso-cas/cas/login"
    ))
    view.resize(width, height)
    view.show()
    app.exec_()
    return cookie


def truncate_middle(s, max_len=30):
    """Truncate string in the middle if longer than max_len, replace with '*'"""
    if len(s) <= max_len:
        return s
    half = (max_len - 1) // 2
    return s[:half] + '*' + s[-half:]


def format_size(size_bytes):
    """Convert size in bytes to human-readable format"""
    if size_bytes is None:
        return "N/A"
    try:
        size = int(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def display_items(cookie_str):
    """Fetch and display file list, updating global pan_files mapping"""
    global pan_files
    json_data = fetch_databox(cookie_str)
    if json_data is None:
        return

    content = json_data.get('content')
    if not isinstance(content, list):
        print("No 'content' list found in response.")
        return

    pan_files.clear()
    rows = []
    for idx, item in enumerate(content, start=1):
        path = item.get('path', '')
        name = path.split('/')[-1] if path else ''
        modified = item.get('modified', '')
        size_raw = item.get('size', 0)
        size = format_size(size_raw)
        neid = item.get('neid', '')
        path_type = item.get('path_type', '')
        rows.append((idx, name, modified, size))
        pan_files[idx] = {
            'path': path,
            'neid': neid,
            'path_type': path_type
        }

    col_widths = (5, 50, 50, 50)

    # Output header
    header = (f"{'No.':<{col_widths[0]}}  "
              f"{'Name':<{col_widths[1]}}  "
              f"{'Date':<{col_widths[2]}}  "
              f"{'Size':<{col_widths[3]}}")
    print(header)

    # Output rows
    for row in rows:
        no = str(row[0])
        name = truncate_middle(row[1], max_len=30)
        date = truncate_middle(row[2], max_len=30)
        size_val = truncate_middle(row[3], max_len=30)
        print(f"{no:<{col_widths[0]}}  "
              f"{name:<{col_widths[1]}}  "
              f"{date:<{col_widths[2]}}  "
              f"{size_val:<{col_widths[3]}}")
    print(f"\nTotal {len(rows)} items.")


def show_help():
    """Display help message"""
    help_text = """
Available commands:
  items                 - Display the list of files (Name, Date, Size)
  download <No.> [path] - Download file by number. Optionally specify save
                          path (file or directory)
  upload <file_path>    - Upload a local file (max 1GB)
  delete <No.>          - Delete file by number
  cookie                - Show current cookie
  help                  - Show this help message
  exit                  - Exit the program
"""
    print(help_text)


def handle_items(cookie):
    display_items(cookie)


def handle_cookie(cookie):
    print(f"Cookie: {cookie}")


def handle_download(cookie, parts):
    if len(parts) < 2:
        print("Usage: download <No.> [local_path]")
        return
    try:
        file_no = int(parts[1])
    except ValueError:
        print("Error: <No.> must be a number.")
        return
    if file_no not in pan_files:
        print(f"Error: Invalid number {file_no}. Use 'items' to see numbers.")
        return
    file_path = pan_files[file_no]['path']
    dest = parts[2] if len(parts) >= 3 else None
    download_file(cookie, file_path, dest)


def handle_upload(cookie, parts):
    if len(parts) < 2:
        print("Usage: upload <local_file_path>")
        return
    local_file = parts[1]
    if not os.path.exists(local_file):
        print(f"Error: File '{local_file}' does not exist.")
        return
    file_size = os.path.getsize(local_file)
    if file_size > 1073741824:
        print("Error: File size exceeds 1GB. Upload not supported.")
        return
    success, info = check_upload_permission(cookie, file_size)
    if success:
        print("Upload permission check passed. Starting upload...")
        upload_success, upload_result = upload_file(cookie, local_file)
        if upload_success:
            if (isinstance(upload_result, dict) and
               upload_result.get("result") == "success"):
                print("Upload file success.")
                display_items(cookie)
            else:
                print(f"Upload failed: {upload_result}")
        else:
            print(f"Upload failed: {upload_result}")
    else:
        print(f"Upload check failed: {info}")


def handle_delete(cookie, parts):
    if len(parts) < 2:
        print("Usage: delete <No.>")
        return
    try:
        file_no = int(parts[1])
    except ValueError:
        print("Error: <No.> must be a number.")
        return
    if file_no not in pan_files:
        print(f"Error: Invalid number {file_no}. Use 'items' to see numbers.")
        return
    info = pan_files[file_no]
    success, result = delete_file(cookie, info['neid'],
                                  info['path'], info['path_type'])
    if success:
        if (isinstance(result, dict) and 'success' in result and
           result.get('success')):
            print("Delete successful.")
            display_items(cookie)
        else:
            print(f"Delete failed: Unexpected response. Response: {result}")
    else:
        print(f"Delete failed: {result}")


def handle_help():
    show_help()


def handle_exit():
    print("Goodbye!")
    return True


def main():
    global pan_files
    args = parse_args()
    if args.cookie:
        cookie = args.cookie
        if cookie.startswith("Cookie: "):
            cookie = cookie[8:]
    else:
        print("No cookie provided. Launching webview to obtain cookie...")
        cookie = get_cookie_via_webview(args.window_size[0],
                                        args.window_size[1])

    # Check if cookie is empty or None
    if not cookie:
        print("ERROR: No valid cookie found. Please provide a cookie via --cookie, "
              "or use the webview to log in and capture the cookie automatically.")
        sys.exit(1)

    print(f"Cookie: {cookie}\n")
    print("Interactive mode. Type 'help' for commands.\n")

    display_items(cookie)

    while True:
        try:
            cmd_line = input("> ").strip()
            if not cmd_line:
                continue
            parts = cmd_line.split()
            cmd = parts[0].lower()

            if cmd == "items":
                handle_items(cookie)
            elif cmd == "cookie":
                handle_cookie(cookie)
            elif cmd == "download":
                handle_download(cookie, parts)
            elif cmd == "upload":
                handle_upload(cookie, parts)
            elif cmd == "delete":
                handle_delete(cookie, parts)
            elif cmd == "help":
                handle_help()
            elif cmd == "exit":
                if handle_exit():
                    break
            else:
                print(f"Unknown command: {cmd}. Type 'help' for commands.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
