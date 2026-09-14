from website import HallToId, get_available_entries, AvailableEntries, MinimalTimeSlot
from bot import get_bot, MAX_AVAILABLE_DAYS
import datetime
import random
import time
import data

DAYS_TO_MONITOR = MAX_AVAILABLE_DAYS
DAYS_TO_REPORT = 90
NOTIFICATION_CHAT_IDS = ['-4632050646']
CELEBRATION_MESSAGES = (
    "🚨 Cancel your fake plans—a slot opened!",
    "⚽ The pitch has chosen you!",
    "🔥 Warm up those suspicious hamstrings!",
    "🎉 A slot escaped the booking system!",
    "🙌 Summon the group chat!",
    "✨ The calendar gods have blinked!",
    "👀 A free pitch in Amsterdam? Miracles happen!",
    "🎊 The football gods demand five-a-side!",
    "🪄 A wild futsal slot appeared!",
    "📺 VAR checked your excuses: rejected!",
    "🧤 Tell the keeper their evening is ruined!",
)
DE_PIJP_HALLS = {
    "Sports centre De Pijp Hall 1",
    "Sports centre De Pijp Hall 2",
}
SPORTS_HALLS_SOUTH = {
    "Sports halls South 1A (front)",
    "Sports halls South 1B (back)",
    "Sports halls South 3",
}
DE_PIJP_JOKES = (
    "🍟 Play for the badge. Stay for the De Pijp fries.",
)
SPORTS_HALLS_SOUTH_JOKES = (
    "🍺 Tactical debrief at the nearby hotel afterward. Strictly professional.",
    "🏨 The nearby hotel bar is preparing for the third half.",
)


def get_celebration_messages(hall):
    if hall in DE_PIJP_HALLS:
        return CELEBRATION_MESSAGES + DE_PIJP_JOKES
    if hall in SPORTS_HALLS_SOUTH:
        return CELEBRATION_MESSAGES + SPORTS_HALLS_SOUTH_JOKES
    return CELEBRATION_MESSAGES


def build_new_slot_message(hall, day, slots_string):
    intro = random.choice(get_celebration_messages(hall))

    return (
        f"{intro}\n\n"
        f"{hall}\n"
        f"{day.strftime('%a, %d-%m-%Y')}\n"
        f"{slots_string}"
    )


def notify_stale_data_once(bot, warning, today):
    if warning is None or data.stale_notification_was_sent_today(today):
        return

    for chat_id in NOTIFICATION_CHAT_IDS:
        bot.send_message(chat_id, warning)
    data.mark_stale_notification_sent(today)


def monitor():
    bot = get_bot()
    today = datetime.date.today()
    stale_data_warning = data.get_stale_data_warning(today)
    for i in range(DAYS_TO_MONITOR):
        day = today + datetime.timedelta(days=i)
        for hall, id in HallToId.items():
            current_schedule = data.get_schedule(hall, day)
            new_available_entries = get_available_entries(hall, day)

            if i < DAYS_TO_REPORT and current_schedule is not None and day.weekday() < 5:
                current_available_entries = AvailableEntries(current_schedule)
                current_start_times = current_available_entries.get_start_times()
                new_start_times = new_available_entries.get_start_times()
                times_to_notify = sorted(list(set(new_start_times) - set(current_start_times)))
                if len(times_to_notify) != 0:
                    new_available_slots = new_available_entries.get_slots()
                    slots_string = ", ".join(
                        f"{start.time_str()}–{end.time_str()}"
                        for start, end in new_available_slots
                    )
                    message = build_new_slot_message(hall, day, slots_string)
                    for chat_id in NOTIFICATION_CHAT_IDS:
                        bot.send_message(chat_id, message)
            
            data.update_schedule(hall, day, new_available_entries.config_value())
            time.sleep(2)

    notify_stale_data_once(bot, stale_data_warning, today)

if __name__ == "__main__":
    monitor()
