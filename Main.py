#!/usr/bin/env python3
"""
devwatch - A multi-purpose developer utility CLI
Monitor URLs, summarize webpages, organize files, and chat with AI.
"""

import argparse
import sys
import os
import json
import time
import shutil
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


# ─── ANSI Colors ────────────────────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"

def banner():
    print(f"""
{C.CYAN}{C.BOLD}
  ██████╗ ███████╗██╗   ██╗██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
  ██╔══██╗██╔════╝██║   ██║██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
  ██║  ██║█████╗  ██║   ██║██║ █╗ ██║███████║   ██║   ██║     ███████║
  ██║  ██║██╔══╝  ╚██╗ ██╔╝██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
  ██████╔╝███████╗ ╚████╔╝ ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝  ╚═══╝   ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
{C.RESET}{C.GRAY}  Your all-in-one developer utility — monitor · summarize · organize · chat{C.RESET}
""")


# ─── CONFIG ──────────────────────────────────────────────────────────────────

CONFIG_PATH = Path.home() / ".devwatch" / "config.json"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"urls": [], "api_key": os.environ.get("ANTHROPIC_API_KEY", "")}

def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# ─── MONITOR ─────────────────────────────────────────────────────────────────

def cmd_monitor(args):
    """Check if URLs are up and measure response time."""
    cfg = load_config()

    urls = list(args.urls) if args.urls else []
    if not urls:
        urls = cfg.get("urls", [])

    if not urls:
        print(f"{C.YELLOW}No URLs to monitor. Add some:{C.RESET}")
        print(f"  devwatch monitor --add https://example.com")
        print(f"  devwatch monitor https://example.com https://google.com")
        return

    if args.add:
        for url in args.add:
            if url not in cfg["urls"]:
                cfg["urls"].append(url)
                print(f"{C.GREEN}✓ Added:{C.RESET} {url}")
        save_config(cfg)
        if not urls:
            return

    if args.remove:
        for url in args.remove:
            if url in cfg["urls"]:
                cfg["urls"].remove(url)
                print(f"{C.RED}✗ Removed:{C.RESET} {url}")
        save_config(cfg)

    loops = args.watch if args.watch else 1
    interval = args.interval if args.interval else 5

    try:
        for i in range(loops):
            if loops > 1:
                print(f"\n{C.GRAY}[{datetime.now().strftime('%H:%M:%S')}] Checking... (Ctrl+C to stop){C.RESET}")
            else:
                print(f"\n{C.BOLD}{'URL':<45} {'STATUS':<10} {'TIME':>8}{C.RESET}")
                print(C.GRAY + "─" * 66 + C.RESET)

            for url in urls:
                check_url(url)

            if i < loops - 1:
                time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{C.GRAY}Stopped.{C.RESET}")


def check_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        start = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "devwatch/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = (time.time() - start) * 1000
            status = resp.status
            if status < 300:
                icon = f"{C.GREEN}●{C.RESET}"
                status_str = f"{C.GREEN}{status} OK{C.RESET}"
            elif status < 400:
                icon = f"{C.YELLOW}●{C.RESET}"
                status_str = f"{C.YELLOW}{status} REDIRECT{C.RESET}"
            else:
                icon = f"{C.RED}●{C.RESET}"
                status_str = f"{C.RED}{status} ERROR{C.RESET}"

            time_color = C.GREEN if elapsed < 500 else C.YELLOW if elapsed < 1500 else C.RED
            time_str = f"{time_color}{elapsed:.0f}ms{C.RESET}"

            short = url[:42] + "..." if len(url) > 45 else url
            print(f" {icon} {short:<45} {status_str:<18} {time_str:>8}")

    except urllib.error.HTTPError as e:
        print(f" {C.RED}●{C.RESET} {url[:45]:<45} {C.RED}{e.code} ERROR{C.RESET}")
    except Exception as e:
        msg = str(e)[:30]
        print(f" {C.RED}●{C.RESET} {url[:45]:<45} {C.RED}UNREACHABLE{C.RESET}  {C.GRAY}{msg}{C.RESET}")


# ─── SUMMARIZE ───────────────────────────────────────────────────────────────

def cmd_summarize(args):
    """Fetch a webpage and summarize it with AI."""
    url = args.url

    api_key = os.environ.get("ANTHROPIC_API_KEY") or load_config().get("api_key", "")
    if not api_key:
        print(f"{C.RED}Error:{C.RESET} No Anthropic API key found.")
        print(f"  Set it: {C.CYAN}export ANTHROPIC_API_KEY=your_key_here{C.RESET}")
        print(f"  Or run: {C.CYAN}devwatch config --key YOUR_KEY{C.RESET}")
        return

    print(f"{C.CYAN}Fetching:{C.RESET} {url}")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 devwatch/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            # Try utf-8, fallback to latin-1
            try:
                html = raw.decode("utf-8")
            except Exception:
                html = raw.decode("latin-1")
    except Exception as e:
        print(f"{C.RED}Failed to fetch URL:{C.RESET} {e}")
        return

    # Strip HTML tags simply
    import re
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text[:8000]  # Trim to avoid huge prompts

    print(f"{C.CYAN}Summarizing with AI...{C.RESET}\n")

    length_map = {"short": "2-3 sentences", "medium": "a paragraph", "long": "3-4 paragraphs"}
    length_desc = length_map.get(args.length, "a paragraph")

    prompt = f"""Summarize the following webpage content in {length_desc}. 
Be concise, factual, and highlight the most important points.

URL: {url}

Content:
{text}"""

    response = call_claude(api_key, prompt)
    if response:
        print(f"{C.BOLD}Summary:{C.RESET}")
        print(f"{C.WHITE}{response}{C.RESET}")
        if args.save:
            out = Path(args.save)
            out.write_text(f"URL: {url}\nDate: {datetime.now()}\n\n{response}\n")
            print(f"\n{C.GREEN}Saved to:{C.RESET} {out}")


# ─── ORGANIZE ────────────────────────────────────────────────────────────────

FILE_TYPES = {
    "Images":     [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".bmp", ".tiff"],
    "Videos":     [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
    "Audio":      [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Documents":  [".pdf", ".doc", ".docx", ".txt", ".md", ".odt", ".rtf", ".pages"],
    "Spreadsheets": [".xls", ".xlsx", ".csv", ".numbers", ".ods"],
    "Presentations": [".ppt", ".pptx", ".key"],
    "Code":       [".py", ".js", ".ts", ".html", ".css", ".sh", ".json", ".yaml", ".yml",
                   ".toml", ".rs", ".go", ".java", ".cpp", ".c", ".h", ".rb", ".php"],
    "Archives":   [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2"],
    "Executables":[".exe", ".deb", ".rpm", ".AppImage", ".dmg"],
}

def cmd_organize(args):
    """Auto-sort files in a folder by type."""
    folder = Path(args.folder).expanduser().resolve()

    if not folder.exists():
        print(f"{C.RED}Error:{C.RESET} Folder not found: {folder}")
        return

    files = [f for f in folder.iterdir() if f.is_file()]

    if not files:
        print(f"{C.YELLOW}No files found in:{C.RESET} {folder}")
        return

    print(f"{C.BOLD}Scanning:{C.RESET} {folder}")
    print(f"{C.GRAY}Found {len(files)} file(s){C.RESET}\n")

    moves = []
    for f in files:
        ext = f.suffix.lower()
        category = "Other"
        for cat, exts in FILE_TYPES.items():
            if ext in exts:
                category = cat
                break
        dest_dir = folder / category
        dest_file = dest_dir / f.name
        moves.append((f, dest_dir, dest_file, category))

    # Preview
    from collections import Counter
    cats = Counter(m[3] for m in moves)
    for cat, count in sorted(cats.items()):
        print(f"  {C.CYAN}{cat:<18}{C.RESET} → {count} file(s)")

    print()

    if args.dry_run:
        print(f"{C.YELLOW}Dry run — no files moved. Remove --dry-run to apply.{C.RESET}")
        return

    if not args.yes:
        answer = input(f"Move {len(files)} files into subfolders? [y/N] ").strip().lower()
        if answer != "y":
            print("Cancelled.")
            return

    moved = 0
    for f, dest_dir, dest_file, cat in moves:
        dest_dir.mkdir(exist_ok=True)
        # Handle filename conflicts
        if dest_file.exists():
            stem = f.stem
            suffix = f.suffix
            counter = 1
            while dest_file.exists():
                dest_file = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        shutil.move(str(f), str(dest_file))
        moved += 1

    print(f"{C.GREEN}✓ Organized {moved} files into subfolders.{C.RESET}")


# ─── CHAT ────────────────────────────────────────────────────────────────────

def cmd_chat(args):
    """Chat with Claude AI in the terminal."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or load_config().get("api_key", "")
    if not api_key:
        print(f"{C.RED}Error:{C.RESET} No Anthropic API key found.")
        print(f"  Set it: {C.CYAN}export ANTHROPIC_API_KEY=your_key_here{C.RESET}")
        return

    print(f"{C.BOLD}{C.CYAN}devwatch AI Chat{C.RESET} {C.GRAY}(type 'exit' or Ctrl+C to quit){C.RESET}\n")

    history = []
    if args.system:
        system = args.system
    else:
        system = "You are a helpful assistant built into devwatch, a developer CLI tool. Be concise and practical. Use plain text — no markdown formatting."

    try:
        while True:
            try:
                user_input = input(f"{C.GREEN}You:{C.RESET} ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "bye", ":q"):
                print(f"{C.GRAY}Goodbye!{C.RESET}")
                break

            history.append({"role": "user", "content": user_input})

            print(f"{C.CYAN}AI:{C.RESET} ", end="", flush=True)
            response = call_claude(api_key, None, messages=history, system=system)
            if response:
                print(f"{C.WHITE}{response}{C.RESET}")
                history.append({"role": "assistant", "content": response})
            print()

    except KeyboardInterrupt:
        print(f"\n{C.GRAY}Goodbye!{C.RESET}")


# ─── CONFIG CMD ──────────────────────────────────────────────────────────────

def cmd_config(args):
    cfg = load_config()
    if args.key:
        cfg["api_key"] = args.key
        save_config(cfg)
        print(f"{C.GREEN}✓ API key saved to {CONFIG_PATH}{C.RESET}")
    if args.show:
        key = cfg.get("api_key", "")
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "(not set)"
        print(f"  API Key: {masked}")
        print(f"  Watched URLs: {cfg.get('urls', [])}")
        print(f"  Config file: {CONFIG_PATH}")


# ─── CLAUDE API ──────────────────────────────────────────────────────────────

def call_claude(api_key, prompt, messages=None, system=None):
    import json
    import urllib.request

    if messages is None:
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": messages,
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"{C.RED}API Error {e.code}:{C.RESET} {body}")
        return None
    except Exception as e:
        print(f"{C.RED}Error:{C.RESET} {e}")
        return None


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="devwatch",
        description="Your all-in-one developer utility CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  monitor     Check if URLs are up and measure response time
  summarize   Fetch a webpage and summarize it with AI
  organize    Auto-sort files in a folder by type
  chat        Chat with AI in your terminal
  config      Manage API key and settings

examples:
  devwatch monitor https://google.com https://github.com
  devwatch monitor --add https://mysite.com
  devwatch monitor --watch 10 --interval 30
  devwatch summarize https://news.ycombinator.com --length short
  devwatch organize ~/Downloads --dry-run
  devwatch organize ~/Downloads -y
  devwatch chat
  devwatch config --key sk-ant-...
"""
    )

    sub = parser.add_subparsers(dest="command")

    # monitor
    m = sub.add_parser("monitor", help="Check if URLs are up")
    m.add_argument("urls", nargs="*", help="URLs to check")
    m.add_argument("--add", nargs="+", metavar="URL", help="Save URLs to watchlist")
    m.add_argument("--remove", nargs="+", metavar="URL", help="Remove URLs from watchlist")
    m.add_argument("--watch", type=int, metavar="N", help="Repeat N times")
    m.add_argument("--interval", type=int, default=5, metavar="SEC", help="Seconds between checks (default: 5)")

    # summarize
    s = sub.add_parser("summarize", help="Summarize a webpage with AI")
    s.add_argument("url", help="URL to summarize")
    s.add_argument("--length", choices=["short", "medium", "long"], default="medium")
    s.add_argument("--save", metavar="FILE", help="Save summary to a file")

    # organize
    o = sub.add_parser("organize", help="Auto-sort files by type")
    o.add_argument("folder", help="Folder to organize")
    o.add_argument("--dry-run", action="store_true", help="Preview without moving files")
    o.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # chat
    ch = sub.add_parser("chat", help="Chat with AI in the terminal")
    ch.add_argument("--system", metavar="PROMPT", help="Custom system prompt")

    # config
    cfg = sub.add_parser("config", help="Manage settings")
    cfg.add_argument("--key", metavar="API_KEY", help="Set your Anthropic API key")
    cfg.add_argument("--show", action="store_true", help="Show current config")

    args = parser.parse_args()

    banner()

    if args.command == "monitor":
        cmd_monitor(args)
    elif args.command == "summarize":
        cmd_summarize(args)
    elif args.command == "organize":
        cmd_organize(args)
    elif args.command == "chat":
        cmd_chat(args)
    elif args.command == "config":
        cmd_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
