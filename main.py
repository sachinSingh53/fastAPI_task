from fastapi import FastAPI, HTTPException, Path, Query, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from bson import ObjectId
from redis_connection import RedisConnection 
import aioredis
from datetime import datetime, timedelta

app = FastAPI()
redis_conn = RedisConnection()

# Connect to MongoDB
client = MongoClient("mongodb+srv://sachin_53:68sXWPJfQ4iHkXg6@cluster0.nvfkv8t.mongodb.net/?retryWrites=true&w=majority")
db = client["mydatabase"]
collection = db["students"]

# Middleware for Rate Limiter
async def rate_limit(request):
    user_id = request.headers.get("user_id")
    if user_id:
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"user:{user_id}:{current_date}"
        value = await redis_conn.redis.get(key)
        if value is None:
            await redis_conn.redis.setex(key, 86400, "1")
        else:
            if int(value) >= 1000:  # Limiting the number of calls per day to 1000
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            else:
                await redis_conn.redis.incr(key)

@app.middleware("http")
async def add_process_time_header(request, call_next):
    await rate_limit(request)
    response = await call_next(request)
    return response

# Create Student
@app.post("/students", status_code=201)
async def create_student(student: dict, x_user_id: str = Header(None)):
    result = collection.insert_one(student)
    return JSONResponse(content={"id": str(result.inserted_id)})

# List Students
@app.get("/students", response_model=list)
async def list_students(country: str = Query(None), age: int = Query(None), x_user_id: str = Header(None)):
    query = {}
    if country:
        query["address.country"] = country
    if age:
        query["age"] = {"$gte": age}
    students = list(collection.find(query, {"_id": 0}))
    return students

# Get Student
@app.get("/students/{id}", response_model=dict)
async def get_student(id: str = Path(...), x_user_id: str = Header(None)):
    student_id = ObjectId(id)
    student = collection.find_one({"_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# Update Student
@app.patch("/students/{id}", status_code=204)
async def update_student(id: str = Path(...), student: dict = {}, x_user_id: str = Header(None)):
    student_id = ObjectId(id)
    if not student:
        raise HTTPException(status_code=400, detail="No data provided to update")
    student_encoded = jsonable_encoder(student)
    updated_student = collection.update_one({"_id": student_id}, {"$set": student_encoded})
    if updated_student.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

# Delete Student
@app.delete("/students/{id}")
async def delete_student(id: str = Path(...), x_user_id: str = Header(None)):
    student_id = ObjectId(id)
    deleted_student = collection.delete_one({"_id": student_id})
    if deleted_student.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

