import pandas as pd
import calendar
from datetime import date
import xlsxwriter
from services import room_service, booking_service

"""
    report_service tạo báo cáo thống kê và xuất excel
"""
def generate_occupancy_report(year):
    """
    Tạo báo cáo công suất và doanh thu các phòng theo năm
    """
    rooms = room_service.load_all()
    bookings = booking_service.load_all()
    
    
    df_result = calculate_monthly_stats(rooms, bookings, year)
    
    output_path = "occupancy_report.xlsx"
    export_to_excel(df_result, output_path, year)
    
    return df_result
# ------------------------------------------



def calculate_monthly_stats(rooms, bookings, year):
    """
    Tính toán OCC% và Doanh thu VNĐ phân bổ theo ngày  cho năm được chỉ định.
    Input:
        - rooms: Danh sách object Room (được load từ room_service.load_all())
        - bookings: Danh sách object Booking
        - year: Năm cần báo cáo
    """
    # Tạo map giá phòng để tra cứu nhanh: {room_id: price}
    room_prices = {r.room_id: r.price_per_night for r in rooms} 
    monthly_data = []

    for month in range(1, 13):
        # Xác định ngày đầu và ngày cuối của tháng
        days_in_month = calendar.monthrange(year, month)[1]
        m_start = date(year, month, 1)
        m_end = date(year, month, days_in_month)
        
        # Rooms Available: Tổng số phòng * số ngày trong tháng
        available = len(rooms) * days_in_month
        occupied, revenue = 0, 0.0
        
        for b in bookings:
            # Chỉ tính booking hợp lệ (confirmed/completed)
            if b.status.lower() not in ["confirmed", "completed"]: 
                continue
            
            # Lấy thời gian check-in/out
            b_in = b.check_in
            b_out = b.check_out
            if b.actual_check_out:
                b_out = max(b.check_out, b.actual_check_out)
            
            # Logic tính toán phần GIAO NHAU (Overlap) giữa booking và tháng hiện tại
            overlap_start = max(b_in, m_start)
            overlap_end = min(b_out, m_end)
            
            if overlap_start < overlap_end:
                # Số ngày khách thực tế ở trong tháng này
                stay_in_month = (overlap_end - overlap_start).days
                
                # Tổng số ngày của cả booking
                total_stay = (b_out - b_in).days
                
                if total_stay > 0:
                    # Doanh thu tháng = (Tổng tiền / Tổng ngày ở) * Số ngày ở trong tháng
                    # Nếu booking chưa có final_price, tính tạm theo giá phòng gốc
                    base_price = b.final_price if pd.notnull(b.final_price) else (room_prices.get(b.room_id, 0) * total_stay)
                    daily_rate = base_price / total_stay
                    
                    revenue += daily_rate * stay_in_month
                    occupied += stay_in_month

        # OCC % = Occupied / Available
        occ_pct = occupied / available if available > 0 else 0

        monthly_data.append({
            "Month": calendar.month_name[month],
            "Available": available,
            "Occupied": occupied,
            "OCC %": occ_pct,
            "Revenue": float(revenue)
        })
        
    return pd.DataFrame(monthly_data)

def print_summary(df, year):
    """In tóm tắt nhanh kết quả kinh doanh ra màn hình."""
    print(f"\n" + "="*35)
    print(f"   BÁO CÁO TỔNG QUAN NĂM {year}")
    print("="*35)
    print(f"- Tổng doanh thu: {df['Revenue'].sum():,.0f} VNĐ")
    print(f"- Công suất TB:   {df['OCC %'].mean()*100:.1f}%")
    
    # Tìm tháng có doanh thu cao nhất
    best_idx = df['Revenue'].idxmax()
    best_month = df.iloc[best_idx]
    print(f"- Tháng cao điểm: {best_month['Month']} ({best_month['Revenue']:,.0f} VNĐ)")
    print("="*35 + "\n")


def export_to_excel(df, file_path, year):
    """
    Xuất file Excel gồm 5 bảng (Năm + 4 Quý) và 5 biểu đồ Combo Chart.
    Trục X biểu đồ được tách nhãn để không bị dính.
    """
    # Xử lý dữ liệu rỗng (NaN) thành 0 để tránh lỗi Excel
    df = df.fillna(0)
    
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet("Dashboard")

    # --- ĐỊNH DẠNG (FORMATS) ---
    # Tiền VNĐ: Phân cách hàng nghìn, có chữ "₫"
    vnd_fmt = workbook.add_format({'num_format': '#,##0 "₫"', 'border': 1, 'align': 'right', 'valign': 'vcenter'})
    # Phần trăm: 1 số lẻ thập phân (e.g. 50.5%)
    pct_fmt = workbook.add_format({'num_format': '0.0%', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    # Header bảng
    header_fmt = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9E1F2', 'align': 'center', 'valign': 'vcenter'})
    # Ô thường
    cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
    # Tiêu đề từng phần
    title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#2F5597'})
    # Dòng Tổng (Total)
    total_fmt = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#E2EFDA', 'align': 'center'})
    total_vnd_fmt = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#E2EFDA', 'num_format': '#,##0 "₫"', 'align': 'right'})
    total_pct_fmt = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#E2EFDA', 'num_format': '0.1%', 'align': 'center'})

    def draw_section(data, title, start_row):
        # 1. Vẽ Bảng
        worksheet.write(start_row, 1, title, title_fmt)
        headers = ["Month", "Available", "Occupied", "OCC %", "Revenue"]
        for c, h in enumerate(headers): 
            worksheet.write(start_row+1, c+1, h, header_fmt)
        
        curr_row = start_row + 2
        for _, row in data.iterrows():
            worksheet.write(curr_row, 1, row["Month"], cell_fmt)
            worksheet.write(curr_row, 2, row["Available"], cell_fmt)
            worksheet.write(curr_row, 3, row["Occupied"], cell_fmt)
            worksheet.write(curr_row, 4, row["OCC %"], pct_fmt)
            worksheet.write(curr_row, 5, row["Revenue"], vnd_fmt)
            curr_row += 1
        
        # Vẽ dòng TOTAL
        sum_avail = data["Available"].sum()
        sum_occ = data["Occupied"].sum()
        sum_rev = data["Revenue"].sum()
        avg_occ = sum_occ / sum_avail if sum_avail > 0 else 0
        
        worksheet.write(curr_row, 1, "TOTAL", total_fmt)
        worksheet.write(curr_row, 2, sum_avail, total_fmt)
        worksheet.write(curr_row, 3, sum_occ, total_fmt)
        worksheet.write(curr_row, 4, avg_occ, total_pct_fmt)
        worksheet.write(curr_row, 5, sum_rev, total_vnd_fmt)

        # 2. Vẽ Biểu đồ Combo (Cột + Đường)
        chart = workbook.add_chart({'type': 'column'})
        
        # Series 1: OCC % (Cột xanh)
        chart.add_series({
            'name': 'OCC %', 
            'categories': ['Dashboard', start_row+2, 1, curr_row-1, 1],
            'values': ['Dashboard', start_row+2, 4, curr_row-1, 4],
            'fill': {'color': '#4472C4'},
            'data_labels': {'value': True, 'num_format': '0%', 'font': {'size': 9}}
        })
        
        # Series 2: Doanh thu (Đường đỏ) - Trục phụ (Y2)
        line_chart = workbook.add_chart({'type': 'line'})
        line_chart.add_series({
            'name': 'Revenue', 
            'categories': ['Dashboard', start_row+2, 1, curr_row-1, 1],
            'values': ['Dashboard', start_row+2, 5, curr_row-1, 5], 
            'line': {'color': 'red', 'width': 2.25}, 
            'marker': {'type': 'circle', 'size': 6},
            'y2_axis': True
        })
        chart.combine(line_chart)

        # Cấu hình Trục để tách nhãn (Label Separation)
        chart.set_x_axis({
            'name': 'Tháng', 
            'label_position': 'low', # Đẩy nhãn xuống thấp, tránh dính biểu đồ
            'name_font': {'bold': True}
        })
        chart.set_y_axis({
            'name': 'OCC (%)', 
            'num_format': '0%', 
            'name_font': {'color': '#4472C4'},
            'major_gridlines': {'visible': True, 'line': {'width': 0.25, 'dash_type': 'dash'}}
        })
        chart.set_y2_axis({
            'name': 'Doanh thu (VNĐ)', 
            'num_format': '#,##0', 
            'name_font': {'color': 'red'}
        })
        
        chart.set_title({'name': f'Biểu đồ {title}'})
        chart.set_size({'width': 650, 'height': 380}) # Kích thước biểu đồ
        
        # Chèn biểu đồ bên phải bảng
        worksheet.insert_chart(start_row, 7, chart)
        
        # Trả về vị trí dòng tiếp theo (cách ra 20 dòng cho đẹp)
        return curr_row + 20 

    # --- THỰC THI VẼ CÁC PHẦN ---
    # 1. Bảng Tổng Năm
    pos = draw_section(df, f"Năm {year}", 1)
    
    # 2. Bảng 4 Quý
    for i in range(4):
        # Cắt DataFrame lấy 3 tháng tương ứng (0-3, 3-6, 6-9, 9-12)
        quarter_data = df.iloc[i*3 : (i+1)*3]
        pos = draw_section(quarter_data, f"Quý {i+1} Năm {year}", pos)

    # Chỉnh độ rộng cột cho dễ nhìn
    worksheet.set_column('B:F', 18)
    writer.close()