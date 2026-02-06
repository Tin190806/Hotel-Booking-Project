from datetime import datetime, date
from utils.date_utils import parse_date
from typing import Optional, Dict, Any
"""
Model Booking đại diện cho một lần đặt phòng trong hệ thống
"""
class Booking:
    
    def __init__(
        self,
        booking_id: str,
        room_id: str,
        customer_id: str,
        check_in: date | None = None,
        check_out: date | None = None,
        actual_check_out: date | None = None,
        final_price: Optional[float] = None,
        status: str ="pending",
        payment_status: str = "unpaid",
        notes: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        """
        Khởi tạo object Booking, đại diện cho một lượt đặt phòng trong hệ thống.

        booking_id: Mã booking duy nhất
        room_id: Mã phòng được đặt
        customer_id: Mã khách hàng thực hiện đặt phòng

        check_in: Ngày check-in dự kiến
        check_out: Ngày check-out dự kiến
        actual_check_out: Ngày check-out thực tế

        final_price: Tổng chi phí cuối cùng của booking
        status: Trạng thái booking (pending, confirmed, canceled, completed)
        payment_status: Trạng thái thanh toán (unpaid,deposit, paid)

        notes: Ghi chú thêm cho booking
        created_at: Thời điểm tạo booking
        updated_at: Thời điểm cập nhật booking gần nhất
        """

        
        self.booking_id        = booking_id
        self.room_id           = room_id
        self.customer_id       = customer_id

        self.check_in          = check_in
        self.check_out         = check_out
        self.actual_check_out  = actual_check_out

        self.final_price       = final_price
        self.status            = status
        self.payment_status    = payment_status
        self.notes             = notes

        now = datetime.now().isoformat()
        self.created_at        = created_at or now
        self.updated_at        = updated_at or now

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Booking":
        """
        Tạo object Booking từ dữ liệu dạng dict
        Được sử dụng khi load dữ liệu từ file booking.csv
        """
        return cls(
            booking_id        = str(d.get("booking_id")),
            room_id           = str(d.get("room_id")),
            customer_id       = str(d.get("customer_id")),
        
            
            check_in          = parse_date(d.get("check_in")),
            check_out         = parse_date(d.get("check_out")),
            actual_check_out  = parse_date(d.get("actual_check_out")) if d.get("actual_check_out") else None,
             
            final_price       = float(d.get("final_price")) if d.get("final_price") else None,
            status            = d.get("status", "pending"),
            payment_status    = d.get("payment_status", "unpaid"),
            notes             = d.get("notes"),
 
            created_at        = d.get("created_at"),
            updated_at        = d.get("updated_at"),
        )
   
    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển đổi object Booking thành dict
        Sử dụng khi lưu trữ về file booking.csv
        """
        return {
            "booking_id"        : self.booking_id,
            "room_id"           : self.room_id,
            "customer_id"       : self.customer_id,
            

            "check_in"          : self.check_in.isoformat() if self.check_in else None,
            "check_out"         : self.check_out.isoformat() if self.check_out else None,
            "actual_check_out"  : self.actual_check_out.isoformat() if self.actual_check_out else None,
            
            "final_price"       : self.final_price,
            "status"            : self.status,
            "payment_status"    : self.payment_status,
            "notes"             : self.notes,
  
            "created_at"        : self.created_at,
            "updated_at"        : self.updated_at,
        }

    def __str__(self) -> str:
        """
        Biểu diễn Booking dưới dạng chuỗi
        """
        return (
        f"Booking("
        f"id={self.booking_id}, "
        f"room_id={self.room_id}, "
        f"customer_id={self.customer_id}, "
        f"status={self.status}, "
        f"payment={self.payment_status}"
        f")"
    )