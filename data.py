#!/usr/bin/env python3
# coding=utf-8

import itertools, uuid, pytz
import icalendar as ic
from loguru import logger
from datetime import datetime, time, timedelta
from utils import *


class Location:
    name: str
    latitude: float | str
    longitude: float | str

    def __init__(self, name="", latitude=0, longitute=0) -> None:
        self.name = name
        self.latitude = latitude
        self.longitude = longitute

    def __str__(self) -> str:
        if self.name == "" and self.latitude == 0 and self.longitude == 0:
            return f"Empty Location Instance <{id(self)}>"
        else:
            return f"[{self.name}]: ({self.latitude}, {self.longitude})"


class Holiday:
    name: str
    type: str
    start: datetime
    end: datetime
    compensations: list[list[datetime, int]]

    def __init__(
        self,
        name: str,
        type: str,
        date: list[datetime | int] | list[int | str],
        compensations: list[list[datetime, int]] | None,
    ) -> None:
        self.name = name
        self.type = type.lower()
        self.compensations = compensations if compensations else []
        if self.type == "fixed":
            if not 0 < len(date) <= 2:  # (0,2]
                logger.error(f"Invalid date list length: {len(date)}, should be 1 or 2")
                exit(0)
                # TODO: work around to see if there is a solution to resolve the error without exit the program
            elif len(date) == 1:
                date.append(date[0])

        elif self.type == "relative":
            raise NotImplementedError("Relative holiday not implemented yet")
            ordinal = date[0][:1]
            weekNum = date[0][1:]

        else:
            logger.critical(
                f"Invalid holiday type: {self.name}: type={repr(self.type)}. Holiday should either be 'fixed' or 'relative'."
            )
            exit(0)

        # if the holiday is a single-day holiday
        # The start and end time of this holiday would be the same day
        self.start, self.end = date[0], date[1]

    def __str__(self) -> str:
        return f"Holiday - {self.name}:\n   Type: {self.type}\n   Compensation: {self.compensations}"


class Term:
    name: str
    uuid: str
    start: datetime
    end: datetime
    duration: int
    timetable: list[list[int, int]]
    cycle: int
    courses: list["Course"]
    holidays: list["Holiday"]

    def __init__(
        self,
        name: str,
        start: datetime,
        end: datetime,
        duration: int,
        timetable: list[list[int]],
        cycle: int,
    ) -> None:
        self.name = name
        self.start, self.end = start, end
        self.duration = duration
        self.timetable = timetable

        if cycle <= 0 or not isinstance(cycle, int):
            logger.critical(
                f'Invalid global cycle number "{cycle}" for "{self.name}", global cycle number should be positive integer'
            )
            exit(0)
        else:
            self.cycle = cycle

        self.courses = []
        self.holidays = []
        self.uuid = str(uuid.uuid4())

    def addCourse(self, course: "Course") -> None:
        course.setCycle(self.cycle)  # set the cycle number of the course instance
        self.courses.append(course)  # add course instance into the term instance

    def addHoliday(self, holiday: Holiday) -> None:
        self.holidays.append(holiday)

    def isHoliday(self, date: datetime) -> bool:
        for holiday in self.holidays:
            if holiday.start <= date <= holiday.end:
                return True
        return False

    def __str__(self) -> str:
        return f"Term - {self.uuid}:\n   Name: {self.name}\n   Start: {self.start}\n   End: {self.end}\n   Class Duration: {self.duration} minutes\n   Timetable: {self.timetable}\n   Cycle: {self.cycle}"


class Course:
    name: str
    teacher: str
    location: Location
    index: list[list[any]]
    cycle: int

    def __init__(
        self,
        name: str,
        teacher: str,
        location: Location,
        index: list[list[any]],
        cycle: int | None,
    ) -> None:
        self.name = name
        self.teacher = teacher
        self.location = location
        self.index = index
        self.cycle = cycle

    def setCycle(self, cycle: int) -> None:
        if self.cycle == None:  # If exceptional cycle is not set
            self.cycle = cycle  # Apply global setting
        else:  # If exceptional cycle is set
            if self.cycle <= 0:
                logger.error(
                    f'Invalid cycle number "{cycle}" in {self.name}, It should be positive integer. Program will try to use the global cycle setting.'
                )
                self.cycle = cycle  # Rollback to global setting

    def getCycleDay(self) -> int:
        return self.cycle * 5

    def getDecodedIndex(self, term: Term) -> list[list[int]]:

        def decode_component(component: list | str | int, maximum: int):
            """
            Decode a component of a schedule.

            This function decodes a given component into a list of corresponding numbers based on the predefined dictionary.
            The component can be an integer, a string abbreviation, or a list containing integers and string abbreviations.

            Parameters:
            - component: The component to be decoded, can be an integer, a string, or a list.
            - maximum: The maximum value that the component can represent.

            Returns:
            - Returns a list of decoded numbers corresponding to the input component.
            """
            # Define a dictionary for different types of abbreviations, mapping to the corresponding number list
            abbrDict = {
                "odd": [i for i in range(1, maximum + 1, 2)],  # List of odd days
                "even": [i for i in range(2, maximum + 1, 2)],  # List of even days
                "everyday": [i for i in range(1, maximum + 1)],  # List of all days
            }

            # If the component is an integer, check if it is within the valid range
            if isinstance(component, int):
                if component > self.getCycleDay() or component < 1:
                    logger.critical(
                        f'Invalid schedule file, Error processing "{term.name}.{self.name}.time", {component} is out of range'
                    )
                    exit(0)
                return [component]

            # If the component is a string abbreviation, convert it to the corresponding number list
            elif isinstance(component, str):
                return abbrDict[component.lower()]

            # If the component is a list, process each item in the list
            elif isinstance(component, list):
                tmp = []
                for item in component:
                    if isinstance(item, int):
                        tmp.append(item)
                    elif isinstance(item, str):
                        tmp.extend(abbrDict[item.lower()])
                    else:
                        logger.critical(
                            f"Invalid schedule file, Error processing {term.name}.{self.name}.time, {item} can not be indentified"
                        )
                        exit(0)
                return tmp

            # If the component is of an unsupported type, output an error message and exit
            else:
                logger.critical(
                    f"Invalid schedule file, Error processing {term.name}.{self.name}.time, {component} can not be indentified"
                )
                exit(0)

        product = []
        for timestamp in self.index:  # [1,2], ["odd",3]
            # 求decodeTimestamp笛卡尔积
            product.extend(
                [
                    list(t)
                    for t in itertools.product(
                        [x for x in decode_component(timestamp[0], self.cycle * 5)],
                        [
                            x - 1
                            for x in decode_component(timestamp[1], len(term.timetable))
                        ],
                    )
                ]
            )
        # return mergeFirstItem(product)
        return product

    def eventify(
        self, term: Term, date: datetime, block: int, reminderSetting: dict
    ) -> ic.Event:
        event: ic.Event = ic.Event()
        event.add("summary", self.name)
        event.add(
            "description", f"{self.teacher}\n{self.location.name}"
        )  # TODO: work around to provide better support for Location and AppleMapLocation
        event.add(
            "dtstart",
            datetime.combine(
                date,
                time(
                    term.timetable[block][0],
                    term.timetable[block][1],
                ),
            ),
        )
        event.add(
            "dtend",
            datetime.combine(
                date,
                time(
                    term.timetable[block][0],
                    term.timetable[block][1],
                ),
            )
            + timedelta(minutes=term.duration),
        )
        event.add("dtstamp", datetime.now())
        event.add("uid", uuid.uuid4())

        if reminderSetting["enabled"] == True:
            reminder: ic.Alarm = ic.Alarm()
            reminder.add("ACTION", "DISPLAY")
            reminder.add("DESCRIPTION", "提醒事项")
            reminder.add(
                "TRIGGER",
                timedelta(
                    hours=-reminderSetting["before"][0],
                    minutes=-reminderSetting["before"][1],
                ),
            )
            event.add_component(reminder)

        return event


@timer
def generateICS(term: Term, config: dict) -> bytes:
    ics: ic.Calendar = ic.Calendar()
    ics.add("VERSION", "2.0")
    ics.add("PRODID", "iScheduler by @Jinyuan")
    ics.add("CALSCALE", "GREGORIAN")
    ics.add("X-APPLE-CALENDAR-COLOR", parseHexColor(config["color"]))
    ics.add("X-WR-CALNAME", f"{config['name']} - {term.name}")
    ics.add("X-WR-TIMEZONE", "Asia/Shanghai")  # TODO: add time zone support

    # If there are holidays, the rrule strategy is not gonna work effectively though
    if term.holidays:
        logger.debug("Using Date Range Strategy")
        for course in term.courses:  # iterate through all courses
            cnt: int = 0  # day counter
            timetable: list[list[int]] = course.getDecodedIndex(term)
            for date in dateRange(term.start, term.end):  # iterate through the term
                if date.weekday() < 5:
                    # if the day is a workday
                    if cnt >= course.getCycleDay():
                        # if the day counter overflow, reset the counter
                        cnt = 0
                    if not term.isHoliday(date):
                        # if the day is both a workday and non-holiday
                        for timestamp in timetable:
                            if timestamp[0] - 1 == cnt:
                                event: ic.Event = course.eventify(
                                    term, date, timestamp[1], config["alarm"]
                                )

                                ics.add_component(event)
                        cnt += 1
                    else:  # workday but holiday
                        if config["countDayInHoliday"] == True:
                            cnt += 1

            for holiday in term.holidays:
                for compensation in holiday.compensations:
                    for timestamp in timetable:
                        if timestamp[0] == compensation[1]:
                            event = course.eventify(
                                term, compensation[0], timestamp[1], config["alarm"]
                            )
                            ics.add_component(event)

    # Else, use rrule strategy to reduce the file size and increase the performance
    else:
        logger.debug("Using RRule Strategy")
        initDay: datetime = term.start - timedelta(days=term.start.weekday())
        for course in term.courses:
            timetable = course.getDecodedIndex(term)
            for timestamp in timetable:
                weekInfo: list[int] = getWeekInfo(timestamp[0])
                event: ic.Event = course.eventify(
                    term,
                    initDay + timedelta(weeks=weekInfo[1], days=weekInfo[0] - 1),
                    timestamp[1],
                    config["alarm"],
                )
                rrule = ic.vRecur(
                    freq="weekly",
                    interval=course.cycle,
                    byday=day2str(weekInfo[0]),
                    until=term.end,
                )  # TODO: work around, try to merge some rrule which are in the same week
                logger.debug(f"Adding {course.name} with rrule:{rrule}")
                event.add("RRULE", rrule)
                ics.add_component(event)

    return ics.to_ical()

if __name__ == "__main__":
    logger.warning("This module cannot run independently")
