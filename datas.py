from pydantic import BaseModel
import time
import struct
import io
import math

class DataLine(BaseModel):
    trusted: bool = True

    temperature: float
    pressure: float
    altitude: float
    humidity: float
    
    timestamp: int

# каждый тип данных по 4 байта, итого 20 на каждую запись, 1 байт на обозначение достоверности
linesize = 21

def unpack(f: io.BytesIO, items: int = 1, offcet: int = 0, step: int = 0) -> list[DataLine]:
    if offcet < 0:
        f.seek(0, 2)
        offcet = int(f.tell() / linesize + offcet)

    if offcet + items > f.tell() / linesize:
        f.seek(0, 2)
        items = int(f.tell() / linesize) - offcet

    f.seek(offcet * linesize)
    result = []

    for i in range(items):
        item = DataLine(
            trusted=struct.unpack("?", f.read(1))[0],

            temperature=struct.unpack("f", f.read(4))[0],
            pressure=struct.unpack("f", f.read(4))[0],
            altitude=struct.unpack("f", f.read(4))[0],
            humidity=struct.unpack("f", f.read(4))[0],

            timestamp=struct.unpack("I", f.read(4))[0]
        )

        f.seek(f.tell() + step*linesize)

        result.append(item)
        
    return result

def pack(f: io.BytesIO, data: DataLine):

    f.seek(0, 2)
    last = f.tell()

    if last != 0: 
        f.seek(last - 4) # нам нужно прочитать только последний timestamp
        last_timestamp = struct.unpack("I", f.read(4))[0]
    else: 
        last_timestamp = int(time.time() - 11)
        
    result = b""

    result += struct.pack("f", data.temperature)
    result += struct.pack("f", data.pressure)
    result += struct.pack("f", data.altitude)
    result += struct.pack("f", data.humidity)
    result += struct.pack("I", data.timestamp)

    if (last_timestamp > data.timestamp // 10 * 10): # просто ограничиваем запись каждые десять секунд
        ...
    else:

        count = math.floor((data.timestamp - last_timestamp) / 10) # смотрим сколько нужно заполнить данных с прошлой записи
        f.seek(last)
        for i in range(count):
            f.write(struct.pack("?", False)) # почечаем сгенерированные данные как недостоверные
            f.write(result)

        f.write(struct.pack("?", True))
        f.write(result)