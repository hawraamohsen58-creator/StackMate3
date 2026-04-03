from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import certifi
import os
import shutil

app = FastAPI()

# ===============================
# MongoDB Connection
# ===============================



uri = "mongodb+srv://hawraawaleed33_db_user:k0c6YSVbOChqqyOn@cluster0.qk8xvxh.mongodb.net/test?retryWrites=true&w=majority"

client = MongoClient(
    uri,
    tls=True,
    tlsAllowInvalidCertificates=True,  # 🔥 هذا الحل المهم
    tlsCAFile=certifi.where()
)

db = client["test"] # اسم الداتابيس

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
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")

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
    description: str = ""   
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
@app.get("/db-check")
def db_check():
    try:
        client.admin.command('ping')  # 🔥 يفحص الاتصال الحقيقي
        return {"message": "Database connected successfully ✅"}
    except Exception as e:
        return {"error": str(e)}
# ===============================
# Auth / Accounts
# ===============================

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
        raise HTTPException(
            status_code=400,
            detail="Email or username already exists"
        )

    # حفظ الحساب
    result = accounts_collection.insert_one(account.dict())
    account_id = str(result.inserted_id)

    # 🔥 إذا الحساب Developer ينضاف لقائمة المبرمجين
    if account.account_type == "developer":
        developers_collection.insert_one({
            "account_id": account_id,
            "name": account.username,
            "skill": "",
            "bio": "",
            "avatar": "",
            "job": "",
            "location": "",
            "experience": "",
            "technologies": "",
            "portfolio": ""
        })

    return {
        "message": "Account created",
        "id": account_id,
        "account_type": account.account_type
    }

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

@app.put("/accounts/{account_id}/profile")
def update_user_profile(account_id: str, profile: UpdateUserProfile):

    existing = accounts_collection.find_one({"_id": safe_object_id(account_id)})

    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    # تحديث الحساب
    accounts_collection.update_one(
        {"_id": safe_object_id(account_id)},
        {
            "$set": {
                "name": profile.name,
                "username": profile.username,
                "email": profile.email,
                "description": profile.description,
                "profile_image": profile.profile_image,
                "job": profile.job,
                "location": profile.location,
                "experience": profile.experience,
                "skills": profile.skills,
                "technologies": profile.technologies,
                "portfolio": profile.portfolio,
            }
        }
    )

    # 🔥 تحديث developer أيضاً
    if existing.get("account_type") == "developer":
        developers_collection.update_one(
            {"account_id": account_id},
            {
                "$set": {
                    "account_id": account_id,
                    "name": profile.name,
                    "skill": profile.skills,
                    "bio": profile.description,
                    "avatar": profile.profile_image,
                    "job": profile.job,
                    "location": profile.location,
                    "experience": profile.experience,
                    "technologies": profile.technologies,
                    "portfolio": profile.portfolio
                }
            },
            upsert=True
        )

    return {"message": "Profile updated successfully"}

# ===============================
# Developers
# ===============================

@app.post("/developers")
def add_developer(dev: Developer):
    developers_collection.insert_one({
        "account_id": "",  # 👈 مهم جدًا نضيفه
        "name": dev.name,
        "skill": dev.skill,
        "bio": dev.bio,
        "avatar": dev.avatar,
        "job": dev.job,
        "location": dev.location,
        "experience": dev.experience,
        "technologies": dev.technologies,
        "portfolio": dev.portfolio
    })
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
    if follow.follower == follow.following:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    existing = follows_collection.find_one({
        "follower": follow.follower,
        "following": follow.following,
        "status": "accepted"
    })

    if existing:
        return {"message": "Already following"}

    follows_collection.insert_one({
        "follower": follow.follower,
        "following": follow.following,
        "status": "accepted"
    })

    return {"message": "Followed successfully"}


# 🔴 unfollow
@app.delete("/follow")
def unfollow_user(follower: str, following: str):
    result = follows_collection.delete_one({
        "follower": follower,
        "following": following,
        "status": "accepted"
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not following")

    return {"message": "Unfollowed successfully"}


# 📥 كل العلاقات (اختياري)
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


# ✅ هل هذا المستخدم متابع؟
@app.get("/follow/check")
def check_follow(follower: str, following: str):
    existing = follows_collection.find_one({
        "follower": follower,
        "following": following,
        "status": "accepted"
    })

    return {
        "is_following": True if existing else False
    }


#  عدد المتابعين + المتابَعين
@app.get("/follow/counts/{account_id}")
def get_follow_counts(account_id: str):

    followers_count = follows_collection.count_documents({
        "following": account_id,
        "status": "accepted"
    })

    following_count = follows_collection.count_documents({
        "follower": account_id,
        "status": "accepted"
    })

    return {
        "followers_count": followers_count,
        "following_count": following_count
    }
# عدد المتابعين + المتابَعين
@app.get("/follow/counts/{account_id}")
def get_follow_counts(account_id: str):
    followers_count = follows_collection.count_documents({
        "following": account_id,
        "status": "accepted"
    })
    following_count = follows_collection.count_documents({
        "follower": account_id,
        "status": "accepted"
    })
    return {
        "followers_count": followers_count,
        "following_count": following_count
    }
#جلب المتابعين 

@app.get("/followers/{account_id}")
def get_followers(account_id: str):
    follows = follows_collection.find({
        "following": account_id,
        "status": "accepted"
    })

    result = []
    for f in follows:
        acc = accounts_collection.find_one({"_id": safe_object_id(f["follower"])})
        if acc:
            result.append({
                "id": str(acc["_id"]),
                "username": acc.get("username", ""),
                "name": acc.get("name", ""),
                "profile_image": acc.get("profile_image", "")
            })

    return result

#جلب المتابعين المتابعهم 
@app.get("/following/{account_id}")
def get_following(account_id: str):
    follows = follows_collection.find({
        "follower": account_id,
        "status": "accepted"
    })

    result = []
    for f in follows:
        acc = accounts_collection.find_one({"_id": safe_object_id(f["following"])})
        if acc:
            result.append({
                "id": str(acc["_id"]),
                "username": acc.get("username", ""),
                "name": acc.get("name", ""),
                "profile_image": acc.get("profile_image", "")
            })
            

    return result
@app.get("/ffmpeg-check")
def ffmpeg_check():
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return {"message": "ffmpeg installed ✅", "output": result.stdout[:200]}
    except Exception as e:
        return {"error": str(e)}
