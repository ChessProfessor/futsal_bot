from website import HallToId, get_available_entries, AvailableEntries, MinimalTimeSlot
from bot import get_bot
import datetime
import time
import data

DAYS_TO_MONITOR = 90

def monitor():
    chat_ids = ['-4632050646']
    bot = get_bot()
    today = datetime.date.today()
    for i in range(DAYS_TO_MONITOR):
        day = today + datetime.timedelta(days=i)
        for hall, id in HallToId.items():
            current_schedule = data.get_schedule(hall, day)
            new_available_entries = get_available_entries(hall, day)

            if current_schedule is not None and day.weekday() < 5:
                current_available_entries = AvailableEntries(current_schedule)
                current_start_times = current_available_entries.get_start_times()
                new_start_times = new_available_entries.get_start_times()
                times_to_notify = sorted(list(set(new_start_times) - set(current_start_times)))
                if len(times_to_notify) != 0:
                    new_available_slots = new_available_entries.get_slots()
                    slots_strings = list(map(lambda x: f"{x[0].time_str()}-{x[1].time_str()}", new_available_slots))
                    day_str = day.strftime("%a, %d-%m-%Y")
                    message = f"New time slots available for {hall} on {day_str}: {slots_strings}"
                    for chat_id in chat_ids:
                        bot.send_message(chat_id, message)
            
            data.update_schedule(hall, day, new_available_entries.config_value())
            time.sleep(2)

if __name__ == "__main__":
    monitor()