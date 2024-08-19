from fastapi import FastAPI, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from pydantic import BaseModel, Field
from model_lib import recommend_songs
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from typing import Optional, List


app = FastAPI()


# MongoDB 연결 설정
MONGO_DETAILS = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.inside_out_dj
user_collection = database.get_collection("users")
playlist_collection = database.get_collection("playlists")


# Pydantic 모델 (데이터 검증)
class User(BaseModel):
    id: Optional[str]  # id 필드를 _id로 매핑
    username: str
    email: str
    hashed_password: str

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True  # ObjectId 타입의 필드를 허용

    @classmethod
    def from_mongo(cls, user: dict) -> "User":
        return cls(**user, id=str(user["_id"]))

    def to_mongo(self):
        user_dict = self.dict(by_alias=True)
        if 'id' in user_dict and user_dict['id'] is not None:
            user_dict['_id'] = user_dict['id']  # 전달된 id 값을 _id로 설정
            del user_dict['id']
        return user_dict

class Playlist(BaseModel):
    id: Optional[str] = Field(alias="_id")
    user_id: str
    playlist_name: str
    playlist_id: str
    emotion_analysis: dict
    recommended_songs: List[dict]

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}

# 사용자 생성
@app.post("/users/", response_model=User)
async def create_user(user: User):
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user_dict = user.to_mongo()
    new_user = await user_collection.insert_one(user_dict)
    created_user = await user_collection.find_one({"_id": new_user.inserted_id})
    return User.from_mongo(created_user)

# 모든 사용자 조회
@app.get("/users/", response_model=List[User])
async def get_users():
    users = await user_collection.find().to_list(1000)
    return users

# 이메일을 기반으로 사용자 존재 여부 확인
@app.get("/users/check_by_email/{email}")
async def check_user_exists_by_email(email: str):
    user = await user_collection.find_one({"email": email})
    if user:
        return {"exists": True}
    return {"exists": False}


# 특정 사용자 조회
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)


# 플레이리스트 생성
@app.post("/playlists/", response_model=Playlist)
async def create_playlist(playlist: Playlist):
    playlist_dict = playlist.dict(by_alias=True)
    new_playlist = await playlist_collection.insert_one(playlist_dict)
    created_playlist = await playlist_collection.find_one({"_id": new_playlist.inserted_id})
    return Playlist(**created_playlist)


# 특정 사용자의 모든 플레이리스트 조회
@app.get("/users/{user_id}/playlists/", response_model=List[Playlist])
async def get_user_playlists(user_id: str):
    playlists = await playlist_collection.find({"user_id": user_id}).to_list(1000)
    return playlists


# 특정 플레이리스트 조회
@app.get("/playlists/{playlist_id}", response_model=Playlist)
async def get_playlist(playlist_id: str):
    playlist = await playlist_collection.find_one({"_id": ObjectId(playlist_id)})
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return Playlist(**playlist)


# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 앱이 실행되는 도메인 (예: 포트 3000)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드를 허용
    allow_headers=["*"],  # 모든 헤더를 허용
)

@app.post("/generate_playlist")
def generate_playlist(diary: str = Body(..., example="오늘 하루는 정말 힘들었어...")):
    print(f"Received diary: {diary}")
    songs = recommend_songs(diary)  # 모델과 토크나이저를 사용하여 추천된 노래 목록 생성
    return {"recommended_songs": songs}

