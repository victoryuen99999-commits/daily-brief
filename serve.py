# -*- coding: utf-8 -*-
"""每日情報站 —— 本機／區域網絡伺服器
執行： python serve.py        然後開 http://localhost:8080/
手機會同一 Wi-Fi 用啟動時印出嘅 LAN 網址。
每 60 分鐘會自動重新抓一次資料（要關掉就設環境變數 AUTO=0）。
"""
import os, sys, json, time, socket, threading, mimetypes
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone, timedelta

import refresh

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
PORT = int(os.environ.get("PORT", "8090"))
INTERVAL = int(os.environ.get("INTERVAL_MIN", "60"))
AUTO = os.environ.get("AUTO", "1") != "0"
HKT = timezone(timedelta(hours=8))

STATE = {"last": None, "busy": False, "error": None}


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def do_refresh(tag="auto"):
    if STATE["busy"]:
        return
    STATE["busy"] = True
    STATE["started"] = time.time()
    try:
        d = refresh.build()
        STATE["last"] = d["generated_at"]
        STATE["error"] = None
        print(f"  [refresh:{tag}] {d['generated_at']}  " + "  ".join(
            f"{k}={len(d['sections'][k]['items'])}" for k in refresh.SEC_ORDER), flush=True)
    except Exception as e:
        STATE["error"] = f"{type(e).__name__}: {e}"
        print(f"  [refresh:{tag}] 失敗 {STATE['error']}（沿用舊資料）", flush=True)
    finally:
        STATE["busy"] = False


def watchdog():
    """抓取卡住超過 4 分鐘就解鎖，免得之後永遠唔再更新。"""
    while True:
        time.sleep(30)
        if STATE["busy"] and STATE.get("started") and time.time() - STATE["started"] > 240:
            STATE["busy"] = False
            STATE["error"] = "上一次抓取逾時（已解鎖）"
            print("  [watchdog] 抓取逾時，已解鎖", flush=True)


def loop():
    while True:
        do_refresh()
        time.sleep(max(60, INTERVAL * 60))


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def end_headers(self):
        if self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/api/live"):
            return self._json(200, {
                "ok": True, "mode": "live", "auto": AUTO,
                "last_refresh": STATE["last"], "error": STATE["error"],
                "now": datetime.now(HKT).isoformat(timespec="seconds"),
            })
        if self.path.startswith("/api/refresh"):
            do_refresh("manual")
            return self._json(200, {"ok": STATE["error"] is None, "last": STATE["last"], "error": STATE["error"]})
        return super().do_GET()

    def log_message(self, fmt, *args):
        try:
            msg = fmt % args
        except Exception:
            msg = str(fmt)
        if "/api/" in msg:
            return
        sys.stderr.write("  " + msg + "\n")


if __name__ == "__main__":
    mimetypes.add_type("text/javascript", ".js")
    print("=" * 54)
    print("  每日情報站")
    print("=" * 54)
    print(f"  電腦：  http://localhost:{PORT}/")
    print(f"  手機：  http://{lan_ip()}:{PORT}/     （同一個 Wi-Fi）")
    print(f"  自動更新：{'每 ' + str(INTERVAL) + ' 分鐘' if AUTO else '關閉'}")
    print("  按 Ctrl+C 停止")
    print("=" * 54)
    threading.Thread(target=watchdog, daemon=True).start()
    if AUTO:
        threading.Thread(target=loop, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
