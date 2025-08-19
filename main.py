from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Dict

# 1. Khai báo thông tin kết nối từ database của bạn
# Lưu ý: Trong môi trường thực tế, bạn nên lưu các thông tin này trong biến môi trường
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

# 6. Định nghĩa một model cho bảng 'utility'
# Sử dụng String(255) cho các trường chuỗi và Text() cho các chuỗi dài hơn
class Utility(Base):
    __tablename__ = "utility"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255), index=True)
    images = Column(Text)
    title = Column(String(255))
    description = Column(Text)
    vr360_url = Column(String(255))
    video_url = Column(String(255))

# 7. Hàm dependency để tạo và đóng session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 8. Tạo ứng dụng FastAPI
app = FastAPI()

# 9. Tự động tạo bảng 'utility' nếu chưa tồn tại
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully or already exist.")
except Exception as e:
    print(f"Error creating database tables: {e}")

# 10. Định nghĩa endpoint để lấy danh sách tất cả các tiện ích
@app.get("/utilities/")
def get_all_utilities(db: Session = Depends(get_db)):
    """
    Lấy danh sách tất cả các tiện ích từ database.
    """
    utilities = db.query(Utility).all()
    if not utilities:
        raise HTTPException(status_code=404, detail="Không có tiện ích nào được tìm thấy.")
    return utilities

# 11. Định nghĩa endpoint để lấy thông tin một tiện ích cụ thể theo ID
@app.get("/utilities/{utility_id}")
def get_utility_by_id(utility_id: int, db: Session = Depends(get_db)):
    """
    Lấy thông tin một tiện ích cụ thể bằng ID.
    """
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    if not utility:
        raise HTTPException(status_code=404, detail="Không tìm thấy tiện ích.")
    return utility

@app.get("/")
def home():
    return {"message": "Server FastAPI đang hoạt động!"}