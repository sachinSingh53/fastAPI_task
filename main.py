from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb+srv://sachin_53:68sXWPJfQ4iHkXg6@cluster0.nvfkv8t.mongodb.net/?retryWrites=true&w=majority")
db = client["mydatabase"]
collection = db["students"]

# Create Student
@app.post("/students", status_code=201)
async def create_student(student: dict):
    result = collection.insert_one(student)
    return JSONResponse(content={"id": str(result.inserted_id)})

# List Students
@app.get("/students", response_model=list)
async def list_students(country: str = Query(None), age: int = Query(None)):
    query = {}
    if country:
        query["address.country"] = country
    if age:
        query["age"] = {"$gte": age}
    students = list(collection.find(query, {"_id": 0}))
    return students

# Get Student
@app.get("/students/{id}", response_model=dict)
async def get_student(id: str = Path(...)):
    student_id = ObjectId(id)
    student = collection.find_one({"_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# Update Student
@app.patch("/students/{id}", status_code=204)
async def update_student(id: str = Path(...), student: dict = {}):
    student_id = ObjectId(id)
    if not student:
        raise HTTPException(status_code=400, detail="No data provided to update")
    student_encoded = jsonable_encoder(student)
    updated_student = collection.update_one({"_id": student_id}, {"$set": student_encoded})
    if updated_student.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

# Delete Student
@app.delete("/students/{id}")
async def delete_student(id: str = Path(...)):
    student_id = ObjectId(id)
    deleted_student = collection.delete_one({"_id": student_id})
    if deleted_student.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
