from fpdf import FPDF
import unicodedata
import re

# Hàm chuyển đổi Tiếng Việt có dấu -> Không dấu
def remove_accents(input_str):
    if not input_str: return ""
    if not isinstance(input_str, str): return str(input_str)
    
    # Chuẩn hóa unicode
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace("Đ", "D").replace("đ", "d")

class InvoicePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'HOA DON THANH TOAN (INVOICE)', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_invoice_pdf(booking, customer, room):
    pdf = InvoicePDF()
    pdf.add_page()
    
    # Cấu hình font (Arial mặc định)
    pdf.set_font('Arial', '', 12)

    # --- Dữ liệu thô ---
    b_id = booking.booking_id
    b_date = booking.created_at[:10] if booking.created_at else ""
    
    c_name = customer.name if customer else "N/A"
    c_phone = customer.phone if customer else "N/A"
    
    r_id = room.room_id if room else "N/A"
    r_type = room.room_type if room else "N/A"
    r_price = room.price_per_night if room else 0
    
    check_in = str(booking.check_in)
    check_out = str(booking.check_out)
    final_price = booking.final_price if booking.final_price else 0

    # --- IN RA PDF (Dùng remove_accents để tránh lỗi font) ---
    
    # 1. Thông tin chung
    pdf.cell(0, 10, f"Ma don: {b_id}", ln=True)
    pdf.cell(0, 10, f"Ngay: {b_date}", ln=True)
    pdf.ln(5)

    # 2. Thông tin khách hàng
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "THONG TIN KHACH HANG", ln=True)
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(0, 10, f"Ten: {remove_accents(c_name)}", ln=True) 
    pdf.cell(0, 10, f"SDT: {c_phone}", ln=True)
    
    pdf.ln(5)

    # 3. Chi tiết phòng
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "CHI TIET PHONG", ln=True)
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(0, 10, f"Phong: {r_id} ({remove_accents(r_type)})", ln=True)
    pdf.cell(0, 10, f"Gia: {r_price:,.0f} VND/dem", ln=True)
    pdf.cell(0, 10, f"Check-in: {check_in}", ln=True)
    pdf.cell(0, 10, f"Check-out: {check_out}", ln=True)

    pdf.ln(10)

    # 4. Tổng tiền
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"TONG CONG: {final_price:,.0f} VND", ln=True, align='R')

    # Lưu file
    file_name = f"invoice_{b_id}.pdf"
    pdf.output(file_name)
    return file_name