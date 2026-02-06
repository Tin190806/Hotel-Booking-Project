from datetime import datetime, date, timedelta
from typing import Optional
"""
Module tiện ích xử lý ngày tháng.
Cung cấp các hàm parse, so sánh và tính toán liên quan đến date.
"""

def is_overlap(a_start, a_end, b_start, b_end) -> bool:
    """
    Kiểm tra hai khoảng thời gian có bị trùng nhau hay không.

    Trả về True nếu hai khoảng [a_start, a_end) và [b_start, b_end) giao nhau.
    """
    a_start = parse_date(a_start)
    a_end   = parse_date(a_end)
    b_start = parse_date(b_start)
    b_end   = parse_date(b_end)

    if a_start is None or a_end is None or b_start is None or b_end is None:
        return False
    
    if a_start > a_end:
        return False
    
    if b_start > b_end:
        return False
    
    return (a_start < b_end) and (a_end > b_start)

def parse_date(s: Optional[str]) -> Optional[date]:
    """
    Chuyển dữ liệu đầu vào về kiểu date.

    - Hỗ trợ string định dạng YYYY-MM-DD
    - Hỗ trợ datetime và date
    - Trả về None nếu dữ liệu không hợp lệ
    """
    if not s:
        return None
    if isinstance(s, date) and not isinstance(s, datetime):
        return s
    if isinstance(s, datetime):
        return s.date()
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None
    
def weekend_nights(check_in,check_out):
    """
    Đếm số đêm rơi vào cuối tuần (thứ 7, chủ nhật)
    trong khoảng thời gian từ check_in đến check_out.
    """
    start = parse_date(check_in)
    end = parse_date(check_out)

    if not start or not end:
        return 0
    if start > end:
        return 0
    
    weekend_count = 0
    current_day = start
    while current_day < end:
        if current_day.weekday() in [5,6]:
            weekend_count += 1
        current_day += timedelta(days=1)
    return weekend_count

def count_days(check_in,check_out):
    """
    Tính số ngày lưu trú giữa check_in và check_out.

    Không bao gồm ngày check_out.
    """
    start = parse_date(check_in)
    end = parse_date(check_out)

    if not start or not end:
        return 0
    if start > end:
        return 0
    return (end - start).days 