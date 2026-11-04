from datetime import time, timezone, timedelta

JST = timezone(timedelta(hours=9))

TIME_SLOTS = {
    1: (time(8, 50), time(10, 30)),
    2: (time(10, 40), time(12, 20)),
    3: (time(12, 20), time(13, 10)),
    4: (time(13, 10), time(14, 50)),
    5: (time(15, 5), time(16, 45)),
    6: (time(17, 0), time(18, 40)),
    7: (time(18, 55), time(20, 35))
}

def get_slot_id(start_time: time, end_time: time) -> int | None:
    for slot_id, (start, end) in TIME_SLOTS.items():
        if start_time == start and end_time == end:
            return slot_id
    return None

if __name__ == "__main__":
    print(get_slot_id(time(8, 50), time(10, 30)))
    print(get_slot_id(time(12, 20), time(13, 10)))
    print(get_slot_id(time(9, 0), time(10, 30)))