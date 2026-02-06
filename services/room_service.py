from pathlib import Path
from typing import List
from models.room import Room
from utils.date_utils import parse_date, is_overlap
from services import booking_service as booking_srv
from datetime import date
from utils.csv_io import read_csv

PATH = Path("data/room.csv")
"""
Service xử lý nghiệp vụ liên quan tới phòng
"""
def load_all() -> List[Room]:
    """
    Load danh sách các phòng từ file room.csv
    """
    return [Room.from_dict(r) for r in read_csv(PATH)]

def find_by_id(room_id):
    """
    TÌm kiếm phòng theo room_id
    """
    for r in load_all():
        if str(r.room_id) == str(room_id):
            return r
    return None

def filter_rooms(room_name=None, room_type=None, min_capacity=None) -> List[Room]:
    """
    Lọc phòng theo hạng, loại, sức chứa của phòng
    """
    rooms = load_all()
    results = []

    for r in rooms:

        if min_capacity is not None and r.capacity < min_capacity:
            continue

        if room_type is not None and r.room_type.lower() != room_type.lower():
            continue

        if room_name is not None and r.room_name.lower() != room_name.lower():
            continue

        results.append(r)
    return results

def is_available(room_id: str, check_in: str, check_out: str) -> bool:
    """
    Kiểm tra phòng có trống trong khoảng thời gian đó không
    """

    new_start = parse_date(check_in)
    new_end = parse_date(check_out)
    if not new_start or not new_end:
        raise ValueError("Invalid dates")
    if new_start >= new_end:
        raise ValueError("Check-in must be before Check-out")
    
    # Kiểm tra trùng lịch
    for b in booking_srv.load_all():
        if str(b.room_id) != str(room_id): continue
        if (b.status or "").lower() in ["canceled", "completed"]: continue
        
        if is_overlap(check_in, check_out, b.check_in, b.check_out):
            return False
    return True

def get_room_status(room_id):
    """
    Xác định trạng thái phòng hiện tại theo room_id (occupied/vacant)
    """
    today = date.today()
    for b in booking_srv.load_all():
        if str(b.room_id) != str(room_id): continue
        
        
        status = (b.status or "").lower()
        if status in ["canceled", "completed"]: 
            continue
            
        if b.check_in <= today <= b.check_out:
            return "occupied"
    return "vacant"

def get_available_rooms(check_in, check_out):
    """
    Load danh sách phòng trống theo thời gian
    """
    return [r for r in load_all() if is_available(r.room_id, check_in, check_out)]

