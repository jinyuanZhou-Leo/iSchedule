import json
import logging
import random
from colorama import init,Fore, Back, Style
from pathlib import Path
from data import Course, Term
from generator import generateICS
from datetime import datetime

def getRandomHexColor():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

VERSION = 1.2

#initialize

#initialize logging
logger = logging.getLogger("main")
logger.setLevel(level=logging.INFO)

formatter = logging.Formatter('%(levelname)s - %(message)s')
stream_handler = logging.StreamHandler() # for logging in CLI
stream_handler.setLevel(level = logging.INFO) # log level
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger.info("iScheduler "+str(VERSION))
logger.info("Current Path: "+ str(Path.cwd()))

#initialize colorama
#init(autoreset=True)


# parsing config
currentPath = str(Path.cwd())
configPath = Path(currentPath+"/config.json")

config = {}
if configPath.is_file(): #如果存在配置文件
    with configPath.open() as file:
        config = json.load(file)
        logger.debug("Config.json is successfully parsed")
else: #配置文件不存在
    logger.error("No such file dictionary, Cannot find Config.json")
    config["defaultFileName"] = "schedule.json"



# look for schedule file
schedulePath = Path(currentPath+"/"+config["defaultFileName"])
schedule = {}
if schedulePath.is_file():
    with schedulePath.open() as file:
        schedule = json.load(file)
        logger.info("Schedule is successfully parsed")
else:
    while True:
        logger.error(f"{config["defaultFileName"]} could not be found, please enter the path of schedule")
        schedulePathTmp = input("Please enter the schedule file path: ")
        #TODO:处理文件名被"或者‘包裹的情况
        schedulePath = Path(schedulePathTmp)
        if schedulePath.is_file():
            with schedulePath.open() as file:
                schedule = json.load(file)
                logger.info("Schedule is successfully parsed")
                break


# schedule parser

term = Term(schedule["Term"]["start"],schedule["Term"]["end"], schedule["Term"]["classDuration"], schedule["Term"]["classInfo"])
courses = []
for c in schedule["Courses"]:
    courses.append(Course(c,schedule["Courses"][c]["teacher"],schedule["Courses"][c]["time"],schedule["Courses"][c]["room"]))
    
logger.debug("Schedule is successfully objectified")

# customizations
scheduleColor = config["color"]
while True:
    tmpColor = input(f"Please enter the color of your schedule in HEX format (ENTER for using default setting - {scheduleColor}):")
    if tmpColor=="":
        break
    elif tmpColor.lower() == "random":
        scheduleColor = getRandomHexColor()
        break
    else:
        if tmpColor.startswith("#") and len(tmpColor) == 7:
            scheduleColor = tmpColor
            break
        else:
            logger.error(f"Invalid HEX color format - \"{tmpColor}\", Example: #FF50FF")
            continue


if "Name" not in schedule:
    logger.error("Schedule file does not have a name")
    tmpName = input("Please enter the schedule name (Enter for using default setting):")
    if tmpName == "":
        scheduleName = f"Schedule-{datetime.now().strftime('%X-%Y.%m.%d')}"
    else:
        scheduleName = tmpName
else:
    scheduleName = schedule["Name"]

minutesBefore = 0
if config["alarm"]["enabled"] == True:
    minutesBefore = int(config["alarm"]["minutesBefore"])


status = generateICS(term, courses, scheduleName, scheduleColor,minutesBefore)
if status:
    logger.info(f"Successfully generated ICS file - {scheduleName}.ics")
    logger.info(Fore.RED+"To import the ICS file, drag the generated ICS file into your calendar app")




