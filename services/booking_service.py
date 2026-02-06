import random
import string

from pathlib import Path
from typing import List, Optional
from datetime import date, datetime

from models.booking import Booking
from services import room_service, customer_service, pricing_service
from utils.csv_io import read_csv, write_csv
from utils.date_utils import parse_date
"""
booking_service xử lý các nghiệp vụ liên quan tới booking
Bao gồm tạo booking, thanh toán, hủy và trả phòng
"""
PATH = Path("data/booking.csv")
FIELDS = [
    "booking_id",
    "room_id",
    "customer_id",
    "check_in",
    "check_out",
    "actual_check_out",
    "final_price",
    "status",
    "payment_status",
    "notes",
    "created_at",
    "updated_at",
]
_BOOKING_CACHE = None # Lưu danh sách bookings vô thanh RAM
# ----------------------------------------------------------------------------------
#          LOAD/SAVE
# ----------------------------------------------------------------------------------

def load_all() -> List[Booking]:
    """
    Load toàn bộ booking từ booking.csv
    Sử dụng cache để giảm số lần đọc file
    """
    global _BOOKING_CACHE
    if _BOOKING_CACHE is None:
        _BOOKING_CACHE = [Booking.from_dict(r) for r in read_csv(PATH)]
    return _BOOKING_CACHE

def save_all(bookings: List[Booking]) -> None:
    """
    Lưu danh sách booking xuống booking.csv
    """
    global _BOOKING_CACHE
    _BOOKING_CACHE = bookings
    write_csv(PATH, [b.to_dict() for b in bookings], FIELDS)

def save_one(booking: Booking) -> None:
    """
    Lưu hoặc cập nhật một booking
    """
    bookings = load_all()
    
    for i, b in enumerate(bookings):
        if str(b.booking_id) == str(booking.booking_id):
            bookings[i] = booking
            
            break
    else: 
        bookings.append(booking)
    save_all(bookings)

# ----------------------------------------------------------------------------------
#          HELPER
# ----------------------------------------------------------------------------------

def next_id() -> str:
    
    """
    Sinh mã booking ngẫu nhiên
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def find_by_id(booking_id: str) -> Optional[Booking]:
    """
    Tìm booking theo booking_id
    """
    bookings = load_all()
    for b in bookings:
        if str(b.booking_id) == str(booking_id):
            return b
    return None

def get_bookings_for_room(room_id: str) -> List[Booking]:
    """
    Tìm kiếm các booking hợp lệ theo room_id
    """
    return [
        b
        for b in load_all()
        if str(b.room_id) == str(room_id) and getattr(b, "status", "") != "canceled"
    ]

# ----------------------------------------------------------------------------------
#          LOGIC CORE
# ----------------------------------------------------------------------------------
def create_booking(room_id: str, customer_id: str, check_in: str, check_out: str) -> Booking:
    """
    Tạo booking mới
    Kiểm tra phòng có trống hay khách hàng có tồn tại hay ko 
    Đồng thời tính giá tiền theo đêm
    """
    if not room_id or not customer_id:
        raise ValueError("Missing room_id or customer_id")
    if not check_in or not check_out:
        raise ValueError("Missing check_in or check_out")

    room = room_service.find_by_id(room_id)
    if not room:
        raise ValueError("Room not found")
    if not room_service.is_available(room_id,check_in,check_out):
        raise ValueError("Room is not available for requested date")

    customer = customer_service.find_by_id(customer_id)
    if not customer:
        raise ValueError("Customer not found")

    price_per_night = room.price_per_night
    is_loyalty_member = customer.is_loyalty_member

    final_price = pricing_service.calculate_booking_price(
        check_in, check_out, price_per_night, is_loyalty_member
    )
    
    check_in_date = parse_date(check_in)
    check_out_date = parse_date(check_out)
    
    booking_id = next_id()
    created_at = datetime.now().isoformat()

    booking = Booking(
        booking_id=booking_id,
        room_id=room_id,
        customer_id=customer_id,
        check_in=check_in_date,
        check_out=check_out_date,
        actual_check_out=None,
        final_price=final_price,
        status="confirmed",
        payment_status="unpaid",
        notes=None,
        created_at=created_at,
        updated_at=created_at,
    )

    save_one(booking)
    return booking

def cancel_booking(booking_id: str) -> bool:
    """
    Hủy booking theo booking_id
    """
    bookings = load_all()
    changed = False
    for i, b in enumerate(bookings):
        if str(b.booking_id) == str(booking_id):
            if b.cancel():
                bookings[i] = b
                changed = True
            break
    if changed:
        save_all(bookings)
    return changed

def confirm_payment(booking_id: str, amount_paid: float) -> Booking:
    """
    Xác nhận thanh toán booking (cọc hoặc thanh toán đủ)
    """

    booking = find_by_id(booking_id)
    if not booking:
        raise ValueError("Booking not found")

    if booking.status != "confirmed":
        raise ValueError("Booking must be confirmed before payment")

    # Logic cọc 50%
    if amount_paid <= 0:
        raise ValueError("Invalid payment amount")

    if amount_paid >= booking.final_price:
        booking.payment_status = "paid"
    elif amount_paid >= 0.5 * booking.final_price:
        booking.payment_status = "deposit"
    else:
        raise ValueError("Payment must be at least 50%")

    booking.updated_at = datetime.now().isoformat()
    save_one(booking)
    return booking

def finalize_checkout(booking_id: str, actual_check_out: Optional[date], notes=None) -> Booking:
    """
    Hoàn tất quá trình trả phòng
    Tính lại giá tiền và cập nhật trạng thái booking
    """
    b = find_by_id(booking_id)
    if b is None:
        raise ValueError("Booking not found")

    if b.status != "confirmed":
        raise ValueError("Only confirmed booking can be finalized")

    room = room_service.find_by_id(b.room_id)
    customer = customer_service.find_by_id(b.customer_id)

    checkout_date = actual_check_out or b.check_out
    
    check_in_str = b.check_in.isoformat() if b.check_in else ""
    check_out_str = b.check_out.isoformat() if checkout_date else ""

    final_price = pricing_service.calculate_booking_price(
        check_in_str, check_out_str, room.price_per_night, customer.loyalty_member
    )

    b.final_price = final_price
    b.actual_check_out = checkout_date
    b.payment_status = "paid"
    b.status = "completed"
    if notes:
        b.notes = notes
    b.updated_at = datetime.now().isoformat()

    save_one(b)
    return b