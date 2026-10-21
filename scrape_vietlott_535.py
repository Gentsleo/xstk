import urllib.request
import json
import re
import time
import sqlite3
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

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

def fetch_page(opener, key, render_info, arr_numbers, page_idx, max_retries=3):
    payload = {
        "ORenderInfo": render_info,
        "Key": key,
        "GameDrawId": "",
        "ArrayNumbers": arr_numbers,
        "CheckMulti": False,
        "PageIndex": page_idx
    }
    for attempt in range(1, max_retries + 1):
        try:
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
            return page_idx, rows
        except Exception as e:
            if attempt == max_retries:
                print(f"[!] Page {page_idx} failed after {max_retries} attempts: {e}")
                return page_idx, []
            time.sleep(1)

def main():
    print("[*] Đang khởi tạo kết nối với Vietlott...")
    opener, key, render_info = get_session_and_key()
    arr_numbers = [[""] * 35 for _ in range(5)]
    
    # Check total pages: page 0 has the latest draw
    _, first_page_rows = fetch_page(opener, key, render_info, arr_numbers, 0)
    if not first_page_rows:
        print("[!] Không lấy được dữ liệu trang đầu tiên.")
        return
    
    latest_draw = first_page_rows[0]["draw_id"]
    # Estimate total pages (each page has ~8 draws)
    estimated_pages = (latest_draw // 8) + 5
    print(f"[*] Kỳ mới nhất: #{latest_draw:05d} ({first_page_rows[0]['date']}). Dự kiến ~{estimated_pages} trang.")
    
    all_draws = {}
    for item in first_page_rows:
        all_draws[item["draw_id"]] = item
        
    start_time = time.time()
    batch_size = 10
    total_pages = estimated_pages
    
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = {
            executor.submit(fetch_page, opener, key, render_info, arr_numbers, p): p 
            for p in range(1, total_pages)
        }
        for future in as_completed(futures):
            p, rows = future.result()
            for r in rows:
                all_draws[r["draw_id"]] = r
                
    sorted_draws = sorted(all_draws.values(), key=lambda x: x["draw_id"])
    duration = time.time() - start_time
    print(f"[*] Đã cào xong {len(sorted_draws)} kỳ quay trong {duration:.2f}s!")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Save CSV
    csv_file = os.path.join(BASE_DIR, "vietlott_535.csv")
    fieldnames = ["draw_id", "draw_code", "date", "num1", "num2", "num3", "num4", "num5", "special", "numbers_str"]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_draws)
    print(f"[✓] Đã lưu CSV: {csv_file}")
    
    # Save JSON
    json_file = os.path.join(BASE_DIR, "vietlott_535.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(sorted_draws, f, ensure_ascii=False, indent=2)
    print(f"[✓] Đã lưu JSON: {json_file}")
    
    # Save SQLite
    db_file = os.path.join(BASE_DIR, "vietlott_535.db")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS draws")
    cur.execute("""
        CREATE TABLE draws (
            draw_id INTEGER PRIMARY KEY,
            draw_code TEXT,
            date TEXT,
            num1 INTEGER,
            num2 INTEGER,
            num3 INTEGER,
            num4 INTEGER,
            num5 INTEGER,
            special INTEGER,
            numbers_str TEXT
        )
    """)
    for r in sorted_draws:
        cur.execute("""
            INSERT INTO draws VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["draw_id"], r["draw_code"], r["date"],
            r["num1"], r["num2"], r["num3"], r["num4"], r["num5"],
            r["special"], r["numbers_str"]
        ))
    conn.commit()
    conn.close()
    print(f"[✓] Đã lưu SQLite DB: {db_file}")

if __name__ == "__main__":
    main()
