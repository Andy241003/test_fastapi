from fastapi import APIRouter, HTTPException, Query
import requests, os
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/bookings", tags=["bookings"])

WP_API_URL = os.getenv("WP_API_URL", "https://staytour.vtlink.link/wp-json/mphb/v1")
WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY", "ck_972eead1eeee1b8340185d63929a96058fa42757")
WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET", "cs_eb8b8e24af51ddd8e7fa793f9bf7279cff33c8bb")

# ---------- SCHEMAS ----------
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

# ---------- ROUTES ----------
@router.post("/", summary="Create new booking")
def create_booking(booking: BookingCreate):
    try:
        url = f"{WP_API_URL}/bookings"
        payload = booking.dict(exclude_none=True)

        # ⚡ Đảo ngược tên: first_name ⇄ last_name
        swapped_first = booking.customer.last_name
        swapped_last = booking.customer.first_name

        payload["customer"]["first_name"] = swapped_first
        payload["customer"]["last_name"] = swapped_last

        # ⚡ Ghép guest_name = "last_name first_name" (sau khi đã đảo)
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


@router.get("/", summary="Get list of bookings")
def get_bookings(
    status: Optional[str] = Query(None, description="Filter by booking status"),
    page: int = Query(1, description="Page number"),
    per_page: int = Query(10, description="Items per page")
):
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


@router.get("/accommodation_types/", summary="Get list of accommodation types with selected details")
def get_accommodation_types():
    """
    Lấy danh sách các loại phòng (accommodation types) từ WordPress API,
    chỉ bao gồm id, title, adults, và children.
    """
    try:
        url = f"{WP_API_URL}/accommodation_types"
        
        # Gửi yêu cầu GET tới API WordPress với xác thực
        response = requests.get(
            url,
            auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET),
            timeout=20
        )

        # Xử lý lỗi nếu API không trả về 200 OK
        if response.status_code != 200:
            print(f"Lỗi WP API {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())
        
        # Lấy dữ liệu JSON từ phản hồi
        raw_data = response.json()

        # Lọc dữ liệu để chỉ giữ lại các trường mong muốn
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
        # Xử lý các lỗi khác như lỗi kết nối, lỗi phân tích cú pháp JSON, ...
        raise HTTPException(status_code=500, detail=str(e))
