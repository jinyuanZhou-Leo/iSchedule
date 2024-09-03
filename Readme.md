# iSchedule 课程表转ICS工具

### 模块功能说明
- **data.py:** 类
- **main.py:** 主程序
- **config.json:** 配置文件（设置）
- **schedule.json:** 课表样例

### 使用说明
1. **完成配置文件**
  **完整的配置文件格式详见schedule.json和config.json**
   * ```defaultFileName```: 默认读取的课程表json文件路径

   * ```color```: ("random":表示随机 | Hex色值)生成的ics文件在日历中的颜色
   * ```alarm```:闹钟相关设置
     * ```enabled```:(True|False) 是否再上课前通知提醒
     * ```minutesBefore```:(Integer) 多少分钟前通知提醒
