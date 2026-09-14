import datetime
import json
import os


STALE_DATA_DAYS = 7


def get_stale_data_warning():
    today_file = f"data/{datetime.date.today().strftime('%Y%m%d')}.json"
    try:
        last_updated_timestamp = os.path.getmtime(today_file)
    except OSError:
        return "⚠️ Cached availability data has not been updated."

    age = datetime.datetime.now().timestamp() - last_updated_timestamp
    if age <= datetime.timedelta(days=STALE_DATA_DAYS).total_seconds():
        return None

    last_updated = datetime.datetime.fromtimestamp(last_updated_timestamp)
    return (
        f"⚠️ Cached availability data is over {STALE_DATA_DAYS} days old "
        f"(last update: {last_updated.strftime('%d-%m-%Y')})."
    )

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
