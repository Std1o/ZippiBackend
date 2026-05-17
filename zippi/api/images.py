from fastapi import APIRouter, UploadFile, Request
from fastapi.responses import FileResponse, PlainTextResponse
import shutil
import os
import re


router = APIRouter(prefix='/images', tags=["images"])

@router.get('/{image_name}')
def get_image(image_name: str):
    return FileResponse(f"taximetr/images/{image_name}".encode('utf-8').decode('utf-8'))

@router.post("/upload/")
async def create_upload_file(request: Request, upload_file: UploadFile):
    try:
        file_path = f"taximetr/images/{upload_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
    base_url = str(request.base_url).rstrip('/')
    return PlainTextResponse(f"{base_url}/images/{upload_file.filename}")