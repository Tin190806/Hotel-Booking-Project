import services.report_service as report_svc
import services.room_service as room_svc
import services.booking_service as booking_svc


def run_test():
    print("=" * 60)
    print("BẮT ĐẦU KIỂM THỬ CHỨC NĂNG BÁO CÁO DOANH THU")
    print("=" * 60)

    # TEST 1: Tải dữ liệu phòng
    print("\n[TEST 1] Tải dữ liệu phòng")
    rooms = room_svc.load_all()
    print(f"✔ Số phòng tải được: {len(rooms)}")

    # TEST 2: Tải dữ liệu booking
    print("\n[TEST 2] Tải dữ liệu booking")
    bookings = booking_svc.load_all()
    print(f"✔ Số booking tải được: {len(bookings)}")

    if not rooms or not bookings:
        print("✘ LỖI: Không có dữ liệu để kiểm thử")
        print(">>> KẾT LUẬN: KIỂM THỬ THẤT BẠI")
        return

    # TEST 3: Tính toán báo cáo theo năm
    target_year = 2026
    print(f"\n[TEST 3] Tính toán báo cáo doanh thu năm {target_year}")

    df = report_svc.calculate_monthly_stats(
        rooms,
        bookings,
        year=target_year
    )

    if df is None or df.empty:
        print("✘ LỖI: Không tạo được bảng thống kê")
        print(">>> KẾT LUẬN: KIỂM THỬ THẤT BẠI")
        return

    print("✔ Bảng thống kê được tạo thành công:")
    print(df)

    # TEST 4: Xuất báo cáo Excel
    print("\n[TEST 4] Xuất báo cáo Excel")
    file_name = f"data/Bao_Cao_Hoan_Chinh_{target_year}.xlsx"
    report_svc.export_to_excel(df, file_name, target_year)
    print(f"✔ File Excel đã được tạo: {file_name}")

    # Mở file Excel (Windows)
    try:
        import os
        os.startfile(file_name)
    except:
        pass

    # KẾT LUẬN
    print("\n" + "=" * 60)
    print(">>> KẾT LUẬN: TẤT CẢ CÁC BƯỚC KIỂM THỬ ĐỀU THÀNH CÔNG")
    print("=" * 60)


if __name__ == "__main__":
    run_test()
