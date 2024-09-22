# iSchedule 课程表转ICS工具

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

   * ```color```: ("random":表示随机 | Hex色值)生成的ics文件在日历中的颜色
   * ```alarm```:闹钟相关设置
     * ```enabled```:(True|False) 是否再上课前通知提醒
     * ```before```:(list[int, int]) 提前多长时间通知：```[小时，分钟]```

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

- **classDuration**
  - **类型**: `int`
  - **含义**: 表示每节课的时长（分钟）。
  - **示例**: `70`

- **classStartingTime**
  - **类型**: `array` of `array` of `int`
  - **含义**: 表示每天的课程开始时间，每个子数组格式为 `[小时, 分钟]`。
  - **示例**: `[[8,0],[9,15],[10,30],[13,0],[14,15]]`

- **cycleWeek**
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

- **time**
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

- **room**
  - **类型**: `string`
  - **含义**: 表示上课的教室。
  - **示例**: `"A205"`, `"A312/A212"`, `"A308/Library"`
  
----------------

备注: 第`x`个工作日表示`w`周中去除工作日后的第`x`天