import os
import csv
import io
import uuid
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Dict
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy import create_engine, Column, String, Integer, Enum as SQLEnum, JSON, ForeignKey, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from fulfillment import process_from_queue

from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5436/fulfillment")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Database Models
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    status = Column(String, default=TaskStatus.PENDING)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    rows = relationship("JobRow", back_populates="job", cascade="all, delete-orphan")

class JobRow(Base):
    __tablename__ = "job_rows"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    row_index = Column(Integer)
    status = Column(String, default=TaskStatus.PENDING)
    data = Column(JSON)
    error = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    job = relationship("Job", back_populates="rows")

# Create tables
Base.metadata.create_all(bind=engine)

class CSVRow(BaseModel):
    order_item_id: str
    reg_no: str
    challan_no: str
    payment_remarks: str
    type: str

class CSVImportResponse(BaseModel):
    success: bool
    total_rows: int
    valid_rows: int
    errors: List[dict]
    job_id: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    total_rows: int
    processed_rows: int
    failed_rows: int
    row_statuses: Dict[int, dict]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def process_row_sync(job_id: str, row_index: int, row_data: dict):
    """Synchronous row processing - runs in background"""
    import time
    db = SessionLocal()
    try:
        # Update status to processing
        job_row = db.query(JobRow).filter(JobRow.job_id == job_id, JobRow.row_index == row_index).first()
        job_row.status = TaskStatus.PROCESSING
        db.commit()
        
        # Your long-running workflow logic here
        time.sleep(5)  # Simulate long processing (replace with actual logic)
        result = process_from_queue(**row_data)
        # Update to completed
        job_row.status = TaskStatus.COMPLETED
        job_row.result = result
        
        job = db.query(Job).filter(Job.id == job_id).first()
        job.processed_rows += 1
        db.commit()
        
    except Exception as e:
        db.rollback()
        job_row = db.query(JobRow).filter(JobRow.job_id == job_id, JobRow.row_index == row_index).first()
        job_row.status = TaskStatus.FAILED
        job_row.error = str(e)
        
        job = db.query(Job).filter(Job.id == job_id).first()
        job.failed_rows += 1
        db.commit()
    finally:
        # Check if all rows are processed
        job = db.query(Job).filter(Job.id == job_id).first()
        pending_rows = db.query(JobRow).filter(
            JobRow.job_id == job_id,
            JobRow.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING])
        ).count()
        
        if pending_rows == 0:
            job.status = TaskStatus.COMPLETED
            db.commit()
        
        db.close()

def process_all_rows_background(job_id: str, valid_rows: List[dict]):
    """Process all rows sequentially in background"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = TaskStatus.PROCESSING
        db.commit()
    finally:
        db.close()
    
    for i, row in enumerate(valid_rows):
        process_row_sync(job_id, i, row)

@app.post("/import-csv", response_model=CSVImportResponse)
async def import_csv(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    contents = await file.read()
    decoded = contents.decode('utf-8')
    
    reader = csv.DictReader(io.StringIO(decoded))
    
    valid_rows = []
    errors = []
    total_rows = 0
    
    for row_num, row in enumerate(reader, start=1):
        total_rows += 1
        try:
            validated_row = CSVRow(**row)
            valid_rows.append(validated_row.dict())
        except Exception as e:
            errors.append({
                "row": row_num,
                "data": row,
                "error": str(e)
            })
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Store job in database
    db = SessionLocal()
    try:
        job = Job(
            id=job_id,
            status=TaskStatus.PENDING,
            total_rows=len(valid_rows),
            processed_rows=0,
            failed_rows=0
        )
        db.add(job)
        
        for i, row in enumerate(valid_rows):
            job_row = JobRow(
                job_id=job_id,
                row_index=i,
                status=TaskStatus.PENDING,
                data=row,
                error=None,
                result=None
            )
            db.add(job_row)
        
        db.commit()
    finally:
        db.close()
    
    # Start background processing
    background_tasks.add_task(process_all_rows_background, job_id, valid_rows)
    
    return CSVImportResponse(
        success=len(errors) == 0,
        total_rows=total_rows,
        valid_rows=len(valid_rows),
        errors=errors,
        job_id=job_id
    )

@app.get("/job-status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_rows = db.query(JobRow).filter(JobRow.job_id == job_id).all()
        row_statuses = {
            row.row_index: {
                "status": row.status,
                "data": row.data,
                "error": row.error,
                "result": row.result
            }
            for row in job_rows
        }
        
        return JobStatusResponse(
            job_id=job_id,
            status=job.status,
            total_rows=job.total_rows,
            processed_rows=job.processed_rows,
            failed_rows=job.failed_rows,
            row_statuses=row_statuses
        )
    finally:
        db.close()

@app.get("/job-list", response_model=List[JobStatusResponse])
async def get_job_list():
    db = SessionLocal()
    try:
        jobs = db.query(Job).all()
        if not jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        job_list = [JobStatusResponse(
            job_id=job.id,
            status=job.status,
            total_rows=job.total_rows,
            processed_rows=job.processed_rows,
            failed_rows=job.failed_rows,
            row_statuses={}
        ) for job in jobs]
        return job_list
    finally:
        db.close()
    