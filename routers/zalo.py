from fastapi import APIRouter, HTTPException;

from pydantic import BaseModel;
import requests
import os


ZALO_APP_ID = os.environ.get("ZALO_APP_ID")
ZALO_APP_SECRET = os.environ.get("ZALO_APP_SECRET")


router = APIRouter()


class ZaloPhoneRequest(BaseModel):
    token: str  # token frontend gửi về sau khi gọi getPhoneNumber()
    access_token: str  # access_token của OA

@router.post("/get-phone-number")
def get_phone_number_from_token(request_data: ZaloPhoneRequest):

    if not all([ZALO_APP_ID, ZALO_APP_SECRET]):
        raise HTTPException(
            status_code=500,
            detail="Missing Zalo API configuration"
        )

    try:

        response = requests.get(
            "https://graph.zalo.me/v2.0/me/info",
            params={
                "access_token": request_data.access_token,
                "code": request_data.token,
            },
            headers={
                "secret_key": ZALO_APP_SECRET
            }
        )

        zalo_data = response.json()

        if response.status_code == 200 and "data" in zalo_data and "number" in zalo_data["data"]:
            return {"status": "success", "phone_number": zalo_data["data"]["number"]}
        else:
            
            raise HTTPException(
                status_code=response.status_code,
                detail=zalo_data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
