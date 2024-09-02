from datetime import date, time, datetime, timedelta
from data import Course, Term
import icalendar as ic


def generateICS(term, courseList, name, color, minutesBefore=0):
    schedule = ic.Calendar()
    schedule.add("VERSION", "2.0")
    schedule.add("PRODID", "iScheduler")
    schedule.add("CALSCALE", "GREGORIAN")
    schedule.add("X-APPLE-CALENDAR-COLOR", color)
    schedule.add("X-WR-CALNAME", name)  # 日历名称
    schedule.add("X-WR-TIMEZONE", "Asia/Shanghai")

    for day in dateRange(term.start, term.end):
        if day.weekday() < 5:  # 假设周末（星期六和星期日）为非工作日
            for course in courseList:
                # print(course)
                block = course.getBlock(day.weekday())
                if block < len(term.classStartingTime) and block >= 0:
                    # print("selected")
                    lesson = ic.Event()
                    lesson.add("summary", course.name)  # 事件名称
                    lesson.add(
                        "description", f"{course.teacher}\n{course.room}"
                    )  # 事件描述

                    lesson.add(
                        "dtstart",
                        datetime.combine(
                            day,
                            time(
                                term.classStartingTime[block][0],
                                term.classStartingTime[block][1],
                            ),
                        ),
                    )  # 开始时间
                    lesson.add(
                        "dtend",
                        datetime.combine(
                            day,
                            time(
                                term.classStartingTime[block][0],
                                term.classStartingTime[block][1],
                            ),
                        )
                        + timedelta(minutes=term.classDuration),
                    )  # 结束时间

                    if minutesBefore:
                        alarm = ic.Alarm()
                        alarm.add("ACTION", "DISPLAY")
                        alarm.add("DESCRIPTION", "提醒事项")
                        alarm.add("TRIGGER", timedelta(minutes=-minutesBefore))
                        lesson.add_component(alarm)

                    schedule.add_component(lesson)

    fileName = name + ".ics"
    with open(fileName, "wb") as file:
        file.write(schedule.to_ical())
        return True


def dateRange(start, end):
    for n in range(int((end - start).days) + 1):
        yield start + timedelta(n)
