from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
from email.message import EmailMessage
import certifi
import os
import shutil
import subprocess
import uuid
import random
import smtplib

app = FastAPI()

# ===============================
# MongoDB Connection
# ===============================
uri = "mongodb+srv://hawraawaleed33_db_user:k0c6YSVbOChqqyOn@cluster0.qk8xvxh.mongodb.net/test?retryWrites=true&w=majority"

client = MongoClient(
    uri,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsCAFile=certifi.where()
)

db = client["test"]

developers_collection = db["developers"]
projects_collection = db["projects"]
videos_collection = db["videos"]
shorts_collection = db["shorts"]
follows_collection = db["follows"]
accounts_collection = db["accounts"]
reset_codes_collection = db["reset_codes"]
notifications_collection = db["notifications"]

# ===============================
# Static Files
# ===============================
os.makedirs("videos", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

app.mount("/media/videos", StaticFiles(directory="videos"), name="media_videos")
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")

URL_BASE = "https://stackmate3.onrender.com"

# ===============================
# Email / SMTP Config
# ===============================
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "hawraamohsen58@gmail.com"
SMTP_PASS = "zqwqatvyydikoajm"
SMTP_FROM_EMAIL = SMTP_USER

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

class FollowToggleRequest(BaseModel):
    follower_id: str
    following_id: str

class NotificationCreate(BaseModel):
    receiver_id: str
    sender_id: str
    sender_name: str = ""
    sender_image: str = ""
    sender_account_type: str = ""
    title: str = ""
    message: str
    type: str = "follow"


class Account(BaseModel):
    email: str
    username: str
    password: str
    account_type: str
    name: str = ""
    description: str = ""
    profile_image: str = ""
    phone: str = ""
    job: str = ""
    location: str = ""
    experience: str = ""
    skills: str = ""
    technologies: str = ""
    portfolio: str = ""


class LoginData(BaseModel):
    email: str
    password: str


class UpdateUserProfile(BaseModel):
    name: str = ""
    username: str = ""
    email: str = ""
    description: str = ""
    profile_image: str = ""
    phone: str = ""
    job: str = ""
    location: str = ""
    experience: str = ""
    skills: str = ""
    technologies: str = ""
    portfolio: str = ""


class ForgotPasswordRequest(BaseModel):
    email_or_phone: str


class VerifyResetCodeRequest(BaseModel):
    email_or_phone: str
    code: str


class ResetPasswordRequest(BaseModel):
    email_or_phone: str
    code: str
    new_password: str


# ===============================
# Helper
# ===============================
def safe_object_id(value: str):
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")


def generate_otp():
    return f"{random.randint(100000, 999999)}"


def send_email_code(to_email: str, code: str):
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS or not SMTP_FROM_EMAIL:
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = "StackMate Password Reset Code"
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.set_content(
            f"Your StackMate verification code is: {code}\n\n"
            f"This code will expire in 10 minutes."
        )

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        return True
    except Exception as e:
        print("Email sending error:", str(e))
        return False


def find_account_by_identifier(identifier: str):
    return accounts_collection.find_one({
        "$or": [
            {"email": identifier},
            {"phone": identifier}
        ]
    })


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
        client.admin.command("ping")
        return {"message": "Database connected successfully ✅"}
    except Exception as e:
        return {"error": str(e)}


# ===============================
# Auth / Accounts
# ===============================
@app.post("/signup")
def signup(account: Account):
    account_type = account.account_type.lower().strip()

    if account_type not in ["developer", "user", "company"]:
        raise HTTPException(status_code=400, detail="Invalid account type")

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

    account_data = account.dict()
    account_data["account_type"] = account_type

    result = accounts_collection.insert_one(account_data)
    account_id = str(result.inserted_id)

    if account_type == "developer":
        developers_collection.insert_one({
            "account_id": account_id,
            "name": account.username,
            "skill": account.skills,
            "bio": account.description,
            "avatar": account.profile_image,
            "job": account.job,
            "location": account.location,
            "experience": account.experience,
            "technologies": account.technologies,
            "portfolio": account.portfolio
        })

    return {
        "message": "Account created successfully",
        "id": account_id,
        "account_type": account_type
    }


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
        "profile_image": account.get("profile_image", ""),
        "phone": account.get("phone", ""),
        "job": account.get("job", ""),
        "location": account.get("location", ""),
        "experience": account.get("experience", ""),
        "skills": account.get("skills", ""),
        "technologies": account.get("technologies", ""),
        "portfolio": account.get("portfolio", "")
    }


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
        "phone": account.get("phone", ""),
        "job": account.get("job", ""),
        "location": account.get("location", ""),
        "experience": account.get("experience", ""),
        "skills": account.get("skills", ""),
        "technologies": account.get("technologies", ""),
        "portfolio": account.get("portfolio", "")
    }


@app.put("/accounts/{account_id}/profile")
def update_user_profile(account_id: str, profile: UpdateUserProfile):
    existing = accounts_collection.find_one({"_id": safe_object_id(account_id)})

    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = {
        "name": profile.name,
        "username": profile.username,
        "email": profile.email,
        "description": profile.description,
        "profile_image": profile.profile_image,
        "phone": profile.phone,
        "job": profile.job,
        "location": profile.location,
        "experience": profile.experience,
        "skills": profile.skills,
        "technologies": profile.technologies,
        "portfolio": profile.portfolio,
    }

    accounts_collection.update_one(
        {"_id": safe_object_id(account_id)},
        {"$set": update_data}
    )

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
# Forgot Password / Verify / Reset
# ===============================
@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    identifier = data.email_or_phone.strip()

    if not identifier:
        raise HTTPException(status_code=400, detail="Email or phone is required")

    account = find_account_by_identifier(identifier)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    reset_codes_collection.update_many(
        {
            "account_id": str(account["_id"]),
            "used": False
        },
        {
            "$set": {"used": True}
        }
    )

    reset_codes_collection.insert_one({
        "account_id": str(account["_id"]),
        "email_or_phone": identifier,
        "code": code,
        "used": False,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    })

    account_email = account.get("email", "")

    if account_email:
        email_sent = send_email_code(account_email, code)

        if email_sent:
            return {
                "message": "Verification code sent successfully"
            }

        # للتجربة إذا SMTP مو مضبوط
        return {
            "message": "Verification code generated successfully (SMTP not configured)",
            "debug_code": code
        }

    raise HTTPException(
        status_code=400,
        detail="This account does not have a valid email for code delivery"
    )
@app.post("/verify-reset-code")
def verify_reset_code(data: VerifyResetCodeRequest):
    identifier = data.email_or_phone.strip()
    code = data.code.strip()

    if not identifier or not code:
        raise HTTPException(status_code=400, detail="Missing data")

    account = find_account_by_identifier(identifier)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    reset_record = reset_codes_collection.find_one({
        "account_id": str(account["_id"]),
        "email_or_phone": identifier,
        "code": code,
        "used": False
    })

    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    expires_at = reset_record.get("expires_at")
    if expires_at and datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Verification code has expired")

    return {"message": "Code verified successfully"}


@app.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    identifier = data.email_or_phone.strip()
    code = data.code.strip()
    new_password = data.new_password.strip()

    if not identifier or not code or not new_password:
        raise HTTPException(status_code=400, detail="Missing data")

    if len(new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )

    account = find_account_by_identifier(identifier)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    reset_record = reset_codes_collection.find_one({
        "account_id": str(account["_id"]),
        "email_or_phone": identifier,
        "code": code,
        "used": False
    })

    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    expires_at = reset_record.get("expires_at")
    if expires_at and datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Verification code has expired")

    accounts_collection.update_one(
        {"_id": account["_id"]},
        {"$set": {"password": new_password}}
    )

    reset_codes_collection.update_one(
        {"_id": reset_record["_id"]},
        {"$set": {"used": True}}
    )

    return {"message": "Password reset successfully"}


# ===============================
# Developers
# ===============================
@app.post("/developers")
def add_developer(dev: Developer):
    developers_collection.insert_one({
        "account_id": "",
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

    account_id = dev.get("account_id", "")

    followers_count = follows_collection.count_documents({
        "following": account_id,
        "status": "accepted"
    })

    following_count = follows_collection.count_documents({
        "follower": account_id,
        "status": "accepted"
    })

    return {
        "id": str(dev["_id"]),
        "account_id": account_id,
        "name": dev.get("name", ""),
        "job": dev.get("job", ""),
        "location": dev.get("location", ""),
        "experience": dev.get("experience", ""),
        "skill": dev.get("skill", ""),
        "technologies": dev.get("technologies", ""),
        "portfolio": dev.get("portfolio", ""),
        "bio": dev.get("bio", ""),
        "avatar": dev.get("avatar", ""),
        "followers_count": followers_count,
        "following_count": following_count
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


@app.post("/videos/upload")
def upload_video(
    title: str = Form(...),
    description: str = Form(""),
    developer_id: str = Form(...),
    file: UploadFile = File(...),
    thumbnail: UploadFile = File(None)
):
    os.makedirs("videos", exist_ok=True)
    os.makedirs("thumbnails", exist_ok=True)

    dev = developers_collection.find_one({"account_id": developer_id})
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")

    unique_id = str(uuid.uuid4())
    video_filename = f"{unique_id}.mp4"
    video_path = os.path.join("videos", video_filename)

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    thumbnail_url = ""
    if thumbnail:
        thumb_filename = f"{unique_id}_thumb.jpg"
        thumb_path = os.path.join("thumbnails", thumb_filename)

        with open(thumb_path, "wb") as buffer:
            shutil.copyfileobj(thumbnail.file, buffer)

        thumbnail_url = f"{URL_BASE}/thumbnails/{thumb_filename}"

    videos_collection.insert_one({
        "developer_id": str(dev["_id"]),
        "title": title,
        "description": description,
        "url": video_filename,
        "thumbnail": thumbnail_url,
        "views": 0
    })

    return {"message": "Video uploaded successfully ✅"}


@app.get("/developers/{developer_id}/videos")
def get_videos(developer_id: str):
    videos = list(videos_collection.find({"developer_id": developer_id}))
    result = []
    dev = developers_collection.find_one({"_id": safe_object_id(developer_id)})

    for v in videos:
        url = v.get("url", "")
        result.append({"id": str(v["_id"]),
            "developer_id": v.get("developer_id", ""),
            "title": v.get("title", ""),
            "description": v.get("description", ""),
            "url": f"{URL_BASE}/media/videos/{url}" if url else "",
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
            except Exception:
                dev = None

        url = v.get("url", "")

        result.append({
            "id": str(v["_id"]),
            "developer_id": developer_id,
            "title": v.get("title", ""),
            "description": v.get("description", ""),
            "url": f"{URL_BASE}/media/videos/{url}" if url else "",
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
        except Exception:
            dev = None

    url = video.get("url", "")

    return {
        "id": str(video["_id"]),
        "developer_id": developer_id,
        "title": video.get("title", ""),
        "description": video.get("description", ""),
        "url": f"{URL_BASE}/media/videos/{url}" if url else "",
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
@app.get("/follow/status/{follower_id}/{following_id}")
def get_follow_status(follower_id: str, following_id: str):
    existing = follows_collection.find_one({
        "follower": follower_id,
        "following": following_id,
        "status": "accepted"
    })
    return {"followed": True if existing else False}


@app.post("/follow/toggle")
def toggle_follow(data: FollowToggleRequest):
    if data.follower_id == data.following_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    existing = follows_collection.find_one({
        "follower": data.follower_id,
        "following": data.following_id,
        "status": "accepted"
    })

    if existing:
        follows_collection.delete_one({
            "_id": existing["_id"]
        })
        return {
            "message": "Unfollowed successfully",
            "followed": False
        }

    follows_collection.insert_one({
        "follower": data.follower_id,
        "following": data.following_id,
        "status": "accepted",
        "created_at": datetime.utcnow()
    })

    return {
        "message": "Followed successfully",
        "followed": True
    }


@app.get("/follow/followers/{account_id}")
def get_followers_new(account_id: str):
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
                "profile_image": acc.get("profile_image", ""),
                "account_type": acc.get("account_type", "")
            })

    return result


@app.get("/follow/following/{account_id}")
def get_following_new(account_id: str):
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
                "profile_image": acc.get("profile_image", ""),
                "account_type": acc.get("account_type", "")
            })

    return result


@app.post("/notifications/follow")
def create_follow_notification(data: NotificationCreate):
    notifications_collection.insert_one({
        "receiver_id": data.receiver_id,
        "sender_id": data.sender_id,
        "sender_name": data.sender_name,
        "sender_image": data.sender_image,
        "sender_account_type": data.sender_account_type,
        "title": data.title,
        "message": data.message,
        "type": data.type,
        "is_read": False,
        "created_at": datetime.utcnow()
    })
    return {"message": "Notification created successfully"}


@app.get("/notifications/{user_id}")
def get_notifications(user_id: str):
    notifications = notifications_collection.find({
        "receiver_id": user_id
    }).sort("created_at", -1)

    result = []
    for n in notifications:
        result.append({
            "id": str(n["_id"]),
            "receiver_id": n.get("receiver_id", ""),
            "sender_id": n.get("sender_id", ""),
            "sender_name": n.get("sender_name", ""),
            "sender_image": n.get("sender_image", ""),
            "sender_account_type": n.get("sender_account_type", ""),
            "title": n.get("title", ""),
            "message": n.get("message", ""),
            "type": n.get("type", ""),
            "is_read": n.get("is_read", False),
            "created_at": str(n.get("created_at", ""))
        })

    return result


# ===============================
# TEST FFMPEG
# ===============================
@app.get("/ffmpeg-check")
def ffmpeg_check():
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return {
            "message": "ffmpeg installed ✅",
            "output": result.stdout[:200]
        }
    except Exception as e:
        return {"error": str(e)}
    
