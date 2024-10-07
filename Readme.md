
<p align="center"><img src="img/icon.png" alt="示例图片" style="width: 150px;height:150px;margin:20px auto 40px auto;"></p>

<div style="margin:10px auto 70px;"><h1 align="center">iSchedule: 课程表转ICS工具</h1></div>


## 模块功能说明
- **data.py:** 类
- **main.py:** 主程序
- **util.py:** 工具库
- **json_generator.py:** json格式课程表生成器
- **rule.md** Schedule.json格式Prompt
- **config.json:** ics生成配置
- **schedule.json:** 课表样例



## 使用说明
1. **完成配置文件**: (完整的配置文件样例详见schedule.json和config.json)
2. **(如果需要使用AI JSON生成)**: 
   * 在程序运行目录下创建```.env```文件
   * 在```.env```文件中填写：```ZHIPU_API_KEY = "your-zhipu-api-key"```



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
  
----------------

备注: 第`x`个工作日表示`w`周中去除工作日后的第`x`天