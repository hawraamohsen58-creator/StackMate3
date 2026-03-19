from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import os

app = FastAPI()

# ===============================
# MongoDB
# ===============================
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.get_database()

developers_collection = db["developers"]
projects_collection = db["projects"]
videos_collection = db["videos"]
shorts_collection = db["shorts"]
follows_collection = db["follows"]

# ===============================
# Videos Folder
# ===============================
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# ⚠️ حطي رابط السيرفر مالج هنا
URL_BASE = "https://stackmate3.onrender.com"

# ===============================
# Models
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

class Project(BaseModel):
    developer_id: str
    title: str
    description: str
    url: str
    technologies: str = ""
    image: str = ""
    status: str = "successful"
    tips: str = ""

class Video(BaseModel):
    developer_id: str
    title: str
    url: str  # اسم الملف مثل hm6.mp4

class Short(BaseModel):
    developer_id: str
    title: str
    url: str

class Follow(BaseModel):
    follower: str
    following: str
    status: str = "accepted"

# ===============================
# ROOT
# ===============================
@app.get("/")
def home():
    return {"message": "Server is running ✅"}

@app.get("/health")
def health():
    return {"message": "Server is running ✅"}

# ===============================
# Developers
# ===============================
@app.post("/developers")
def add_developer(dev: Developer):
    developers_collection.insert_one(dev.dict())
    return {"message": "Developer added"}

@app.get("/developers")
def get_developers():
    developers = developers_collection.find()
    result = []

    for dev in developers:
        followers = follows_collection.count_documents({
            "following": str(dev["_id"]),
            "status": "accepted"
        })

        result.append({
            "id": str(dev["_id"]),
            "name": dev["name"],
            "skill": dev["skill"],
            "bio": dev["bio"],
            "avatar": dev.get("avatar", ""),
            "followers_count": followers
        })

    return result

@app.get("/developers/search")
def search_developers(q: str):
    devs = developers_collection.find({
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"skill": {"$regex": q, "$options": "i"}}
        ]
    })

    return [{
        "id": str(d["_id"]),
        "name": d["name"],
        "skill": d["skill"],
        "bio": d["bio"],
        "avatar": d.get("avatar", ""),
        "followers_count": 0
    } for d in devs]

@app.get("/developers/{developer_id}")
def get_developer(developer_id: str):
    dev = developers_collection.find_one({"_id": ObjectId(developer_id)})

    if not dev:
        raise HTTPException(status_code=404, detail="Not found")

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
        "followers_count": 0
    }

# ===============================
# Projects
# ===============================
@app.post("/projects")
def add_project(project: Project):
    projects_collection.insert_one(project.dict())
    return {"message": "Project added"}

@app.get("/developers/{developer_id}/projects")
def get_projects(developer_id: str):
    projects = projects_collection.find({"developer_id": developer_id})
    return [{
        "id": str(p["_id"]),
        "title": p["title"],
        "description": p["description"],
        "url": p["url"],
        "technologies": p.get("technologies", ""),
        "image": p.get("image", ""),
        "status": p.get("status", "successful"),
        "tips": p.get("tips", "")
    } for p in projects]

# ===============================
# Videos
# ===============================
@app.post("/videos")
def add_video(video: Video):
    videos_collection.insert_one(video.dict())
    return {"message": "Video added"}

@app.get("/developers/{developer_id}/videos")
def get_videos(developer_id: str):
    videos = videos_collection.find({"developer_id": developer_id})

    return [{
        "id": str(v["_id"]),
        "title": v["title"],
        "url": f"{URL_BASE}/videos/{v['url']}"
    } for v in videos]

# ===============================
# Shorts
# ===============================
@app.post("/shorts")
def add_short(short: Short):
    shorts_collection.insert_one(short.dict())
    return {"message": "Short added"}

@app.get("/developers/{developer_id}/shorts")
def get_shorts(developer_id: str):
    shorts = shorts_collection.find({"developer_id": developer_id})

    return [{
        "id": str(s["_id"]),
        "title": s["title"],
        "url": f"{URL_BASE}/videos/{s['url']}"
    } for s in shorts]

# ===============================
# Follow
# ===============================
@app.post("/follow")
def follow_user(follow: Follow):
    follows_collection.insert_one(follow.dict())
    return {"message": "Followed"}

@app.get("/follow")
def get_follow():
    follows = follows_collection.find()

    return [{
        "id": str(f["_id"]),
        "follower": f["follower"],
        "following": f["following"],
        "status": f["status"]
    } for f in follows]
