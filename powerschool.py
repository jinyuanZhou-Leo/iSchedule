#!/usr/bin/env python3
# coding=utf-8

import itertools
import re
import locale
from tracemalloc import start
from click import progressbar
import requests
from requestHandler import RequestHandler
from bs4 import BeautifulSoup, ResultSet, SoupStrainer, Tag
from loguru import logger
from tqdm import tqdm


class PowerSchool:
    username: str
    password: str
    htmlParser: str
    mode: str
    gradePageContent: BeautifulSoup | None
    schedulePageContent: BeautifulSoup | None

    def __init__(
        self, username: str, password: str, htmlParser: str = "lxml", mode="request"
    ) -> None:
        self.htmlParser = htmlParser
        self.mode = mode
        self.gradePageContent = None  # init
        self.schedulePageContent = None  # init
        try:
            self._login(username, password)
        except Exception as e:
            raise e
        else:
            self.username = username
            self.password = password

    def _login(self, username: str, password: str):
        # TODO: Add English Login Support
        def isLogin(psPage: requests.Response) -> bool:
            psPageContent = BeautifulSoup(psPage.content, self.htmlParser)
            if (
                "pslogin" in psPageContent.body["class"]
                and psPageContent.body["id"] == "pslogin"
            ):
                return False
            else:
                return True

        progressbar = tqdm(desc="Logging into Powerschool", unit="%", total=100)  # TODO: enhance description
        languageSetting = locale.getlocale()[0]
        logger.debug(f"System language: {languageSetting}")
        if languageSetting != "zh_CN" and languageSetting != "en_US":
            logger.warning("Default system language is unsupported, using English as default...")
            languageSetting = "en_US"

        requester = RequestHandler(
            timeout=10,
            retry=3,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            },
        )
        LOGIN_URL = "https://nanjing.powerschool.com/guardian/home.html"
        SCHEDULE_URL = "https://nanjing.powerschool.com/guardian/myschedule.html"
        PSLOGINDATA = {
            "dbpw": password,
            "serviceName": "PS Parent Portal",
            "pcasServerUrl": "/",
            "credentialType": "User Id and Password Credential",
            "request_locale": languageSetting,
            "account": username,
            "pw": password,
        }
        progressbar.update(10)
        logger.info("Connecting to Powerschool...")
        psPage = requester.post(LOGIN_URL, data=PSLOGINDATA)
        progressbar.update(30)
        schedulePage = requester.get(SCHEDULE_URL)
        progressbar.update(30)
        schedulePageFilter = SoupStrainer(["tr", "td", "th", "table", "tbody", "br"])
        self.schedulePageContent = BeautifulSoup(
            schedulePage.content, self.htmlParser, parse_only=schedulePageFilter
        )
        progressbar.update(30)
        if isLogin(psPage):
            self.gradePageContent = BeautifulSoup(psPage.content, "lxml")
            return True
        else:
            raise ValueError("Wrong username or password")

    @staticmethod
    def ps2list(psIndex: str | list, cycle: int) -> list[list]:
        def componentParser(component: str) -> list:
            # pre-processing
            abbrDict = {
                "odd": [i for i in range(1, cycle + 1, 2)],  # List of odd days
                "even": [i for i in range(2, cycle + 1, 2)],  # List of even days
                "everyday": [i for i in range(1, cycle + 1)],  # List of all days
            }
            component = component.strip()  # trim the leading and trailing whitespace

            dashIndex: int = component.find("-")  # if the component is a range
            if dashIndex != -1:  # is range
                # filling the range
                leftBound, rightBound = int(component[:dashIndex]), int(
                    component[dashIndex + 1 :]
                )
                if leftBound > rightBound:
                    raise ValueError(
                        f'Invalid schedule file, Error processing "{psIndex}", "{leftBound}-{rightBound}" is out of range'
                    )
                return [i for i in range(leftBound, rightBound + 1)]

            else:  # not range
                if component.isdigit():
                    return [int(component)]
                elif component in abbrDict:
                    return abbrDict[component]
                else:
                    raise ValueError(
                        f'Invalid Powerschool index format, cannot parse component "{component}"'
                    )

        psIndexes: list = []
        if isinstance(psIndex, str):
            psIndexes = [psIndex]
        else:
            psIndexes = psIndex

        parsedIndex: list = []
        for psIndex in psIndexes:
            psIndex = psIndex.strip().lower()  # trim the trailing and leading spaces
            leftParentheseIndex: int = psIndex.find("(")
            rightParentheseIndex: int = psIndex.rfind(")")
            if leftParentheseIndex == -1 or rightParentheseIndex == -1:
                # can not find parentheses
                raise ValueError(
                    "Invalid Powerschool index format, cannot find parentheses"
                )

            if psIndex.startswith("p"):
                psIndex = psIndex.removeprefix("p")
            elif psIndex.startswith("hr"):
                raise ValueError(
                    'PS index starts with "hr", do you mean "Homeroom"? It isn\'t currently supported by PS Connector'
                )
            else:
                raise ValueError(
                    "Invalid Powerschool index format, it should startwith 'P'"
                )

            if len(psIndex[: leftParentheseIndex - 1]) != 0:
                block: int = int(psIndex[: leftParentheseIndex - 1])
            else:
                block = -1

            if block < 0:
                raise ValueError(
                    "Invalid Powerschool index format, block number is invalid or out of range"
                )
            indexes: str = psIndex[leftParentheseIndex : rightParentheseIndex - 1]

            components: list[str] = indexes.split(",")
            parsedComponent: list[list] = []
            for component in components:
                parsedComponent.extend(
                    [
                        list(t)
                        for t in itertools.product(
                            componentParser(component), [block - 1]
                        )
                    ]
                )

            parsedIndex.extend(parsedComponent)

        print(parsedIndex)
        return parsedIndex

    def _getGradeTable(self) -> Tag:
        return self.gradePageContent.select_one("table.linkDescList.grid")

    def _getGradeTableHeader(self) -> ResultSet[Tag]:
        return (
            self._getGradeTable()
            .find_all(
                lambda tag: tag.get("class") == ["center", "th2"]
                and tag.get("id", "") == "",
                recursive=False,
            )[0]
            .select("th")
        )

    def _getGradeTableContent(self) -> ResultSet[Tag]:
        return self._getGradeTable().find_all(
            lambda tag: tag.get("class") == ["center"]
            and tag.get("id", "").startswith("ccid"),
            recursive=False,
        )

    def _getGradeTableColumnMap(
        self, gradeTableHeader: ResultSet[Tag]
    ) -> dict[str, int]:
        colCnt = 0
        colMap: dict = {}
        logger.debug("Building column map...")
        for item in gradeTableHeader:
            # rowspan+1, colspan+5
            rowSpan = item.get("rowspan", False)
            colSpan = item.get("colspan", False)

            content: str = item.get_text().strip()
            if content == "开课时间" or content == "Exp":
                logger.debug(f'Found "{content}" in col {colCnt}')
                colMap["TimeIndex"] = colCnt
            elif content == "课程" or content == "Content":
                logger.debug(f'Found "{content}" in col {colCnt}')
                colMap["CourseInformation"] = colCnt
            elif content.startswith("T") and content[-1].isdigit():
                logger.debug(f'Found "{content}" in col {colCnt}')
                colMap[f"Term{content[-1]}"] = colCnt
            elif content.startswith("S") and content[-1].isdigit():
                logger.debug(f'Found "{content}" in col {colCnt}')
                colMap[f"Term{content[-1]}"] = colCnt
            elif content == "缺勤":  # TODO: Eng Support
                logger.debug(f'Found "{content}" in col {colCnt}')
                colMap["Absent"] = colCnt
            elif content == "迟到":  # TODO: Eng Support
                logger.debug(f'Found "{content}" in col {colCnt}')
                colMap["Tardy"] = colCnt
            else:
                logger.debug(f'Skipped col {colCnt} with content "{content}"')
                pass

            if rowSpan:
                colCnt += 1
            elif colSpan:
                colCnt += 5

        logger.debug(f"Column map is built: {colMap}")
        return colMap

    def _requestValue(
        self, prompt: str, type_: type, defaultValue: any = None, unit: str = ""
    ) -> any:
        if unit:
            unit = " " + unit
        while True:
            try:
                inputValue = input(f"({defaultValue}{unit}) {prompt}: ").strip()
                if inputValue == "":
                    if defaultValue:
                        return defaultValue
                    else:
                        raise ValueError("Default value does't not exist")
                inputValue = type_(inputValue)
                return type_(inputValue)
            except (ValueError, TypeError) as e:
                logger.error(
                    f'Invalid input, Required input of "{type_}", Message: {e}'
                )

    def _getCourseInformation(self, tCell: Tag) -> dict[str, str]:
        tData = [item for item in tCell.get_text().split("\xa0") if item != "\xa0"]
        # /xa0 represents the &nbsp; in HTML
        courseName: str = tData[0].strip()
        courseLocation: str = (
            tCell.find("span", text="-\xa0Rm:")
            .find_next_sibling("span")
            .get_text(strip=True)
        )
        courseTeacher: str = (
            tCell.find("a", {"target": "_top"}).get_text().removeprefix("Email").strip()
        )
        if courseName and courseLocation and courseTeacher:
            courseLocation.replace("，", ", ")  # TODO: work around: this doesn't work
            # replace chinese comma with English comma
            course: dict[dict] = {}
            courseData: dict = {"location": courseLocation, "teacher": courseTeacher}
            course[courseName] = courseData
            return course
        else:
            raise RuntimeError(
                "Unexpected error occur while finding course information"
            )

    def getAllCourseInformation(self) -> dict[any, dict]:
        gradeTableHeader = self._getGradeTableHeader()  # list of table headers
        gradeTableContent = self._getGradeTableContent()  # list of table content
        columnMap = self._getGradeTableColumnMap(gradeTableHeader)

        course: dict = {}
        for tRow in gradeTableContent:
            tData = tRow.select("td")
            courseInformation: dict = self._getCourseInformation(
                tData[columnMap["CourseInformation"]]
            )
            courseName = list(courseInformation.keys())[0]
            if courseName == "BCA Homeroom":  # ignore BCA Homeroom
                logger.warning(f"Skip {courseName} while parsing course information")
                continue
            courseInformation[courseName]["index"] = [tData[columnMap["TimeIndex"]].get_text().strip()]

            if course.get(courseName) is not None:  # if there is duplicate course with different information, merge it
                logger.debug(f"Duplicate course name: {courseName}, trying to merge content")

                # merge time index
                if course[courseName]["index"] != courseInformation[courseName]["index"]:
                    logger.debug(f'Merging time index for "{courseName}"')
                    course[courseName]["index"].extend(courseInformation[courseName]["index"])

                # merge location
                if course[courseName]["location"] != courseInformation[courseName]["location"]:
                    logger.debug(f'Merging location information for "{courseName}"')
                    course[courseName]["location"] += ", " + courseInformation[courseName]["location"]

                # merge teacher
                if course[courseName]["teacher"] != courseInformation[courseName]["teacher"]:
                    logger.debug(f'Merging teacher information for "{courseName}"')
                    course[courseName]["teacher"] += ", " + courseInformation[courseName]["teacher"]

            else:  # no duplication found, update dict anyway
                course.update(courseInformation)

        logger.debug(f'All course information is parsed, result: "{course}"')
        return course

    def getTimetable(self) -> list[list]:

        def timeParser(timestamp: str) -> list:
            # TODO: English Version support
            tmp = timestamp.split("-")[0].strip().split(" ")
            startingTime, apm = tmp[0], tmp[1]
            startingTime = [int(i) for i in startingTime.split(":")]
            if apm == "下午":
                startingTime[0] += 12

            if 0 <= startingTime[0] <= 24 and 0 <= startingTime[1] < 60:
                return startingTime
            else:
                raise ValueError(f'Unexpected invalid timestamp: "{timestamp}"')

        scheduleTbody: Tag = self.schedulePageContent.select_one("#tableStudentSchedMatrix")
        matrixItemsFilter = re.compile(r"scheduleClass\d+")

        matrixItems = set()
        for item in scheduleTbody.find_all("td", class_=matrixItemsFilter):
            content: list = item.contents
            courseName: str = content[0].strip()
            if courseName == "BCA Homeroom":
                logger.debug(f"Skip {courseName} while parsing timestamp")
                # skipped
                continue

            matrixItems.add(item.contents[-1])
        matrixItems = sorted([timeParser(item) for item in list(matrixItems)])
        logger.debug(f'Timetable parsed, result: "{matrixItems}"')
        return matrixItems

    def getScheduleJsonContent(
        self,
    ) -> dict[any, dict]:
        scheduleJson: dict = {}
        logger.info("PS Connect would ask you for required information")
        logger.info("For example: (Default Value) XXX Info: Your Input")
        logger.info("Press ENTER for using default setting")

        termName: str = self._requestValue("Term Name", str, defaultValue="Term")
        termStart: list = [
            int(item)
            for item in self._requestValue(
                f'"{termName}" start at (YY.mm.dd)', str
            ).split(".")
        ]
        termEnd: list = [
            int(item)
            for item in self._requestValue(
                f'"{termName}" end at (YY.mm.dd)', str
            ).split(".")
        ]

        duration: int = self._requestValue(
            "Duration for each class", int, defaultValue=70, unit="minutes"
        )
        cycle: int = self._requestValue(
            "How many weeks per cycle", int, defaultValue=2, unit="week"
        )

        # input validation checking
        if len(termStart) != 3 or len(termEnd) != 3:
            raise ValueError("Invalid date value")
        if termStart >= termEnd:
            raise ValueError("Start date must earlier than end date")
        if cycle > 2:
            logger.warning(
                f'The cycle number seems rare: "cycle={cycle}", do you mean {cycle*7} days or {cycle*5} workdays? If you KNOW what you are doing, please ignore this warning'
            )

        termSettings: dict[any, dict] = {
            termName: {
                "start": termStart,
                "end": termEnd,
                "duration": duration,
                "timetable": self.getTimetable(),
                "cycle": cycle,
                "courses": self.getAllCourseInformation(),
            }
        }
        scheduleJson.update(termSettings)

        return scheduleJson


if __name__ == "__main__":
    logger.warning("This module cannot run independently")
