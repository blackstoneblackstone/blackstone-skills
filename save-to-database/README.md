# Save to Database

通用数据库保存工具。

## 使用

### OpenClaw 会话
```
保存到数据库
```

### 命令行
```bash
# 保存数据
python3 scripts/db_manager.py save my_table '{"name": "张三", "age": 25}'

# 查询数据
python3 scripts/db_manager.py query my_table

# 列出所有表
python3 scripts/db_manager.py list

# 导出数据
python3 scripts/db_manager.py export my_table
```

数据保存到 `scripts/data.db`
