# routers/zalo.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os

# Lấy giá trị từ biến môi trường bằng cách sử dụng TÊN BIẾN
ZALO_APP_ID = os.environ.get("ZALO_APP_ID")
ZALO_APP_SECRET = os.environ.get("ZALO_APP_SECRET")

# Tạo một APIRouter để quản lý các endpoint liên quan đến Zalo
router = APIRouter()

# Định nghĩa Pydantic model để nhận dữ liệu từ frontend
class ZaloPhoneRequest(BaseModel):
    token: str
    access_token: str # Thêm access_token từ frontend

@router.post("/get-phone-number")
def get_phone_number_from_token(request_data: ZaloPhoneRequest):
    """
    Nhận token và access_token từ frontend, sau đó gửi yêu cầu đến Zalo API để lấy số điện thoại.
    """
    if not all([ZALO_APP_ID, ZALO_APP_SECRET]):
        raise HTTPException(
            status_code=500,
            detail="Missing Zalo API configuration. Please set ZALO_APP_ID and ZALO_APP_SECRET environment variables."
        )

    try:
        # Gửi yêu cầu đến Zalo API để đổi token lấy số điện thoại
        response = requests.get(
            "https://graph.zalo.me/v2.0/oa/phone_numbers",
            params={
                "access_token": request_data.access_token,
                "code": request_data.token,
            },
            headers={
                "secret_key": ZALO_APP_SECRET
            }
        )
        
        # Kiểm tra phản hồi từ Zalo API
        zalo_data = response.json()
        
        if response.status_code == 200 and "data" in zalo_data and "number" in zalo_data["data"]:
            phone_number = zalo_data["data"]["number"]
            # Trả về số điện thoại cho frontend
            return {"status": "success", "phone_number": phone_number}
        else:
            # Xử lý trường hợp Zalo API trả về lỗi
            print(f"Lỗi từ Zalo API: {zalo_data}")
            raise HTTPException(
                status_code=400,
                detail=f"Không thể lấy số điện thoại từ Zalo. Lỗi: {zalo_data.get('message', 'Không rõ')}"
            )
    except Exception as e:
        # Xử lý các lỗi khác (lỗi mạng, server,...)
        print(f"Lỗi trong quá trình xử lý: {e}")
        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi server nội bộ."
        )