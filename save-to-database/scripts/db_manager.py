#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用数据库保存工具
支持任意数据结构的保存和查询
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

# 数据库配置
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "data.db"

def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)

def create_table_if_not_exists(table_name, fields):
    """
    创建表（如果不存在）
    
    Args:
        table_name: 表名
        fields: 字段定义 dict，如 {"name": "TEXT", "age": "INTEGER"}
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 表名清理（只允许字母、数字、下划线）
    table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
    
    # 构建字段定义
    field_defs = [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "data_hash TEXT UNIQUE",  # 用于去重
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    ]
    
    for field_name, field_type in fields.items():
        field_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(field_name))
        field_type = field_type.upper()
        if field_type not in ["TEXT", "INTEGER", "REAL", "BLOB"]:
            field_type = "TEXT"
        field_defs.append(f"{field_name} {field_type}")
    
    # 创建表
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(field_defs)}
        )
    """
    
    cursor.execute(create_sql)
    conn.commit()
    conn.close()
    
    return table_name

def calculate_data_hash(data):
    """计算数据的哈希值（用于去重）"""
    data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(data_str.encode()).hexdigest()

def save_data(table_name, data, fields=None):
    """
    保存数据到数据库
    
    Args:
        table_name: 表名
        data: 数据 dict 或 dict 列表
        fields: 字段定义（可选，自动推断）
    
    Returns:
        dict: 保存结果
    """
    # 支持单条和批量
    if isinstance(data, dict):
        data = [data]
    
    if not data:
        return {"success": False, "message": "数据为空"}
    
    # 自动推断字段
    if not fields:
        fields = infer_fields(data[0])
    
    # 创建表
    actual_table = create_table_if_not_exists(table_name, fields)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    skipped_count = 0
    
    for item in data:
        try:
            # 计算哈希
            data_hash = calculate_data_hash(item)
            
            # 准备字段和值
            field_names = list(fields.keys())
            values = []
            for field_name in field_names:
                value = item.get(field_name)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                values.append(value)
            
            # 插入数据
            placeholders = ', '.join(['?' for _ in field_names])
            insert_sql = f"""
                INSERT OR IGNORE INTO {actual_table} 
                (data_hash, {', '.join(field_names)})
                VALUES (?, {placeholders})
            """
            
            cursor.execute(insert_sql, [data_hash] + values)
            
            if cursor.rowcount > 0:
                saved_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"⚠️ 保存失败：{e}")
            skipped_count += 1
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "table": actual_table,
        "saved": saved_count,
        "skipped": skipped_count,
        "total": len(data)
    }

def infer_fields(data):
    """
    从数据中推断字段定义
    
    Args:
        data: 数据 dict
    
    Returns:
        dict: 字段定义，如 {"name": "TEXT", "age": "INTEGER"}
    """
    fields = {}
    
    for key, value in data.items():
        # 清理字段名
        field_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(key))
        
        # 推断类型
        if value is None:
            field_type = "TEXT"
        elif isinstance(value, bool):
            field_type = "INTEGER"
        elif isinstance(value, int):
            field_type = "INTEGER"
        elif isinstance(value, float):
            field_type = "REAL"
        elif isinstance(value, (dict, list)):
            field_type = "TEXT"  # JSON 存储为 TEXT
        else:
            field_type = "TEXT"
        
        fields[field_name] = field_type
    
    # 添加常用字段
    if "content" not in fields:
        fields["content"] = "TEXT"
    if "data" not in fields:
        fields["data"] = "TEXT"
    
    return fields

def query_data(table_name, limit=100, where=None):
    """
    查询数据
    
    Args:
        table_name: 表名
        limit: 限制条数
        where: WHERE 条件（可选）
    
    Returns:
        list: 数据列表
    """
    table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if where:
        sql = f"SELECT * FROM {table_name} WHERE {where} LIMIT {limit}"
    else:
        sql = f"SELECT * FROM {table_name} LIMIT {limit}"
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    # 获取列名
    columns = [description[0] for description in cursor.description]
    
    conn.close()
    
    # 转换为 dict 列表
    result = []
    for row in rows:
        item = dict(zip(columns, row))
        # 尝试解析 JSON 字段
        for key, value in item.items():
            if isinstance(value, str):
                try:
                    item[key] = json.loads(value)
                except:
                    pass
        result.append(item)
    
    return result

def list_tables():
    """列出所有表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

def export_to_json(table_name, output_path=None):
    """导出数据为 JSON"""
    data = query_data(table_name, limit=10000)
    
    if not output_path:
        output_path = SCRIPT_DIR / f"{table_name}_export.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {
        "success": True,
        "count": len(data),
        "path": str(output_path)
    }

# ==================== 命令行使用 ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 db_manager.py save <table> <json_data>")
        print("  python3 db_manager.py query <table> [limit]")
        print("  python3 db_manager.py list")
        print("  python3 db_manager.py export <table>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "save":
        table = sys.argv[2] if len(sys.argv) > 2 else "default_data"
        data_json = sys.argv[3] if len(sys.argv) > 3 else "{}"
        data = json.loads(data_json)
        result = save_data(table, data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "query":
        table = sys.argv[2] if len(sys.argv) > 2 else "default_data"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        data = query_data(table, limit)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    
    elif command == "list":
        tables = list_tables()
        print(f"表列表：{tables}")
    
    elif command == "export":
        table = sys.argv[2] if len(sys.argv) > 2 else "default_data"
        result = export_to_json(table)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令：{command}")
