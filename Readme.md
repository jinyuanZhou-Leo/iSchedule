
<p align="center"><img src="img/icon.png" alt="示例图片" style="width: 150px;height:150px;margin:20px auto 40px auto;"></p>

<div style="margin:10px auto 70px;"><h1 align="center">iSchedule: 课程表转ICS工具</h1></div>


## 模块功能说明
- **data.py:** 数据处理相关类
- **main.py:** 主程序
- **powerschool_connector.py** 从powerschool导入课程表数据的工具
- **powerschool.py** powerschool相关类
- **util.py:** 工具库
- **json_generator.py:** AI Schedule.json生成器
- **rule.md** 关于Schedule.json格式的AI Prompt
- **config.json:** 程序配置
- **schedule.json:** 样例



## 从JSON日程表生成ICS文件
1. 运行```main.py```,输入JSON文件路径
   
> [!TIP]
> 程序会默认使用目录下```schedule.json```生成ICS,如不希望自动生成，请删除程序目录下名称为```schedule.json```的文件

## AI生成JSON日程表: 
1. 运行```json_generator.py```输入您的智谱API_KEY
2. 通过自然语言对话
3. 完成生成, 成品JSON日程表会以```schedule.json```为文件名保存在程序目录下

## 从PowerSchool生成JSON日程表
1. 运行```powerschool_connector.py```
2. 根据提示输入正确的用户名与密码
3. 根据提示输入所需的信息
4. 完成生成, 成品JSON日程表会以```schedule.json```为文件名保存在程序目录下
  
> [!TIP]
> PowerSchool系统在考试期间无法访问



## Config.json 格式说明 

### name
   * **类型**: `string`
   * **含义**: 表示日程或任务的名称。
   * **示例**: `2025 Schedule`
### color
   * **类型**: string
   * **含义**: 表示日程或任务的颜色，通常以十六进制颜色代码表示。
   * **示例**: `#80e24e`
### alarm
   * **类型**: `object`
   * **含义**: 表示闹钟或提醒的设置。
   * **子字段**：如下
- ### enabled
   * **类型**: `boolean`
   * **含义**: 表示闹钟是否启用。
   * **示例**: `true`
- ### before
   * **类型**: `array of integers`
   * **含义**: 表示在事件开始前多少时间（单位可能为分钟或小时）提醒。数组中的每个元素代表一个提醒时间。
   * **示例**: `[0, 7]`（表示在事件开始时和开始前7分钟提醒）
### countDayInHoliday
   * **类型**: `boolean`
   * **含义**: 表示是否在节假日中保持工作日计数
   * **示例**: `true`

## Schedule.json 格式说明

### 顶级字段
- **Term 1, Term 2, 上学期，下学期......** (学期名称)
  - **类型**: `object`
  - **含义**: 表示一个学期的名字，其子字段为`object`
  - **示例**: `{"start":[2024,9,2],"end":[2024,11,17],"classDuration":70,"classStartingTime".....}`

### Term 字段中的子字段
- **start**
  - **类型**: `array` of `int`
  - **含义**: 表示学期开始日期，格式为 `[年, 月, 日]`。
  - **示例**: `[2024, 9, 2]`

- **end**
  - **类型**: `array` of `int`
  - **含义**: 表示学期结束日期，格式为 `[年, 月, 日]`。
  - **示例**: `[2024, 11, 17]`

- **duration**
  - **类型**: `int`
  - **含义**: 表示每节课的时长（分钟）。
  - **示例**: `70`

- **timetable**
  - **类型**: `array` of `array` of `int`
  - **含义**: 表示每天的课程开始时间，每个子数组格式为 `[小时, 分钟]`。
  - **示例**: `[[8,0],[9,15],[10,30],[13,0],[14,15]]`

- **cycle**
  - **类型**: `int`
  - **含义**: 表示课程循环的周数。
  - **示例**: `2`

- **courses**
  - **类型**: `object`
  - **含义**: 表示该学期内的所有课程及其详细信息。
  - **示例**: `{ "Calculus 12": { "teacher": "Charles Zhang", "time": [["even",1]], "room": "A205" }, ... }`

- **holidays**
  - **类型**: `object`
  - **含义**: 表示该学期内的假期信息。
  - **示例**: `{"National Holiday":{"type": "fixed","date":[[2024,10,1],[2024,10,7]],"compensation":[[[2024,9,29],2]]}, ... }`

### courses 中的子字段（每个课程）
- **Calculus 12, Physics 12, English Studies 12, ...** (课程名称)
  - **类型**: `object`
  - **含义**: 表示具体课程的详细信息。
  - **示例**: `{ "teacher": "Charles Zhang", "time": [["even",1]], "room": "A205" }`

### 每个课程中的子字段
- **teacher**
  - **类型**: `string`
  - **含义**: 表示授课教师的名字。
  - **示例**: `"Charles Zhang"`

- **index**
  - **类型**: `array` of `array` of `mixed`
  - **含义**: 表示课程的上课时间。每个子数组可以有以下几种格式：
    - `["even"|"odd"|"everyday", int]`：表示在第偶数个工作日或第奇数个工作日或每天的第几节课。
    - `[[int, int, ...], int]`：表示在指定的工作日的第几节课。
  - **示例**:
    - `["even", 1]`：第偶数个工作日的第一节课
    - `["odd", 1]`：第奇数个工作日的第一节课
    - `["everyday", 2]`：每天的第二节课
    - `[[1, 6], 3]`：第1个工作日和第6个工作日的第三节课
    - `[[2, 4, 7, 9], 3]`：第2、4、7、9个工作日的第三节课
    - `[[3, 8], 3]`：第3和第8个工作日的第三节课

- **location**
  - **类型**: `string`
  - **含义**: 表示上课的教室。
  - **示例**: `"A205"`, `"A312/A212"`, `"A308/Library"`

- **cycle** (可选字段，如特别声明了某门课的循环周期)
  - **类型** `int`
  - **含义**: 表示单独针对某门课的循环周期
  - **示例**: `1`, `2` ...

### holidays 中的子字段 (节假日)
- **National Holiday, Mid-Autumn Festival,...** (课程名称)
  - **类型**: `object`
  - **含义**: 表示具体课程的详细信息。
  - **示例**: `{"type": "fixed","date":[[2024,10,1],[2024,10,7]],"compensation":[[[2024,9,29],2]]}`

### 每个节假日中的子字段
- **type**
  - **类型**: `string`
  - **含义**: 表示节假日的类型, fixed表示固定日期节假日，relative表示每年不一定在同一天的节假日
  - **示例**: `"fixed","relative"`

- **date**
  - **类型**: `array` of `array` of `int`
  - **含义**: 表示节假日的起止日期或者日期：
    - `[[year, month, day], [year, month, days]]`：表示节假日从几号到几号
    - `[[year, month, day]]`：表示单天节假日的日期
  - **示例**:
    - `[[2024,10,1],[2024,10,7]]`：从2024.10.1到2024.10.7的节假日
    - `[[2024,5,1]]`：2024.5.1的节假日

- **compensation**
  - **类型**: `array` of `array` of `mixed`
  - **含义**: 表示调休信息:
    - `[[[year, month, day], workdayNumber]]`：表示在某天第几个工作日的课
  - **示例**:
    - `[[2024, 9, 30], 1]`：2024年9月30日补上Day 1的课
    - `[[[2024, 10,12],6],[[2024, 11,30],2]]`：2024年10月12日补Day 6的课，11月30日补Day 2的课 
  
----------------

备注: 第`x`个工作日表示`w`周中去除工作日后的第`x`天