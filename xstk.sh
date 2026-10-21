#!/usr/bin/env bash
# ==============================================================================
# QUẢN LÝ DỮ LIỆU XÁC SUẤT THỐNG KÊ (XSTK) - VIETLOTT LOTTO 5/35
# ==============================================================================
# Thư mục dự án: /home/tringuyen/xstk
#
# HƯỚNG DẪN CHI TIẾT SỬ DỤNG 3 FILE PYTHON TRONG DỰ ÁN:
#
# 1. scrape_vietlott_535.py:
#    - Mục đích: Cào (crawl) toàn bộ lịch sử kết quả từ kỳ đầu tiên (#00001)
#      đến kỳ mới nhất hiện tại từ máy chủ Vietlott.
#    - Cách chạy:
#        python3 scrape_vietlott_535.py
#    - Kết quả sinh ra:
#        + vietlott_535.db    : Cơ sở dữ liệu SQLite bảng `draws`
#        + vietlott_535.csv   : File CSV chứa toàn bộ các kỳ
#        + vietlott_535.json  : File JSON có cấu trúc đầy đủ
#
# 2. standardize_and_plot.py:
#    - Mục đích: Sử dụng math-mcp để tính toán chuẩn hóa xác suất thống kê (Z-score,
#      kỳ vọng toán, độ lệch chuẩn) và sinh 4 biểu đồ phân tích trực quan dạng PNG.
#    - Cách chạy:
#        python3 standardize_and_plot.py
#    - Kết quả sinh ra:
#        + vietlott_535_standardized.csv    : Bổ sung Z-Score tổng, Tài/Xỉu, Chẵn/Lẻ
#        + vietlott_535_frequency_stats.csv : Tần suất và Z-Score của 35 số chính
#        + charts/01_frequency_distribution.png
#        + charts/02_zscore_standardized_balls.png
#        + charts/03_sum_histogram.png
#        + charts/04_special_numbers.png
#
# 3. auto_update.py:
#    - Mục đích: Tự động kiểm tra và cập nhật các kỳ quay mới sau mỗi ngày/kỳ.
#      Chỉ tải phần dữ liệu mới phát sinh (incremental update), sau đó tự động
#      chạy lại standardize_and_plot.py để cập nhật lại biểu đồ và các file CSV.
#    - Các lệnh thông dụng:
#        + Kiểm tra & cập nhật ngay 1 lần:
#            python3 auto_update.py
#        + Xem trạng thái hiện tại (kỳ mới nhất, trạng thái Cron):
#            python3 auto_update.py --status
#        + Bật lịch tự động cập nhật qua Cron (mặc định mỗi 30 phút):
#            python3 auto_update.py --install-cron
#            python3 auto_update.py --install-cron --cron-minutes 15
#        + Tắt lịch tự động cập nhật Cron:
#            python3 auto_update.py --remove-cron
#        + Chạy ngầm liên tục dạng daemon (không dùng cron):
#            python3 auto_update.py --watch --interval 1800
#        + Xem nhật ký cập nhật:
#            tail -f auto_update.log
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Màu hiển thị terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${GREEN}      HỆ THỐNG XỬ LÝ DỮ LIỆU XSTK - VIETLOTT LOTTO 5/35${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo -e "Cú pháp: ${YELLOW}./xstk.sh [lệnh]${NC}\n"
    echo -e "Danh sách các lệnh hỗ trợ:"
    echo -e "  ${GREEN}status${NC}       : Xem trạng thái cơ sở dữ liệu, kỳ mới nhất & Cron job"
    echo -e "  ${GREEN}update${NC}       : Kiểm tra và cập nhật kỳ mới ngay lập tức"
    echo -e "  ${GREEN}plot${NC}         : Chạy lại chuẩn hóa thống kê & vẽ lại 4 biểu đồ"
    echo -e "  ${GREEN}scrape-all${NC}   : Cào lại toàn bộ dữ liệu từ kỳ #00001 đến nay"
    echo -e "  ${GREEN}cron-on${NC}      : Bật lịch tự động cập nhật mỗi 30 phút (qua Crontab)"
    echo -e "  ${GREEN}cron-off${NC}     : Tắt lịch tự động cập nhật Cron"
    echo -e "  ${GREEN}watch${NC}        : Chạy daemon theo dõi liên tục trong terminal"
    echo -e "  ${GREEN}logs${NC}         : Xem log theo thời gian thực (tail -f auto_update.log)"
    echo -e "  ${GREEN}qr${NC}           : Đánh giá bộ số QR (vd: ./xstk.sh qr 6 15 21 30 34 6)"
    echo -e "  ${GREEN}qr --gen N${NC}   : Gợi ý N bộ số chuẩn 5+1 nằm trong Typical Set (./xstk.sh qr --gen 5)"
    echo -e "  ${GREEN}gui${NC}          : Mở giao diện Desktop đồ họa PyQt5 (Qt App)"
    echo -e "  ${GREEN}web${NC}          : Mở giao diện Web App trên trình duyệt (Port 8080)"
    echo -e "  ${GREEN}help${NC}         : Hiển thị lại bảng hướng dẫn này"
    echo -e "${BLUE}================================================================${NC}"
}

case "$1" in
    status)
        echo -e "${YELLOW}[*] Kiểm tra trạng thái hệ thống...${NC}"
        python3 "$DIR/auto_update.py" --status
        ;;
    update)
        echo -e "${YELLOW}[*] Kiểm tra và cập nhật kỳ mới...${NC}"
        python3 "$DIR/auto_update.py"
        ;;
    plot)
        echo -e "${YELLOW}[*] Đang chuẩn hóa dữ liệu và xuất biểu đồ qua math-mcp...${NC}"
        python3 "$DIR/standardize_and_plot.py"
        ;;
    scrape-all)
        echo -e "${YELLOW}[*] Cào lại toàn bộ lịch sử các kỳ quay...${NC}"
        python3 "$DIR/scrape_vietlott_535.py"
        echo -e "${YELLOW}[*] Cập nhật lại biểu đồ và chuẩn hóa...${NC}"
        python3 "$DIR/standardize_and_plot.py"
        ;;
    cron-on)
        MINUTES="${2:-30}"
        echo -e "${YELLOW}[*] Cài đặt Cron job cập nhật mỗi ${MINUTES} phút...${NC}"
        python3 "$DIR/auto_update.py" --install-cron --cron-minutes "$MINUTES"
        ;;
    cron-off)
        echo -e "${YELLOW}[*] Gỡ bỏ Cron job tự động...${NC}"
        python3 "$DIR/auto_update.py" --remove-cron
        ;;
    watch)
        INTERVAL="${2:-1800}"
        echo -e "${YELLOW}[*] Bắt đầu chế độ theo dõi liên tục (chu kỳ: ${INTERVAL}s)...${NC}"
        python3 "$DIR/auto_update.py" --watch --interval "$INTERVAL"
        ;;
    logs)
        echo -e "${YELLOW}[*] Đọc file log (${DIR}/auto_update.log)...${NC}"
        tail -n 25 -f "$DIR/auto_update.log"
        ;;
    qr)
        shift
        python3 "$DIR/qr_filter.py" "$@"
        ;;
    gui)
        echo -e "${YELLOW}[*] Đang khởi chạy giao diện Desktop PyQt5...${NC}"
        "$DIR/.venv/bin/python" "$DIR/qt_app.py"
        ;;
    web)
        PORT="${2:-8080}"
        echo -e "${GREEN}[*] Đang khởi chạy Web Dashboard tại http://localhost:${PORT}${NC}"
        echo -e "${YELLOW}[*] Nhấn Ctrl+C để dừng.${NC}"
        python3 -m http.server "$PORT" --directory "$DIR"
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}[!] Lệnh không hợp lệ: $1${NC}"
        echo -e "Chạy ${YELLOW}./xstk.sh help${NC} để xem các lệnh hợp lệ."
        exit 1
        ;;
esac
