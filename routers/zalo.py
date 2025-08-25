# routers/zalo.py

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import requests
from typing import Optional

# Zalo API credentials (nên lưu trong biến môi trường để bảo mật hơn)
# Vui lòng thay thế các giá trị này bằng thông tin Zalo OA của bạn
ZALO_OA_ACCESS_TOKEN = "H6Kr90B_Qp17PJiW2VLfFqTYFIy6xXD61XCnKmdU8ZqGEovi3gqD72DkM78EuKWw62j0TYZXT0OlS5WJDAfCV2LbGMChjcKfSIKmGM7t9bHp31eqOVT9QYKcVdXWwcugSY5VMc3GTZzE0o5f5E0U614g5NqbyJOT021f2n_7TNeU1dq98VmiR64I0dvOyXSVIG83K6RsCI177XGn0kWh83u49qGDuma72HCa4oV965ff1HGiQFuaIp830LaCzW4GA3u4PWpfLH4gA05LAheeGJ1i6IqK-3rEMXXi8axpFqfsC39QSxy4BZLw3Kaxdrj23d8BFJUy92CAVIjFE_8kAoKH9sLandKb8JPtIW2bVmeZQMmK8xb0In9kInyeXt9J26HuD3AYK70aOriW5FHnNWXYT1jbTw9c9WVfOJG" 
ZALO_APP_ID = "2618822866924995266"
ZALO_APP_SECRET = "cMl8B77MQ97Fd31fXBMJ"

# Tạo một APIRouter để quản lý các endpoint liên quan đến Zalo
router = APIRouter()

# Định nghĩa Pydantic model để nhận dữ liệu token từ frontend
class PhoneToken(BaseModel):
    token: str

@router.post("/get-phone-number")
def get_phone_number_from_token(phone_token: PhoneToken):
    """
    Nhận token số điện thoại từ frontend và gửi yêu cầu đến Zalo API để lấy số điện thoại thật.
    """
    if not all([ZALO_OA_ACCESS_TOKEN, ZALO_APP_ID, ZALO_APP_SECRET]):
        raise HTTPException(
            status_code=500,
            detail="Thiếu cấu hình Zalo API. Vui lòng thêm ZALO_OA_ACCESS_TOKEN, ZALO_APP_ID, ZALO_APP_SECRET."
        )

    try:
        # Gửi yêu cầu đến Zalo API để đổi token lấy số điện thoại
        response = requests.get(
            "https://graph.zalo.me/v2.0/oa/phone_numbers",
            params={
                "access_token": ZALO_OA_ACCESS_TOKEN,
                "code": phone_token.token,
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
                detail="Không thể lấy số điện thoại từ Zalo. Mã lỗi: " + str(zalo_data.get("error"))
            )
    except Exception as e:
        # Xử lý các lỗi khác (lỗi mạng, server,...)
        print(f"Lỗi trong quá trình xử lý: {e}")
        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi server nội bộ."
        )