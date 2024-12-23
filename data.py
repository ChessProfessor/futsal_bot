import json
import os

def get_schedule(hall, date):
    file_name = f"data/{date.strftime('%Y%m%d')}.json"
    if not os.path.exists(file_name):
        return None

    with open(file_name, "r") as file:
        data = json.load(file)

    return data.get(hall, None)

def update_schedule(hall, date, times):
    file_name = f"data/{date.strftime('%Y%m%d')}.json"
    
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            data = json.load(file)
    else:
        data = {}

    data[hall] = times
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)

    print(f"Schedule updated for {hall} on {date.strftime('%Y-%m-%d')}.", flush=True)
