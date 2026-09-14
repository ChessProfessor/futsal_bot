import datetime
import os

import telebot

import data
from website import HallToId, get_available_entries, AvailableEntries

DATE_FORMAT = "%d-%m-%Y"
MAX_AVAILABLE_DAYS = 150
TELEGRAM_MESSAGE_LIMIT = 4096
AVAILABLE_USAGE = (
    "Usage:\n"
    "/available END_DATE\n"
    "/available START_DATE END_DATE\n"
    "Dates must use DD-MM-YYYY."
)
HELP_MESSAGE = """
/help - show this help
/schedule DD-MM-YYYY - schedule for a particular day
/available END_DATE - available weekday slots from today through END_DATE
/available START_DATE END_DATE - available weekday slots in an inclusive date range

Dates must use DD-MM-YYYY. Both start and end dates are included.
"""


class AvailableRangeError(ValueError):
    pass

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


def parse_date(date_string):
    is_valid, parsed_date = try_parse_date(date_string, DATE_FORMAT)
    if not is_valid or parsed_date.strftime(DATE_FORMAT) != date_string:
        raise AvailableRangeError(
            f"Invalid date '{date_string}'. Dates must use DD-MM-YYYY."
        )
    return parsed_date.date()


def parse_available_range(arguments, today=None):
    if today is None:
        today = datetime.date.today()

    parts = arguments.split()
    if len(parts) == 1:
        start_date = today
        end_date = parse_date(parts[0])
    elif len(parts) == 2:
        start_date = parse_date(parts[0])
        end_date = parse_date(parts[1])
    else:
        raise AvailableRangeError(AVAILABLE_USAGE)

    if start_date > end_date:
        raise AvailableRangeError("Start date cannot be after end date.")
    if start_date < today:
        raise AvailableRangeError("Dates in the past are not supported.")

    last_available_date = today + datetime.timedelta(days=MAX_AVAILABLE_DAYS - 1)
    if end_date > last_available_date:
        raise AvailableRangeError(
            "Availability can only be requested through "
            f"{last_available_date.strftime(DATE_FORMAT)}."
        )

    return start_date, end_date


def build_available_messages(start_date, end_date):
    header = (
        "⚽ Available slots\n"
        f"🗓 {start_date.strftime(DATE_FORMAT)} – {end_date.strftime(DATE_FORMAT)}"
    )
    date_blocks = []
    number_of_days = (end_date - start_date).days + 1

    for offset in range(number_of_days):
        day = start_date + datetime.timedelta(days=offset)
        if day.weekday() >= 5:
            continue

        hall_lines = []
        for hall in HallToId:
            schedule = data.get_schedule(hall, day)
            if schedule is None:
                continue

            available_entries = AvailableEntries(schedule)
            available_slots = available_entries.get_slots()
            if not available_slots:
                continue

            slots_string = ", ".join(
                f"{start.time_str()}–{end.time_str()}"
                for start, end in available_slots
            )
            hall_lines.append(f"⚽ {hall}\n⏰ {slots_string}")

        if hall_lines:
            date_blocks.append(
                f"🗓 {day.strftime('%a, %d-%m-%Y')}\n" + "\n\n".join(hall_lines)
            )

    if not date_blocks:
        return [f"{header}\n\n😴 No available slots in the given period."]

    messages = []
    current_message = header
    for date_block in date_blocks:
        candidate = f"{current_message}\n\n{date_block}"
        if len(candidate) <= TELEGRAM_MESSAGE_LIMIT:
            current_message = candidate
        else:
            messages.append(current_message)
            current_message = f"{header}\n\n{date_block}"
    messages.append(current_message)
    return messages


def reply_with_messages(message, reply_messages):
    if isinstance(reply_messages, str):
        reply_messages = [reply_messages]
    else:
        reply_messages = list(reply_messages)

    for reply_message in reply_messages:
        bot.reply_to(message, reply_message)


@bot.message_handler(commands=['help'])
def help(message):
    reply_with_messages(message, HELP_MESSAGE)

@bot.message_handler(commands=['schedule'])
def schedule(message):
    text = message.text[len("/schedule "):]
    is_valid, parsed_date = try_parse_date(text, DATE_FORMAT)
    if not is_valid:
        reply_with_messages(
            message,
            f"Your date is in incorrect format, expected format is {DATE_FORMAT}.",
        )
        return

    hall_blocks = []
    for hall, id in HallToId.items():
        available_entries = get_available_entries(hall, parsed_date)
        available_slots = available_entries.get_slots(every=True)
        slots_string = ", ".join(
            f"{start.time_str()}–{end.time_str()}"
            for start, end in available_slots
        ) or "No available slots"
        hall_blocks.append(f"⚽ {hall}\n⏰ {slots_string}")
    reply_message = (
        f"🗓 {parsed_date.strftime('%a, %d-%m-%Y')}\n\n"
        + "\n\n".join(hall_blocks)
    )
    reply_with_messages(message, reply_message)

@bot.message_handler(commands=['available'])
def available(message):
    command_parts = message.text.split(maxsplit=1)
    arguments = command_parts[1] if len(command_parts) == 2 else ""

    try:
        start_date, end_date = parse_available_range(arguments)
    except AvailableRangeError as error:
        error_message = str(error)
        if error_message != AVAILABLE_USAGE:
            error_message = f"{error_message}\n\n{AVAILABLE_USAGE}"
        reply_with_messages(message, error_message)
        return

    reply_with_messages(
        message,
        build_available_messages(start_date, end_date),
    )

if __name__ == "__main__":
    bot.infinity_polling()
