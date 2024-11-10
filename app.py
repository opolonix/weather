from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from datas import pack, DataLine, unpack
import time

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
    global last_weather_data
    last_weather_data = data.model_dump()


    line = DataLine(**last_weather_data, timestamp=int(time.time()))

    with open("data.bin", "ab+") as f:
        pack(f, line)
        f.close()

    return {"status": "success"}

@app.get("/get/weather")
async def receive_weather_data():
    return last_weather_data


@app.get("/get/range")
async def receive_weather_data(items: int = 10, offcet: int = -10, step: int = 0) -> list[DataLine]:
    items = min(items, 15000)
    with open("data.bin", "rb") as f:
        data = unpack(f, items, offcet, step)
        f.close()
    return data