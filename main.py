from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Dict
import json 

# 1. Khai báo thông tin kết nối từ database của bạn
DB_HOST = "sql12.freesqldatabase.com"
DB_NAME = "sql12795417"
DB_USER = "sql12795417"
DB_PASS = "iw8ykWbXXe"

# 2. Tạo chuỗi kết nối (connection string)
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# 3. Tạo một engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# 4. Tạo một SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Tạo một Base class để định nghĩa các model (bảng)
Base = declarative_base()

# 6. Định nghĩa model cho bảng 'utility' (giữ lại từ trước)
class Utility(Base):
    __tablename__ = "utility"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255), index=True)
    images = Column(Text)
    title = Column(String(255))
    description = Column(Text)
    vr360_url = Column(String(255))
    video_url = Column(String(255))

# 7. Định nghĩa model mới cho bảng 'service'
class Service(Base):
    __tablename__ = "service"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    subtitle = Column(String(255))
    discount = Column(String(255))
    rating = Column(String(255))
    image = Column(Text)
    category = Column(String(255))
    description = Column(Text)

# 8. Hàm dependency để tạo và đóng session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 9. Tạo ứng dụng FastAPI
app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 10. Tự động tạo cả hai bảng 'utility' và 'service' nếu chưa tồn tại
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully or already exist.")
except Exception as e:
    print(f"Error creating database tables: {e}")

# 11. Endpoint cho bảng 'utility' (giữ lại từ trước)
@app.get("/utilities/")
def get_all_utilities(db: Session = Depends(get_db)):
    utilities = db.query(Utility).all()
    if not utilities:
        raise HTTPException(status_code=404, detail="Không có tiện ích nào được tìm thấy.")
    return utilities

@app.get("/utilities/")
def get_all_utilities(db: Session = Depends(get_db)):
    utilities = db.query(Utility).all()
    if not utilities:
        raise HTTPException(status_code=404, detail="Không có tiện ích nào được tìm thấy.")
    
    for utility in utilities:
        if utility.images:
            utility.images = json.loads(utility.images)
        else:
            utility.images = []
    return utilities

# 12. Các endpoint MỚI cho bảng 'service'
@app.get("/services/")
def get_all_services(db: Session = Depends(get_db)):
    """
    Lấy danh sách tất cả các dịch vụ từ database.
    """
    services = db.query(Service).all()
    if not services:
        raise HTTPException(status_code=404, detail="Không có dịch vụ nào được tìm thấy.")
    return services

@app.get("/services/{service_id}")
def get_service_by_id(service_id: int, db: Session = Depends(get_db)):
    """
    Lấy thông tin một dịch vụ cụ thể bằng ID.
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ.")
    return service

@app.get("/")
def home():
    return {"message": "Server FastAPI đang hoạt động!"}