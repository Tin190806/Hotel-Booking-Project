import streamlit as st
import streamlit.components.v1 as components
import datetime
import pandas as pd
import sys
import os
import traceback
import re
import urllib.parse

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
os.chdir(project_root)

# --- IMPORTS ---
try:
    from services import room_service, booking_service, customer_service, pricing_service, report_service
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

# --- CSS STYLING (MERGED UI + A5 PRINT SUPPORT) ---
st.markdown("""
<style>
    /* --- CSS Web Interface --- */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        padding-top: 20px;
    }
    .sidebar-card {
        background: white;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 16px;
        text-align: center;
    }
    .sidebar-avatar {
        width: 64px;
        margin-bottom: 10px;
    }
    .sidebar-title {
        font-size: 22px;
        font-weight: 700;
        margin: 0;
        color: #1e293b;
    }
    .sidebar-sub {
        font-size: 13px;
        color: #6b7280;
        margin-top: 4px;
    }
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e0e0e0;
        color: #31333F !important;
    }

    /* --- STEPPER --- */
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

    /* --- CẤU HÌNH IN A5 (QUAN TRỌNG) --- */
    @media print {
        @page {
            size: A5;       /* Khổ giấy A5 */
            margin: 0;      /* Bỏ lề mặc định của trình duyệt */
        }
        
        /* Ẩn toàn bộ giao diện web */
        body * {
            visibility: hidden;
        }
        
        /* Ẩn các thành phần thừa */
        header, footer, aside, .stApp > header {
            display: none !important;
        }

        /* Chỉ hiển thị vùng Hóa đơn */
        .invoice-container, .invoice-container * {
            visibility: visible;
        }

        /* Định vị Hóa đơn full trang A5 */
        .invoice-container {
            position: fixed;
            left: 0;
            top: 0;
            width: 148mm;   /* Chiều rộng chuẩn A5 */
            min-height: 210mm; /* Chiều cao chuẩn A5 */
            margin: 0 auto;
            padding: 10mm;  /* Lề trong an toàn */
            border: none !important;
            box-shadow: none !important;
            background-color: white;
            font-size: 11px; /* Font nhỏ hơn cho vừa khổ A5 */
        }
        
        /* Điều chỉnh font chữ khi in A5 cho cân đối */
        .inv-brand h1 { font-size: 18px !important; }
        .inv-title h2 { font-size: 22px !important; }
        .inv-table th, .inv-table td { padding: 4px !important; }
        .inv-footer { margin-top: 30px !important; }
        
        /* Ẩn nút In khi đang in */
        .no-print {
            display: none !important;
        }
    }

    /* --- Giao diện Hóa Đơn (Hiển thị trên Web) --- */
    .invoice-container {
        background: white;
        padding: 40px;
        margin: 20px auto;
        max-width: 600px; /* Hiển thị gọn hơn trên màn hình */
        border: 1px solid #ddd;
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
        font-family: 'Times New Roman', Times, serif; 
        color: #333;
    }
    
    .inv-header {
        display: flex;
        justify-content: space-between;
        border-bottom: 2px solid #b91c1c; 
        padding-bottom: 15px;
        margin-bottom: 15px;
    }
    
    .inv-brand h1 { margin: 0; color: #b91c1c; font-size: 22px; text-transform: uppercase; }
    .inv-brand p { margin: 2px 0; font-size: 12px; color: #555; }
    
    .inv-title { text-align: right; }
    .inv-title h2 { margin: 0; font-size: 28px; color: #333; }
    .inv-title p { margin: 5px 0; font-size: 12px; }

    .inv-info-grid {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .inv-col { width: 48%; }
    .inv-col h4 { margin: 0 0 5px 0; border-bottom: 1px solid #eee; padding-bottom: 3px; color: #b91c1c; font-size: 12px; text-transform: uppercase;}
    .inv-col p { margin: 3px 0; font-size: 12px; }
    
    /* Bảng chi tiết */
    .inv-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 12px; }
    .inv-table th { border: 1px solid #999; padding: 6px; background: #f3f4f6; text-align: center; font-weight: bold; }
    .inv-table td { border: 1px solid #999; padding: 6px; }
    .text-center { text-align: center; }
    .text-right { text-align: right; }
    
    /* Phần tổng tiền */
    .inv-summary { text-align: right; margin-bottom: 20px; font-size: 12px; }
    .inv-row { display: flex; justify-content: flex-end; margin-bottom: 4px; }
    .inv-label { width: 120px; font-weight: bold; color: #555; }
    .inv-value { width: 120px; font-weight: bold; font-size: 13px; }
    .total-final { color: #b91c1c; font-size: 15px; }

    .inv-footer {
        margin-top: 30px;
        display: flex;
        justify-content: space-between;
        text-align: center;
        font-style: italic;
        font-size: 12px;
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
    st.session_state.current_page = "📅 Đặt phòng mới"

def process_checkout(room_id):
    try:
        bookings = booking_service.get_bookings_for_room(room_id)
        active_booking = None
        for b in bookings:
            if b.status == 'confirmed':
                active_booking = b
                break
        if active_booking:
            booking_service.finalize_checkout(
                booking_id=active_booking.booking_id,
                actual_check_out=datetime.date.today(),
                notes="Early checkout via Console"
            )
            st.toast(f"Đã trả phòng {room_id} thành công!", icon="✅")
            st.rerun()
        else:
            st.error("Không tìm thấy đơn đặt phòng hợp lệ để check-out.")
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
             booking_result = booking_service.confirm_payment(booking_result.booking_id, deposit_amount)
             remain = booking_result.final_price - deposit_amount
             notes += f" | Đã cọc 50%: {deposit_amount:,.0f} VNĐ. Còn lại: {remain:,.0f} VNĐ."
             
        elif payment_type == 'paid':
             booking_result = booking_service.confirm_payment(booking_result.booking_id, booking_result.final_price)
             notes += " | Đã thanh toán đủ."
        else:
             notes += f" | Chưa thanh toán."

        if notes:
            booking_result.notes = notes.strip(" | ")
            booking_service.save_one(booking_result)
        
        keys_to_remove = ['selected_room_id', 'selected_room_name', 'selected_room_type', 'selected_room_price', 'temp_booking_data', 'c_id_input', 'c_name_input', 'c_phone_input', 'c_email_input', 'c_nation_input', 'c_note_input']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.booking_step = 1
        return booking_result

    except ValueError as ve:
        st.error(f"Lỗi logic: {ve}")
        return None
    except Exception as ex:
        st.error(f"Lỗi hệ thống: {ex}")
        traceback.print_exc()
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
        status_raw = room_service.get_room_status(r.room_id)
        status = "available" if status_raw == "vacant" else "occupied"
        
        current_customer = None
        current_checkout = None
        current_booking_id = None
        current_payment_status = None
        current_final_price = 0
        
        if status == 'occupied':
            try:
                bookings = booking_service.get_bookings_for_room(r.room_id)
                for b in bookings:
                    if b.status == 'confirmed':
                        cust = customer_service.find_by_id(b.customer_id)
                        if cust:
                            current_customer = f"{cust.name.title()} ({cust.phone})"
                        else:
                            current_customer = "Khách Vãng Lai"
                        current_checkout = b.check_out
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

# --- LOGIN SCREEN ---
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
        st.markdown(
            """
            <div class="sidebar-card">
                <img src="https://cdn-icons-png.flaticon.com/512/609/609803.png" class="sidebar-avatar">
                <p class="sidebar-title">Hotel APK</p>
                <p class="sidebar-sub">Hotel Management System</p>
            </div>
            """, unsafe_allow_html=True
        )
        
        st.divider()
        
        menu_options = ["🏠 Trang chủ", "🛏️ Danh sách phòng", "📅 Đặt phòng mới", "🔎 Tra cứu & Khách hàng", "📊 Báo cáo"]
        
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "🏠 Trang chủ"

        default_index = 0
        if st.session_state.current_page in menu_options:
            default_index = menu_options.index(st.session_state.current_page)
            
        selected_menu = st.radio("Điều hướng:", menu_options, index=default_index)
        
        if selected_menu != st.session_state.current_page:
            st.session_state.current_page = selected_menu
            st.rerun()
            
        menu = st.session_state.current_page
        
        st.divider()
        with st.expander("👤 Tài khoản", expanded=True):
            st.write("**Admin:** Đào (UI Dev)")
            if st.button("🚪 Đăng xuất", use_container_width=True): logout()
            st.markdown("---")
            if st.button("🗑️ Xóa sạch dữ liệu (Wipe)", help="Xóa hết Booking và Khách hàng để test lại từ đầu"):
                try:
                    bk_path = os.path.join(project_root, "data", "booking.csv")
                    cus_path = os.path.join(project_root, "data", "customer.csv")
                    
                    if os.path.exists(bk_path):
                        try:
                            f = open(bk_path, "a"); f.close()
                        except PermissionError:
                            st.error("❌ Vui lòng tắt file Excel booking.csv đang mở!"); st.stop()
                        with open(bk_path, "w", encoding="utf-8") as f:
                            f.write("booking_id,room_id,customer_id,check_in,check_out,actual_check_out,final_price,status,payment_status,notes,created_at,updated_at\n")
                    
                    if os.path.exists(cus_path):
                        try:
                            f = open(cus_path, "a"); f.close()
                        except PermissionError:
                            st.error("❌ Vui lòng tắt file Excel customer.csv đang mở!"); st.stop()
                        with open(cus_path, "w", encoding="utf-8") as f:
                            f.write("customer_id,name,email,phone,nationality,is_loyalty_member\n")

                    import importlib
                    importlib.reload(booking_service)
                    importlib.reload(customer_service)
                    importlib.reload(room_service)
                    importlib.reload(report_service)

                    st.cache_data.clear()
                    keys_to_clear = ["rooms", "booking_step", "temp_booking_data", "view_room_detail"]
                    for k in keys_to_clear:
                        if k in st.session_state:
                            del st.session_state[k]
                            
                    st.toast("Đã xóa sạch dữ liệu! Hệ thống sẵn sàng test.", icon="🧹")
                    st.rerun()
                except Exception as e: st.error(f"Lỗi khi xóa: {e}")
    
    if menu == "🏠 Trang chủ":
        st.title("Dashboard Tổng quan")
        
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #0068c9, #4fa3ff);
            padding: 25px;
            border-radius: 16px;
            color: white;
            margin-bottom: 25px;
        ">
            <h3 style="margin-bottom: 5px;">👋 Chào mừng bạn quay lại</h3>
            <p style="margin:0; opacity:0.9;">
                Tổng quan tình trạng khách sạn hôm nay và các thao tác nhanh
            </p>
        </div>
        """, unsafe_allow_html=True)

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
        st.subheader("🕒 Hoạt động gần đây")
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
                            "checkin": format_date_vn(b.check_in),
                            "room": b.room_id,
                            "customer": c_name.title(),
                            "status": b.status
                        })
                    
                    for row in reversed(activity_data):
                        status_color = "#22c55e" if row["status"].lower() == "confirmed" else "#64748b"
                        if row["status"].lower() == "canceled": status_color = "#ef4444"
                        
                        col_left, col_right = st.columns([4, 1])
                        with col_left:
                            st.markdown(f"**{row['customer']}**")
                            st.caption(f"🏨 Phòng {row['room']} • 📅 {row['checkin']}")
                        with col_right:
                            st.markdown(f"""
                            <div style="background:{status_color}; color:white; padding:4px 10px; border-radius:12px; font-size:12px; text-align:center;">
                                {row['status'].title()}
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("---")
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
                            st.write(f"📅 Trả dự kiến: {format_date_vn(room_detail['current_checkout'])}")
                            
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
                                if st.button("💰 Đóng tiền ngay"):
                                    st.session_state[f"show_pay_{room_detail['room_id']}"] = True
                                
                                if st.session_state.get(f"show_pay_{room_detail['room_id']}"):
                                    pm = st.radio("Hình thức:", ["Tiền mặt", "QR"], key=f"pm_{room_detail['room_id']}")
                                    
                                    if pm == "Tiền mặt":
                                        rec_pay = st.number_input("Khách đưa:", value=remain_val, step=10000.0, key=f"rec_pay_{room_detail['room_id']}")
                                        if rec_pay < remain_val:
                                            st.error("Tiền khách đưa chưa đủ!")
                                        else:
                                            st.success(f"Tiền thừa: {rec_pay - remain_val:,.0f}")
                                            if st.button("Xác nhận đóng tiền", type="primary"):
                                                booking_service.confirm_payment(room_detail['current_booking_id'], remain_val + paid_val)
                                                st.toast("Đã thanh toán đủ!", icon="🎉")
                                                del st.session_state[f"show_pay_{room_detail['room_id']}"]
                                                st.rerun()
                                    else:
                                        qr = f"https://img.vietqr.io/image/mbbank-277772323-compact.png?amount={remain_val}&addInfo=Tra not {room_detail['room_id']}&accountName=Dao Duc Khoi"
                                        st.image(qr, width=200)
                                        if st.button("Xác nhận đã chuyển khoản", type="primary"):
                                            booking_service.confirm_payment(room_detail['current_booking_id'], remain_val + paid_val)
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
                    st.caption(f"{room['name'].title()} ({room['room_type'].title()})")
                    st.write(f"**{room['price']:,} VNĐ**")
                with col_status:
                    if room["status"] == "available": st.success("Trống")
                    else: st.error("Có khách")
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
                    
                    default_type_idx = 0
                    if 'selected_room_type' in st.session_state:
                        pre_fill_type = st.session_state['selected_room_type'].title()
                        if pre_fill_type in available_types:
                            default_type_idx = available_types.index(pre_fill_type)
                    
                    selected_room_type = st.selectbox("Loại giường", available_types, index=default_type_idx, disabled=is_room_locked)

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
                            price_info = pricing_service.calculate_price_breakdown(check_in.isoformat(), check_out.isoformat(), current_price)
                            final_price = price_info['final_price']
                            
                            st.markdown("---")
                            st.write(f"Đơn giá: **{current_price:,.0f} VNĐ** x **{total_nights} đêm**")
                            st.write(f"= **{current_price * total_nights:,.0f} VNĐ**")
                            if price_info.get('weekend_surcharge', 0) > 0:
                                st.write(f"+ Phụ phí cuối tuần: :orange[{price_info['weekend_surcharge']:,.0f} VNĐ]")
                            st.markdown(f"### Tạm tính: :red[{int(final_price):,} VNĐ]")
                        except: st.error("Lỗi tính giá")
                    else: st.error("Ngày Check-out phải sau Check-in")

            with col_form:
                st.subheader("📝 Thông tin khách")
                
                def on_id_change():
                    cid = st.session_state.c_id_input
                    found_cust = customer_service.find_by_id(cid)
                    if found_cust:
                        st.session_state.c_name_input = found_cust.name
                        st.session_state.c_phone_input = found_cust.phone
                        st.session_state.c_email_input = found_cust.email
                        st.session_state.c_nation_input = found_cust.nationality
                        st.toast(f"Đã tìm thấy khách cũ: {found_cust.name}", icon="👋")

                temp_data = st.session_state.get('temp_booking_data', {})
                
                if "c_id_input" not in st.session_state: st.session_state.c_id_input = temp_data.get('customer_id', "")
                if "c_name_input" not in st.session_state: st.session_state.c_name_input = temp_data.get('customer_name', "")
                if "c_phone_input" not in st.session_state: st.session_state.c_phone_input = temp_data.get('phone', "")
                if "c_email_input" not in st.session_state: st.session_state.c_email_input = temp_data.get('email', "")
                if "c_nation_input" not in st.session_state: st.session_state.c_nation_input = temp_data.get('nationality', "Việt Nam")
                if "c_note_input" not in st.session_state: st.session_state.c_note_input = temp_data.get('notes', "")

                c_id = st.text_input("CCCD/CMND (*)", key="c_id_input", on_change=on_id_change)
                c_name = st.text_input("Họ tên (*)", key="c_name_input")
                c_phone = st.text_input("SĐT (*)", key="c_phone_input")
                c_email = st.text_input("Email", key="c_email_input")
                c_nation = st.text_input("Quốc tịch", key="c_nation_input")
                c_note = st.text_area("Ghi chú đặc biệt (Notes)", key="c_note_input")
                
                if st.button("Tiếp tục thanh toán ➡️", type="primary"):
                    if not c_name or not c_id or not c_phone:
                        st.error("Vui lòng điền đủ thông tin bắt buộc (*)")
                    elif total_nights <= 0:
                        st.error("Ngày đặt không hợp lệ")
                    else:
                        is_vip = False
                        found_cust = customer_service.find_by_id(c_id)
                        if found_cust and found_cust.is_loyalty_member:
                            is_vip = True
                        
                        real_price_info = pricing_service.calculate_price_breakdown(
                            check_in.isoformat(), 
                            check_out.isoformat(), 
                            current_price, 
                            is_vip
                        )
                        real_final_price = real_price_info['final_price']

                        booked_room_id = None
                        try:
                            avail_rooms = room_service.get_available_rooms(check_in.isoformat(), check_out.isoformat())
                        except: 
                            avail_rooms = []

                        if 'selected_room_id' in st.session_state:
                            curr_id = st.session_state['selected_room_id']
                            target_room = next((r for r in avail_rooms if str(r.room_id) == str(curr_id)), None)
                            
                            if target_room:
                                if target_room.room_name.lower() == selected_room_name.lower() and \
                                   target_room.room_type.lower() == selected_room_type.lower():
                                    booked_room_id = target_room.room_id

                        if not booked_room_id:
                            for r in avail_rooms:
                                if r.room_name.lower() == selected_room_name.lower() and \
                                   r.room_type.lower() == selected_room_type.lower():
                                    booked_room_id = r.room_id
                                    break
                        
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
                                "total_price": int(real_final_price),
                                "nights": total_nights,
                                "breakdown": real_price_info
                            }
                            st.session_state.booking_step = 2
                            st.rerun()
                        else: 
                            st.error(f"Xin lỗi, hết phòng loại {selected_room_name} - {selected_room_type} trong giai đoạn này!")

        elif step == 2:
            temp = st.session_state.get('temp_booking_data')
            if not temp:
                st.session_state.booking_step = 1
                st.rerun()

            with st.container(border=True):
                st.markdown(f"### 💳 Thanh toán cho phòng {temp['room_id']}")
                st.info(f"Khách: **{temp['customer_name']}** - Tổng tiền: **{temp['total_price']:,} VNĐ**")
                
                bd = temp.get('breakdown', {})
                if bd:
                    with st.expander("Chi tiết giá"):
                         st.write(f"- Tiền phòng ({bd['nights']} đêm): {bd['base_price']:,.0f} VNĐ")
                         st.write(f"- Phụ phí cuối tuần: {bd['weekend_surcharge']:,.0f} VNĐ")
                         st.write(f"- Giảm giá khách quen: {bd['loyalty_discount']:,.0f} VNĐ")

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

                allow_submit = True
                if amount_needed > 0:
                    st.write(f"Số tiền cần trả: **{amount_needed:,} VNĐ**")
                    pay_method = st.radio("Phương thức:", ["💵 Tiền mặt", "🏦 Chuyển khoản QR"])
                    if pay_method == "💵 Tiền mặt":
                        rec = st.number_input("Khách đưa:", value=amount_needed, step=10000)
                        if rec < amount_needed:
                            st.error("Tiền khách đưa chưa đủ!")
                            allow_submit = False
                        else:
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
                
                if allow_submit:
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
                 c_email = c_info.email if c_info else ""
                 
                 st.balloons()
                 st.success(f"Đã tạo Booking thành công! Mã đơn: **{bid}**")
                 
                 # --- 1. TÍNH TOÁN TIỀN CỌC/CÒN LẠI ---
                 total_val = float(b_info.final_price or 0)
                 paid_val = 0.0
                 remain_val = total_val
                 
                 status_text = "CHƯA THANH TOÁN"
                 
                 if b_info.payment_status == 'paid':
                     paid_val = total_val
                     remain_val = 0
                     status_text = "ĐÃ THANH TOÁN ĐỦ"
                 elif b_info.payment_status == 'deposit':
                     # Mặc định cọc 50% theo logic ở Step 2
                     paid_val = total_val * 0.5
                     remain_val = total_val - paid_val
                     status_text = "ĐÃ ĐẶT CỌC 50%"
                 
                 # --- 2. HTML HÓA ĐƠN CHUẨN A4 (Code lại CSS xịn) ---
                 invoice_html = f"""
                 <div class="invoice-container">
                    <div class="inv-header">
                        <div class="inv-brand">
                            <h1>KHÁCH SẠN HOTEL APK</h1>
                            <p>Địa chỉ: 02 Nguyễn Đình Chiểu, Nha Trang</p>
                            <p>Hotline: 0365.002.590 | Email: booking@hotelapk.com</p>
                        </div>
                        <div class="inv-title">
                            <h2>HÓA ĐƠN</h2>
                            <p>Số: <b>#{bid}</b></p>
                            <p>Ngày: {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
                        </div>
                    </div>

                    <div class="inv-info-grid">
                        <div class="inv-col">
                            <h4>THÔNG TIN KHÁCH HÀNG</h4>
                            <p><strong>Họ tên:</strong> {c_name}</p>
                            <p><strong>Điện thoại:</strong> {c_phone}</p>
                            <p><strong>Email:</strong> {c_email}</p>
                        </div>
                        <div class="inv-col">
                            <h4>THÔNG TIN ĐẶT PHÒNG</h4>
                            <p><strong>Phòng:</strong> {b_info.room_id}</p>
                            <p><strong>Check-in:</strong> {format_date_vn(b_info.check_in)}</p>
                            <p><strong>Check-out:</strong> {format_date_vn(b_info.check_out)}</p>
                        </div>
                    </div>

                    <table class="inv-table">
                        <thead>
                            <tr>
                                <th style="width: 50px;">STT</th>
                                <th>Nội dung thanh toán</th>
                                <th style="width: 80px;">SL</th>
                                <th>Đơn giá</th>
                                <th>Thành tiền</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="text-center">1</td>
                                <td>Tiền thuê phòng ({b_info.room_id})</td>
                                <td class="text-center">1</td>
                                <td class="text-right">{total_val:,.0f}</td>
                                <td class="text-right">{total_val:,.0f}</td>
                            </tr>
                        </tbody>
                    </table>

                    <div class="inv-summary">
                        <div class="inv-row">
                            <div class="inv-label">TỔNG CỘNG:</div>
                            <div class="inv-value">{total_val:,.0f} VNĐ</div>
                        </div>
                        <div class="inv-row">
                            <div class="inv-label">ĐÃ THANH TOÁN:</div>
                            <div class="inv-value" style="color: green;">{paid_val:,.0f} VNĐ</div>
                        </div>
                        <div class="inv-row">
                            <div class="inv-label">CÒN LẠI:</div>
                            <div class="inv-value total-final" style="color: #b91c1c;">{remain_val:,.0f} VNĐ</div>
                        </div>
                        <p style="margin-top: 10px; font-size: 13px;">(Trạng thái: {status_text})</p>
                    </div>

                    <div class="inv-footer">
                        <div>
                            <p><strong>Người lập phiếu</strong></p>
                            <br><br><br>
                            <p>(Ký, họ tên)</p>
                        </div>
                        <div>
                            <p><strong>Khách hàng</strong></p>
                            <br><br><br>
                            <p>(Ký, họ tên)</p>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 40px; font-size: 12px; color: #999;">
                        Cảm ơn quý khách đã sử dụng dịch vụ!
                    </div>
                 </div>
                 """
                 
                 st.markdown(invoice_html, unsafe_allow_html=True)
                 
                 # --- NÚT IN (JAVASCRIPT) ---
                 components.html(
                     """
                     <div style="text-align: center; margin-top: 20px;">
                        <button onclick="window.parent.print()" style="
                            background-color: #2563eb; 
                            color: white; 
                            padding: 12px 28px; 
                            border: none; 
                            border-radius: 6px; 
                            font-size: 16px; 
                            font-weight: bold; 
                            cursor: pointer; 
                            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                            transition: 0.3s;
                        ">
                            🖨️ IN HÓA ĐƠN NGAY
                        </button>
                     </div>
                     """,
                     height=100
                 )

             if st.button("Về trang chủ"):
                 navigate_to("🛏️ Danh sách phòng")

    elif menu == "🔎 Tra cứu & Khách hàng":
        st.title("Tra cứu khách hàng")
        kw = st.text_input("Nhập SĐT hoặc CCCD:")
        if kw:
            cust = customer_service.find_by_id(kw) or customer_service.find_by_phone(kw)
            if cust:
                st.success(f"Khách: {cust.name.title()} - {cust.nationality.title()}")
                st.write(f"**SĐT:** {cust.phone}")
                st.write(f"**Email:** {cust.email}")
                st.write(f"**CCCD:** {cust.customer_id}")
                
                all_bks = booking_service.load_all()
                completed_bks = [b for b in all_bks if str(b.customer_id) == str(cust.customer_id) and b.status == 'completed']
                total_spent = sum(float(b.final_price or 0) for b in completed_bks)
                
                vip_threshold = 10000000
                progress = min(total_spent / vip_threshold, 1.0)
                
                st.write(f"**Tổng chi tiêu (Đã hoàn thành):** {total_spent:,.0f} VNĐ")
                st.progress(progress)
                if total_spent < vip_threshold:
                    st.caption(f"Cần thêm {vip_threshold - total_spent:,.0f} VNĐ để lên hạng VIP")
                else:
                    st.success("🌟 Khách hàng VIP")

                with st.expander("📝 Cập nhật thông tin chi tiết", expanded=True):
                    with st.form("update_cust_full"):
                        c1, c2 = st.columns(2)
                        new_id = c1.text_input("CCCD/CMND (Không thể sửa)", value=cust.customer_id, disabled=True)
                        new_name = c2.text_input("Họ tên", value=cust.name)
                        c3, c4 = st.columns(2)
                        new_phone = c3.text_input("Số điện thoại", value=cust.phone)
                        new_email = c4.text_input("Email", value=cust.email)
                        new_nationality = st.text_input("Quốc tịch", value=cust.nationality)
                        new_loyalty = st.checkbox("Kích hoạt VIP (Thủ công)", value=cust.is_loyalty_member)
                        
                        if st.form_submit_button("💾 Lưu thay đổi", type="primary"):
                            customer_service.update_customer(
                                cust.customer_id,
                                name=new_name,
                                phone=new_phone,
                                email=new_email,
                                nationality=new_nationality,
                                is_loyalty_member=new_loyalty
                            )
                            st.toast("Đã cập nhật thông tin thành công!", icon="✅")
                            st.rerun()
                
                st.subheader("Lịch sử đặt phòng")
                if completed_bks:
                    hist_data = []
                    for b in completed_bks:
                        hist_data.append({
                            "Mã": b.booking_id,
                            "Phòng": b.room_id,
                            "Check-in": format_date_vn(b.check_in),
                            "Tổng tiền": f"{b.final_price:,.0f}"
                        })
                    st.dataframe(pd.DataFrame(hist_data), use_container_width=True)
                else:
                    st.info("Chưa có lịch sử hoàn thành.")
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
                    df_res = report_service.generate_occupancy_report(end_d.year)
                    st.dataframe(df_res, use_container_width=True)
                    with open("occupancy_report.xlsx", "rb") as f:
                        st.download_button(
                            label="📥 Tải xuống báo cáo (Excel)",
                            data=f,
                            file_name=f'Occupancy_Report_{end_d.year}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            type="primary"
                        )
                else:
                    st.info("Chưa có dữ liệu booking.")
        except Exception as e:
            st.error(f"Lỗi khi tạo báo cáo: {e}")

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: grey;'>© 2025 Hotel Booking Project - Team APK</div>", unsafe_allow_html=True)