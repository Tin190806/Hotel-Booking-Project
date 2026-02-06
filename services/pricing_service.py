from utils.date_utils import count_days,weekend_nights


loyalty_rate = 0.05
weekend_rate = 0.2
"""
pricing_service xử lý các nghiệp vụ liên quan tới tính giá booking
"""
def calculate_booking_price(
        check_in:str,
        check_out:str,
        price_per_night:float,
        is_loyalty_member = False,
    ) -> float:
    """
        Tính giá booking dựa trên:
        - Số đêm
        - Phụ thu cuối tuần
        - Giảm giá VIP cho khách hàng thân thiết
    """
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
    """
    Áp dụng giảm giá VIP cho khách hàng thân thiết
    """
    return base_price - (base_price * loyalty_rate)


def calculate_price_breakdown(
        check_in:str,
        check_out:str,
        price_per_night:float,
        is_loyalty_member = False,

) -> dict:
    """
    Báo cáo thành phần của giá booking
    """
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

