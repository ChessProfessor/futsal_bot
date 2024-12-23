import telebot
from website import HallToId, get_available_entries, AvailableEntries, MinimalTimeSlot
import datetime
import time
import data
import os

def get_key():
    api_key = os.getenv("FUTSAL_BOT_API_KEY")
    
    if api_key is None:
        raise EnvironmentError(f"Environment variable FUTSAL_BOT_API_KEY is not set.")

    return api_key

DAYS_TO_MONITOR = 90

def try_parse_date(date_string, date_format):
    try:
        parsed_date = datetime.datetime.strptime(date_string, date_format)
        return True, parsed_date
    except ValueError:
        return False, None

bot = telebot.TeleBot(get_key())

@bot.message_handler(commands=['help'])
def help(message):
    reply_message = """
/help - for help
/schedule %d-%m-%Y - schedule for particular day
    """
    bot.reply_to(message, reply_message)

@bot.message_handler(commands=['schedule'])
def schedule(message):
    text = message.text[len("/schedule "):]
    date_format = "%d-%m-%Y"
    is_valid, parsed_date = try_parse_date(text, date_format)
    if not is_valid:
        bot.reply_to(message, f"Your date is in incorrect format, expected format is {date_format}.")
        return

    reply_message = ""
    for hall, id in HallToId.items():
        available_entries = get_available_entries(hall, parsed_date)
        available_slots = available_entries.get_slots()
        slots_strings = list(map(lambda x: f"{x[0].time_str()}-{x[1].time_str()}", available_slots))
        reply_message += f"Available slots for {hall}: {slots_strings}\n"
    bot.reply_to(message, reply_message)

def monitor():
    chat_ids = ['420051874', '-4632050646']
    while True:
        today = datetime.date.today()
        for i in range(DAYS_TO_MONITOR):
            day = today + datetime.timedelta(days=i)
            for hall, id in HallToId.items():
                current_schedule = data.get_schedule(hall, day)
                new_available_entries = get_available_entries(hall, day)

                if current_schedule is not None:
                    current_available_entries = AvailableEntries(current_schedule)
                    current_start_times = current_available_entries.get_start_times()
                    new_start_times = new_available_entries.get_start_times()
                    times_to_notify = list(set(new_start_times) - set(current_start_times))
                    if len(times_to_notify) != 0:
                        day_str = day.strftime("%d-%m-%Y")
                        message = f"New time slots available for {hall} on {day_str} for {MinimalTimeSlot} minutes: {times_to_notify}"
                        for chat_id in chat_ids:
                            bot.send_message(chat_id, message)
                
                data.update_schedule(hall, day, new_available_entries.config_value())
                time.sleep(2)
        bot.send_message("420051874", "Full cycle is checked, sleep for 10 min")
        time.sleep(10*60)
