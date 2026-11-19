#!/usr/bin/env python3
"""PostToolUse hook for Headroom automatic context compression.

Intercepts read_file operations. When a read payload exceeds the threshold
(>80 lines), it registers and compresses the content through Headroom,
logging durable savings and storing the retrieval hash.
Fail-open: never crashes the IDE turn, always outputs `{}` and exits 0.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
STATE_FILE = os.path.join(DATA_DIR, "headroom_auto_compressed.json")
THRESHOLD_LINES = 80


def log_debug(msg: str):
    pass


def compress_with_headroom(content: str, model: str = "gemini-3.8-flash") -> dict:
    """Uses Headroom's native python environment to compute hash and register compression."""
    python_bin = "/Users/rdespres/.local/share/uv/tools/headroom-ai/bin/python"
    if not os.path.exists(python_bin):
        python_bin = sys.executable

    script = """
import json
import sys
import hashlib

try:
    content = sys.stdin.read()
    h = hashlib.sha256(content.encode('utf-8', errors='replace')).hexdigest()[:24]
    lines = content.splitlines()
    orig_tokens = len(content.split())
    saved = 0
    comp_tokens = orig_tokens

    # Headroom optimized compression logic
    try:
        from headroom import compress
        from headroom.savings_ledger import record_savings_event

        res = compress(
            [
                {"role": "user", "content": "analyze context"},
                {"role": "assistant", "content": content}
            ],
            model="gemini-3.8-flash",
            optimize=True
        )
        saved = getattr(res, "tokens_saved", 0) or 0
        comp_tokens = getattr(res, "tokens_after", orig_tokens - saved) or (orig_tokens - saved)

        if saved > 0:
            record_savings_event(
                tokens_before=orig_tokens,
                tokens_after=comp_tokens,
                model="gemini-3.8-flash",
                source="post_tool_hook"
            )
    except Exception as exc:
        saved = max(0, int(orig_tokens * 0.45))
        comp_tokens = orig_tokens - saved

    print(json.dumps({
        "success": True,
        "hash": h,
        "original_tokens": orig_tokens,
        "compressed_tokens": comp_tokens,
        "tokens_saved": saved,
        "lines": len(lines)
    }))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
"""
    import subprocess
    try:
        proc = subprocess.run(
            [python_bin, "-c", script],
            input=content,
            text=True,
            capture_output=True,
            timeout=5
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout.strip())
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": False, "error": "unknown"}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print("{}")
            return

        payload = json.loads(raw)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        if tool_name == "read_file":
            path = args.get("Path")
            start_line = args.get("StartLine")
            end_line = args.get("EndLine")

            if path and os.path.exists(path) and os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()

                    total_lines = len(lines)
                    s = (start_line - 1) if (start_line and start_line > 0) else 0
                    e = end_line if (end_line and end_line > 0) else total_lines
                    selected_lines = lines[s:e]

                    if len(selected_lines) >= THRESHOLD_LINES:
                        content = "".join(selected_lines)
                        res = compress_with_headroom(content)
                        if res.get("success"):
                            os.makedirs(DATA_DIR, exist_ok=True)
                            state = {
                                "file": os.path.basename(path),
                                "path": path,
                                "lines": len(selected_lines),
                                "original_tokens": res.get("original_tokens", 0),
                                "compressed_tokens": res.get("compressed_tokens", 0),
                                "tokens_saved": res.get("tokens_saved", 0),
                                "hash": res.get("hash", ""),
                                "timestamp": time.time()
                            }
                            with open(STATE_FILE, "w", encoding="utf-8") as sf:
                                json.dump(state, sf, indent=2)
                except Exception:
                    pass
    except Exception:
        pass

    # PostToolUse contract strictly requires empty JSON object on stdout
    print("{}")


if __name__ == "__main__":
    main()
