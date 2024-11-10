from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from datas import TimeRow
import struct

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="html")

last_weather_data = {}

class WeatherData(BaseModel):
    temperature: float
    pressure: float
    altitude: float
    humidity: float

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "w": last_weather_data})

@app.post("/api/weather")
async def receive_weather_data(data: WeatherData):

    stantion_id = 1

    global last_weather_data
    last_weather_data = data.model_dump()

    with open(f"bin/{stantion_id}/temperature.bin", "ab+") as f:
        t = TimeRow(f)
        t.wrire(struct.pack("f", data.temperature))

    with open(f"bin/{stantion_id}/humidity.bin", "ab+") as f:
        t = TimeRow(f)
        t.wrire(struct.pack("f", data.humidity))

    with open(f"bin/{stantion_id}/pressure.bin", "ab+") as f:
        t = TimeRow(f)
        t.wrire(struct.pack("f", data.pressure))

    return {"status": "success"}

@app.get("/get/weather")
async def receive_weather_data():

    stantion_id = 1

    return last_weather_data


@app.get("/get/range")
async def receive_weather_data(items: int = 10, offcet: int = -10, step: int = 0) -> list:
    
    stantion_id = 1

    items = min(items, 15000)
    ...