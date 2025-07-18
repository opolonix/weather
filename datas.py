import time
import struct
import io
from typing import Generator


class TimeRow:
    def __init__(self, fp: io.BytesIO):
        self.fp = fp
        self.metasize = 8 + 8 + 4 # dd>I поле под метаданные файла

    def find_item(self, timestamp: float, start: int = -1, end: int = -1) -> int:
        if end == -1:
            self.fp.seek(0, 2)
            end = self.fp.tell()
        if start == -1: start = self.metasize

        length = end - start
        step = length // self.datasize
        center_index = start + self.datasize * (step // 2)

        if length == 1: return center_index
        if length == 0: return -1

        self.fp.seek(center_index)
        center_timestamp = struct.unpack('>I', self.fp.read(4))[0]

        if center_timestamp < timestamp:
            return self.find_item(timestamp, center_index, end)
        elif center_timestamp > timestamp:
            return self.find_item(timestamp, start, center_index)

        return center_index
    
    def get_last(self) -> tuple[float, bytes]:
        self.fp.seek(0, 2)
        size = self.fp.tell()

        self.fp.seek(8)
        first_timestamp = struct.unpack('d', self.fp.read(8))[0]
        datasize = struct.unpack('>I', self.fp.read(4))[0]

        self.fp.seek(size - datasize - 4)
        return int(struct.unpack('>I', self.fp.read(4))[0] + first_timestamp), self.fp.read(datasize)

    def get_range(self, start: float, end: float) -> Generator[tuple[int, bytes], None, None]:
        self.fp.seek(0, 2)
        size = self.fp.tell()

        self.fp.seek(0)

        last_timestamp = struct.unpack('d', self.fp.read(8))[0]
        first_timestamp = struct.unpack('d', self.fp.read(8))[0]
        self.datasize = struct.unpack('>I', self.fp.read(4))[0]

        # start_timestamp = start - first_timestamp if start - first_timestamp > 0 else 0
        # start_index = self.find_item(start_timestamp)

        # if end < last_timestamp:
        #     end_timestamp = end - first_timestamp
        #     end_index = self.find_item(start_timestamp)
        # else:
        #     end_index = size - self.datasize
        start_index = self.metasize
        end_index = size
        self.fp.seek(start_index)

        print(start_index, (end_index-start_index)/(self.datasize + 4))

        result = []

        for item in range(start_index, end_index, self.datasize+4):
            result.append([struct.unpack('>I', self.fp.read(4))[0] + first_timestamp, self.fp.read(self.datasize)])

        return result

    def wrire(self, data: bytes):
        self.fp.seek(0, 2)
        size = self.fp.tell()

        self.fp.seek(0)
        self.fp.write(struct.pack('d', time.time())) # время последней записи

        if size == 0:
            self.fp.write(struct.pack('d', time.time())) # время первой записи
            self.fp.write(struct.pack('>I', len(data))) # размер записи

        self.fp.seek(8) # считываем метаданные
        first_timestamp = struct.unpack('d', self.fp.read(8))[0]
        datasize = struct.unpack('>I', self.fp.read(4))[0]

        if len(data) != datasize:
            raise TypeError("Тип данных не соответствует исходному")

        self.fp.seek(size - datasize - 4) # читаем последний таймстамп
        last_timestamp = struct.unpack('>I', self.fp.read(4))[0]
        current_timestamp = int(time.time()-first_timestamp)

        if (last_timestamp < current_timestamp): # создаем новую запись
            self.fp.seek(0, 2)
        else: # перепишем последнюю запись
            self.fp.seek(size - datasize - 4)

        self.fp.write(struct.pack('>I', current_timestamp // 10 * 10 + 10))
        self.fp.write(data)