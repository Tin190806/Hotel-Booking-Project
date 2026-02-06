from pathlib import Path
from utils.csv_io import read_csv,write_csv
from models.customer import Customer
from typing import List,Optional

PATH = Path("data/customer.csv")

FIELDS = [
    "customer_id",
    "name",
    "phone",
    "email",
    "nationality",
    "is_loyalty_member"
]
"""
    Customer_service xử lý các nghiệp vụ liên quan tới khách hàng
    """
# ----------------------------------------------------------------------------------
#          LOAD/SAVE
# ----------------------------------------------------------------------------------

def load_all() -> List[Customer]:
    """
    Load danh sách khách hàng từ customer.csv
    """
    return [Customer.from_dict(r) for r in read_csv(PATH)]

def save_all(customers: List[Customer]) -> None:
    """
    Save danh sách khách hàng xuống customer.csv
    """
    write_csv(PATH,[c.to_dict() for c in customers],FIELDS)

def save_one(customer: Customer) -> None:
    """
    Thêm khách hàng
    """
    customers = load_all()
    customers.append(customer)
    save_all(customers)
# ----------------------------------------------------------------------------------
#          HELPERS
# ----------------------------------------------------------------------------------
def find_by_id(customer_id:str) -> Optional[Customer]:
    """
    Tìm kiếm khách hàng theo customer_id
    """
    for c in load_all():
        if c.customer_id == customer_id:
            return c
    return None

def find_by_phone(phone):
    """
    Tìm kiếm khách hàng theo phone
    """
    return next(
        (c for c in load_all() if c.phone.lower() == phone.lower()),None
    )

def update_customer(customer_id:str,**updates) -> Customer:
    """
    Cập nhật thông tin khách hàng
    """
    customers = load_all()
    target = None

    for c in customers:
        if c.customer_id == customer_id:
            target = c
            break
    if target is None:
        raise ValueError("Customer not found")
    
    allowed_fields = {
        "name",
        "email",
        "phone",
        "nationality",
        "is_loyalty_member"
    }

    for key,value in updates.items():
        if key in allowed_fields:
            setattr(target,key,value)
    
    save_all(customers)
    return target
