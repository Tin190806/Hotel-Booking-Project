from typing import Dict, Any
"""
Model Customer đại diện cho một khách hàng
Lưu trữ thông tin cá nhân và trạng thái thành viên
"""
class Customer:

    def __init__(
        self,
        customer_id: str,
        name: str,
        phone: str,
        email: str,
        nationality: str,
        is_loyalty_member: bool = False
    ):
        """
        Khởi tạo object Customer, đại diện cho một khách hàng trong hệ thống.

        customer_id: Mã khách hàng
        name: Họ tên khách hàng
        phone: Số điện thoại liên hệ
        email: Địa chỉ email của khách hàng
        nationality: Quốc tịch của khách hàng
        is_loyalty_member: Trạng thái khách hàng thân thiết (True / False)
        """

        self.customer_id = customer_id
        self.name              = name
        self.email             = email
        self.phone             = phone
        self.nationality       = nationality
        self.is_loyalty_member = is_loyalty_member

    @classmethod

    def from_dict(cls, d: Dict[str, Any]) -> "Customer":
        return cls(
            customer_id       = str(d.get("customer_id")),
            
            name              = d.get("name", ""),
            email             = d.get("email", ""),
            phone             = d.get("phone", ""),

            nationality       = d.get("nationality"),
            is_loyalty_member = str(d.get("is_loyalty_member")).lower() == "true",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id"      : self.customer_id,
            "name"             : self.name,
            "email"            : self.email,
            "phone"            : self.phone,
            "nationality"      : self.nationality,
            "is_loyalty_member": self.is_loyalty_member,
        }

    def __str__(self) -> str:
        return (
        f"Customer("
        f"id={self.customer_id}, "
        f"name={self.name}, "
        f"phone={self.phone}, "
        f"loyalty={self.is_loyalty_member}"
        f")"
    )
