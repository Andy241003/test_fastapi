from fastapi import FastAPI, APIRouter, HTTPException, Query
import requests
import os
from pydantic import BaseModel
from typing import List, Optional

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Booking API Proxy")

# Định nghĩa router cho các endpoint đặt phòng
router = APIRouter(prefix="/bookings", tags=["bookings"])

# Lấy các biến môi trường hoặc sử dụng giá trị mặc định
# Trong môi trường sản xuất, bạn nên cấu hình các biến này
WP_API_URL = os.getenv("WP_API_URL", "https://staytour.vtlink.link/wp-json/mphb/v1")
WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY", "ck_972eead1eeee1b8340185d63929a96058fa42757")
WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET", "cs_eb8b8e24af51ddd8e7fa793f9bf7279cff33c8bb")

# Ánh xạ tên phòng tới ID để dễ sử dụng
ROOM_TYPES_MAP = {
    "Economy Classic Room": 1943,
    "Triple Classic Room": 1189,
    "Business Class Room": 1190,
    "Royal Class Room": 1191,
    "Superior Ocean Room": 1192,
    "Classic Room": 1015,
    "Double Room": 1006,
    "Standard Room": 986,
    "Deluxe room": 3632
}

# --- SCHEMAS (Định nghĩa cấu trúc dữ liệu cho request và response) ---
class ReservedAccommodation(BaseModel):
    accommodation: int
    accommodation_type: int
    adults: int
    children: Optional[int] = 0
    guest_name: Optional[str] = None

class Customer(BaseModel):
    first_name: str
    last_name: str
    email: str

class BookingCreate(BaseModel):
    status: Optional[str] = "pending"
    check_in_date: str
    check_out_date: str
    reserved_accommodations: List[ReservedAccommodation]
    customer: Customer
    notes: Optional[str] = None

# --- ENDPOINTS (Đóng vai trò là proxy cho API WordPress) ---
@router.post("/", summary="Tạo đơn đặt phòng mới trên WordPress")
def create_booking(booking: BookingCreate):
    """
    Endpoint này nhận dữ liệu đặt phòng từ frontend và chuyển tiếp đến API WordPress.
    - Đảo ngược `first_name` và `last_name` của khách hàng.
    - Ghép thành `guest_name` cho mỗi phòng được đặt.
    """
    try:
        url = f"{WP_API_URL}/bookings"
        payload = booking.dict(exclude_none=True)

        # Đảo ngược tên
        swapped_first = booking.customer.last_name
        swapped_last = booking.customer.first_name

        payload["customer"]["first_name"] = swapped_first
        payload["customer"]["last_name"] = swapped_last

        # Cập nhật guest_name cho mỗi phòng
        full_name = f"{swapped_last} {swapped_first}"
        for ra in payload["reserved_accommodations"]:
            ra["guest_name"] = full_name

        print(f"Payload gửi tới WordPress: {payload}")

        response = requests.post(
            url,
            json=payload,
            auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET),
            timeout=20
        )
        if response.status_code not in (200, 201):
            print(f"Lỗi WP API {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", summary="Lấy danh sách các đơn đặt phòng từ WordPress")
def get_bookings(
    status: Optional[str] = Query(None, description="Lọc theo trạng thái đặt phòng"),
    page: int = Query(1, description="Số trang"),
    per_page: int = Query(10, description="Số mục trên mỗi trang")
):
    """
    Lấy danh sách các đơn đặt phòng với các tham số phân trang và lọc trạng thái.
    """
    try:
        url = f"{WP_API_URL}/bookings"
        params = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status

        response = requests.get(
            url,
            params=params,
            auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET),
            timeout=20
        )
        if response.status_code != 200:
            print(f"Lỗi WP API {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accommodation_types/", summary="Lấy danh sách các loại phòng")
def get_accommodation_types():
    """
    Lấy danh sách các loại phòng (accommodation types) từ WordPress API,
    chỉ bao gồm id, title, adults, và children.
    """
    try:
        url = f"{WP_API_URL}/accommodation_types"
        
        response = requests.get(
            url,
            auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET),
            timeout=20
        )

        if response.status_code != 200:
            print(f"Lỗi WP API {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())
        
        raw_data = response.json()

        filtered_data = []
        for item in raw_data:
            filtered_data.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "adults": item.get("adults", 0),
                "children": item.get("children", 0)
            })

        return filtered_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accommodations/", summary="Lấy danh sách các phòng nghỉ riêng lẻ")
def get_accommodations():
    """
    Endpoint mới để lấy danh sách tất cả các phòng nghỉ riêng lẻ từ API WordPress.
    """
    try:
        url = f"{WP_API_URL}/accommodations"
        
        response = requests.get(
            url,
            auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET),
            timeout=20
        )

        if response.status_code != 200:
            print(f"Lỗi WP API {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())

        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/availability/", summary="Kiểm tra phòng trống")
def get_room_availability(
    check_in_date: str = Query(..., description="Ngày nhận phòng (YYYY-MM-DD)"),
    check_out_date: str = Query(..., description="Ngày trả phòng (YYYY-MM-DD)"),
    accommodation_title: str = Query(..., description="Tiêu đề loại phòng"),
    adults: int = Query(1, description="Số người lớn"),
    children: Optional[int] = Query(0, description="Số trẻ em")
):
    """
    Lấy thông tin phòng trống từ WordPress API dựa trên ngày và tên loại phòng đã chọn.
    """
    try:
        # Lấy ID từ tên phòng
        accommodation_type = ROOM_TYPES_MAP.get(accommodation_title)
        if accommodation_type is None:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy loại phòng '{accommodation_title}'")

        # Xây dựng URL với các tham số từ query
        url = (
            f"{WP_API_URL}/bookings/availability/"
            f"?check_in_date={check_in_date}"
            f"&check_out_date={check_out_date}"
            f"&accommodation_type={accommodation_type}"
            f"&adults={adults}"
            f"&children={children}"
        )

        # Gửi yêu cầu GET tới API WordPress
        response = requests.get(
            url,
            auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET),
            timeout=20
        )

        # Xử lý lỗi nếu có
        if response.status_code != 200:
            print(f"Lỗi WP API {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())

        # Trả về toàn bộ dữ liệu JSON từ API
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Thêm router vào ứng dụng chính
app.include_router(router)

# Endpoint gốc để kiểm tra tình trạng hoạt động của backend
@app.get("/")
def read_root():
    return {"message": "Backend trung gian đang hoạt động!"}
