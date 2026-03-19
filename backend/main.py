from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI()

# ===============================
# اتصال قاعدة البيانات عبر MongoDB Atlas
# ===============================
MONGO_URI = "mongodb+srv://hawraawaleed33_db_user:VyTQdtnppS9lT0RK@cluster0.jeyjiot.mongodb.net/developers_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client.get_database()

developers_collection = db["developers"]
follows_collection = db["follows"]
projects_collection = db["projects"]
videos_collection = db["videos"]
shorts_collection = db["shorts"]

# ===============================
# Pydantic Models
# ===============================
class Developer(BaseModel):
    name: str
    skill: str
    bio: str
    avatar: str = ""
    job: str = ""
    location: str = ""
    experience: str = ""
    technologies: str = ""
    portfolio: str = ""

class Follow(BaseModel):
    follower: str
    following: str
    status: str = "pending"

class Project(BaseModel):
    developer_id: str
    title: str
    description: str
    url: str

class Video(BaseModel):
    developer_id: str
    title: str
    url: str  # اسم ملف الفيديو فقط مثل hm6.mp4

class Short(BaseModel):
    developer_id: str
    title: str
    url: str

# ===============================
# Serve local videos from "videos" folder
# ===============================
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# ===============================
# Base URL للفيديوهات
# ===============================
URL_BASE = "https://m-9ha7.onrender.com"  # هذا الرابط رح يعطيه Render بعد ما يرفع المشروع

# ===============================
# Developers APIs
# ===============================
@app.post("/developers")
def add_developer(dev: Developer):
    developers_collection.insert_one(dev.dict())
    return {"message": "Developer added successfully"}

@app.get("/developers")
def get_developers():
    developers = developers_collection.find()
    result = []
    for dev in developers:
        followers_count = follows_collection.count_documents({
            "following": str(dev["_id"]),
            "status": "accepted"
        })
        result.append({
            "id": str(dev["_id"]),
            "name": dev["name"],
            "skill": dev["skill"],
            "bio": dev["bio"],
            "avatar": dev.get("avatar", ""),
            "followers_count": followers_count
        })
    return result

@app.get("/developers/search")
def search_developer(q: str):
    developers = developers_collection.find({
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"skill": {"$regex": q, "$options": "i"}}
        ]
    })
    result = []
    for dev in developers:
        followers_count = follows_collection.count_documents({
            "following": str(dev["_id"]),
            "status": "accepted"
        })
        result.append({
            "id": str(dev["_id"]),
            "name": dev["name"],
            "skill": dev["skill"],
            "bio": dev["bio"],
            "avatar": dev.get("avatar", ""),
            "followers_count": followers_count
        })
    return result

@app.get("/developers/{developer_id}")
def get_developer_by_id(developer_id: str):
    dev = developers_collection.find_one({"_id": ObjectId(developer_id)})
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")
    followers_count = follows_collection.count_documents({
        "following": developer_id,
        "status": "accepted"
    })
    return {
        "id": str(dev["_id"]),
        "name": dev["name"],
        "job": dev.get("job", ""),
        "location": dev.get("location", ""),
        "experience": dev.get("experience", ""),
        "skills": dev.get("skill", ""),
        "technologies": dev.get("technologies", ""),
        "portfolio": dev.get("portfolio", ""),
        "bio": dev.get("bio", ""),
        "avatar": dev.get("avatar", ""),
        "followers_count": followers_count
    }

# ===============================
# Projects APIs
# ===============================
@app.post("/projects")
def add_project(project: Project):
    projects_collection.insert_one(project.dict())
    return {"message": "Project added"}

@app.get("/developers/{developer_id}/projects")
def get_developer_projects(developer_id: str):
    projects = list(projects_collection.find({"developer_id": developer_id}))
    return [
        {
            "id": str(p["_id"]),
            "title": p["title"],
            "description": p["description"],
            "url": p["url"]
        } for p in projects
    ]

# ===============================
# Videos APIs
# ===============================
@app.post("/videos")
def add_video(video: Video):
    videos_collection.insert_one(video.dict())
    return {"message": "Video added"}

@app.get("/developers/{developer_id}/videos")
def get_developer_videos(developer_id: str):
    videos = list(videos_collection.find({"developer_id": developer_id}))
    return [
        {
            "id": str(v["_id"]),
            "title": v["title"],
            "url": f"{URL_BASE}/videos/{v['url']}"
        } for v in videos
    ]

# ===============================
# Shorts APIs
# ===============================
@app.post("/shorts")
def add_short(short: Short):
    shorts_collection.insert_one(short.dict())
    return {"message": "Short added"}

@app.get("/developers/{developer_id}/shorts")
def get_developer_shorts(developer_id: str):
    shorts = list(shorts_collection.find({"developer_id": developer_id}))
    return [
        {
            "id": str(s["_id"]),
            "title": s["title"],
            "url": f"{URL_BASE}/videos/{s['url']}"
        } for s in shorts
    ]

# ===============================
# Follow APIs
# ===============================
@app.post("/follow")
def follow_user(follow: Follow):
    follows_collection.insert_one(follow.dict())
    return {"message": "Follow request sent"}

@app.get("/follow")
def get_follows():
    follows = follows_collection.find()
    result = []
    for f in follows:
        result.append({
            "id": str(f["_id"]),
            "follower": f["follower"],
            "following": f["following"],
            "status": f.get("status", "pending")
        })
    return result

# ===============================
# Root Test
# ===============================
@app.get("/health")
def root():
    return {"message": "Server is running ✅"}