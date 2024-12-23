from PIL import Image
import requests
from io import BytesIO
import datetime

HallToId = {
    "Sports centre De Pijp Hall 1": 1000000015,
    "Sports centre De Pijp Hall 2": 1000000016,
    "Sports halls South 1A (front)": 1000000002,
    "Sports halls South 1B (back)": 1000000003,
    "Europaboulevard Sports Hall": 1000000127,
    "Sports halls South 3": 1000000006,
    "Calvijn Sports Hall": 1000000174,
}

MinimalTimeSlot = 90

def get_schedule_url(id, date):
    date_str = date.strftime("%Y%m%d")
    return f"https://sportverhuur.amsterdam.nl/amisweb/amsterdam/amis/amis.php?action=objschema&obj_id={id}&date={date_str}&period=0"

class AvailableEntries:
    class AvailableEntry:
        def __init__(self, time):
            self.time = time
    
        def time_str(self):
            return datetime.time(hour=self.time // 60, minute=self.time % 60).strftime("%H:%M")
    
        def id(self):
            return self.time//15

        def next_entry(self):
            return AvailableEntries.AvailableEntry(self.time + 15)

    def __init__(self, times=[]):
        self.entries = []
        for time in times:
            self.add_entry(time)

    def config_value(self):
        times = []
        for entry in self.entries:
            times.append(entry.time)
        return times

    def add_entry(self, time):
        self.entries.append(self.AvailableEntry(time))

    def get_start_times(self):
        required_len = MinimalTimeSlot // 15
        result = []
        for i in range(len(self.entries)):
            if i + required_len <= len(self.entries) and self.entries[i].id() + required_len - 1 == self.entries[i + required_len - 1].id():
                result.append(self.entries[i].time_str())
        return result

    def get_slots(self):
        required_len = MinimalTimeSlot // 15
        result = []
        start = 0
        while start < len(self.entries):
            end = start
            while end + 1 < len(self.entries) and self.entries[end].id() + 1 == self.entries[end + 1].id():
                end += 1
            if end - start + 1 >= required_len:
                result.append((self.entries[start], self.entries[end].next_entry()))
            start = end + 1
            
        return result

def get_available_entries(hall, date):
    img_size = (566, 26)
    def get_schedule_pixels():
        start = 7*60 + 38
        end = 23*60 + 22
        total = end - start
        
        time = 8*60 + 7
        last_time = 23*60
        while time < last_time:
            pixel_x = ((time - start) / total) * img_size[0]
            yield (int(pixel_x), 11), time - 7
            time += 15

    def color_to_available(color):
        def equal(lhs, rhs):
            dist = abs(rhs[0] - lhs[0]) + abs(rhs[1] - lhs[1]) + abs(rhs[2] - lhs[2])
            return dist < 10

        available = (255, 255, 255)
        available_school_holiday = (217, 224, 255)
        return equal(color, available) or equal(color, available_school_holiday)

    id = HallToId[hall]
    response = requests.get(get_schedule_url(id, date))
    result = AvailableEntries()
    
    if response.status_code != 200:
        print("Failed to download image. Status code:", response.status_code, flush=True)
        return result

    img = Image.open(BytesIO(response.content))
    img = img.convert("RGB")
    assert img.size == img_size

    for pixel, time in get_schedule_pixels():
        if color_to_available(img.getpixel(pixel)):
            result.add_entry(time)

    return result
