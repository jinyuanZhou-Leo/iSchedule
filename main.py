import json
import logging
import random
from tqdm import tqdm,trange
from tqdm.contrib.logging import logging_redirect_tqdm
from pathlib import Path
from data import Course, Term
from datetime import datetime, timedelta
import icalendar as ic

def dateRange(start, end):
    for n in range(int((end - start).days) + 1):
        yield start + timedelta(n)
        
def getRandomHexColor():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def isHexColor(str):
    if str.startswith("#") and len(str) == 7:
        return True
    return False

def generateICS(term:Term, baseName:str, configDict) -> bool:
    icsFile = ic.Calendar()
    icsFile.add("VERSION", "2.0")
    icsFile.add("PRODID", "iScheduler")
    icsFile.add("CALSCALE", "GREGORIAN")
    icsFile.add("X-APPLE-CALENDAR-COLOR", configDict["color"])
    icsFile.add("X-WR-CALNAME", f"{baseName} - {term.name}")  # 日历名称
    icsFile.add("X-WR-TIMEZONE", "Asia/Shanghai")
    cnt = 0 # day counter
    for date in tqdm(dateRange(term.start, term.end),desc="Generating: ",total=int((term.end - term.start).days) + 1):
        if date.weekday()<5:
            if cnt>=term.cycleWeek:
                cnt = 0  
            for course in term.courses:
                blocksList = course.get_block_on(cnt)
                if blocksList:
                    for block in blocksList:
                        event = course.eventify(date, block)
                        if configDict["alarm"]["enabled"] == True:
                            reminder = ic.Alarm()
                            reminder.add("ACTION","DISPLAY")
                            reminder.add("DESCRIPTION", "提醒事项")
                            reminder.add("TRIGGER", timedelta(minutes=-configDict["alarm"]["minutesBefore"]))
                            event.add_component(reminder)  
                            
                        icsFile.add_component(event)        
            cnt+=1
            

    fileName = f"{baseName} - {term.name}.ics"
    try:
        with open(fileName, "wb") as f:
            f.write(icsFile.to_ical())
            return True
    except IOError as e:
        logger.error(f"{e}: Permission denied, Try re-run the program by using \'sudo\'.")
        return False
    except Exception as e:
        logger.error(f"Unknown error occurred while parsing \'{f}\': {e}")
        return False  

def loadJsonFile(path):
    try:
        with path.open() as f:
            data = json.load(f)
            logger.debug(f"{path} is successfully parsed")
            return data
    except FileNotFoundError as e:
        logger.error(f"{e}: \"{path}\" cannot be found")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in {path}")
    except IOError as e:
        logger.error(f"{e}: Permission denied, Try re-run the program by using 'sudo'.")
    except Exception as e:
        logger.error(f"Unknown error occurred while parsing '{path}': {e}")
    return None

VERSION = "1.6"

#initialize

#initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

formatter = logging.Formatter('%(levelname)s - %(message)s')
stream_handler = logging.StreamHandler() # for logging in CLI
stream_handler.setLevel(level = logging.INFO) # log level
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger.info("iScheduler "+str(VERSION))


# parsing config
currentPath = str(Path.cwd())
configPath = Path(currentPath+"/config.json")

configDict = {}
try:
    with configPath.open() as f:
        try:
            configDict = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in {f}")
            exit(0)
        else: logger.debug("Config.json is successfully parsed")
except FileNotFoundError as e:
    logger.error(f"{e}: \"{configPath}\" cannot be found")
    exit(0)
except IOError as e:
    logger.error(f"{e}: Permission denied, Try re-run the program by using \'sudo\'.")
    exit(0)
except Exception as e:
    logger.error(f"Unknown error occurred while parsing \'{f}\': {e}")
    exit(0)   


scheduleDict = {}
schedulePath = Path(currentPath+"/"+configDict["defaultFileName"]) if Path(currentPath+"/"+configDict["defaultFileName"]).is_file() else False
if not schedulePath:
    schedulePathInput = input("Please enter the schedule file path: ").strip()
    if (schedulePathInput.startswith("\'") and schedulePathInput.endswith("\'")) or (schedulePathInput.startswith("\"") and schedulePathInput.endswith("\"")):
            schedulePathInput = schedulePathInput[1:-1] #去掉引号
    schedulePath = Path(schedulePathInput)
try:
    with schedulePath.open() as f:
        try:
            scheduleDict = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in {f}")
            exit(0)
        else:logger.info("Schedule is successfully parsed")
except FileNotFoundError as e:
    logger.error(f"{e}: \"{schedulePath}\" cannot be found")
    exit(0)
except IOError as e:
    logger.error(f"{e}: Permission denied, Try re-run the program by using \'sudo\'.")
    exit(0)
except Exception as e:
    logger.error(f"Unknown error occurred while parsing \'{f}\': {e}")
    exit(0)


# schedule parser
termsDict = dict(filter(lambda x: x[0] != 'Name', scheduleDict.items())) # filter out "Name" key
termsObjList = []
for t in termsDict:
    termTmp = Term(t,scheduleDict[t]["start"],scheduleDict[t]["end"], scheduleDict[t]["classDuration"], scheduleDict[t]["classStartingTime"],scheduleDict[t]["cycleWeek"])
    termsObjList.append(termTmp)
    for c in scheduleDict[t]["courses"]:
        courseTmp = Course(c,scheduleDict[t]["courses"][c]["teacher"],scheduleDict[t]["courses"][c]["time"],scheduleDict[t]["courses"][c]["room"])
        termTmp.addCourse(courseTmp) 

logger.debug("Schedule is successfully objectified")

while True:
    colorInput = input(f"\nHEX color for ICS file (ENTER for defult - {configDict["color"]}):").strip() 
    if colorInput!="": #不使用默认设置，则覆盖默认设置
        configDict["color"] = colorInput
        
    if configDict["color"].lower() == "random":
        configDict["color"] = getRandomHexColor()
        break
    elif not isHexColor(configDict["color"]):
        logger.error(f"Invalid HEX color format - \"{configDict["color"]}\", Example: #FF50FF")
    else:
        break

baseName = ""
if "Name" not in scheduleDict:
    logger.error("Schedule file does not have a name")
    nameInput = input("Please enter the schedule name (Enter for using default setting):")
    if nameInput == "":
        baseName = f"Schedule-{datetime.now().strftime('%X-%Y.%m.%d')}"
    else:
        baseName = nameInput
else:
    baseName = scheduleDict["Name"]

if configDict["alarm"]["enabled"] != True:
    configDict["alarm"]["minutesBefore"] = 0 #没启用则归零


# generate .ics file for each term
for i in trange(len(termsObjList),desc="Total: "):
    termObj = termsObjList[i]
    if generateICS(termObj,baseName,configDict):
        logger.info(f"[{i+1} of {len(termsObjList)}] Successfully generated ICS file - {baseName} - {termObj.name}.ics")
    else:
        logger.error(f"[{i+1} of {len(termsObjList)}] Failed to generate ICS file - {baseName} - {termObj.name}.ics")

print("\n")

logger.info("To import the ICS file, drag the generated ICS file into your calendar app")

