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
    try:
        # Thêm kiểm tra an toàn để đảm bảo raw_data là một dictionary
        if not isinstance(raw_data, dict):
            print(f"Lỗi: Dữ liệu phòng nghỉ không phải là dictionary: {raw_data}")
            return None

        # Lấy thông tin chính từ đối tượng phòng nghỉ
        accommodation_id = raw_data.get("id")
        title = raw_data.get("title", "")
        status = raw_data.get("status", "")

        # Lấy thông tin chi tiết từ trường "_embedded"
        embedded_data = raw_data.get("_embedded", {})
        accommodation_type_list = embedded_data.get("accommodation_type_id", [])

        # Lấy đối tượng loại phòng đầu tiên và kiểm tra an toàn
        room_type_data = None
        if isinstance(accommodation_type_list, list) and accommodation_type_list:
            room_type_data = accommodation_type_list[0]
        elif raw_data.get("accommodation_type_id"):
            # Nếu không có dữ liệu nhúng, lấy ID từ cấp cao nhất và tạo URL để lấy dữ liệu
            room_type_id = raw_data.get("accommodation_type_id")
            try:
                room_type_url = f"{WP_API_URL}/accommodation_types/{room_type_id}"
                room_type_response = requests.get(room_type_url, auth=(WP_CONSUMER_KEY, WP_CONSUMER_SECRET), timeout=10)
                if room_type_response.status_code == 200:
                    room_type_data = room_type_response.json()
                else:
                    print(f"Lỗi khi lấy dữ liệu loại phòng {room_type_id}: {room_type_response.text}")
            except Exception as e:
                print(f"Lỗi kết nối khi lấy dữ liệu loại phòng {room_type_id}: {e}")

        # Xử lý trường hợp không có dữ liệu loại phòng
        if not room_type_data or not isinstance(room_type_data, dict):
            return {
                "id": accommodation_id,
                "status": status,
                "title": title,
                "accommodation_type": None
            }
        
        # Trích xuất các trường cần thiết từ loại phòng
        room_type_id = room_type_data.get("id")
        room_type_title = room_type_data.get("title", "")
        adults = room_type_data.get("adults")
        children = room_type_data.get("children")
        size_sqft = room_type_data.get("size")
        prices_start_at = room_type_data.get("price", {}).get("regular_price_label", "Giá chưa xác định")
        
        # Lấy thêm thông tin mô tả ngắn
        excerpt = raw_data.get("excerpt", "")

        # Xử lý danh sách tiện nghi và dịch vụ
        amenities = [item.get("title", "") for item in room_type_data.get("amenities", []) if isinstance(item, dict)]
        services = [item.get("title", "") for item in room_type_data.get("services", []) if isinstance(item, dict)]

        # Trích xuất các URL hình ảnh
        images = [item.get("src", "") for item in room_type_data.get("images", []) if isinstance(item, dict)]

        # Xây dựng cấu trúc JSON mới, gọn gàng hơn
        return {
            "id": accommodation_id,
            "status": status,
            "title": title,
            "accommodation_type": {
                "id": room_type_id,
                "title": room_type_title,
                "summary": excerpt,
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
    except Exception as e:
        print(f"Lỗi khi xử lý dữ liệu phòng nghỉ: {e}, dữ liệu gốc: {raw_data}")
        return None

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
            raise HTTPException(status_code=response.status_code, detail={"message": response.text})

        try:
            raw_accommodations = response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(f"Lỗi: Phản hồi từ WordPress không phải JSON. Nội dung thô: {response.text}")
            raise HTTPException(
                status_code=500,
                detail={"message": f"Lỗi khi giải mã phản hồi JSON từ WordPress API: {e}. Nội dung phản hồi có thể không phải JSON."}
            )
        
        # Xử lý trường hợp phản hồi là một dictionary thay vì một list
        if isinstance(raw_accommodations, dict):
            raw_accommodations = [raw_accommodations]
        
        # Thêm kiểm tra an toàn mới để đảm bảo phản hồi là một danh sách
        if not isinstance(raw_accommodations, list):
            raise HTTPException(
                status_code=500,
                detail={"message": "Phản hồi từ WordPress API không phải là một danh sách hợp lệ."}
            )
        
        # Lọc bỏ các mục không phải dictionary trước khi xử lý
        valid_accommodations = [item for item in raw_accommodations if isinstance(item, dict)]

        # Áp dụng hàm xử lý cho từng đối tượng phòng nghỉ và lọc bỏ các giá trị None
        processed_accommodations = [
            _process_accommodation_data(item) for item in valid_accommodations
        ]
        
        # Lọc bỏ các mục None nếu có (do lỗi dữ liệu)
        return [item for item in processed_accommodations if item is not None]
    
    except requests.exceptions.JSONDecodeError as e:
        # Xử lý trường hợp phản hồi không phải JSON
        raise HTTPException(
            status_code=500,
            detail={"message": f"Lỗi khi giải mã phản hồi JSON từ WordPress API: {e}"}
        )
    except Exception as e:
        # Xử lý các lỗi khác
        raise HTTPException(status_code=500, detail={"message": str(e)})
