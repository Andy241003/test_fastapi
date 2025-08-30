from fastapi import APIRouter, HTTPException
import requests
from typing import List, Dict, Any

# Import các biến cấu hình từ file config.py
from .config import WP_API_URL, WP_CONSUMER_KEY, WP_CONSUMER_SECRET

# Định nghĩa router cho các endpoint phòng nghỉ
router = APIRouter(tags=["accommodations"])

def _process_accommodation_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hàm helper để xử lý và tinh gọn dữ liệu từ một phòng nghỉ.
    """
    # Lấy thông tin chính từ đối tượng phòng nghỉ
    accommodation_id = raw_data.get("id")
    title = raw_data.get("title", "")
    status = raw_data.get("status", "")

    # Lấy thông tin chi tiết từ trường "_embedded"
    embedded_data = raw_data.get("_embedded", {})
    accommodation_type_list = embedded_data.get("accommodation_type_id", [])

    # Xử lý trường hợp không có dữ liệu loại phòng nhúng
    if not accommodation_type_list:
        return {
            "id": accommodation_id,
            "status": status,
            "title": title,
            "accommodation_type": None
        }

    # Lấy đối tượng loại phòng đầu tiên
    room_type_data = accommodation_type_list[0]
    
    # Trích xuất các trường cần thiết từ loại phòng
    room_type_id = room_type_data.get("id")
    room_type_title = room_type_data.get("title", "")
    adults = room_type_data.get("adults")
    children = room_type_data.get("children")
    size_sqft = room_type_data.get("size")
    prices_start_at = room_type_data.get("price", {}).get("regular_price_label", "Giá chưa xác định")
    
    # Xử lý danh sách tiện nghi và dịch vụ
    amenities = [item.get("title", "") for item in room_type_data.get("amenities", [])]
    services = [item.get("title", "") for item in room_type_data.get("services", [])]

    # Trích xuất các URL hình ảnh
    images = [item.get("src", "") for item in room_type_data.get("images", [])]

    # Xây dựng cấu trúc JSON mới, gọn gàng hơn
    return {
        "id": accommodation_id,
        "status": status,
        "title": title,
        "accommodation_type": {
            "id": room_type_id,
            "title": room_type_title,
            "details": {
                "adults": adults,
                "children": children,
                "size_sqft": size_sqft,
                "prices_start_at": prices_start_at
            },
            "images": images,
            "amenities": amenities,
            "services": services
        }
    }

@router.get("/accommodations/", summary="Lấy danh sách các phòng nghỉ riêng lẻ")
def get_accommodations():
    """
    Lấy danh sách tất cả các phòng nghỉ riêng lẻ từ API WordPress, với các tham số
    _embed và per_page=100.
    """
    try:
        url = f"{WP_API_URL}/accommodations?_embed&per_page=100"
        
        response = requests.get(
            url,
            auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET),
            timeout=20
        )

        if response.status_code != 200:
            print(f"Lỗi WP API {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())

        raw_accommodations = response.json()
        
        # Áp dụng hàm xử lý cho từng đối tượng phòng nghỉ và trả về kết quả
        processed_accommodations = [
            _process_accommodation_data(item) for item in raw_accommodations
        ]

        return processed_accommodations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
