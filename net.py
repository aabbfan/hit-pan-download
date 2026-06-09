import sys
import os
import json
import uuid
import requests

DEFAULT_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) '
                   'Gecko/20100101 Firefox/120.0'),
    'Referer': 'https://pan.hit.edu.cn',
}


def extract_cookie_value(cookie_str, key):
    """Extract value of given key from cookie string"""
    if not cookie_str:
        return None
    pairs = cookie_str.split(';')
    for pair in pairs:
        pair = pair.strip()
        if pair.startswith(key + '='):
            return pair[len(key) + 1:]
    return None


def fetch_databox(cookie_str):
    """Send request to fetch databox data"""
    s_value = extract_cookie_value(cookie_str, 'S')
    if not s_value:
        print("Error: 'S' not found in cookie", file=sys.stderr)
        return None

    url = (
        "https://pan.hit.edu.cn/v2/metadata_page/databox/"
        "?path_type=self&page_button_count=1&include_deleted=false"
        "&page_size=500&waitContent=.lui-filelist&page_num=0&offset=0"
        f"&sort=desc&orderby=mtime&account_id=1&S={s_value}"
    )

    headers = DEFAULT_HEADERS.copy()
    headers['Cookie'] = cookie_str

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return None


def download_file(cookie_str, file_path, dest_path=None):
    """Download file from cloud storage to local path"""
    s_value = extract_cookie_value(cookie_str, 'S')
    if not s_value:
        print("Error: 'S' not found in cookie", file=sys.stderr)
        return False

    url = (
        f"https://pan.hit.edu.cn:10081/v2/files/databox/{file_path}"
        "?path_type=self&from=&rev=&action=&op_type="
        f"&S={s_value}"
    )

    headers = DEFAULT_HEADERS.copy()
    headers['Cookie'] = cookie_str

    if dest_path is None:
        filename = os.path.basename(file_path)
        dest_path = os.path.join(os.getcwd(), filename)
    else:
        if os.path.isdir(dest_path):
            filename = os.path.basename(file_path)
            dest_path = os.path.join(dest_path, filename)

    try:
        print(f"Downloading: {file_path} -> {dest_path}")
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        print("\nDownload completed successfully.")
        return True
    except requests.RequestException as e:
        print(f"\nDownload failed: {e}", file=sys.stderr)
        return False


def check_upload_permission(cookie_str, file_size):
    """Check upload permission, return (success, info)"""
    s_value = extract_cookie_value(cookie_str, 'S')
    if not s_value:
        return False, "Error: 'S' not found in cookie"

    url = (
        f"https://pan.hit.edu.cn/v2/fileops/auth_upload/databox/"
        f"?path_type=self&bytes={file_size}&account_id=1&S={s_value}"
    )

    headers = DEFAULT_HEADERS.copy()
    headers['Cookie'] = cookie_str

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            return True, data
        else:
            msgcode = data.get("msgcode", "unknown")
            message = data.get("message", "unknown error")
            return False, f"{msgcode} : {message}"
    except requests.RequestException as e:
        return False, str(e)


def upload_file_with_progress(url, file_path, headers):
    """Upload file with progress display, return response object"""
    boundary = str(uuid.uuid4())
    content_type = f'multipart/form-data; boundary={boundary}'
    headers['Content-Type'] = content_type

    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    def multipart_generator():
        yield f'--{boundary}\r\n'.encode()
        yield (f'Content-Disposition: form-data; name="file"; '
               f'filename="{filename}"\r\n').encode()
        yield 'Content-Type: application/octet-stream\r\n\r\n'.encode()
        with open(file_path, 'rb') as f:
            sent = 0
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sent += len(chunk)
                percent = (sent / file_size) * 100
                print(f"\rUploading... {percent:.1f}%", end='', flush=True)
                yield chunk
        print()
        yield f'\r\n--{boundary}--\r\n'.encode()

    response = requests.post(url, data=multipart_generator(),
                             headers=headers, timeout=60)
    return response


def upload_file(cookie_str, local_file_path):
    """Upload file to HIT cloud storage, return (success, result)"""
    s_value = extract_cookie_value(cookie_str, 'S')
    if not s_value:
        return False, "Error: 'S' not found in cookie"

    filename = os.path.basename(local_file_path)
    cookie_query = cookie_str.replace('; ', '&').replace(';', '&')
    url = (
        f"https://pan.hit.edu.cn:10081/v2/files/databox/{filename}"
        f"?{cookie_query}&overwrite=true&source=file&path_type=self&="
    )

    headers = DEFAULT_HEADERS.copy()

    try:
        response = upload_file_with_progress(url, local_file_path, headers)
        response.raise_for_status()
        result = response.json()
        return True, result
    except requests.RequestException as e:
        return False, str(e)


def delete_file(cookie_str, neid, path, path_type):
    """Delete file, return (success, result)"""
    s_value = extract_cookie_value(cookie_str, 'S')
    if not s_value:
        return False, "Error: 'S' not found in cookie"

    url = f"https://pan.hit.edu.cn/v2/fileops/batch_delete?account_id=1&S={s_value}"
    headers = DEFAULT_HEADERS.copy()
    headers['Cookie'] = cookie_str
    headers['Content-Type'] = 'application/x-www-form-urlencoded'

    payload_dict = {
        "pathes": [{
            "root": "databox",
            "neid": neid,
            "path": path,
            "from": "",
            "path_type": path_type,
            "prefix_neid": ""
        }]
    }
    json_str = json.dumps(payload_dict)
    data = {'json': json_str}

    try:
        response = requests.post(url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        return False, str(e)
