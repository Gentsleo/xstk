#!/usr/bin/env python3
import sys
import os
import time
import argparse
import subprocess
import json
import re
import csv
import sqlite3
import datetime
import urllib.request
from bs4 import BeautifulSoup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vietlott_535.db")
CSV_PATH = os.path.join(BASE_DIR, "vietlott_535.csv")
JSON_PATH = os.path.join(BASE_DIR, "vietlott_535.json")
LOG_PATH = os.path.join(BASE_DIR, "auto_update.log")

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now}] {msg}"
    print(formatted)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def get_session_and_key():
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    url = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/winning-number-535"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    html = opener.open(req, timeout=15).read().decode("utf-8")
    
    key_match = re.search(r"ServerSideDrawResult\(RenderInfo,\s*[\x27\"]([^\x27\"]+)[\x27\"]", html)
    if not key_match:
        raise ValueError("Could not find Key in page HTML")
    key = key_match.group(1)
    
    render_req = urllib.request.Request(
        "https://vietlott.vn/ajaxpro/Vietlott.Utility.WebEnvironments,Vietlott.Utility.ashx",
        data=json.dumps({"SiteId": "main.frontend.vi"}).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "text/plain; charset=utf-8",
            "X-AjaxPro-Method": "ServerSideFrontEndCreateRenderInfo"
        }
    )
    render_info = json.loads(opener.open(render_req, timeout=15).read().decode("utf-8"))["value"]
    render_info["SiteLang"] = "vi"
    return opener, key, render_info

def fetch_page_draws(opener, key, render_info, arr_numbers, page_idx):
    payload = {
        "ORenderInfo": render_info,
        "Key": key,
        "GameDrawId": "",
        "ArrayNumbers": arr_numbers,
        "CheckMulti": False,
        "PageIndex": page_idx
    }
    req = urllib.request.Request(
        "https://vietlott.vn/ajaxpro/Vietlott.PlugIn.WebParts.Game535CompareWebPart,Vietlott.PlugIn.WebParts.ashx",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "text/plain; charset=utf-8",
            "X-AjaxPro-Method": "ServerSideDrawResult"
        }
    )
    raw = opener.open(req, timeout=20).read().decode("utf-8")
    data = json.loads(raw)["value"]
    soup = BeautifulSoup(data.get("HtmlContent", ""), "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 3:
            date_str = tds[0].get_text(strip=True)
            draw_str = tds[1].get_text(strip=True)
            spans = tds[2].find_all("span", class_="bong_tron")
            nums = [s.get_text(strip=True) for s in spans]
            if len(nums) == 6:
                rows.append({
                    "draw_id": int(draw_str),
                    "draw_code": draw_str,
                    "date": date_str,
                    "num1": int(nums[0]),
                    "num2": int(nums[1]),
                    "num3": int(nums[2]),
                    "num4": int(nums[3]),
                    "num5": int(nums[4]),
                    "special": int(nums[5]),
                    "numbers_str": f"{nums[0]} {nums[1]} {nums[2]} {nums[3]} {nums[4]} | {nums[5]}"
                })
    return rows

def sync_exports(conn):
    cur = conn.cursor()
    cur.execute("SELECT draw_id, draw_code, date, num1, num2, num3, num4, num5, special, numbers_str FROM draws ORDER BY draw_id ASC")
    rows = cur.fetchall()
    
    draws_list = []
    for r in rows:
        draws_list.append({
            "draw_id": r[0],
            "draw_code": r[1],
            "date": r[2],
            "num1": r[3],
            "num2": r[4],
            "num3": r[5],
            "num4": r[6],
            "num5": r[7],
            "special": r[8],
            "numbers_str": r[9]
        })
        
    # Write CSV
    fieldnames = ["draw_id", "draw_code", "date", "num1", "num2", "num3", "num4", "num5", "special", "numbers_str"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(draws_list)
        
    # Write JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(draws_list, f, ensure_ascii=False, indent=2)

def update_charts_and_stats():
    script_path = os.path.join(BASE_DIR, "standardize_and_plot.py")
    if os.path.exists(script_path):
        log("[*] Đang cập nhật biểu đồ và bảng chuẩn hóa thống kê...")
        ret = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        if ret.returncode == 0:
            log("[✓] Đã cập nhật thành công 4 biểu đồ trong charts/ và file standardized.csv!")
        else:
            log(f"[!] Cảnh báo khi cập nhật biểu đồ: {ret.stderr[:200]}")

def update_once():
    if not os.path.exists(DB_PATH):
        log("[!] Chưa có cơ sở dữ liệu vietlott_535.db. Đang chạy cào toàn bộ...")
        scrape_script = os.path.join(BASE_DIR, "scrape_vietlott_535.py")
        subprocess.run([sys.executable, scrape_script], check=True)
        update_charts_and_stats()
        return True

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    local_max = cur.execute("SELECT MAX(draw_id) FROM draws").fetchone()[0] or 0
    
    log(f"[*] Kiểm tra cập nhật... Kỳ hiện tại trong máy: #{local_max:05d}")
    try:
        opener, key, render_info = get_session_and_key()
    except Exception as e:
        log(f"[!] Không thể kết nối với Vietlott: {e}")
        conn.close()
        return False
        
    arr_numbers = [[""] * 35 for _ in range(5)]
    new_draws = []
    page = 0
    done = False
    
    while not done:
        try:
            page_rows = fetch_page_draws(opener, key, render_info, arr_numbers, page)
        except Exception as e:
            log(f"[!] Lỗi khi lấy trang {page}: {e}")
            break
            
        if not page_rows:
            break
            
        for d in page_rows:
            if d["draw_id"] <= local_max:
                done = True
                break
            new_draws.append(d)
            
        page += 1
        if page > 10:  # Safety cap for incremental check
            break
            
    if not new_draws:
        log(f"[-] Dữ liệu đã là mới nhất (Kỳ #{local_max:05d}). Không có kỳ mới.")
        conn.close()
        return False

    log(f"[+] Phát hiện {len(new_draws)} kỳ quay mới trên Vietlott!")
    sorted_new = sorted(new_draws, key=lambda x: x["draw_id"])
    for d in sorted_new:
        log(f"    + Thêm kỳ #{d['draw_code']} ({d['date']}): {d['numbers_str']}")
        cur.execute("INSERT OR REPLACE INTO draws VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            d["draw_id"], d["draw_code"], d["date"],
            d["num1"], d["num2"], d["num3"], d["num4"], d["num5"],
            d["special"], d["numbers_str"]
        ))
        
    conn.commit()
    new_max, total_cnt = cur.execute("SELECT MAX(draw_id), count(*) FROM draws").fetchone()
    
    # Sync CSV and JSON
    sync_exports(conn)
    conn.close()
    log(f"[✓] Đã lưu vào database, CSV và JSON! Tổng cộng hiện có: {total_cnt} kỳ (Kỳ mới nhất: #{new_max:05d})")
    
    # Refresh charts & standardized data
    update_charts_and_stats()
    
    # Refresh static web app files (index.html & docs/index.html)
    gen_script = os.path.join(BASE_DIR, "generate_web_app.py")
    if os.path.exists(gen_script):
        subprocess.run([sys.executable, gen_script], cwd=BASE_DIR, capture_output=True)
        log("[✓] Đã tạo lại index.html và docs/index.html cho Web App!")

    # Auto git commit and push if in git repo
    try:
        git_dir = os.path.join(BASE_DIR, ".git")
        if os.path.exists(git_dir):
            subprocess.run(["git", "add", "-A"], cwd=BASE_DIR, capture_output=True)
            msg = f"chore(auto-update): cập nhật kỳ #{new_max:05d} ({total_cnt} kỳ)"
            c_res = subprocess.run(["git", "commit", "-m", msg], cwd=BASE_DIR, capture_output=True, text=True)
            if c_res.returncode == 0:
                p_res = subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
                if p_res.returncode == 0:
                    log(f"[✓] Đã tự động đẩy kỳ #{new_max:05d} lên GitHub thành công!")
                else:
                    log(f"[!] Push GitHub không thành công: {p_res.stderr.strip()[:100]}")
    except Exception as ge:
        log(f"[!] Lỗi khi commit/push git: {ge}")

    return True

def watch_loop(interval_sec):
    log(f"[*] Bắt đầu chế độ theo dõi tự động (Watch mode). Chu kỳ kiểm tra: {interval_sec} giây ({interval_sec/60:.1f} phút)...")
    log("[*] Nhấn Ctrl+C để dừng.")
    while True:
        try:
            update_once()
        except Exception as e:
            log(f"[!] Ngoại lệ trong vòng lặp cập nhật: {e}")
        time.sleep(interval_sec)

def install_cron(minutes=30):
    python_bin = sys.executable
    script_path = os.path.abspath(__file__)
    cron_cmd = f"*/{minutes} * * * * {python_bin} {script_path} >> {LOG_PATH} 2>&1"
    
    # Read existing crontab
    res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current_cron = res.stdout if res.returncode == 0 else ""
    
    # Check if already present
    lines = [line for line in current_cron.splitlines() if script_path not in line]
    lines.append(f"# Vietlott 5/35 Auto Update every {minutes} mins")
    lines.append(cron_cmd)
    new_cron = "\n".join(lines).strip() + "\n"
    
    proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
    proc.communicate(new_cron)
    if proc.returncode == 0:
        log(f"[✓] Đã cài đặt Cron job thành công! Tự động cập nhật mỗi {minutes} phút.")
        log(f"    Cron entry: {cron_cmd}")
    else:
        log("[!] Cài đặt Cron job thất bại.")

def remove_cron():
    script_path = os.path.abspath(__file__)
    res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if res.returncode != 0:
        log("[-] Hiện không có crontab nào được cài đặt.")
        return
        
    current_cron = res.stdout
    lines = [line for line in current_cron.splitlines() if script_path not in line and "Vietlott 5/35" not in line]
    new_cron = "\n".join(lines).strip()
    if new_cron:
        new_cron += "\n"
        proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        proc.communicate(new_cron)
    else:
        subprocess.run(["crontab", "-r"])
    log("[✓] Đã gỡ bỏ Cron job tự động cập nhật.")

def show_status():
    print("=== TRẠNG THÁI HỆ THỐNG XSTK (VIETLOTT 5/35) ===")
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        total = cur.execute("SELECT count(*) FROM draws").fetchone()[0]
        first = cur.execute("SELECT draw_code, date, numbers_str FROM draws ORDER BY draw_id ASC LIMIT 1").fetchone()
        last = cur.execute("SELECT draw_code, date, numbers_str FROM draws ORDER BY draw_id DESC LIMIT 1").fetchone()
        conn.close()
        print(f"• Cơ sở dữ liệu: {DB_PATH}")
        print(f"• Tổng số kỳ:    {total}")
        print(f"• Kỳ đầu tiên:   #{first[0]} ({first[1]}) -> {first[2]}")
        print(f"• Kỳ mới nhất:   #{last[0]} ({last[1]}) -> {last[2]}")
    else:
        print("• Cơ sở dữ liệu: Chưa khởi tạo.")

    res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    script_path = os.path.abspath(__file__)
    if res.returncode == 0 and script_path in res.stdout:
        cron_line = [l for l in res.stdout.splitlines() if script_path in l][0]
        print(f"• Lịch tự động (Cron): ĐANG BẬT ({cron_line.split()[0]} {cron_line.split()[1]})")
    else:
        print("• Lịch tự động (Cron): TẮT")
        
    if os.path.exists(LOG_PATH):
        print(f"• File nhật ký (Log):  {LOG_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tự động kiểm tra và cập nhật kết quả Vietlott 5/35 sau mỗi kỳ")
    parser.add_argument("--watch", action="store_true", help="Chạy ngầm liên tục theo chu kỳ")
    parser.add_argument("--interval", type=int, default=1800, help="Khoảng thời gian kiểm tra lại (giây, mặc định 1800s = 30 phút)")
    parser.add_argument("--install-cron", action="store_true", help="Cài đặt lịch tự động vào crontab của hệ thống")
    parser.add_argument("--cron-minutes", type=int, default=30, help="Chu kỳ phút cho Cron job (mặc định 30 phút)")
    parser.add_argument("--remove-cron", action="store_true", help="Gỡ bỏ Cron job tự động")
    parser.add_argument("--status", action="store_true", help="Xem trạng thái dữ liệu và lịch cập nhật")
    
    args = parser.parse_args()
    
    if args.install_cron:
        install_cron(args.cron_minutes)
    elif args.remove_cron:
        remove_cron()
    elif args.status:
        show_status()
    elif args.watch:
        watch_loop(args.interval)
    else:
        update_once()
