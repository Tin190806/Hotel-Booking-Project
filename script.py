import random
from datetime import date, timedelta
from pathlib import Path
from utils.csv_io import write_csv

# ================== CẤU HÌNH ==================

OUTPUT_PATH = Path("data/booking.csv")

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

ROOM_IDS = [f"R{i:03}" for i in range(1, 21)]       # 20 phòng
CUSTOMER_IDS = [str(i) for i in range(1, 201)]     # 200 khách

TOTAL_BOOKINGS = 500

START_DATE = date(2024, 1, 1)
END_DATE   = date(2025, 12, 31)

# ================== HÀM HỖ TRỢ ==================

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def random_booking_id(i):
    return f"B{i:04}"

# ================== TẠO DỮ LIỆU ==================

rows = []

for i in range(1, TOTAL_BOOKINGS + 1):
    check_in = random_date(START_DATE, END_DATE - timedelta(days=3))
    stay_days = random.randint(1, 5)
    check_out = check_in + timedelta(days=stay_days)

    # 30% khách trả sớm / trễ
    if random.random() < 0.3:
        actual_check_out = check_out + timedelta(days=random.choice([-1, 1]))
    else:
        actual_check_out = ""

    price_per_night = random.randint(500_000, 2_000_000)
    final_price = price_per_night * stay_days

    status = random.choices(
        ["completed", "canceled"],
        weights=[0.85, 0.15]
    )[0]

    payment_status = "paid" if status == "completed" else "unpaid"

    created_at = check_in.isoformat() + "T10:00:00"
    updated_at = check_out.isoformat() + "T12:00:00"

    rows.append({
        "booking_id": random_booking_id(i),
        "room_id": random.choice(ROOM_IDS),
        "customer_id": random.choice(CUSTOMER_IDS),
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "actual_check_out": actual_check_out.isoformat() if actual_check_out else "",
        "final_price": final_price,
        "status": status,
        "payment_status": payment_status,
        "notes": "",
        "created_at": created_at,
        "updated_at": updated_at,
    })

# ================== GHI FILE ==================

write_csv(OUTPUT_PATH, rows, FIELDS)

print(f"Đã tạo {TOTAL_BOOKINGS} booking (2024–2025)")
