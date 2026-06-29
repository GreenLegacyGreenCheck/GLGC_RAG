from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

app = FastAPI()

# 1. 베이스 데이터 로드
try:
    df = pd.read_csv('ragbase.csv', encoding='cp949')
except FileNotFoundError:
    df = pd.DataFrame() 

# 2. 추천 데이터 추출 함수 
def get_recommendation_data(cause: str, target: str) -> dict:
    filtered_df = df[(df['cause'] == cause) & (df['target'].str.contains(target))]
    
    if filtered_df.empty:
        return {
            "status": "empty",
            "message": "현재 조건에 딱 맞는 지원사업이 없습니다.",
            "data": []
        }
    
    business_list = []
    for _, row in filtered_df.iterrows():
        business = {
            "title": row['name'],
            "action_title": row['action_name'],
            "description": row['action_des'],
            "benefit": row['takes'],
            "documents": row['need'],
            "link": row['url'],
            "difficulty": row['level'],
            "carbon_saving": row['saving'] 
        }
        business_list.append(business)
        
    return {
        "status": "success",
        "user_cause": cause,
        "user_target": target,
        "total_count": len(business_list),
        "data": business_list
    }


# API 엔드포인트
# 추천을 요청할 때 보낼 데이터 형식
class RecommendRequest(BaseModel):
    cause: str
    target: str

# API 1: Nest.js가 유저의 조건을 보내면 추천 결과를 리턴해주는 API
@app.post("/recommend")
def recommend_policy(req: RecommendRequest):
    return get_recommendation_data(req.cause, req.target)


# API 2: 백엔드에서 크롤링->LLM 가공이 끝난 새 데이터를 RAG 서버로 쏴줄 때 쓸 API
class UpdateDataRequest(BaseModel):
    new_data: list 
    
@app.post("/update-data")
def update_rag_data(req: UpdateDataRequest):
    global df
    # 받은 데이터를 데이터프레임으로 변환
    new_df = pd.DataFrame(req.new_data)
    
    # 데이터 붙이기,중복 제거
    updated_df = pd.concat([df, new_df], ignore_index=True).drop_duplicates(['name'])
    
    # 저장
    updated_df.to_csv('ragbase.csv', index=False, encoding='cp949')
    
    # 최신화
    df = updated_df 
    
    return {"status": "success", "message": f"기존 데이터에 성공적으로 합쳐졌습니다. 현재 총 {len(df)}개"}

# 서버 상태 확인용
@app.get("/")
def read_root():
    return {"message": "RAG API Server is running!"}