# routers/zalo.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ValidationError
import requests
import os
import json
from typing import Dict

ZALO_APP_ID = os.environ.get("ZALO_APP_ID")
ZALO_APP_SECRET = os.environ.get("ZALO_APP_SECRET")


router = APIRouter()


class ZaloPhoneRequest(BaseModel):
    token: str           # token frontend gửi về sau khi gọi getPhoneNumber()
    access_token: str    # access_token từ OA SDK (frontend lấy bằng getAccessToken)

@router.post("/get-phone-number")
async def get_phone_number_from_token(request: Request):
    """
    Nhận token từ frontend, validate, gọi Zalo Graph API để đổi token -> số điện thoại.
    """
    # 1) đọc raw body và log (giúp debug 422)
    try:
        body = await request.json()
    except Exception as e:
        # không phải JSON
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {str(e)}")

    print("📩 /api/get-phone-number raw body:", body)

    # 2) kiểm tra env
    if not all([ZALO_APP_ID, ZALO_APP_SECRET]):
        raise HTTPException(status_code=500, detail="Missing Zalo API configuration (ZALO_APP_ID/ZALO_APP_SECRET)")

    # 3) validate body với Pydantic (nếu sai sẽ trả 422 với detail rõ ràng)
    try:
        req = ZaloPhoneRequest(**body)
    except ValidationError as ve:
        # in ra log để dev dễ debug
        print("⚠️ Validation error:", ve.json())
        # trả về 422 với chi tiết validation
        # (FastAPI mặc định làm điều này nếu dùng model param; ở đây ta custom để log)
        raise HTTPException(status_code=422, detail=json.loads(ve.json()))

    token = req.token
    access_token = req.access_token

    # 4) gọi Zalo Graph API để đổi token -> phone number
    endpoint = "https://graph.zalo.me/v2.0/me/info"
    headers: Dict[str, str] = {
        # Theo docs Zalo: gửi access_token, code, secret_key trong header
        "access_token": access_token,
        "code": token,
        "secret_key": ZALO_APP_SECRET,
    }

    try:
        resp = requests.get(endpoint, headers=headers, timeout=10)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error calling Zalo Graph API: {str(e)}")

    try:
        resp_json = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"Zalo response not JSON (status {resp.status_code})")

    print("🔁 Zalo Graph API response:", resp.status_code, resp_json)

    # 5) xử lý response
    # theo docs: trả về {"data": {"number": "849..."}, "error": 0, ...}
    if resp.status_code == 200 and isinstance(resp_json, dict):
        data = resp_json.get("data", {})
        if isinstance(data, dict) and "number" in data:
            phone_number = data["number"]
            return {"status": "success", "phone_number": phone_number}
        # nếu lỗi do Zalo (vd: code expired), trả nguyên body
        raise HTTPException(status_code=400, detail={"zalo": resp_json})
    else:
        # chuyển lỗi Zalo về client để debug
        raise HTTPException(status_code=resp.status_code or 502, detail=resp_json)
