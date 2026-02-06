# Hotel-Booking-Project

# My team created a website that help management hotel booking

# Hotel Booking Management System

## 1. Giới thiệu

Hotel Booking Management System là một hệ thống quản lý đặt phòng khách sạn ở mức cơ bản,  
được xây dựng bằng Python theo hướng lập trình hướng đối tượng (OOP).

Hệ thống tập trung xử lý các nghiệp vụ cốt lõi của khách sạn như:

- Quản lý phòng
- Quản lý khách hàng
- Đặt phòng (booking)
- Thanh toán và trả phòng
- Thống kê công suất phòng và doanh thu

Hệ thống **không xử lý realtime**, phù hợp với mô hình quản lý offline hoặc admin-side.

---

## 2. Phạm vi và đặc điểm hệ thống

- Không xử lý đồng thời nhiều người dùng
- Không có cơ chế giữ phòng tạm thời (pending booking)
- Dữ liệu được lưu trữ dưới dạng file CSV
- Tập trung vào nghiệp vụ và cấu trúc code rõ ràng

Hệ thống được thiết kế để dễ mở rộng sang cơ sở dữ liệu (MySQL, PostgreSQL) trong tương lai.

---

## 3. Công nghệ sử dụng

- Ngôn ngữ: **Python 3.10**
- Thư viện:
  - `csv`, `pathlib` (xử lý file)
  - `datetime` (xử lý ngày tháng)
  - `pandas`, `xlsxwriter` (báo cáo và xuất Excel)
- Lưu trữ dữ liệu: **CSV**

---

## 4. Kiến trúc hệ thống

Hệ thống được tổ chức theo mô hình phân tầng (Layered Architecture):

UI / App
└── Service Layer
├── booking_service
├── room_service
├── customer_service
├── pricing_service
└── report_service
↓
Model Layer
↓
Utils Layer
↓
CSV Files

### Mô tả các tầng

- **Model**:  
  Đại diện cho các thực thể (Booking, Room, Customer).  
  Chỉ lưu trữ dữ liệu, không xử lý nghiệp vụ (passive model).

- **Service**:  
  Xử lý toàn bộ nghiệp vụ của hệ thống như đặt phòng, thanh toán, trả phòng, báo cáo.

- **Utils**:  
  Cung cấp các hàm tiện ích dùng chung (đọc/ghi CSV, xử lý ngày tháng).

---

## 5. Cấu trúc thư mục

project/
│
├── models/
│ ├── booking.py
│ ├── room.py
│ └── customer.py
│
├── services/
│ ├── booking_service.py
│ ├── room_service.py
│ ├── customer_service.py
│ ├── pricing_service.py
│ └── report_service.py
│
├── utils/
│ ├── csv_io.py
│ └── date_utils.py
│
├── data/
│ ├── booking.csv
│ ├── room.csv
│ └── customer.csv
│
├── app.py
└── README.md

---

## 6. Nghiệp vụ chính

### 6.1 Quản lý phòng

- Lưu thông tin phòng (tên, loại, sức chứa, giá)
- Kiểm tra phòng trống theo thời gian
- Xác định trạng thái phòng (vacant / occupied) dựa trên booking

### 6.2 Quản lý khách hàng

- Lưu thông tin cá nhân
- Phân biệt khách hàng thân thiết (loyalty member)

### 6.3 Đặt phòng (Booking)

- Tạo booking mới
- Kiểm tra trùng lịch phòng
- Xác nhận thanh toán (đặt cọc hoặc thanh toán đủ)
- Hủy booking
- Hoàn tất trả phòng

### 6.4 Tính giá

- Tính theo số đêm lưu trú
- Phụ thu cuối tuần
- Giảm giá cho khách hàng thân thiết

### 6.5 Báo cáo

- Tính công suất phòng (OCC%)
- Tính doanh thu theo tháng và năm
- Xuất báo cáo Excel kèm biểu đồ

---

## 7. Bộ nhớ đệm (Cache)

Hệ thống sử dụng `_BOOKING_CACHE` để lưu danh sách booking trong bộ nhớ sau lần đọc đầu tiên từ file CSV.

Mục đích:

- Giảm số lần đọc file
- Tăng hiệu năng xử lý
- Phù hợp với hệ thống không realtime

---

## 8. Giới hạn hệ thống

- Không hỗ trợ realtime
- Không xử lý concurrent booking
- Không có cơ chế timeout cho booking pending
- Không có phân quyền người dùng

Các giới hạn này được chấp nhận do phạm vi đồ án.

---

## 9. Hướng phát triển

- Chuyển từ CSV sang cơ sở dữ liệu quan hệ
- Thêm giao diện web (Flask / Django)
- Bổ sung realtime booking
- Thêm phân quyền người dùng
- Áp dụng design pattern nâng cao (Repository, Unit of Work)

---

## 10. Kết luận

Hệ thống đáp ứng đầy đủ các nghiệp vụ cơ bản của một hệ thống booking khách sạn ở mức độ cơ bản.  
Cấu trúc code rõ ràng, dễ đọc, dễ mở rộng và phù hợp với mục tiêu học tập về Python, OOP và thiết kế hệ thống backend.

Hotel booking system project/
├── console/
│ └── app.py
├── data/
│ ├── room.csv
│ ├── customer.csv
│ └── booking.csv
├── models/
│ ├── room.py
│ ├── customer.py
│ └── booking.py
├── services/
│ ├── room_service.py
│ ├── customer_service.py
│ ├── booking_service.py
│ ├── pricing_service.py
│ └── report_service.py
├── utils/
│ ├── csv_io.py
│ └── date_utils.py
└── **pycache**/
