import base64,io,os,threading
from contextlib import asynccontextmanager
import cv2,numpy as np
from PIL import Image,ImageOps
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from starlette.concurrency import run_in_threadpool
from coverswap.pipeline import CoverSwapPipeline
from coverswap.config import TryOnSettings
lock=threading.Lock()
pipeline=None
@asynccontextmanager
async def lifespan(app):
 global pipeline
 pipeline=CoverSwapPipeline(device=os.getenv('DEVICE','cuda'),low_vram=True)
 yield
app=FastAPI(lifespan=lifespan)
class Photo(BaseModel):
 photo:str=Field(max_length=16000000)
class Swap(Photo):
 garment:str=Field(max_length=16000000)
 person:int=Field(default=0,ge=0)
 category:str='upper_body'
 steps:int=Field(default=30,ge=1,le=60)
 seed:int=Field(default=42,ge=0,le=2147483647)
 high_resolution:bool=False
 guidance:float=Field(default=4,ge=0,le=10)
def decode(s):
 try:
  raw=base64.b64decode(s,validate=True)
  with Image.open(io.BytesIO(raw)) as im:
   if im.width*im.height>16000000:raise ValueError('Maximum 16 megapixels')
   a=np.asarray(ImageOps.exif_transpose(im).convert('RGB'))
  return cv2.cvtColor(a,cv2.COLOR_RGB2BGR)
 except Exception as e:raise HTTPException(400,'Invalid image or image exceeds 16 megapixels') from e
def detect_work(req):
 image=decode(req.photo)
 with lock:people=pipeline.detect_people(image)
 return {'people':[{'index':i,'label':p.label,'box':list(map(int,p.box))} for i,p in enumerate(people)]}
def swap_work(req):
 if req.category not in ('upper_body','lower_body','dress'):raise HTTPException(400,'Invalid garment category')
 image,garment=decode(req.photo),decode(req.garment)
 with lock:
  people=pipeline.detect_people(image)
  if req.person>=len(people):raise HTTPException(400,'Selected person is no longer available')
  settings=TryOnSettings(category=req.category,steps=req.steps,seed=req.seed,guidance_scale=req.guidance,width=768 if req.high_resolution else 576,height=1024 if req.high_resolution else 768)
  result=pipeline.swap_person(image,people[req.person],garment,settings)
 ok,data=cv2.imencode('.png',result)
 if not ok:raise RuntimeError('PNG encoding failed')
 return {'image':base64.b64encode(data).decode(),'mime':'image/png'}
@app.get('/health')
def health():return {'status':'ready','backend':'original CoverSwap CatVTON'}
@app.post('/detect')
async def detect(req:Photo):return await run_in_threadpool(detect_work,req)
@app.post('/swap')
async def swap(req:Swap):return await run_in_threadpool(swap_work,req)
