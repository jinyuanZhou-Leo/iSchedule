import json
import logging
import random
from pathlib import Path
from data import Course, Term
#from generator import generateICS
from datetime import date, time, datetime, timedelta
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

def generateICS(term:Term, baseName:str, configDict):
    icsFile = ic.Calendar()
    icsFile.add("VERSION", "2.0")
    icsFile.add("PRODID", "iScheduler")
    icsFile.add("CALSCALE", "GREGORIAN")
    icsFile.add("X-APPLE-CALENDAR-COLOR", configDict["color"])
    icsFile.add("X-WR-CALNAME", f"{baseName} - {term.name}")  # 日历名称
    icsFile.add("X-WR-TIMEZONE", "Asia/Shanghai")
    
    cnt = 0 # day counter
    for day in dateRange(term.start, term.end):
        if day.weekday()<5:
            if cnt>=term.cycle:
                cnt = 0  
            for course in term.courses:
                #TODO:把以下部分封装到Class Course
                blocksList = course.get_block(cnt)
                if blocksList:
                    for block in blocksList:
                        event = ic.Event()
                        event.add("summary", course.name)     
                        event.add("description", f"{course.teacher}\n{course.room}")
                        event.add("dtstart",datetime.combine(day,time(term.classStartingTime[block][0],
                            term.classStartingTime[block][1])))
                        event.add("dtend",datetime.combine(day,time(term.classStartingTime[block][0],
                            term.classStartingTime[block][1]))+timedelta(minutes=term.classDuration))
                            
                        if configDict["alarm"]["enabled"] == True:
                            reminder = ic.Alarm()
                            reminder.add("ACTION","DISPLAY")
                            reminder.add("DESCRIPTION", "提醒事项")
                            reminder.add("TRIGGER", timedelta(minutes=-configDict["alarm"]["minutesBefore"]))
                            event.add_component(reminder)  
                            
                        icsFile.add_component(event)        
            cnt+=1
            

    fileName = f"{baseName} - {term.name}.ics"
    with open(fileName, "wb") as file:
        file.write(icsFile.to_ical())
        return True

VERSION = 1.6

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
logger.info("Current Path: "+ str(Path.cwd()))

#initialize colorama
#init(autoreset=True)


# parsing config
currentPath = str(Path.cwd())
configPath = Path(currentPath+"/config.json")

configDict = {}
if configPath.is_file(): #如果存在配置文件
    with configPath.open() as file:
        configDict = json.load(file)
        logger.debug("Config.json is successfully parsed")
else: #配置文件不存在
    logger.error("No such file dictionary, Cannot find Config.json")
    configDict["defaultFileName"] = "schedule.json"



# look for schedule file
schedulePath = Path(currentPath+"/"+configDict["defaultFileName"])
scheduleDict = {}
if schedulePath.is_file():
    with schedulePath.open() as file:
        scheduleDict = json.load(file)
        logger.info("Schedule is successfully parsed")
else:
    while True:
        logger.error(f"{configDict["defaultFileName"]} could not be found, please enter the path of schedule")
        schedulePathInput = input("Please enter the schedule file path: ").strip()
        
        if (schedulePathInput.startswith("\'") and schedulePathInput.endswith("\'")) or (schedulePathInput.startswith("\"") and schedulePathInput.endswith("\"")):
            schedulePathInput = schedulePathInput[1:-1] #去掉引号
            
        schedulePath = Path(schedulePathInput)
        if schedulePath.is_file():
            with schedulePath.open() as file:
                scheduleDict = json.load(file)
                logger.info("Schedule is successfully parsed")
                break


# schedule parser
termsDict = dict(filter(lambda x: x[0] != 'Name', scheduleDict.items())) # filter out "Name" key
termsObjList = []
for t in termsDict:
    termTmp = Term(t,scheduleDict[t]["start"],scheduleDict[t]["end"], scheduleDict[t]["classDuration"], scheduleDict[t]["classStartingTime"],scheduleDict[t]["cycle"])
    termsObjList.append(termTmp)
    #coursesObj = []
    for c in scheduleDict[t]["courses"]:
        courseTmp = Course(c,scheduleDict[t]["courses"][c]["teacher"],scheduleDict[t]["courses"][c]["time"],scheduleDict[t]["courses"][c]["room"])
        termTmp.addCourse(courseTmp) 
    
    
        
    
logger.debug("Schedule is successfully objectified")

# customizations
#scheduleColor = config["color"]
while True:
    colorInput = input(f"Please enter the color of your schedule in HEX format (ENTER for using default setting - {configDict["color"]}):").strip() # strip() help cut beginning and trailing whitespace
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
for i in range(len(termsObjList)):
    termObj = termsObjList[i]
    status_generateICS = generateICS(termObj,baseName,configDict)
    if status_generateICS:
        logger.info(f"[{i+1} of {len(termsObjList)}] Successfully generated ICS file - {baseName} - {termObj.name}.ics")

logger.info("To import the ICS file, drag the generated ICS file into your calendar app")

