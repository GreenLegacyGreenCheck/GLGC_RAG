import os
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo import MongoClient, UpdateOne 
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
        return {
            "status": "empty",
            "message": "조건에 맞는 지원사업이 없습니다.", 
            "data": [],
            "default_actions": [ 
                {
                    "id": 1,
                    "title": "에너지 바우처 신청",
                    "description": "에너지 취약계층을 위한 전기, 도시가스, 지역난방 등의 요금 지원을 알아보세요.",
                    "url": "https://www.energyv.or.kr"
                },
                {
                    "id": 2,
                    "title": "정부24 보조금24 확인하기",
                    "description": "내가 받을 수 있는 국가보조금과 정부 혜택을 한 번에 조회하고 신청해 보세요.",
                    "url": "https://www.gov.kr/portal/rcvfvrSvc/main"
                },
                {
                    "id": 3,
                    "title": "복지로 맞춤형 복지 찾기",
                    "description": "대한민국 대표 복지포털에서 나의 상황에 맞는 맞춤형 복지 서비스를 검색해 보세요.",
                    "url": "https://www.bokjiro.go.kr"
                }
            ]
        }
        
    return {
        "status": "success",
        "user_cause": req.cause,
        "user_target": req.target,
        "total_count": len(results),
        "data": results
    }


class UpdateDataRequest(BaseModel):
    new_data: list 

# API 2: 데이터 업데이트
@app.post("/update-data")
def update_rag_data(req: UpdateDataRequest):
    if not req.new_data:
        return {"status": "error", "message": "받은 데이터가 없습니다."}

    #중복 제거 및 병합
    operations = []
    for item in req.new_data:
        op = UpdateOne(
            {"url": item["url"]},  
            {"$set": item},       
            upsert=True           
        )
        operations.append(op)
    
    # DB에  전송
    if operations:
        collection.bulk_write(operations)
    
    return {"status": "success", "message": f"MongoDB에 {len(req.new_data)}개의 데이터가 똑똑하게 병합(Upsert) 되었습니다!"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "서버가 살아있습니다!"}