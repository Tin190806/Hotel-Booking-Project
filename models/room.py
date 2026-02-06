from typing import Optional, Dict, Any
"""
Model Room đại diện cho một phòng trong khách sạn
Chỉ lưu trữ thông tin cố định của phòng
"""

class Room:

    def __init__(
        self,
        room_id: str,
        room_name: str,
        room_type: str,
        capacity: int,
        price_per_night: float,
        status: str
    ):  
        """
        Khởi tạo object Room
        room_id: Mã phòng (vd: 101,102)
        room_name: Hạng phòng (standard,superior,deluxe,suite)
        room_type: Loại phòng (single,double,twin,king,junior,executive,family)
        capacity: Số lượng tối đa khách có thể ở trong phòng
        price_per_night: Giá phòng 1 đêm
        status: Trạng thái của phòng
        """
        self.room_id         = room_id
        self.room_name       = room_name
        self.room_type       = room_type
        self.capacity        = capacity
        self.price_per_night = price_per_night
        self.status          = status

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Room":
        """
        Tạo object Room từ dữ liệu dạng dict
        Được sử dụng khi load dữ liệu từ file room.csv
        """
        return cls(
            room_id         = d.get("room_id"),
            room_name       = d.get("room_name", ""),
            room_type       = d.get("room_type", ""),
            capacity        = int(d.get("capacity",1)),
            price_per_night = float(d.get("price_per_night") or 0.0),
            status          = d.get("status")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển đổi object Room thành dict
        Sử dụng khi lưu trữ về file room.csv
        """
        return {
            "room_id"         : self.room_id,
            "room_name"       : self.room_name,
            "room_type"       : self.room_type,
            "capacity"        : self.capacity,
            "price_per_night" : self.price_per_night,
            "status"          : self.status
        }

    def __str__(self) -> str:
        """
        Biểu diễn Booking dưới dạng chuỗi
        """
        return (
        f"Room("
        f"id={self.room_id}, "
        f"name={self.room_name}, "
        f"type={self.room_type}, "
        f"capacity={self.capacity}, "
        f"price={self.price_per_night}"
        f")"
    )
