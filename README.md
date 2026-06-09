# HITPanDownload

A command-line interactive tool for HIT (Harbin Institute of Technology) cloud storage (pan.hit.edu.cn).  
It allows you to list, download, upload (≤1GB), and delete files using cookie authentication.

## Features

- **List files** – Display all files in your databox with index number, name, modification date, and size.
- **Download files** – Download a file by its index number, optionally specify a local save path.
- **Upload files** – Upload local files (max 1 GB) after permission check.
- **Delete files** – Remove a file from the cloud storage by index number.
- **Cookie management** – View current cookie or obtain it automatically via an embedded webview (PyQt5).
- **Interactive shell** – Simple command‑line interface with tab‑completion (not built‑in, but easy to type).

## Installation

### Prerequisites

- Python 3.6 or higher
- `pip` (Python package installer)

### Dependencies

The tool requires the following Python packages:
- `requests`
- `PyQt5`
- `PyQtWebEngine`

You can install them manually or let the installation process handle them.

### Install from source

1. Clone or download the project files (`main.py`, `net.py`, `parser.py`, `setup.py`).
2. Open a terminal in the project directory.
3. Run the installation command:

```bash
pip install .
```

This will install the package and create an executable script named hitpandownload.

Alternatively, you can run the script directly without installation:

```bash
python main.py [--cookie COOKIE_STRING] [--window-size WIDTH HEIGHT]
```

## Usage
After installation, launch the tool by typing:
```bash
# First time
hitpandownload  # Please make sure you have a graphic desktop environment
                # You can also get your cookie string after LOGIN

# When you want to use it on a desktop enviroment without graphic display
# such as ssh terminal
hitpandownload --cookie <Cookie String>
```

If you don't provide a cookie via the `--cookie` argument, an embedded webview will open for you to log in to `https://pan.hit.edu.cn/` and automatically capture the cookie.

### Command-line arguments
| Argument | Description |
| --- | --- |
| --cookie | Provide cookie string directly (e.g., "S=xxx; ..."). |
| --window-size | Set the size of the webview window (default: 800 600). |

### Interactive commands
Once the tool starts, you will see a prompt `>`. Available commands:
| command | Description |
| --- | --- |
| items   | Show the list of files with index numbers. |
| download <No.> [path] | Download the file with the given index number. Optional path can be a file or directory. | 
| upload <local_file_path> | Upload a local file (max size 1 GB). |
| delete <No.> | Delete the file with the given index number. |
| cookie | Display the current cookie string. |
| help | Show this help message. |
| exit | Quit the program. |

### Example session
```bash
$ hitpandownload
Cookie: S=abcdef12345; ...

Interactive mode. Type 'help' for commands.

No.  Name                                               Date                                               Size
1    document.pdf                                       2025-03-15 10:30:00                                1.2 MB
2    photo.jpg                                          2025-03-14 22:15:00                                3.4 MB

Total 2 items.

> download 1
Downloading: /document.pdf -> ./document.pdf
Progress: 100.0%
Download completed successfully.

> upload report.pdf
Upload permission check passed. Starting upload...
Uploading... 100.0%
Upload file success.

> delete 2
Delete successful.

> exit
Goodbye!
```

## Note
- Upload is limited to 1 GB per file.

- The delete operation sends a application/x-www-form-urlencoded POST request with a JSON payload.

- After successful upload or delete, the file list is automatically refreshed.

- All HTTP requests use a consistent User-Agent and Referer header defined in net.py

## Troubleshooting
- __Cookie not captured__  Make sure you complete the login in the webview and that the page redirects to `https://pan.hit.edu.cn/`.
- __Upload fails with size error__  Reduce file size or split it into smaller parts.

## License
This project is open‑source and provided as‑is. Use at your own risk.
