Hãy xem xét hết tất cả các file code dưới đây và nhận ra hết tất cả các vấn đề, lỗi, bất thường và đưa ra hướng giải quyết 

/console/app.py :
import streamlit as st
import datetime
import pandas as pd
import sys
import os
import traceback
import re
import urllib.parse

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)

project_root = current_dir
while not os.path.exists(os.path.join(project_root, 'data')) and os.path.dirname(project_root) != project_root:
    project_root = os.path.dirname(project_root)

if os.path.exists(os.path.join(project_root, 'data')):
    os.chdir(project_root)
    src_path = os.path.join(project_root, 'src')
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.append(src_path)
    if project_root not in sys.path:
        sys.path.append(project_root)
else:
    st.error("⚠️ Không tìm thấy thư mục gốc dự án (chứa folder 'data').")
    st.stop()

try:
    from services import room_service, booking_service, customer_service, report_service, pricing_service
    from models.customer import Customer
except ImportError as e:
    st.error(f"❌ Lỗi Import hệ thống: {e}")
    st.stop()
except Exception as e:
    st.error(f"❌ Lỗi khởi động: {e}")
    st.stop()

st.set_page_config(
    page_title="Hotel Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: visible;}
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e0e0e0;
        color: #31333F !important;
    }
    div[data-testid="stMetric"] label {
        color: #555555 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #000000 !important;
    }
    .step-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        background: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
    }
    .step {
        flex: 1;
        text-align: center;
        padding: 8px;
        font-weight: 600;
        color: #adb5bd;
        border-bottom: 3px solid #dee2e6;
    }
    .step.active {
        color: #0d6efd;
        border-bottom: 3px solid #0d6efd;
    }
    .step.completed {
        color: #198754;
        border-bottom: 3px solid #198754;
    }
    .invoice-box {
        max-width: 800px;
        margin: auto;
        padding: 30px;
        border: 1px solid #eee;
        box-shadow: 0 0 10px rgba(0, 0, 0, .15);
        font-size: 16px;
        line-height: 24px;
        font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;
        color: #555;
        background-color: #fff;
    }
    .invoice-box table {
        width: 100%;
        line-height: inherit;
        text-align: left;
    }
    .invoice-box table td {
        padding: 5px;
        vertical-align: top;
    }
    .invoice-box table tr.top table td {
        padding-bottom: 20px;
    }
    .invoice-box table tr.top table td.title {
        font-size: 45px;
        line-height: 45px;
        color: #333;
    }
    .invoice-box table tr.information table td {
        padding-bottom: 40px;
    }
    .invoice-box table tr.heading td {
        background: #eee;
        border-bottom: 1px solid #ddd;
        font-weight: bold;
    }
    .invoice-box table tr.details td {
        padding-bottom: 20px;
    }
    .invoice-box table tr.item td {
        border-bottom: 1px solid #eee;
    }
    .invoice-box table tr.item.last td {
        border-bottom: none;
    }
    .invoice-box table tr.total td:nth-child(2) {
        border-top: 2px solid #eee;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'booking_step' not in st.session_state:
    st.session_state.booking_step = 1

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def go_to_booking_page(room_id, room_name, room_type, room_price):
    st.session_state['selected_room_id'] = room_id
    st.session_state['selected_room_name'] = room_name
    st.session_state['selected_room_type'] = room_type
    st.session_state['selected_room_price'] = room_price
    st.session_state.booking_step = 1
    navigate_to("📅 Đặt phòng mới")

def process_checkout(room_id):
    try:
        bookings = booking_service.get_bookings_for_room(room_id)
        active_booking = None
        today = datetime.date.today()
        
        for b in bookings:
            b_in = b.check_in
            b_out = b.check_out
            if isinstance(b_in, str): b_in = datetime.datetime.strptime(b_in, "%Y-%m-%d").date()
            if isinstance(b_out, str): b_out = datetime.datetime.strptime(b_out, "%Y-%m-%d").date()
            
            if b_in <= today < b_out and getattr(b, 'status', '') == 'confirmed':
                active_booking = b
                break
        
        if active_booking:
            booking_service.finalize_checkout(
                booking_id=active_booking.booking_id,
                actual_check_out=today,
                notes="Early checkout via UI"
            )
            st.toast(f"Đã trả phòng {room_id} thành công!", icon="✅")
            st.rerun()
        else:
            st.error("Không tìm thấy đơn đặt phòng đang hoạt động (confirmed) để check-out.")
    except Exception as e:
        st.error(f"Lỗi check-out: {e}")

def perform_booking_logic():
    temp_data = st.session_state.get('temp_booking_data')
    if not temp_data: return None

    try:
        try:
            existing_cust = customer_service.find_by_id(temp_data['customer_id'])
            if not existing_cust:
                new_customer = Customer(
                    customer_id=temp_data['customer_id'], 
                    name=temp_data['customer_name'], 
                    phone=temp_data['phone'], 
                    email=temp_data['email'], 
                    nationality=temp_data['nationality']
                )
                customer_service.save_one(new_customer)
            else:
                customer_service.update_customer(
                    temp_data['customer_id'],
                    name=temp_data['customer_name'],
                    phone=temp_data['phone'],
                    email=temp_data['email'],
                    nationality=temp_data['nationality']
                )
        except Exception: pass 

        check_in_str = temp_data['check_in'].isoformat()
        check_out_str = temp_data['check_out'].isoformat()

        booking_result = booking_service.create_booking(
            room_id=temp_data['room_id'],
            customer_id=temp_data['customer_id'], 
            check_in=check_in_str,
            check_out=check_out_str
        )

        notes = temp_data.get('notes', "")
        payment_type = temp_data.get('payment_type', 'unpaid')
        
        if payment_type == 'deposit_50':
             deposit_amount = booking_result.final_price * 0.5
             booking_service.confirm_payment(booking_result.booking_id, deposit_amount)
             remain = booking_result.final_price - deposit_amount
             notes += f" | Đã cọc 50%: {deposit_amount:,.0f} VNĐ. Còn lại: {remain:,.0f} VNĐ hạn {format_date_vn(check_in_str)}."
        elif payment_type == 'paid':
             booking_service.confirm_payment(booking_result.booking_id, booking_result.final_price)
             notes += " | Đã thanh toán đủ."
        else:
             notes += f" | Chưa thanh toán. Giữ phòng đến hết ngày hôm nay."

        if notes:
            booking_result.notes = notes.strip(" | ")
            booking_service.save_one(booking_result)
        
        keys_to_remove = ['selected_room_id', 'selected_room_name', 'selected_room_type', 'selected_room_price', 'temp_booking_data']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.booking_step = 1
        return booking_result

    except ValueError as ve:
        st.error(f"⛔ Lỗi: {ve}")
        return None
    except Exception as ex:
        st.error(f"⛔ Lỗi hệ thống: {ex}")
        return None

def load_room_data():
    if not os.path.exists("data/room.csv"):
        st.warning("Thiếu file data/room.csv")
        return []
    try:
        backend_rooms = room_service.load_all()
    except Exception:
        return []

    ui_rooms = []
    
    img_map = {
        "standard": "https://cdn-icons-png.flaticon.com/512/3009/3009968.png",
        "superior": "https://cdn-icons-png.flaticon.com/512/3009/3009968.png",
        "deluxe": "https://cdn-icons-png.flaticon.com/512/3009/3009968.png",
        "suite": "https://cdn-icons-png.flaticon.com/512/3009/3009968.png",
        "service": "https://cdn-icons-png.flaticon.com/512/3009/3009968.png"
    }

    for r in backend_rooms:
        try:
            status = room_service.get_room_status(r.room_id)
            if status == "vacant": status = "available"
        except AttributeError:
            status = getattr(r, 'status', 'available')
        
        current_customer = None
        current_checkout = None
        current_booking_id = None
        current_payment_status = None
        current_final_price = 0
        
        if status == 'occupied':
            try:
                bookings = booking_service.get_bookings_for_room(r.room_id)
                today = datetime.date.today()
                for b in bookings:
                    b_in = b.check_in
                    b_out = b.check_out
                    if isinstance(b_in, str): b_in = datetime.datetime.strptime(b_in, "%Y-%m-%d").date()
                    if isinstance(b_out, str): b_out = datetime.datetime.strptime(b_out, "%Y-%m-%d").date()

                    if isinstance(b_in, datetime.date) and isinstance(b_out, datetime.date):
                        if b_in <= today < b_out and getattr(b, 'status', '') == 'confirmed':
                            cust = customer_service.find_by_id(b.customer_id)
                            if cust:
                                current_customer = f"{cust.name.title()} ({cust.phone})"
                            else:
                                current_customer = "Khách Vãng Lai"
                            current_checkout = b_out
                            current_booking_id = b.booking_id
                            current_payment_status = getattr(b, 'payment_status', 'unpaid')
                            current_final_price = getattr(b, 'final_price', 0)
                            break
            except Exception: pass

        r_name_key = getattr(r, 'room_name', 'standard').lower()
        
        floor = getattr(r, 'floor', 0)
        if not floor or int(floor) == 0:
            try: floor = str(r.room_id)[0]
            except: floor = "0"

        ui_rooms.append({
            "room_id": str(r.room_id),
            "name": r.room_name,
            "room_type": r.room_type,
            "price": r.price_per_night,
            "capacity": r.capacity,
            "floor": floor,
            "status": status,
            "img": img_map.get(r_name_key, img_map["standard"]),
            "current_customer_name": current_customer,
            "current_checkout": current_checkout,
            "current_booking_id": current_booking_id,
            "current_payment_status": current_payment_status,
            "current_final_price": current_final_price
        })
    return ui_rooms

def get_real_revenue():
    try:
        bookings = booking_service.load_all()
        total_rev = 0
        for b in bookings:
            if getattr(b, 'status', '') == 'canceled': continue
            if getattr(b, 'final_price', None):
                total_rev += float(b.final_price)
            else:
                pass 
        return total_rev
    except: return 0

def format_date_vn(d):
    if not d: return ""
    if isinstance(d, (datetime.date, datetime.datetime)):
        return d.strftime("%d/%m/%Y")
    if isinstance(d, str):
        try:
            return datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
        except: return d
    return str(d)

# --- MAIN APP ---
def login():
    st.session_state.logged_in = True
    st.rerun()

def logout():
    st.session_state.logged_in = False
    st.rerun()

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown("<h1 style='text-align: center;'>🏨 Hotel Admin Portal</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", placeholder="admin")
            password = st.text_input("Mật khẩu", type="password", placeholder="123456")
            submit_login = st.form_submit_button("Đăng nhập", type="primary", use_container_width=True)
            if submit_login:
                if username == "admin" and password == "123456":
                    st.success("Thành công!")
                    login()
                else:
                    st.error("Sai thông tin!")
else:
    rooms_data = load_room_data()
    st.session_state.rooms = rooms_data

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/5977/5977591.png", width=80)
        st.title("Hotel Admin")
        st.caption("Phiên bản Demo v1.0")
        st.divider()
        
        menu_options = ["🏠 Trang chủ", "🛏️ Danh sách phòng", "📅 Đặt phòng mới", "🔎 Tra cứu & Khách hàng", "📊 Báo cáo"]
        if 'current_page' not in st.session_state: st.session_state.current_page = "🏠 Trang chủ"

        default_index = 0
        if st.session_state.current_page in menu_options:
            default_index = menu_options.index(st.session_state.current_page)
            
        selected_menu = st.radio("Điều hướng:", menu_options, index=default_index)
        
        if selected_menu != st.session_state.current_page:
            st.session_state.current_page = selected_menu
            st.rerun()
            
        menu = st.session_state.current_page
        
        st.divider()
        with st.expander("👤 Thông tin tài khoản", expanded=True):
            st.write("**Admin:** Đào (UI Dev)")
            if st.button("🚪 Đăng xuất", use_container_width=True): logout()
            st.markdown("---")
            if st.button("🔄 Reset Dữ liệu Gốc", help="Xóa sạch toàn bộ booking"):
                try:
                    bk_path = os.path.join(project_root, "data", "booking.csv")
                    if os.path.exists(bk_path):
                        with open(bk_path, "w", encoding="utf-8") as f:
                            f.write("booking_id,room_id,customer_id,check_in,check_out,actual_check_out,final_price,status,payment_status,notes,created_at,updated_at\n")
                    st.cache_data.clear()
                    for key in list(st.session_state.keys()):
                        if key != 'logged_in': del st.session_state[key]
                    st.toast("Đã reset hệ thống!", icon="✨")
                    st.rerun()
                except Exception as e: st.error(f"Lỗi: {e}")
    
    if menu == "🏠 Trang chủ":
        st.title("Dashboard Tổng quan")
        total_rooms = len(rooms_data)
        available_rooms = len([r for r in rooms_data if r['status'] == 'available'])
        occupied_rooms = len([r for r in rooms_data if r['status'] == 'occupied'])
        monthly_revenue = get_real_revenue() 
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng số phòng", f"{total_rooms}")
        col2.metric("Phòng trống", f"{available_rooms}")
        col3.metric("Đang sử dụng", f"{occupied_rooms}")
        col4.metric("Tổng Doanh thu", f"{monthly_revenue:,.0f} VNĐ")
        
        st.divider()
        st.subheader("Hoạt động gần đây")
        try:
            if os.path.exists("data/booking.csv"):
                all_bks = booking_service.load_all()
                if all_bks:
                    activity_data = []
                    for b in all_bks[-10:]:
                        c_name = "N/A"
                        cust = customer_service.find_by_id(b.customer_id)
                        if cust: c_name = cust.name
                        activity_data.append({
                            "Ngày Check-in": format_date_vn(b.check_in),
                            "Mã Booking": b.booking_id,
                            "Phòng": b.room_id,
                            "Khách hàng": c_name.title(),
                            "Trạng thái": b.status.title()
                        })
                    
                    df_chart = pd.DataFrame(activity_data)
                    df_chart.index = range(1, len(df_chart) + 1)
                    st.dataframe(df_chart, use_container_width=True)
                else: st.info("Chưa có giao dịch.")
        except: pass

    elif menu == "🛏️ Danh sách phòng":
        st.title("Quản lý phòng")
        
        if 'view_room_detail' in st.session_state:
            view_id = st.session_state.view_room_detail
            room_detail = next((r for r in rooms_data if r['room_id'] == view_id), None)
            
            if room_detail:
                with st.expander(f"ℹ️ Chi tiết Phòng {room_detail['room_id']} - {room_detail['name'].title()}", expanded=True):
                    c_det1, c_det2 = st.columns(2)
                    with c_det1:
                        st.markdown(f"**Trạng thái:** {room_detail['status'].title()}")
                        st.markdown(f"**Loại:** {room_detail['room_type'].title()}")
                        st.markdown(f"**Tầng:** {room_detail['floor']}")
                        st.markdown(f"**Giá:** {room_detail['price']:,} VNĐ/đêm")
                    with c_det2:
                        if room_detail['status'] == 'occupied':
                            st.info(f"👤 **{room_detail['current_customer_name']}**")
                            checkout_vn = format_date_vn(room_detail['current_checkout'])
                            st.write(f"📅 Ngày trả dự kiến: {checkout_vn}")
                            
                            # LOGIC THANH TOÁN & CHECKOUT
                            pay_stat = room_detail.get('current_payment_status', 'unpaid')
                            total_p = float(room_detail.get('current_final_price') or 0)
                            
                            paid_val = 0.0
                            if pay_stat == 'paid':
                                paid_val = total_p
                                st.success("✅ Đã thanh toán đủ")
                            elif pay_stat == 'deposit':
                                paid_val = total_p * 0.5
                                st.warning("⚠️ Đã cọc 50%")
                            else:
                                st.error("❌ Chưa thanh toán")
                                
                            remain_val = total_p - paid_val
                            if remain_val > 0:
                                st.write(f"Còn thiếu: :red[**{remain_val:,.0f} VNĐ**]")
                                if st.button("💰 Đóng tiền còn lại"):
                                    st.session_state[f"show_pay_{room_detail['room_id']}"] = True
                                
                                if st.session_state.get(f"show_pay_{room_detail['room_id']}"):
                                    pm = st.radio("Hình thức:", ["Tiền mặt", "QR"], key=f"pm_{room_detail['room_id']}")
                                    if st.button("Xác nhận đóng tiền", type="primary"):
                                        booking_service.confirm_payment(room_detail['current_booking_id'], remain_val)
                                        st.toast("Đã thanh toán đủ!", icon="🎉")
                                        del st.session_state[f"show_pay_{room_detail['room_id']}"]
                                        st.rerun()

                            st.write("---")
                            if st.button("🛑 Trả phòng ngay (Check-out)", key="btn_checkout_early", type="primary"):
                                process_checkout(room_detail['room_id'])
                        else:
                            st.success("Phòng đang trống.")
                    if st.button("Đóng chi tiết"):
                        del st.session_state['view_room_detail']
                        st.rerun()
                st.divider()

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: search_term = st.text_input("🔍 Tìm kiếm", placeholder="Số phòng...")
        with c2: filter_name = st.multiselect("Hạng phòng", sorted(list(set([r['name'].title() for r in rooms_data]))))
        with c3: filter_status = st.selectbox("Trạng thái", ["Tất cả", "Trống", "Có khách"])

        filtered_rooms = []
        for room in rooms_data:
            if filter_status == "Trống" and room["status"] != "available": continue
            if filter_status == "Có khách" and room["status"] != "occupied": continue
            if filter_name and room["name"].title() not in filter_name: continue
            if search_term and search_term.lower() not in room["room_id"].lower(): continue
            filtered_rooms.append(room)

        st.caption(f"Hiển thị {len(filtered_rooms)} phòng.")
        for idx, room in enumerate(filtered_rooms):
            with st.container(border=True):
                col_img, col_info, col_status, col_action = st.columns([1, 4, 2, 2])
                with col_img: st.image(room['img'], width=60)
                with col_info:
                    st.subheader(f"P.{room['room_id']}")
                    st.caption(f"Tầng {room['floor']} | {room['name'].title()} ({room['room_type'].title()}) | {room['capacity']} người")
                    st.write(f"**{room['price']:,} VNĐ/đêm**")
                with col_status:
                    if room["status"] == "available": st.success("✅ Trống")
                    else: st.error("❌ Có khách")
                with col_action:
                    btn_key = f"btn_{room['room_id']}_{idx}"
                    if room["status"] == "available":
                        st.button("Chọn đặt", key=btn_key, type="primary", use_container_width=True,
                                  on_click=go_to_booking_page,
                                  args=(room['room_id'], room['name'], room['room_type'], room['price']))
                    else:
                        if st.button("Xem chi tiết", key=btn_key, use_container_width=True):
                            st.session_state.view_room_detail = room['room_id']
                            st.rerun()

    elif menu == "📅 Đặt phòng mới":
        st.title("Tạo Booking mới")
        
        step = st.session_state.get('booking_step', 1)
        
        # --- STEPPER BAR ---
        col_s1, col_s2, col_s3 = st.columns(3)
        steps = ["1. Thông tin & Ghi chú", "2. Thanh toán", "3. Hoàn tất"]
        for i, (col, title) in enumerate(zip([col_s1, col_s2, col_s3], steps)):
            cls = "active" if step == i+1 else "completed" if step > i+1 else ""
            col.markdown(f'<div class="step {cls}">{title}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if step == 1:
            col_form, col_bill = st.columns([1, 1])
            with col_bill:
                st.subheader("📋 Chi tiết phòng")
                with st.container(border=True):
                    unique_names = sorted(list(set([r['name'].title() for r in rooms_data]))) if rooms_data else []
                    pre_fill_name = unique_names[0] if unique_names else "Standard"
                    is_room_locked = False
                    if 'selected_room_id' in st.session_state:
                        pre_fill_name = st.session_state.get('selected_room_name', "standard").title()
                        is_room_locked = True
                        st.success(f"Đang chọn: **Phòng {st.session_state['selected_room_id']}**")

                    room_name_options = unique_names
                    default_idx = 0
                    if pre_fill_name in room_name_options: default_idx = room_name_options.index(pre_fill_name)
                        
                    selected_room_name = st.selectbox("Hạng phòng", room_name_options, index=default_idx, disabled=is_room_locked)
                    available_types = sorted(list(set([r['room_type'].title() for r in rooms_data if r['name'].lower() == selected_room_name.lower()])))
                    selected_room_type = st.selectbox("Loại giường", available_types)

                    current_price = 0
                    max_cap = 2
                    for r in rooms_data:
                        if r['name'].lower() == selected_room_name.lower() and r['room_type'].lower() == selected_room_type.lower():
                            current_price = r['price']
                            max_cap = r['capacity']
                            break
                    
                    c_d1, c_d2 = st.columns(2)
                    check_in = c_d1.date_input("Check-in", datetime.date.today())
                    check_out = c_d2.date_input("Check-out", datetime.date.today() + datetime.timedelta(days=1))
                    
                    num_guests = st.number_input("Số khách", 1, int(max_cap), min(2, int(max_cap)))
                    st.caption(f"Tối đa: {max_cap} người")

                    total_nights = (check_out - check_in).days
                    if total_nights > 0:
                        try:
                            # TÍNH TOÁN CHI TIẾT
                            price_info = pricing_service.calculate_price_breakdown(check_in.isoformat(), check_out.isoformat(), current_price)
                            final_price = price_info['final_price']
                            
                            st.markdown("---")
                            st.write(f"Đơn giá: **{current_price:,.0f} VNĐ** x **{total_nights} đêm**")
                            st.write(f"= **{current_price * total_nights:,.0f} VNĐ**")
                            if price_info.get('weekend_surcharge', 0) > 0:
                                st.write(f"+ Phụ phí cuối tuần (20%): :orange[{price_info['weekend_surcharge']:,.0f} VNĐ]")
                            st.markdown(f"### Tổng cộng: :red[{int(final_price):,} VNĐ]")
                        except: st.error("Lỗi tính giá")
                    else: st.error("Ngày Check-out phải sau Check-in")

            with col_form:
                st.subheader("📝 Thông tin khách")
                with st.form("info_form"):
                    c_name = st.text_input("Họ tên (*)")
                    c_id = st.text_input("CCCD/CMND (*)")
                    c_phone = st.text_input("SĐT (*)")
                    c_email = st.text_input("Email")
                    c_nation = st.text_input("Quốc tịch", "Việt Nam")
                    c_note = st.text_area("Ghi chú đặc biệt (Notes)")
                    
                    if st.form_submit_button("Tiếp tục thanh toán ➡️", type="primary"):
                        if not c_name or not c_id or not c_phone:
                            st.error("Vui lòng điền đủ thông tin bắt buộc (*)")
                        elif total_nights <= 0:
                            st.error("Ngày đặt không hợp lệ")
                        else:
                            booked_room_id = None
                            if 'selected_room_id' in st.session_state:
                                booked_room_id = st.session_state['selected_room_id']
                            else:
                                try:
                                    avail = room_service.get_available_rooms(check_in.isoformat(), check_out.isoformat())
                                    for r in avail:
                                        if r.room_name.lower() == selected_room_name.lower() and r.room_type.lower() == selected_room_type.lower():
                                            booked_room_id = r.room_id
                                            break
                                except: pass
                            
                            if booked_room_id:
                                st.session_state['temp_booking_data'] = {
                                    "room_id": booked_room_id,
                                    "customer_id": c_id,
                                    "customer_name": c_name,
                                    "phone": c_phone,
                                    "email": c_email,
                                    "nationality": c_nation,
                                    "notes": c_note,
                                    "check_in": check_in,
                                    "check_out": check_out,
                                    "total_price": int(final_price),
                                    "nights": total_nights
                                }
                                st.session_state.booking_step = 2
                                st.rerun()
                            else:
                                st.error("Hết phòng loại này!")

        elif step == 2:
            temp = st.session_state.get('temp_booking_data')
            if not temp:
                st.session_state.booking_step = 1
                st.rerun()

            with st.container(border=True):
                st.markdown(f"### 💳 Thanh toán cho phòng {temp['room_id']}")
                st.info(f"Khách: **{temp['customer_name']}** - Tổng tiền: **{temp['total_price']:,} VNĐ**")
                
                pay_option = st.radio("Loại thanh toán:", ["Thanh toán ngay (Giữ phòng)", "Đặt cọc 50% (Giữ phòng)", "Chưa thanh toán (Giữ trong ngày)"])
                
                amount_needed = 0
                if pay_option == "Thanh toán ngay (Giữ phòng)":
                    amount_needed = temp['total_price']
                    temp['payment_type'] = 'paid'
                elif pay_option == "Đặt cọc 50% (Giữ phòng)":
                    amount_needed = int(temp['total_price'] * 0.5)
                    temp['payment_type'] = 'deposit_50'
                else:
                    amount_needed = 0
                    temp['payment_type'] = 'unpaid'

                if amount_needed > 0:
                    st.write(f"Số tiền cần trả: **{amount_needed:,} VNĐ**")
                    pay_method = st.radio("Phương thức:", ["💵 Tiền mặt", "🏦 Chuyển khoản QR"])
                    if pay_method == "💵 Tiền mặt":
                        rec = st.number_input("Khách đưa:", value=amount_needed, step=10000)
                        if rec >= amount_needed:
                            st.success(f"Tiền thừa: {rec - amount_needed:,} VNĐ")
                    else:
                        qr_url = f"https://img.vietqr.io/image/mbbank-277772323-compact.png?amount={amount_needed}&addInfo=Phong {temp['room_id']}&accountName=Dao Duc Khoi"
                        st.image(qr_url, width=250)
                        st.caption("Quét mã để thanh toán")
                else:
                    st.warning("Lưu ý: Booking chưa thanh toán chỉ được giữ đến 18:00 hôm nay.")

                c_back, c_next = st.columns(2)
                if c_back.button("⬅️ Quay lại"):
                    st.session_state.booking_step = 1
                    st.rerun()
                
                if c_next.button("✅ Hoàn tất Booking", type="primary"):
                    booking_result = perform_booking_logic()
                    if booking_result:
                        st.session_state.final_booking_id = booking_result.booking_id
                        st.session_state.booking_step = 3
                        st.rerun()
        
        elif step == 3:
             bid = st.session_state.get('final_booking_id')
             b_info = booking_service.find_by_id(bid)
             if b_info:
                 c_info = customer_service.find_by_id(b_info.customer_id)
                 c_name = c_info.name if c_info else "N/A"
                 c_phone = c_info.phone if c_info else "N/A"
                 
                 st.balloons()
                 st.success(f"Đã tạo Booking thành công! Mã đơn: **{bid}**")
                 
                 # --- HÓA ĐƠN ĐẸP ---
                 invoice_html = f"""
                 <div class="invoice-box">
                    <table cellpadding="0" cellspacing="0">
                        <tr class="top">
                            <td colspan="2">
                                <table>
                                    <tr>
                                        <td class="title">HOTEL BOOKING</td>
                                        <td>
                                            Mã đơn: {bid}<br>
                                            Ngày tạo: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr class="information">
                            <td colspan="2">
                                <table>
                                    <tr>
                                        <td>
                                            <b>Khách hàng:</b> {c_name}<br>
                                            SĐT: {c_phone}
                                        </td>
                                        <td>
                                            <b>Phòng:</b> {b_info.room_id}<br>
                                            Check-in: {format_date_vn(b_info.check_in)}<br>
                                            Check-out: {format_date_vn(b_info.check_out)}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr class="heading">
                            <td>Mô tả</td>
                            <td>Chi tiết</td>
                        </tr>
                        <tr class="item">
                            <td>Trạng thái</td>
                            <td>{b_info.status.upper()}</td>
                        </tr>
                        <tr class="item">
                            <td>Thanh toán</td>
                            <td>{b_info.payment_status.upper()}</td>
                        </tr>
                        <tr class="item last">
                            <td>Ghi chú</td>
                            <td>{b_info.notes or 'Không có'}</td>
                        </tr>
                        <tr class="total">
                            <td></td>
                            <td>Tổng tiền: {b_info.final_price:,.0f} VNĐ</td>
                        </tr>
                    </table>
                 </div>
                 """
                 st.markdown(invoice_html, unsafe_allow_html=True)
                 
                 if st.button("🖨️ In Hóa Đơn (Giả lập)"):
                     st.toast("Đang gửi lệnh in...", icon="🖨️")

             if st.button("Về trang chủ"):
                 navigate_to("🛏️ Danh sách phòng")

    elif menu == "🔎 Tra cứu & Khách hàng":
        st.title("Tra cứu khách hàng")
        kw = st.text_input("Nhập SĐT hoặc CCCD:")
        if kw:
            cust = customer_service.find_by_id(kw) or customer_service.find_by_phone(kw)
            if cust:
                st.success(f"Khách: {cust.name.title()} - {cust.nationality.title()}")
                with st.expander("Sửa thông tin"):
                    n_email = st.text_input("Email", cust.email)
                    if st.button("Lưu"):
                        customer_service.update_customer(cust.customer_id, email=n_email)
                        st.toast("Đã lưu")
            else: st.warning("Không tìm thấy")

    elif menu == "📊 Báo cáo":
        st.title("Báo cáo Doanh thu & Hiệu suất")
        
        try:
            today_r = datetime.date.today()
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_d = st.date_input("Từ ngày", today_r.replace(day=1))
            with col_date2:
                end_d = st.date_input("Đến ngày", today_r)

            if st.button("Xem báo cáo"):
                if os.path.exists("data/booking.csv"):
                    bookings_all = booking_service.load_all()
                    rooms_all = room_service.load_all()
                    
                    utilization = report_service.room_utilization(
                        start_d.isoformat(), 
                        end_d.isoformat(), 
                        rooms_all, 
                        bookings_all
                    )
                    
                    rev_by_month = report_service.revenue_by_month(bookings_all, end_d.year, end_d.month)
                    
                    m1, m2 = st.columns(2)
                    m1.metric(f"Doanh thu T{end_d.month}/{end_d.year}", f"{rev_by_month:,.0f} VNĐ")
                    m2.metric("Số phòng khai thác", f"{len(rooms_all)}")
                    
                    st.subheader("Tỷ lệ lấp đầy (Utilization)")
                    df_util = pd.DataFrame(list(utilization.items()), columns=["Mã phòng", "Tỷ lệ"])
                    df_util['Tỷ lệ %'] = (df_util['Tỷ lệ'] * 100).round(1)
                    df_util.index = range(1, len(df_util) + 1)
                    
                    st.bar_chart(df_util.set_index("Mã phòng")['Tỷ lệ %'])
                    st.dataframe(df_util, use_container_width=True)
                    
                    csv = df_util.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Tải xuống báo cáo (Excel/CSV)",
                        data=csv,
                        file_name='bao_cao_hieu_suat.csv',
                        mime='text/csv',
                        type="primary"
                    )
                else:
                    st.info("Chưa có dữ liệu booking.")

        except Exception as e:
            st.error(f"Lỗi khi tạo báo cáo: {e}")

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: grey;'>© 2025 Hotel Booking Project - Team APK</div>", unsafe_allow_html=True)

/data/booking.csv :
booking_id,room_id,customer_id,check_in,check_out,actual_check_out,final_price,status,payment_status,notes,created_at,updated_at

/data/customer.csv :
customer_id,name,phone,email,nationality,is_loyalty_member

/data/room.csv :
room_id,floor,room_name,room_type,capacity,price_per_night,status

201,2,standard,twin,2,550000,available
202,2,standard,twin,2,550000,available
203,2,standard,twin,2,550000,available
204,2,standard,twin,2,550000,available
205,2,standard,twin,2,550000,available
206,2,standard,twin,2,550000,available
207,2,standard,twin,2,550000,available
208,2,standard,twin,2,550000,available
209,2,standard,twin,2,550000,available
210,2,standard,twin,2,550000,available
211,2,standard,double,2,650000,available
212,2,standard,double,2,650000,available

301,3,standard,double,2,650000,available
302,3,standard,double,2,650000,available
303,3,standard,double,2,650000,available
304,3,standard,double,2,650000,available
305,3,standard,double,2,650000,available
306,3,standard,double,2,650000,available
307,3,standard,double,2,650000,available
308,3,standard,double,2,650000,available

309,3,superior,double,2,850000,available
310,3,superior,twin,2,800000,available
311,3,superior,double,2,850000,available
312,3,superior,twin,2,800000,available

401,4,superior,double,2,850000,available
402,4,superior,double,2,850000,available
403,4,superior,double,2,850000,available
404,4,superior,double,2,850000,available
405,4,superior,double,2,850000,available
406,4,superior,double,2,850000,available
407,4,superior,double,2,850000,available
408,4,superior,twin,2,800000,available
409,4,superior,twin,2,800000,available
410,4,superior,twin,2,800000,available
411,4,superior,twin,2,800000,available

412,4,deluxe,king,2,1100000,available
413,4,deluxe,king,2,1100000,available

501,5,deluxe,king,2,1200000,available
502,5,deluxe,king,2,1200000,available
503,5,deluxe,king,2,1200000,available
504,5,deluxe,twin,2,1100000,available
505,5,deluxe,twin,2,1100000,available
506,5,deluxe,twin,2,1100000,available
507,5,deluxe,twin,2,1100000,available
508,5,deluxe,twin,2,1100000,available

509,5,suite,junior,2,1500000,available
510,5,suite,junior,2,1500000,available
511,5,suite,junior,2,1500000,available
512,5,suite,executive,3,1800000,available
513,5,suite,family,4,2200000,available

/models/booking.py :
from datetime import datetime, date
from utils.date_utils import parse_date
from typing import Optional, Dict, Any



class Booking:
    """
    Booking status: pending -> confirmed -> completed
                            ↘ canceled
    """
    def __init__(
        self,
        booking_id: str,
        room_id: str,
        customer_id: str,
        check_in: date | None,
        check_out: date | None,
        actual_check_out: date | None,
        final_price: Optional[float] = None,
        status: str ="pending",
        payment_status: str = "unpaid",
        notes: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):

        self.booking_id        = booking_id
        self.room_id           = room_id
        self.customer_id       = customer_id

        self.check_in          = check_in
        self.check_out         = check_out
        self.actual_check_out  = actual_check_out

        self.final_price       = final_price
        self.status            = status
        self.payment_status    = payment_status
        self.notes             = notes

        now = datetime.now().isoformat()
        self.created_at        = created_at or now
        self.updated_at        = updated_at or now
# ---------------------------------------------------
# Serialization
# ---------------------------------------------------
    @classmethod

    def from_dict(cls, d: Dict[str, Any]) -> "Booking":

        return cls(
            booking_id        = str(d.get("booking_id")),
            room_id           = str(d.get("room_id")),
            customer_id       = str(d.get("customer_id")),

            check_in          = parse_date(d.get("check_in")),
            check_out         = parse_date(d.get("check_out")),
            actual_check_out  = parse_date(d.get("actual_check_out")) if d.get("actual_check_out") else None,
             
            final_price       = float(d.get("final_price")) if d.get("final_price") else None,
            status            = d.get("status", "pending"),
            payment_status    = d.get("payment_status", "unpaid"),
            notes             = d.get("notes"),
 
            created_at        = d.get("created_at"),
            updated_at        = d.get("updated_at"),
        )

    def to_dict(self) -> Dict[str, Any]:

        return {
            "booking_id"        : self.booking_id,
            "room_id"           : self.room_id,
            "customer_id"       : self.customer_id,

            "check_in"          : self.check_in.isoformat() if self.check_in else None,
            "check_out"         : self.check_out.isoformat() if self.check_out else None,
            "actual_check_out"  : self.actual_check_out.isoformat() if self.actual_check_out else None,
            
            "final_price"       : self.final_price,
            "status"            : self.status,
            "payment_status"    : self.payment_status,
            "notes"             : self.notes,
  
            "created_at"        : self.created_at,
            "updated_at"        : self.updated_at,
        }
    
# ---------------------------------------------------
# Domain logic
# ---------------------------------------------------
    def nights_used(self) -> Optional[int]:

        end = self.actual_check_out or self.check_out
        return max((end - self.check_in).days,0)
    
    def confirm(self) -> bool:

        if self.status != "pending":
            return False
        self.status = "confirmed"
        self.updated_at = datetime.now().isoformat()
        return True
    
    def cancel(self) -> bool:
        
        if self.status != "confirmed":
            return False
        
        if self.payment_status != "unpaid":
            return False
        
        self.status = "canceled"
        self.updated_at = datetime.now().isoformat()
        return True
    
    def finalize_checkout(
        self,
        final_price: float,
        actual_check_out: date | None,
        payment_status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        
        if (self.status or "").lower() != "confirmed":
            return False

        if actual_check_out is not None:
            self.actual_check_out = actual_check_out


        self.final_price = float(final_price)

        self.payment_status = "paid"
        if notes is not None:
            self.notes = notes

        self.status = "completed"
        self.updated_at = datetime.now().isoformat()
        return True
    
    def __str__(self) -> str:
        return (
            f"Booking("
            f"id={self.booking_id}, "
            f"room_id={self.room_id}, "
            f"customer_id={self.customer_id}, "
            f"check_in={self.check_in}, "
            f"check_out={self.check_out}, "
            f"status={self.status}, "
            f"final_price={self.final_price}"
            f")"
        )

/models/customer.py :
from typing import Optional, Dict, Any

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
        self.customer_id = customer_id

        self.name              = name
        self.email             = email
        self.phone             = phone

        self.nationality       = nationality
        self.is_loyalty_member = is_loyalty_member

    @classmethod

    def from_dict(cls, d: Dict[str, Any]) -> "Customer":
        return cls(
            customer_id       = str(d.get("customer_id")),
            
            name              = d.get("name", ""),
            email             = d.get("email", ""),
            phone             = d.get("phone", ""),

            nationality       = d.get("nationality"),
            is_loyalty_member = str(d.get("is_loyalty_member")).lower() == "true",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id"      : self.customer_id,
            "name"             : self.name,
            "email"            : self.email,
            "phone"            : self.phone,
            "nationality"      : self.nationality,
            "is_loyalty_member": self.is_loyalty_member,
        }

    def __str__(self) -> str:
        return f"Customer(id={self.customer_id}, name={self.name}, email={self.email})"

/models/room.py :
from typing import Optional, Dict, Any


class Room:

    def __init__(
        self,
        room_id: str,
        room_name: str,
        room_type: str,
        capacity: int,
        price_per_night: float,
        status: str = "available"
    ):  # Khai báo room

        self.room_id         = room_id
        self.room_name       = room_name
        self.room_type       = room_type
        self.capacity        = capacity
        self.price_per_night = price_per_night
        self.status          = (status or "available").lower()

    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> "Room":  # lấy dữ liệu từ csv

        return cls(
            room_id         = row.get("room_id"),
            room_name       = row.get("room_name", ""),
            room_type       = row.get("room_type", ""),
            capacity        = int(row.get("capacity",1)),
            price_per_night = float(row.get("price_per_night") or 0.0),
            status          = row.get("status","available")
        )

    def to_dict(self) -> Dict[str, Any]:  # lưu dữ liệu về csv
        return {
            "room_id"         : self.room_id,
            "room_name"       : self.room_name,
            "room_type"       : self.room_type,
            "capacity"        : self.capacity,
            "price_per_night" : self.price_per_night,
            "status"          : self.status
        }

    def __str__(self) -> str:
        return (
            f"Room("
            f"id              = {self.room_id}, "
            f"name            = {self.room_name}, "
            f"type            = {self.room_type}, "
            f"capacity        = {self.capacity}, "
            f"price_per_night = {self.price_per_night}"
            f"status          = {self.status}"
            f")"
        )

/services/booking_service.py :
from pathlib import Path
from typing import List, Optional
from datetime import date, datetime
from models.booking import Booking
from services import room_service, customer_service, pricing_service
from utils.csv_io import read_csv, write_csv
from utils.date_utils import parse_date
import uuid
import random
import string

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

def load_all() -> List[Booking]:
    return [Booking.from_dict(r) for r in read_csv(PATH)]

def save_all(bookings: List[Booking]) -> None:
    write_csv(PATH, [b.to_dict() for b in bookings], FIELDS)

def save_one(booking: Booking) -> None:
    bookings = load_all()
    # Kiểm tra xem booking đã tồn tại chưa để update thay vì append
    exists = False
    for i, b in enumerate(bookings):
        if str(b.booking_id) == str(booking.booking_id):
            bookings[i] = booking
            exists = True
            break
    if not exists:
        bookings.append(booking)
    save_all(bookings)

def next_id() -> int:
    # Tạo mã random gồm 6 ký tự viết hoa để tránh trùng lặp
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def find_by_id(booking_id: str) -> Optional[Booking]:
    bookings = load_all()
    for b in bookings:
        if str(b.booking_id) == str(booking_id):
            return b
    return None

def get_bookings_for_room(room_id: str) -> List[Booking]:
    return [
        b
        for b in load_all()
        if str(b.room_id) == str(room_id) and getattr(b, "status", "") != "canceled"
    ]

def create_booking(
    room_id: str, customer_id: str, check_in: str, check_out: str
) -> Booking:
    if not room_id or not customer_id:
        raise ValueError("Missing room_id or customer_id")
    if not check_in or not check_out:
        raise ValueError("Missing check_in or check_out")

    room = room_service.find_by_id(room_id)
    if not room:
        raise ValueError("Room not found")

    # Kiểm tra available phải được thực hiện ở UI trước khi gọi
    
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
    booking = find_by_id(booking_id)
    if not booking:
        raise ValueError("Booking not found")

    if booking.status != "confirmed":
        raise ValueError("Booking must be confirmed before payment")

    # Logic cọc 50%
    if amount_paid >= booking.final_price:
        booking.payment_status = "paid"
    elif amount_paid > 0:
        booking.payment_status = "deposit"
    
    booking.updated_at = datetime.now().isoformat()
    save_one(booking)
    return booking

def finalize_checkout(
    booking_id: str, actual_check_out: date | None, notes=None
) -> Booking:
    b = find_by_id(booking_id)
    if b is None:
        raise ValueError("Booking not found")

    # Cho phép checkout nếu trạng thái là confirmed
    if b.status != "confirmed":
        raise ValueError("Only confirmed booking can be finalized")

    room = room_service.find_by_id(b.room_id)
    customer = customer_service.find_by_id(b.customer_id)

    checkout_date = actual_check_out or b.check_out
    
    check_in_str = b.check_in.isoformat() if b.check_in else ""
    check_out_str = checkout_date.isoformat() if checkout_date else ""

    final_price = pricing_service.calculate_booking_price(
        check_in_str, check_out_str, room.price_per_night, customer.is_loyalty_member
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

/services/customer_service.py :
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
# ----------------------------------------------------------------------------------
#          LOAD/SAVE
# ----------------------------------------------------------------------------------

def load_all() -> List[Customer]:

    return [Customer.from_dict(r) for r in read_csv(PATH)]

def save_all(customers: List[Customer]) -> None:
    write_csv(PATH,[c.to_dict() for c in customers],FIELDS)

def save_one(customer: Customer) -> None:
    customers = load_all()
    customers.append(customer)
    save_all(customers)
# ----------------------------------------------------------------------------------
#          HELPERS
# ----------------------------------------------------------------------------------
def next_id() -> int:

    customers = load_all()
    if not customers:
        return 1
    try: 
        return max(int(c.customer_id) for c in customers) + 1
    except Exception:
        return len(customers) + 1 
       
def find_by_id(customer_id:str) -> Optional[Customer]:

    for c in load_all():
        if c.customer_id == customer_id:
            return c
    return None

def find_by_phone(phone):
    return next(
        (c for c in load_all() if c.phone.lower() == phone.lower()),None
    )

def update_customer(customer_id:str,**updates) -> Customer:
    
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

/services/pricing_service.py :
from utils.date_utils import count_days,weekend_nights


loyalty_rate = 0.05
weekend_rate = 0.2

def calculate_booking_price(
        check_in:str,
        check_out:str,
        price_per_night:float,
        is_loyalty_member = False,
    ) -> float:

    nights = count_days(check_in,check_out)

    if nights <= 0:
        return 0.0
    
    weekend = weekend_nights(check_in, check_out)
    base_price = nights * price_per_night

    weekend_surcharge = weekend * price_per_night * weekend_rate
    base_price += weekend_surcharge
    
    if is_loyalty_member:
        base_price = apply_loyalty_discount(base_price)
    
    return round(base_price,2)

def apply_loyalty_discount(base_price: float) -> float:
    return base_price - (base_price * loyalty_rate)


def calculate_price_breakdown(
        check_in:str,
        check_out:str,
        price_per_night:float,
        is_loyalty_member = False,

) -> dict:
    
    nights = count_days(check_in,check_out)
    weekend = weekend_nights(check_in,check_out)
    
    base_price = nights * price_per_night
    weekend_surcharge = weekend * price_per_night * weekend_rate
    loyalty_discount = base_price * loyalty_rate if is_loyalty_member else 0.0

    final_price = calculate_booking_price(
        check_in,
        check_out,
        price_per_night,
        is_loyalty_member
    )

    return {
        "nights": nights,
        "price_per_night": price_per_night,
        "base_price": base_price,
        "weekend_nights": weekend,
        "weekend_surcharge": weekend_surcharge,
        "loyalty_applied": is_loyalty_member,
        "loyalty_discount": loyalty_discount,
        "final_price": final_price,
    }

/services/report_service.py :
import pandas as pd
from pathlib import Path
import calendar

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter


ROOM_FILE = Path("data/room.csv")
BOOKING_FILE = Path("data/booking.csv")
OUTPUT_FILE = Path("occupancy_report.xlsx")


def generate_occupancy_report(year: int, quarter: int | None = None):
    """
    year: required
    quarter: optional (1,2,3,4)
    """

    # ---------- LOAD DATA ----------
    rooms_df = pd.read_csv(ROOM_FILE)
    total_rooms = len(rooms_df)
    if total_rooms == 0:
        raise ValueError("No rooms found")

    bookings = pd.read_csv(BOOKING_FILE)
    bookings = bookings[bookings["status"].isin(["confirmed", "completed"])]
    bookings["check_in"] = pd.to_datetime(bookings["check_in"])
    bookings["check_out"] = pd.to_datetime(bookings["check_out"])

    # ---------- MONTH RANGE ----------
    if quarter:
        start_month = (quarter - 1) * 3 + 1
        months = range(start_month, start_month + 3)
        sheet_name = f"Q{quarter}_{year}"
        title_text = f"Occupancy Report – Q{quarter} / {year}"
    else:
        months = range(1, 13)
        sheet_name = str(year)
        title_text = f"Occupancy Report – Year {year}"

    rows = []

    # ---------- CALCULATION ----------
    for m in months:
        days = calendar.monthrange(year, m)[1]
        month_start = pd.Timestamp(year, m, 1)
        month_end = pd.Timestamp(year, m, days)

        occupied_nights = 0
        for _, b in bookings.iterrows():
            start = max(b["check_in"], month_start)
            end = min(b["check_out"], month_end)
            if start < end:
                occupied_nights += (end - start).days

        rooms_available = total_rooms * days
        occ = (occupied_nights / rooms_available * 100) if rooms_available else 0

        rows.append([
            calendar.month_name[m],
            rooms_available,
            occupied_nights,
            round(occ, 1),
        ])

    df = pd.DataFrame(
        rows,
        columns=["Month", "Rooms Available", "Rooms Occupied", "OCC %"]
    )

    # ---------- TOTAL ----------
    total_available = df["Rooms Available"].sum()
    total_occupied = df["Rooms Occupied"].sum()
    total_occ = round((total_occupied / total_available) * 100, 1)

    # ---------- EXPORT EXCEL ----------
    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="a" if OUTPUT_FILE.exists() else "w"
    ) as writer:

        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]

        # ===== STYLE =====
        bold = Font(bold=True)
        header_fill = PatternFill("solid", fgColor="D9D9D9")
        total_fill = PatternFill("solid", fgColor="E7F3FF")

        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Title
        ws.insert_rows(1)
        ws["A1"] = title_text
        ws["A1"].font = Font(bold=True, size=12)
        ws.merge_cells("A1:D1")

        # Header
        for c in ws[2]:
            c.font = bold
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center")
            c.border = border

        # Body
        for r in ws.iter_rows(min_row=3):
            r[0].alignment = Alignment(horizontal="left")
            for c in r[1:]:
                c.alignment = Alignment(horizontal="right")
            for c in r:
                c.border = border

        # % format
        for c in ws["D"][2:]:
            c.number_format = '0.0"%"'

        # TOTAL row
        ws.append(["TOTAL", total_available, total_occupied, total_occ])
        last = ws.max_row
        for c in ws[last]:
            c.font = bold
            c.fill = total_fill
            c.border = border
            c.alignment = Alignment(horizontal="right")
        ws[f"A{last}"].alignment = Alignment(horizontal="left")
        ws[f"D{last}"].number_format = '0.0"%"'

        # ---------- BAR CHART (GIỮ KIỂU CŨ) ----------
        chart = BarChart()
        chart.title = "Monthly OCC (%)"
        chart.y_axis.title = "OCC %"
        chart.x_axis.title = "Month"

        data = Reference(ws, min_col=4, min_row=2, max_row=last - 1)
        cats = Reference(ws, min_col=1, min_row=3, max_row=last - 1)

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        ws.add_chart(chart, "F3")

        # ---------- NOTE ----------
        note_row = last + 2
        ws[f"A{note_row}"] = "OCC (%) = Rooms Occupied / Rooms Available × 100"
        ws[f"A{note_row}"].font = Font(italic=True)
        ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=4)

        # ---------- AUTO WIDTH (FIXED) ----------
        for i, col in enumerate(ws.columns, start=1):
            max_len = max(len(str(cell.value)) for cell in col if cell.value)
            ws.column_dimensions[get_column_letter(i)].width = max_len + 3

    return df

/services/room_service.py :
from pathlib import Path
from typing import List
from models.room import Room
from utils.date_utils import parse_date, is_overlap
from services import booking_service as booking_srv
from datetime import date
from utils.csv_io import read_csv

PATH = Path("data/room.csv")  # file trong data


def load_all() -> List[Room]:

    return [Room.from_csv_row(r) for r in read_csv(PATH)]

def find_by_id(room_id):
    # load danh sách và tìm ID phòng
    for r in load_all():
        if r.room_id == room_id:
            return r
    return None

def filter_rooms(room_name=None, room_type=None, min_capacity=None) -> List[Room]:

    rooms = load_all()
    results = []

    for r in rooms:
        if min_capacity is not None:
            if r.capacity < min_capacity:
                continue

        if room_type is not None:

            if r.room_type.lower() != room_type.lower():
                continue
        if room_name is not None:

            if r.room_name.lower() != room_name.lower():
                continue
        results.append(r)
    return results


def is_available(room_id: str, check_in: str, check_out: str) -> bool:

    rooms = load_all()
    new_start = parse_date(check_in)
    new_end = parse_date(check_out)

    if not new_start or not new_end:
        raise ValueError("Invalid check_in/check_out date")
    if new_start > new_end:
        raise ValueError("Check_in must be before check_out")
    if booking_srv is None:
        return True
    
    for b in booking_srv.load_all():
        if b.room_id != room_id:
            continue
        if is_overlap(check_in,check_out,b.check_in,b.check_out):
            return False
    return True

def get_room_status(room_id):
    
    today = date.today()
    for b in booking_srv.load_all():
        if b.room_id != room_id:
                continue
        if(b.status or "").lower() == "canceled":
            continue
        if b.check_in <= today < b.check_out:
            return "occupied"
    return "vacant"

def get_available_rooms(check_in,check_out):
    return [
        r for r in load_all() if is_available(r.room_id,check_in,check_out)
    ]

/utils/csv_io.py :
import csv 
from pathlib import Path
from typing import List,Dict

def read_csv(path: Path) -> List[Dict]:

    if not path.exists():
        return []
    
    with path.open("r",encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)
    
def write_csv(path: Path,rows: List[Dict],fieldnames: List[str]) -> None:

    path.parent.mkdir(parents = True,exist_ok= True)

    with path.open("w",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

/utils/date_utils.py :
from datetime import datetime, date, timedelta
from typing import Optional

def is_overlap(a_start, a_end, b_start, b_end) -> bool:
    
    a_start = parse_date(a_start)
    a_end   = parse_date(a_end)
    b_start = parse_date(b_start)
    b_end   = parse_date(b_end)

    if a_start is None or a_end is None or b_start is None or b_end is None:
        return False
    
    if a_start > a_end:
        return False
    
    if b_start > b_end:
        return False
    
    return (a_start < b_end) and (a_end > b_start)

def parse_date(s: Optional[str]) -> Optional[date]:

    if not s:
        return None
    if isinstance(s, date) and not isinstance(s, datetime):
        return s
    if isinstance(s, datetime):
        return s.date()
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None
    
def weekend_nights(check_in,check_out):

    start = parse_date(check_in)
    end = parse_date(check_out)

    if not start or not end:
        return 0
    if start > end:
        return 0
    
    weekend_count = 0
    current_day = start
    while current_day < end:
        if current_day.weekday() in [5,6]:
            weekend_count += 1
        current_day += timedelta(days=1)
    return weekend_count

def count_days(check_in,check_out):

    start = parse_date(check_in)
    end = parse_date(check_out)

    if not start or not end:
        return 0
    if start > end:
        return 0
    return (end - start).days 

/utils/pricing_utils.py :
from utils.date_utils import parse_date

def calculate_pricing(check_in,check_out,price_per_night) -> float:
    start = parse_date(check_in)
    end = parse_date(check_out)

    if not start or not end:
        raise ValueError("Invalid dates")
    if start > end:
        raise ValueError("Check_in must be before check_out")
    
    nights = (end - start).days
    return nights * price_per_night

/API_SPEC.md :
HOTEL BOOKING SYSTEM – API SPECIFICATION

Base URL: /api
Data format: JSON
Date format: YYYY-MM-DD (ISO 8601)
Currency: VND

======================================================================

ENDPOINT: GET /rooms

Purpose:
Retrieve list of rooms so users can view and select rooms.

Request:
Method: GET
URL: /api/rooms
Query Parameters (optional):
- room_type: string (single | double | suite)
- capacity: integer

Example:
GET /api/rooms?capacity=2

Response:
Status 200 OK
{
  "rooms": [
    {
      "room_id": "101",
      "room_name": "Deluxe Room",
      "room_type": "double",
      "capacity": 2,
      "price_per_night": 800000,
      "status": "available"
    }
  ]
}

Error:
Status 500 Internal Server Error
{
  "error": "Unable to fetch rooms"
}

======================================================================

ENDPOINT: POST /bookings

Purpose:
Create a new booking for a room.

Request:
Method: POST
URL: /api/bookings
Body (JSON):
{
  "room_id": "101",
  "customer_id": "1",
  "check_in": "2025-01-10",
  "check_out": "2025-01-12"
}

Business Rules:
- check_in must be before check_out
- room must exist and be available
- booking dates must not overlap existing bookings
- customer must exist

Response:
Status 201 Created
{
  "booking_id": "1",
  "room_id": "101",
  "customer_id": "1",
  "check_in": "2025-01-10",
  "check_out": "2025-01-12",
  "final_price": 1600000,
  "status": "confirmed",
  "payment_status": "unpaid",
  "created_at": "2025-01-01T10:00:00"
}

Errors:
Status 400 Bad Request
{
  "error": "Invalid booking dates"
}

Status 404 Not Found
{
  "error": "Room or Customer not found"
}

Status 409 Conflict
{
  "error": "Room is not available for the requested dates"
}

======================================================================

ENDPOINT: DELETE /bookings/{id}

Purpose:
Cancel an existing booking by booking ID.

Request:
Method: DELETE
URL: /api/bookings/{id}

Example:
DELETE /api/bookings/1

Response:
Status 200 OK
{
  "message": "Booking cancelled successfully"
}

Error:
Status 404 Not Found
{
  "error": "Booking not found"
}

Notes:
- Cancel only applies to bookings with status: pending or confirmed
- Canceled bookings are kept for history but marked as status = canceled

======================================================================

END OF API SPECIFICATION

======================================================================

import pandas as pd
from pathlib import Path
import calendar

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter


ROOM_FILE = Path("data/room.csv")
BOOKING_FILE = Path("data/booking.csv")
OUTPUT_FILE = Path("occupancy_report.xlsx")


def generate_occupancy_report(year: int, quarter: int | None = None):
    """
    year: required
    quarter: optional (1,2,3,4)
    """

    # ---------- LOAD DATA ----------
    rooms_df = pd.read_csv(ROOM_FILE)
    total_rooms = len(rooms_df)
    if total_rooms == 0:
        raise ValueError("No rooms found")

    bookings = pd.read_csv(BOOKING_FILE)
    bookings = bookings[bookings["status"].isin(["confirmed", "completed"])]
    bookings["check_in"] = pd.to_datetime(bookings["check_in"])
    bookings["check_out"] = pd.to_datetime(bookings["check_out"])

    # ---------- MONTH RANGE ----------
    if quarter:
        start_month = (quarter - 1) * 3 + 1
        months = range(start_month, start_month + 3)
        sheet_name = f"Q{quarter}_{year}"
        title_text = f"Occupancy Report – Q{quarter} / {year}"
    else:
        months = range(1, 13)
        sheet_name = str(year)
        title_text = f"Occupancy Report – Year {year}"

    rows = []

    # ---------- CALCULATION ----------
    for m in months:
        days = calendar.monthrange(year, m)[1]
        month_start = pd.Timestamp(year, m, 1)
        month_end = pd.Timestamp(year, m, days)

        occupied_nights = 0
        for _, b in bookings.iterrows():
            start = max(b["check_in"], month_start)
            end = min(b["check_out"], month_end)
            if start < end:
                occupied_nights += (end - start).days

        rooms_available = total_rooms * days
        occ = (occupied_nights / rooms_available * 100) if rooms_available else 0

        rows.append([
            calendar.month_name[m],
            rooms_available,
            occupied_nights,
            round(occ, 1),
        ])

    df = pd.DataFrame(
        rows,
        columns=["Month", "Rooms Available", "Rooms Occupied", "OCC %"]
    )

    # ---------- TOTAL ----------
    total_available = df["Rooms Available"].sum()
    total_occupied = df["Rooms Occupied"].sum()
    total_occ = round((total_occupied / total_available) * 100, 1)

    # ---------- EXPORT EXCEL ----------
    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="a" if OUTPUT_FILE.exists() else "w"
    ) as writer:

        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]

        # ===== STYLE =====
        bold = Font(bold=True)
        header_fill = PatternFill("solid", fgColor="D9D9D9")
        total_fill = PatternFill("solid", fgColor="E7F3FF")

        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Title
        ws.insert_rows(1)
        ws["A1"] = title_text
        ws["A1"].font = Font(bold=True, size=12)
        ws.merge_cells("A1:D1")

        # Header
        for c in ws[2]:
            c.font = bold
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center")
            c.border = border

        # Body
        for r in ws.iter_rows(min_row=3):
            r[0].alignment = Alignment(horizontal="left")
            for c in r[1:]:
                c.alignment = Alignment(horizontal="right")
            for c in r:
                c.border = border

        # % format
        for c in ws["D"][2:]:
            c.number_format = '0.0"%"'

        # TOTAL row
        ws.append(["TOTAL", total_available, total_occupied, total_occ])
        last = ws.max_row
        for c in ws[last]:
            c.font = bold
            c.fill = total_fill
            c.border = border
            c.alignment = Alignment(horizontal="right")
        ws[f"A{last}"].alignment = Alignment(horizontal="left")
        ws[f"D{last}"].number_format = '0.0"%"'

        # ---------- BAR CHART (GIỮ KIỂU CŨ) ----------
        chart = BarChart()
        chart.title = "Monthly OCC (%)"
        chart.y_axis.title = "OCC %"
        chart.x_axis.title = "Month"

        data = Reference(ws, min_col=4, min_row=2, max_row=last - 1)
        cats = Reference(ws, min_col=1, min_row=3, max_row=last - 1)

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        ws.add_chart(chart, "F3")

        # ---------- NOTE ----------
        note_row = last + 2
        ws[f"A{note_row}"] = "OCC (%) = Rooms Occupied / Rooms Available × 100"
        ws[f"A{note_row}"].font = Font(italic=True)
        ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=4)

        # ---------- AUTO WIDTH (FIXED) ----------
        for i, col in enumerate(ws.columns, start=1):
            max_len = max(len(str(cell.value)) for cell in col if cell.value)
            ws.column_dimensions[get_column_letter(i)].width = max_len + 3

    return df
