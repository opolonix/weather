from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import Literal
from datas import TimeRow

import struct
import time
import json

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
    return templates.TemplateResponse("index.html", {"request": request, "w": last_weather_data, "json": json})

@app.post("/api/weather")
async def receive_weather_data(data: WeatherData):

    stantion_id = 1

    global last_weather_data
    last_weather_data = data.model_dump()

    with open(f"bin/{stantion_id}/temperature.bin", "ab+") as f:
        t = TimeRow(f)
        t.wrire(struct.pack("f", data.temperature))

    # with open(f"bin/{stantion_id}/humidity.bin", "ab+") as f:
    #     t = TimeRow(f)
    #     t.wrire(struct.pack("f", data.humidity))

    # with open(f"bin/{stantion_id}/pressure.bin", "ab+") as f:
    #     t = TimeRow(f)
    #     t.wrire(struct.pack("f", data.pressure))

    return {"status": "success"}

@app.get("/get/weather")
async def receive_weather_data():

    stantion_id = 1

    return last_weather_data


@app.get("/get/range")
async def receive_weather_data(parametr: Literal["temperature"], start: float) -> list:
    stantion_id = 1

    with open(f"bin/{stantion_id}/{parametr}.bin", "ab+") as f:
        t = TimeRow(f)
        result = []
        rows = t.get_range(start, time.time())
        for row in rows:
            timestamp = row[0]
            value = struct.unpack("f", row[1])[0]
            result.append([timestamp, value])

        return result



app.mount("/", StaticFiles(directory="html"), name="static")