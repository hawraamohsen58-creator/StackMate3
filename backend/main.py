from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI()

# ===============================
# Database
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
# Static Files
# ===============================
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

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

class Follow(BaseModel):
    follower: str
    following: str
    status: str = "pending"

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
    url: str
    thumbnail: str = ""
    description: str = ""
    views: int = 0
    developer_name: str = ""
    developer_avatar: str = ""

class Short(BaseModel):
    developer_id: str
    title: str
    url: str
    description: str = ""
    developer_name: str = ""
    developer_avatar: str = ""

# ===============================
# Helpers
# ===============================
def safe_object_id(id_value: str):
    try:
        return ObjectId(id_value)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID")

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
    dev = developers_collection.find_one({"_id": safe_object_id(developer_id)})

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
            "developer_id": p["developer_id"],
            "title": p["title"],
            "description": p["description"],
            "url": p["url"],
            "technologies": p.get("technologies", ""),
            "image": p.get("image", ""),
            "status": p.get("status", "successful"),
            "tips": p.get("tips", "")
        }
        for p in projects
    ]

@app.get("/projects/{project_id}")
def get_project_by_id(project_id: str):
    project = projects_collection.find_one({"_id": safe_object_id(project_id)})

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": str(project["_id"]),
        "developer_id": project["developer_id"],
        "title": project["title"],
        "description": project["description"],
        "url": project["url"],
        "technologies": project.get("technologies", ""),
        "image": project.get("image", ""),
        "status": project.get("status", "successful"),
        "tips": project.get("tips", "")
    }

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
            "developer_id": v["developer_id"],
            "title": v["title"],
            "url": f"{URL_BASE}/videos/{v['url']}",
            "thumbnail": v.get("thumbnail", ""),
            "description": v.get("description", ""),
            "views": v.get("views", 0),
            "developer_name": v.get("developer_name", ""),
            "developer_avatar": v.get("developer_avatar", "")
        }
        for v in videos
    ]

@app.get("/videos/search")
def search_videos(q: str = ""):
    videos = list(videos_collection.find({
        "title": {"$regex": q, "$options": "i"}
    }))

    return [
        {
            "id": str(v["_id"]),
            "developer_id": v["developer_id"],
            "title": v["title"],
            "url": f"{URL_BASE}/videos/{v['url']}",
            "thumbnail": v.get("thumbnail", ""),
            "description": v.get("description", ""),
            "views": v.get("views", 0),
            "developer_name": v.get("developer_name", ""),
            "developer_avatar": v.get("developer_avatar", "")
        }
        for v in videos
    ]

@app.get("/videos/{video_id}")
def get_video_by_id(video_id: str):
    video = videos_collection.find_one({"_id": safe_object_id(video_id)})

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "id": str(video["_id"]),
        "developer_id": video["developer_id"],"title": video["title"],
        "url": f"{URL_BASE}/videos/{video['url']}",
        "thumbnail": video.get("thumbnail", ""),
        "description": video.get("description", ""),
        "views": video.get("views", 0),
        "developer_name": video.get("developer_name", ""),
        "developer_avatar": video.get("developer_avatar", "")
    }

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
            "developer_id": s["developer_id"],
            "title": s["title"],
            "url": f"{URL_BASE}/videos/{s['url']}",
            "description": s.get("description", ""),
            "developer_name": s.get("developer_name", ""),
            "developer_avatar": s.get("developer_avatar", "")
        }
        for s in shorts
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
# Root
# ===============================
@app.get("/")
def home():
    return {"message": "Server is running ✅"}

@app.get("/health")
def health():
    return {"message": "Server is running ✅"}
