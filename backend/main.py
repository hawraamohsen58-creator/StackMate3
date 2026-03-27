from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI()

# ===============================
# MongoDB Connection
# ===============================
MONGO_URI = "mongodb+srv://user:user246810@cluster0.jeyjiot.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["developers_db"]

developers_collection = db["developers"]
projects_collection = db["projects"]
videos_collection = db["videos"]
shorts_collection = db["shorts"]
follows_collection = db["follows"]
accounts_collection = db["accounts"]

# ===============================
# Static Files
# ===============================
app.mount("/media/videos", StaticFiles(directory="videos"), name="media_videos")

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
    url: str = ""
    url_480: str = ""
    url_720: str = ""
    url_1080: str = ""
    thumbnail: str = ""
    views: int = 0

class Short(BaseModel):
    developer_id: str
    title: str
    url: str

class Follow(BaseModel):
    follower: str
    following: str
    status: str = "accepted"
    
class Account(BaseModel):
    email: str
    username: str
    password: str
    account_type: str
    name: str = ""
    description: str = ""
    profile_image: str = ""
# ===============================
# Helper
# ===============================
def safe_object_id(value: str):
    try:
        return ObjectId(value)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID")

# ===============================
# Root
# ===============================
@app.get("/")
def home():
    return {"message": "Server is running ✅"}

@app.get("/health")
def health():
    return {"message": "Server is running ✅"}
# ===============================
# Auth / Accounts
# ===============================

from fastapi import HTTPException

# تسجيل حساب جديد
@app.post("/signup")
def signup(account: Account):
    existing = accounts_collection.find_one({
        "$or": [
            {"email": account.email},
            {"username": account.username}
        ]
    })

    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")

    result = accounts_collection.insert_one(account.dict())

    return {
        "message": "Account created",
        "id": str(result.inserted_id),
        "account_type": account.account_type
    }


# 🔥 هذا الجديد ضيفيه هنا بالضبط
class LoginData(BaseModel):
    email: str
    password: str


@app.post("/login")
def login(data: LoginData):
    account = accounts_collection.find_one({
        "email": data.email,
        "password": data.password
    })

    if not account:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "message": "Login successful",
        "id": str(account["_id"]),
        "email": account.get("email", ""),
        "username": account.get("username", ""),
        "account_type": account.get("account_type", ""),
        "name": account.get("name", ""),
        "description": account.get("description", ""),
        "profile_image": account.get("profile_image", "")
    }


# 🔥 جلب بيانات حساب
@app.get("/accounts/{account_id}")
def get_account(account_id: str):
    account = accounts_collection.find_one({"_id": safe_object_id(account_id)})

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
    "id": str(account["_id"]),
    "email": account.get("email", ""),
    "username": account.get("username", ""),
    "account_type": account.get("account_type", ""),
    "name": account.get("name", ""),
    "description": account.get("description", ""),
    "profile_image": account.get("profile_image", ""),

    "job": account.get("job", ""),
    "location": account.get("location", ""),
    "experience": account.get("experience", ""),
    "skills": account.get("skills", ""),
    "technologies": account.get("technologies", ""),
    "portfolio": account.get("portfolio", "")
}


# 🔥 موديل تحديث البروفايل
class UpdateUserProfile(BaseModel):
    name: str = ""
    username: str = ""
    email: str = ""
    description: str = ""
    profile_image: str = ""

    job: str = ""
    location: str = ""
    experience: str = ""
    skills: str = ""
    technologies: str = ""
    portfolio: str = ""

# 🔥 تحديث بيانات المستخدم
@app.put("/accounts/{account_id}/profile")
def update_user_profile(account_id: str, profile: UpdateUserProfile):
    existing = accounts_collection.find_one({"_id": safe_object_id(account_id)})

    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    accounts_collection.update_one(
        {"_id": safe_object_id(account_id)},
        {
            "$set": {
                "name": profile.name,
                "username": profile.username,
                "email": profile.email,
                "description": profile.description,
                "profile_image": profile.profile_image,

                # 🔥 الجديد (المهم)
                "job": profile.job,
                "location": profile.location,
                "experience": profile.experience,
                "skills": profile.skills,
                "technologies": profile.technologies,
                "portfolio": profile.portfolio,
            }
        }
    )

    return {"message": "Profile updated successfully"}

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
        followers_count = follows_collection.count_documents({
            "following": str(dev["_id"]),
            "status": "accepted"
        })

        result.append({
            "id": str(dev["_id"]),
            "name": dev.get("name", ""),
            "skill": dev.get("skill", ""),
            "bio": dev.get("bio", ""),
            "avatar": dev.get("avatar", ""),
            "followers_count": followers_count
        })

    return result

@app.get("/developers/search")
def search_developers(q: str):
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
            "name": dev.get("name", ""),
            "skill": dev.get("skill", ""),
            "bio": dev.get("bio", ""),
            "avatar": dev.get("avatar", ""),
            "followers_count": followers_count
        })

    return result

@app.get("/developers/{developer_id}")
def get_developer(developer_id: str):
    dev = developers_collection.find_one({"_id": safe_object_id(developer_id)})

    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")

    followers_count = follows_collection.count_documents({
        "following": developer_id,
        "status": "accepted"
    })
    return {
        "id": str(dev["_id"]),
        "name": dev.get("name", ""),
        "job": dev.get("job", ""),
        "location": dev.get("location", ""),
        "experience": dev.get("experience", ""),
        "skill": dev.get("skill", ""),
        "technologies": dev.get("technologies", ""),
        "portfolio": dev.get("portfolio", ""),
        "bio": dev.get("bio", ""),
        "avatar": dev.get("avatar", ""),
        "followers_count": followers_count
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
    projects = list(projects_collection.find({"developer_id": developer_id}))

    return [
        {
            "id": str(p["_id"]),
            "title": p.get("title", ""),
            "description": p.get("description", ""),
            "url": p.get("url", ""),
            "technologies": p.get("technologies", ""),
            "image": p.get("image", ""),
            "status": p.get("status", "successful"),
            "tips": p.get("tips", "")
        }
        for p in projects
    ]

# ===============================
# Videos
# ===============================
@app.post("/videos")
def add_video(video: Video):
    videos_collection.insert_one(video.dict())
    return {"message": "Video added"}

@app.get("/developers/{developer_id}/videos")
def get_videos(developer_id: str):
    videos = list(videos_collection.find({"developer_id": developer_id}))
    result = []
    dev = developers_collection.find_one({"_id": safe_object_id(developer_id)})

    for v in videos:
        url = v.get("url", "")
        url_480 = v.get("url_480", "")
        url_720 = v.get("url_720", "")
        url_1080 = v.get("url_1080", "")

        result.append({
            "id": str(v["_id"]),
            "developer_id": v.get("developer_id", ""),
            "title": v.get("title", ""),
            "url": f"{URL_BASE}/media/videos/{url}" if url else "",
            "url_480": f"{URL_BASE}/media/videos/{url_480}" if url_480 else "",
            "url_720": f"{URL_BASE}/media/videos/{url_720}" if url_720 else "",
            "url_1080": f"{URL_BASE}/media/videos/{url_1080}" if url_1080 else "",
            "thumbnail": v.get("thumbnail", ""),
            "developer_name": dev.get("name", "") if dev else "",
            "developer_avatar": dev.get("avatar", "") if dev else "",
            "views": v.get("views", 0)
        })

    return result
@app.get("/videos/search")
def search_videos(q: str):
    videos = list(videos_collection.find({
        "title": {"$regex": q, "$options": "i"}
    }))
    result = []

    for v in videos:
        developer_id = v.get("developer_id", "")
        dev = None

        if developer_id:
            try:
                dev = developers_collection.find_one({"_id": safe_object_id(developer_id)})
            except:
                dev = None

        url = v.get("url", "")
        url_480 = v.get("url_480", "")
        url_720 = v.get("url_720", "")
        url_1080 = v.get("url_1080", "")

        result.append({
            "id": str(v["_id"]),
            "developer_id": developer_id,
            "title": v.get("title", ""),
            "url": f"{URL_BASE}/media/videos/{url}" if url else "",
            "url_480": f"{URL_BASE}/media/videos/{url_480}" if url_480 else "",
            "url_720": f"{URL_BASE}/media/videos/{url_720}" if url_720 else "",
            "url_1080": f"{URL_BASE}/media/videos/{url_1080}" if url_1080 else "",
            "thumbnail": v.get("thumbnail", ""),
            "developer_name": dev.get("name", "") if dev else "",
            "developer_avatar": dev.get("avatar", "") if dev else "",
            "views": v.get("views", 0)
        })

    return result

@app.get("/videos/{video_id}")
def get_video_by_id(video_id: str):
    video = videos_collection.find_one({"_id": safe_object_id(video_id)})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    developer_id = video.get("developer_id", "")
    dev = None

    if developer_id:
        try:
            dev = developers_collection.find_one({"_id": safe_object_id(developer_id)})
        except:
            dev = None

    url = video.get("url", "")
    url_480 = video.get("url_480", "")
    url_720 = video.get("url_720", "")
    url_1080 = video.get("url_1080", "")

    return {
        "id": str(video["_id"]),
        "developer_id": developer_id,
        "title": video.get("title", ""),
        "url": f"{URL_BASE}/media/videos/{url}" if url else "",
        "url_480": f"{URL_BASE}/media/videos/{url_480}" if url_480 else "",
        "url_720": f"{URL_BASE}/media/videos/{url_720}" if url_720 else "",
        "url_1080": f"{URL_BASE}/media/videos/{url_1080}" if url_1080 else "",
        "thumbnail": video.get("thumbnail", ""),
        "developer_name": dev.get("name", "") if dev else "",
        "developer_avatar": dev.get("avatar", "") if dev else "",
        "views": video.get("views", 0)
    }

@app.delete("/videos/{video_id}")
def delete_video(video_id: str):
    result = videos_collection.delete_one({"_id": safe_object_id(video_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": "Video deleted"}

# ===============================
# Shorts
# ===============================
@app.post("/shorts")
def add_short(short: Short):
    shorts_collection.insert_one(short.dict())
    return {"message": "Short added"}

@app.get("/developers/{developer_id}/shorts")
def get_shorts(developer_id: str):
    shorts = list(shorts_collection.find({"developer_id": developer_id}))
    result = []

    dev = developers_collection.find_one({"_id": safe_object_id(developer_id)})

    for s in shorts:
        result.append({
            "id": str(s["_id"]),
            "title": s.get("title", ""),
            "url": f"{URL_BASE}/media/videos/{s.get('url', '')}",
            "developer_name": dev.get("name", "") if dev else "",
            "developer_avatar": dev.get("avatar", "") if dev else "",
            "likes": 0
        })

    return result

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
    result = []

    for f in follows:
        result.append({
            "id": str(f["_id"]),
            "follower": f.get("follower", ""),
            "following": f.get("following", ""),
            "status": f.get("status", "accepted")
        })

    return result
