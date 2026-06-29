import os
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()

MONGO_URL = os.environ.get("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["glgc_database"] 
collection = db["policies"]  

# --- API 엔드포인트 ---
class RecommendRequest(BaseModel):
    cause: str
    target: str

# 정책 추천 창구 
@app.post("/recommend")
def recommend_policy(req: RecommendRequest):
    query = {
        "cause": req.cause,
        "target": {"$regex": req.target} 
    }
    
    # DB에서 찾은 결과를 리스트로 변환 (
    results = list(collection.find(query, {"_id": 0})) 
    
    if not results:
        return {"status": "empty", "message": "조건에 맞는 지원사업이 없습니다.", "data": []}
        
    return {
        "status": "success",
        "user_cause": req.cause,
        "user_target": req.target,
        "total_count": len(results),
        "data": results
    }


class UpdateDataRequest(BaseModel):
    new_data: list 

# 데이터 업데이트
@app.post("/update-data")
def update_rag_data(req: UpdateDataRequest):
    if not req.new_data:
        return {"status": "error", "message": "받은 데이터가 없습니다."}

    # 기존 DB 데이터 지우기
    collection.delete_many({})
    
    # 백엔드가 준 새 데이터 DB에 저장
    collection.insert_many(req.new_data)
    
    return {"status": "success", "message": f"MongoDB에 {len(req.new_data)}개의 데이터가 안전하게 업데이트 되었습니다!"}


# 서버 상태 확인용
@app.get("/")
def read_root():
    return {"message": "RAG API Server with MongoDB is running!"}