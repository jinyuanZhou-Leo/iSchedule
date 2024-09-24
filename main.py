#!/usr/bin/env python3
# coding=utf-8

import os
import sys
from loguru import logger
from tqdm import tqdm, trange
from pathlib import Path
from datetime import datetime
from utils import *
from data import Location, Term, Course, generateICS

VERSION = "2.0"

logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), format="{level}: <level>{message}</level>", level="INFO", colorize=True)
logger.info(f"iSchedule {VERSION}")

# read files
config: dict = loadJSON(Path.cwd() / "config.json")  # Program configuration
schedulePath: Path = Path.cwd() / "schedule.json"
if not os.path.exists(
    schedulePath
):  # schedule file with default file name is not found
    tmp: str = input("ENTER the schedule file path: ").strip()
    if (tmp.startswith("'") and tmp.endswith("'")) or (
        tmp.startswith('"') and tmp.endswith('"')
    ):
        tmp = tmp[1:-1]  # remove quotes
    schedulePath = Path(tmp)
schedule: dict = loadJSON(schedulePath)

# parse schedule file into objects
terms: list[Term] = []
for termName, termData in schedule.items():
    tmp: Term = Term(
        name = termName,
        start = datetime(*termData["start"]),
        end = datetime(*termData["end"]),
        duration = termData["duration"],
        timetable = termData["timetable"],
        cycle = termData["cycle"],
    )
    terms.append(tmp)
    for courseName, courseData in termData["courses"].items():
        # Term.addCourse() will automatically set the cycle to the course's cycle if it is provided
        courseCycle: int | None = None 
        courseLocation:str| Location | None
        if courseData.get("cycle") is not None:
            logger.warning(f"Exceptional cycle \"{courseData["cycle"]}\" is provided in \"{termName}.{courseName}\" and this will OVERRIDE the default cycle. If you see this warning UNKNOWINGLY, please remove the \"cycle\" field under \"{termName}.courses.{courseName}\"")
            
            courseCycle = int(courseData["cycle"])
        if courseData.get("location"):
            if isinstance(courseData["location"], tuple) or isinstance(courseData["location"], list):
                courseLocation = Location(*courseData["location"])
            elif isinstance(courseData["location"], str):
                courseLocation = Location(name=courseData["location"])
            else:
                logger.warning(f"Empty location is provided in \"{termName}.{courseName}\"")
                courseLocation = None

        tmp.addCourse(
            Course(
                name = courseName,
                teacher = courseData["teacher"],
                location = courseLocation,
                index = courseData["index"],
                cycle = courseCycle,
            )
        )

print("\n")

# parse config file
config["name"] = (
    config["name"]
    if config["name"] != ""
    else f"Schedule-{datetime.now().strftime('%X-%Y.%m.%d')}"
)


for i in trange(len(terms), desc="Total: "):
    ics = generateICS(terms[i], config)
    try:
        with open(f"{config['name']} - {terms[i].name}.ics", "wb") as f:
            f.write(ics)
    except Exception as e:
        logger.error(
            f"[{i+1} of {len(terms)}] Failed to generate ICS file - {config["name"]} - {terms[i].name}.ics"
        )
        if isinstance(e,IOError):
            logger.critical(f"{e}: Permission denied, Try re-run the program by using 'sudo'.")
        else:
            logger.critical(f"Unknown error occurred while creating file.")
        exit(0)
    else:
        logger.success(
            f"[{i+1} of {len(terms)}] Successfully generated ICS file - {config["name"]} - {terms[i].name}.ics"
        )

print("\n")
logger.info("To import the ICS file, drag the generated ICS file into your calendar app")
