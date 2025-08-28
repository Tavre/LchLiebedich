#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：将SQLite数据库数据迁移到JSON存储
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def migrate_database_to_json(db_path: str, json_path: str) -> bool:
    """
    将SQLite数据库数据迁移到JSON文件
    
    Args:
        db_path: SQLite数据库文件路径
        json_path: 目标JSON文件路径
        
    Returns:
        bool: 迁移是否成功
    """
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"数据库文件不存在: {db_path}")
            return True  # 没有数据库文件，视为成功
            
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wordlib_entries'")
        if not cursor.fetchone():
            print("数据库中没有wordlib_entries表")
            conn.close()
            return True
            
        # 查询所有词条数据
        cursor.execute("""
            SELECT id, keyword, response, category, tags, created_at, updated_at, usage_count
            FROM wordlib_entries
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为JSON格式
        entries = []
        for row in rows:
            entry = {
                "id": row[0],
                "keyword": row[1],
                "response": row[2],
                "category": row[3] or "默认",
                "tags": json.loads(row[4]) if row[4] else [],
                "created_at": row[5] or datetime.now().isoformat(),
                "updated_at": row[6] or datetime.now().isoformat(),
                "usage_count": row[7] or 0
            }
            entries.append(entry)
            
        # 创建JSON数据结构
        json_data = {
            "version": "1.0",
            "migrated_at": datetime.now().isoformat(),
            "total_entries": len(entries),
            "entries": entries
        }
        
        # 确保目标目录存在
        json_file = Path(json_path)
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 备份现有JSON文件（如果存在）
        if json_file.exists():
            backup_path = json_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            json_file.rename(backup_path)
            print(f"已备份现有JSON文件到: {backup_path}")
            
        # 写入JSON文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
            
        print(f"成功迁移 {len(entries)} 条词条到 {json_path}")
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        return False

def main():
    """
    主函数
    """
    # 默认路径
    db_path = "data/wordlib.db"
    json_path = "data/wordlib.json"
    
    print("开始数据迁移...")
    print(f"源数据库: {db_path}")
    print(f"目标JSON: {json_path}")
    
    if migrate_database_to_json(db_path, json_path):
        print("数据迁移完成！")
    else:
        print("数据迁移失败！")
        exit(1)

if __name__ == "__main__":
    main()