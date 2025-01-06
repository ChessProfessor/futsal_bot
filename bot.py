import telebot
from website import HallToId, get_available_entries, AvailableEntries
import datetime
import os
import data

MAX_AVAILABLE_DAYS = 100

def get_key():
    api_key = os.getenv("FUTSAL_BOT_API_KEY")
    
    if api_key is None:
        raise EnvironmentError(f"Environment variable FUTSAL_BOT_API_KEY is not set.")

    return api_key

def get_bot():
    return telebot.TeleBot(get_key())

bot = get_bot()

def try_parse_date(date_string, date_format):
    try:
        parsed_date = datetime.datetime.strptime(date_string, date_format)
        return True, parsed_date
    except ValueError:
        return False, None

@bot.message_handler(commands=['help'])
def help(message):
    reply_message = """
/help - for help
/schedule %d-%m-%Y - schedule for particular day
/available N - all available slots for the next N days
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
        available_slots = available_entries.get_slots(every=True)
        slots_strings = list(map(lambda x: f"{x[0].time_str()}-{x[1].time_str()}", available_slots))
        reply_message += f"Available slots for {hall}: {slots_strings}\n"
    bot.reply_to(message, reply_message)

@bot.message_handler(commands=['available'])
def available(message):
    text = message.text[len("/available "):]
    try:
        days = int(text)
    except ValueError:
        print("Invalid input, number of days is required")
        return
    if days > MAX_AVAILABLE_DAYS:
        print(f"Invalid input, number of days should be less than {MAX_AVAILABLE_DAYS}")
        return

    reply_messages = []
    reply_message = ""
    today = datetime.date.today()
    for i in range(days):
        day = today + datetime.timedelta(days=i)
        if day.weekday() >= 5:
            # skip weekends
            continue
        for hall, id in HallToId.items():
            schedule = data.get_schedule(hall, day)
            if schedule is None:
                continue
            available_entries = AvailableEntries(schedule)
            start_times = available_entries.get_start_times()
            if len(start_times) > 0:
                available_slots = available_entries.get_slots()
                slots_strings = list(map(lambda x: f"{x[0].time_str()}-{x[1].time_str()}", available_slots))
                day_str = day.strftime("%a, %d-%m-%Y")
                current_message = f"{hall} on {day_str}: {slots_strings}\n"
                if len(reply_message) + len(current_message) > 4096:
                    reply_messages.append(reply_message)
                    reply_message = current_message
                else:
                    reply_message += current_message
    if len(reply_message) > 0:
        reply_messages.append(reply_message)
    if len(reply_messages) == 0:
        reply_messages.append("No available slots in the given period")
    for reply_message in reply_messages:
        bot.reply_to(message, reply_message)

if __name__ == "__main__":
    bot.infinity_polling()
