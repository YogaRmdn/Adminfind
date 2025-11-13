# scanner.py
import time
import random
import requests
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from options.headers import *
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timezone
from threading import Lock, Event

# --- Konfigurasi ---
MAX_WORKERS = 30
REQUEST_TIMEOUT = 6
DELAY_BETWEEN = 0.0
SAVE_RESULTS = True
RESULTS_FILE = "found_paths.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

schemes = ["https", "http"]

lock = Lock()
stop_event = Event()  

def make_session():
    s = requests.Session()
    retries = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST", "HEAD"])
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

def scan_path(target, word, session, save_file=None):
    if stop_event.is_set():
        return (None, None)

    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    headers["Referer"] = f"https://{target}/"

    if DELAY_BETWEEN > 0:
        total_sleep = DELAY_BETWEEN + random.random() * 0.02
        slept = 0.0
        step = 0.01
        while slept < total_sleep:
            if stop_event.is_set():
                return (None, None)
            time.sleep(step)
            slept += step

    for scheme in schemes:
        if stop_event.is_set():
            return (None, None)

        url = f"{scheme}://{target}/{word.lstrip('/')}"
        try:
            if stop_event.is_set():
                return (None, None)

            resp = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            code = resp.status_code

            if code < 400:
                with lock:
                    print(f"{g}[SUKSES] {code}{rs} {url}")
                    if save_file:
                        save_file.write(f"{datetime.now(timezone.utc).isoformat()} {code} {url}\n")
                return (url, code)
            elif code in (401, 403):
                with lock:
                    print(f"{r}[FAILED] {code}{rs} {url}")
                    if save_file:
                        save_file.write(f"{datetime.now(timezone.utc).isoformat()} {code} {url}\n")
                return (url, code)
            else:
                return (url, code)
        except requests.RequestException:
            if stop_event.is_set():
                return (None, None)
            continue
    return (None, None)

def _signal_handler(signum, frame):
    print(f"\n{r}[x] Diterima SIGINT/SIGTERM — menghentikan...")
    stop_event.set()
    try:
        sys.exit(0)
    except SystemExit:
        raise

def run():
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    save_fp = None
    try:
        clean_screen()
        header_tools()
        try:
            target = input(f"{y}[?]{rs} Domain target (contoh: example.com): ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{r}[x] Dibatalkan oleh pengguna saat input.")
            return

        if not target:
            print(f"{r}[!] Isi domain target dulu.")
            return

        wl_path = "wordlists/word.txt"
        try:
            with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                words = [w.strip() for w in f.read().splitlines() if w.strip()]
        except FileNotFoundError:
            print(f"{r}[!] File wordlist tidak ditemukan: {wl_path}")
            return

        max_workers = input(f"{y}[?]{rs} jumlah thread (default {MAX_WORKERS}): ").strip()
        try:
            max_workers = int(max_workers) if max_workers else MAX_WORKERS
        except ValueError:
            max_workers = MAX_WORKERS

        if SAVE_RESULTS:
            save_fp = open(RESULTS_FILE, "a", encoding="utf-8")
            print(f"{r}[!] Menyimpan hasil di: {RESULTS_FILE}")

        start = time.time()
        session = make_session()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(scan_path, target, w, session, save_fp) for w in words]

            try:
                for fut in as_completed(futures):
                    if stop_event.is_set():
                        for f in futures:
                            try:
                                f.cancel()
                            except Exception:
                                pass
                        break
                    try:
                        _ = fut.result()
                    except Exception:
                        pass
            except KeyboardInterrupt:
                stop_event.set()
                for f in futures:
                    try:
                        f.cancel()
                    except Exception:
                        pass

        elapsed = time.time() - start
        if stop_event.is_set():
            print(f"{r}[!] Dihentikan. Waktu berjalan: {elapsed:.2f}s. Hasil tersimpan: {RESULTS_FILE if SAVE_RESULTS else 'tidak disimpan'}")
        else:
            print(f"{g}[+] Selesai. Waktu: {elapsed:.2f}s. Hasil tersimpan: {RESULTS_FILE if SAVE_RESULTS else 'tidak disimpan'}")

    except Exception as e:
        print(f"{r}[!] Error: {e}")
    finally:
        try:
            if save_fp:
                save_fp.close()
        except Exception:
            pass

if __name__ == "__main__":
    run()
