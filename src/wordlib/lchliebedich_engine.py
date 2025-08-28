#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lchliebedich词库解析引擎
基于lchliebedich变量大全.txt的语法规范实现
"""

import re
import json
import time
import random
import os
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class LexiconEntry:
    """词库条目"""
    trigger: str  # 触发词（支持正则）
    responses: List[str]  # 回复内容列表
    variables: Dict[str, str] = None  # 局部变量
    conditions: List[str] = None  # 条件语句
    category: str = None  # 分类
    enabled: bool = True  # 是否启用
    id: str = None  # 条目ID
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.conditions is None:
            self.conditions = []


class LchliebedichEngine:
    """lchliebedich词库解析引擎"""
    
    def __init__(self):
        self.entries: List[LexiconEntry] = []
        self.global_variables: Dict[str, Any] = {}
        self.message_context: Dict[str, Any] = {}
        self.functions = self._init_functions()
        
    def _init_functions(self) -> Dict[str, callable]:
        """初始化内置函数"""
        return {

            '随机数': self._random_func,
            '字符长度': lambda text: len(str(text)),
            '文件大小': self._file_size_func,
            '变量': self._variable_func,
            '取变量': self._get_variable_func,
            '读': self._read_config_func,
            '写': self._write_config_func,
            '图片': self._image_func,
            '动图': self._gif_func,
            '闪照': self._flash_image_func,
            '语音': self._voice_func,
            'Emoy': self._emoji_func,
            'Emoq': self._super_emoji_func,
            '发送': self._send_func,
            '新建消息': self._new_message_func,
            '添加消息': self._add_message_func,
            '发送消息': self._send_message_func,
            '存在消息': self._exists_message_func,
            '获取消息': self._get_message_func,
            '群聊消息': self._is_group_message_func,
            '好友消息': self._is_friend_message_func,
            '临时消息': self._is_temp_message_func,
            '系统消息': self._is_system_message_func,
            '未授权': self._is_unauthorized_func,
        }
    
    def load_lexicon_file(self, file_path: str) -> bool:
        """加载词库文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.entries = self._parse_lexicon_content(content)
            return True
        except Exception as e:
            print(f"加载词库文件失败: {e}")
            return False
    
    def _parse_lexicon_content(self, content: str) -> List[LexiconEntry]:
        """解析词库内容"""
        entries = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过注释行
            if self._is_comment_line(line):
                i += 1
                continue
            
            # 跳过空行
            if not line:
                i += 1
                continue
            
            # 解析词库条目
            entry, next_i = self._parse_entry(lines, i)
            if entry:
                entries.append(entry)
            i = next_i
        
        return entries
    
    def _is_comment_line(self, line: str) -> bool:
        """判断是否为注释行"""
        return line.startswith('//') or line.startswith('##') or line.startswith('&&')
    
    def _parse_entry(self, lines: List[str], start_index: int) -> Tuple[Optional[LexiconEntry], int]:
        """解析单个词库条目"""
        trigger = lines[start_index].strip()
        responses = []
        variables = {}
        conditions = []
        category = self._extract_category_from_context(lines, start_index)
        
        i = start_index + 1
        
        # 解析响应内容
        while i < len(lines):
            line = lines[i].strip()
            
            # 遇到空行表示条目结束
            if not line:
                break
            
            # 遇到注释行跳过
            if self._is_comment_line(line):
                i += 1
                continue
            
            # 遇到下一个触发词，回退
            if self._looks_like_trigger(line, i, lines):
                break
            
            # 解析变量定义
            if self._is_variable_definition(line):
                var_name, var_value = self._parse_variable_definition(line)
                variables[var_name] = var_value
            # 解析行变量
            elif line.startswith('#->var:'):
                var_content, next_i = self._parse_line_variable(lines, i)
                var_name = line[7:].strip() or 'default_var'
                variables[var_name] = var_content
                i = next_i
                continue
            # 解析条件语句
            elif line.startswith('如果:') or line.startswith('if:'):
                condition_block, next_i = self._parse_condition_block(lines, i)
                conditions.extend(condition_block)
                i = next_i
                continue
            else:
                # 普通响应内容
                responses.append(line)
            
            i += 1
        
        if responses or variables or conditions:
            entry = LexiconEntry(
                trigger=trigger,
                responses=responses,
                variables=variables,
                conditions=conditions,
                category=category,
                id=str(uuid.uuid4())
            )
            return entry, i
        
        return None, i
    
    def _extract_category_from_context(self, lines: List[str], start_index: int) -> Optional[str]:
        """从上下文中提取分类信息"""
        # 向前查找最近的注释行作为分类
        for i in range(start_index - 1, -1, -1):
            line = lines[i].strip()
            if not line:
                continue
            if self._is_comment_line(line):
                # 提取注释内容作为分类
                comment = line.lstrip('//').lstrip('##').lstrip('&&').strip()
                if comment and not comment.startswith('lchliebedich') and not comment.startswith('这是注释'):
                    return comment
            else:
                # 遇到非注释非空行，停止查找
                break
        return None
    
    def _looks_like_trigger(self, line: str, index: int, lines: List[str]) -> bool:
        """判断是否像触发词"""
        # 改进的触发词判断逻辑
        # 1. 如果是变量定义、条件语句或特殊指令，不是触发词
        if (self._is_variable_definition(line) or 
            line.startswith('如果:') or line.startswith('if:') or
            line.startswith('#->var:') or
            line.startswith('else') or line.startswith('返回') or
            line.startswith('如果尾')):
            return False
        
        # 2. 检查前面是否有空行分隔（触发词通常在空行后）
        has_empty_line_before = False
        has_non_comment_before = False
        
        for i in range(index - 1, -1, -1):
            prev_line = lines[i].strip()
            if not prev_line:
                has_empty_line_before = True
                break
            if self._is_comment_line(prev_line):
                continue
            has_non_comment_before = True
            break
        
        # 3. 如果前面有非注释内容且没有空行分隔，很可能是响应内容
        if has_non_comment_before and not has_empty_line_before:
            return False
        
        # 4. 如果是文件开头或前面有空行/注释，可能是触发词
        return True
    
    def _is_variable_definition(self, line: str) -> bool:
        """判断是否为变量定义"""
        # 如果包含%变量%，很可能是回复内容而不是变量定义
        if '%' in line:
            return False
        
        # 形式1: K:V (单字节键)
        if re.match(r'^[a-zA-Z0-9]:.*', line):
            return True
        # 形式2: 键:值 (三字节键，通常是中文)
        if re.match(r'^.{1,3}:.*', line) and ':' in line:
            return True
        return False
    
    def _parse_variable_definition(self, line: str) -> Tuple[str, str]:
        """解析变量定义"""
        parts = line.split(':', 1)
        return parts[0].strip(), parts[1].strip()
    
    def _parse_line_variable(self, lines: List[str], start_index: int) -> Tuple[str, int]:
        """解析行变量"""
        content_lines = []
        i = start_index + 1
        
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            
            # 遇到另一个变量定义时停止
            if line_stripped.startswith('#->var:'):
                break
            
            # 遇到空行时停止（表示词条结束）
            if not line_stripped:
                break
                
            # 遇到注释行时停止
            if self._is_comment_line(line_stripped):
                break
                
            # 遇到下一个触发词时停止
            if self._looks_like_trigger(line_stripped, i, lines):
                break
            
            content_lines.append(line)
            i += 1
        
        return '\n'.join(content_lines), i
    
    def _parse_condition_block(self, lines: List[str], start_index: int) -> Tuple[List[str], int]:
        """解析条件语句块"""
        conditions = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('如果尾') or not line:
                break
            conditions.append(line)
            i += 1
        
        return conditions, i + 1
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """处理消息并返回回复"""
        self.message_context = context
        
        for entry in self.entries:
            if self._match_trigger(entry.trigger, message):
                return self._generate_response(entry, message)
        
        return None
    
    def _match_trigger(self, trigger: str, message: str) -> bool:
        """匹配触发词"""
        try:
            # 使用正则表达式匹配
            pattern = re.compile(trigger, re.IGNORECASE)
            match = pattern.search(message)
            
            if match:
                # 保存匹配的参数和括号内容
                self._save_match_params(match, message)
                return True
        except re.error:
            # 如果正则表达式无效，使用精确匹配
            return trigger == message
        
        return False
    
    def _save_match_params(self, match: re.Match, message: str):
        """保存匹配参数"""
        # 保存括号参数
        for i, group in enumerate(match.groups(), 1):
            self.global_variables[f'括号{i}'] = group or ''
        
        self.global_variables['括号量'] = str(len(match.groups()))
        
        # 保存参数（按空格分割）
        parts = message.split()
        for i, part in enumerate(parts[1:], 1):  # 跳过第一个词（触发词）
            self.global_variables[f'参数{i}'] = part
        
        self.global_variables['参数量'] = str(len(parts) - 1)
        self.global_variables['参数-1'] = message
    
    def _generate_response(self, entry: LexiconEntry, message: str) -> str:
        """生成回复内容"""
        # 设置局部变量
        local_vars = entry.variables.copy()
        
        # 处理条件语句
        if entry.conditions:
            response = self._process_conditions(entry.conditions)
            if response:
                return self._process_variables_and_functions(response)
        
        # 处理普通回复
        if entry.responses:
            response = '\n'.join(entry.responses)
            return self._process_variables_and_functions(response)
        
        return ''
    
    def _process_conditions(self, conditions: List[str]) -> Optional[str]:
        """处理条件语句"""
        i = 0
        while i < len(conditions):
            condition = conditions[i].strip()
            
            if condition.startswith('如果:') or condition.startswith('if:'):
                expr = condition[3:].strip()
                if self._evaluate_condition(expr):
                    # 收集if块的内容
                    i += 1
                    if_content = []
                    while i < len(conditions):
                        current_line = conditions[i].strip()
                        if current_line.startswith('返回'):
                            return ""
                        if current_line.startswith(('else', '如果尾')):
                            break
                        if_content.append(conditions[i])
                        i += 1
                    return '\n'.join(if_content)
                else:
                    # 跳到else块
                    i += 1
                    while i < len(conditions):
                        current_line = conditions[i].strip()
                        if current_line.startswith('返回'):
                            return ""
                        if current_line.startswith(('else', '如果尾')):
                            break
                        i += 1
                    if i < len(conditions) and conditions[i].strip().startswith('else'):
                        i += 1
                        else_content = []
                        while i < len(conditions):
                            current_line = conditions[i].strip()
                            if current_line.startswith('返回'):
                                return ""
                            if current_line.startswith('如果尾'):
                                break
                            else_content.append(conditions[i])
                            i += 1
                        return '\n'.join(else_content)
            i += 1
        
        return None
    
    def _evaluate_condition(self, expr: str) -> bool:
        """评估条件表达式"""
        # 处理变量替换
        expr = self._process_variables_and_functions(expr)
        
        try:
            # 简单的条件评估
            if '==' in expr:
                left, right = expr.split('==', 1)
                return left.strip() == right.strip()
            elif '!=' in expr:
                left, right = expr.split('!=', 1)
                return left.strip() != right.strip()
            elif '<=' in expr:
                left, right = expr.split('<=', 1)
                return float(left.strip()) <= float(right.strip())
            elif '>=' in expr:
                left, right = expr.split('>=', 1)
                return float(left.strip()) >= float(right.strip())
            elif '<' in expr:
                left, right = expr.split('<', 1)
                return float(left.strip()) < float(right.strip())
            elif '>' in expr:
                left, right = expr.split('>', 1)
                return float(left.strip()) > float(right.strip())
            elif '&' in expr:
                parts = expr.split('&')
                return all(self._evaluate_condition(part.strip()) for part in parts)
            elif '|' in expr:
                parts = expr.split('|')
                return any(self._evaluate_condition(part.strip()) for part in parts)
            else:
                # 处理数值条件：如果是数字，非零为真
                expr_stripped = expr.strip()
                try:
                    return float(expr_stripped) != 0
                except ValueError:
                    # 布尔值
                    return expr_stripped.lower() in ('true', '1', 'yes')
        except (ValueError, TypeError):
            return False
    
    def _process_variables_and_functions(self, text: str) -> str:
        """处理变量和函数"""
        # 处理变量 %变量名%
        def replace_variable(match):
            var_name = match.group(1)
            return str(self._get_variable_value(var_name))
        
        text = re.sub(r'%([^%]+)%', replace_variable, text)
        
        # 处理函数 $函数名 参数1 参数2$
        def replace_function(match):
            func_content = match.group(1)
            return str(self._call_function(func_content))
        
        text = re.sub(r'\$([^$]+)\$', replace_function, text)
        
        return text
    
    def _get_variable_value(self, var_name: str) -> Any:
        """获取变量值"""
        # 优先从全局变量获取
        if var_name in self.global_variables:
            return self.global_variables[var_name]
        
        # 从消息上下文获取
        if var_name in self.message_context:
            return self.message_context[var_name]
        
        # 内置变量
        builtin_vars = {
            'QQ': self.message_context.get('user_id', ''),
            'Uin': self.message_context.get('user_id', ''),
            '昵称': self.message_context.get('nickname', ''),
            'UinName': self.message_context.get('nickname', ''),
            '群号': self.message_context.get('group_id', ''),
            'GroupId': self.message_context.get('group_id', ''),
            '群': self.message_context.get('group_id', ''),
            'Groupid': self.message_context.get('group_id', ''),
            'MSG': self.message_context.get('raw_message', ''),
            'MSGJ': json.dumps(self.message_context, ensure_ascii=False),
            '登录账号': self.message_context.get('self_id', ''),
            'Account': self.message_context.get('self_id', ''),
            'Robot': self.message_context.get('self_id', ''),
            'MsgId': self.message_context.get('message_id', ''),
            '消息来源': self._get_message_source(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '时间戳': int(time.time()),
            '时间戳毫秒': int(time.time() * 1000),
            '时间': datetime.now().strftime('%H:%M:%S'),
            '日期': datetime.now().strftime('%Y-%m-%d'),
        }
        
        return builtin_vars.get(var_name, '')
    
    def _get_message_source(self) -> str:
        """获取消息来源"""
        if self.message_context.get('message_type') == 'group':
            return '群聊消息'
        elif self.message_context.get('message_type') == 'private':
            return '好友消息'
        else:
            return '其他消息'
    
    def _call_function(self, func_content: str) -> Any:
        """调用函数"""
        parts = func_content.strip().split()
        if not parts:
            return ''
        
        func_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if func_name in self.functions:
            try:
                return self.functions[func_name](*args)
            except Exception as e:
                print(f"函数调用错误 {func_name}: {e}")
                return ''
        
        return ''
    
    # 内置函数实现
    def _random_func(self, *args):
        """随机数函数"""
        if len(args) == 2:
            try:
                return random.randint(int(args[0]), int(args[1]))
            except ValueError:
                return 0
        elif len(args) == 1:
            # 从数组中随机选择
            try:
                arr = json.loads(self._get_variable_value(args[0]))
                return random.choice(arr)
            except:
                return 0
        return random.randint(1, 100)
    
    def _file_size_func(self, file_path: str):
        """文件大小函数"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    def _variable_func(self, var_name: str, value: str):
        """设置变量函数"""
        self.global_variables[var_name] = value
        return ''
    
    def _get_variable_func(self, var_name: str):
        """获取变量函数"""
        return self._get_variable_value(var_name)
    
    def _read_config_func(self, path: str, key: str, default: str = ''):
        """读取配置函数"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get(key, default)
        except (FileNotFoundError, json.JSONDecodeError):
            return default
        except Exception as e:
            print(f"读取配置文件失败 {path}: {e}")
            return default
    
    def _write_config_func(self, path: str, key: str, value: str):
        """写入配置函数"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            config = {}
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        config = json.load(f)
                    except json.JSONDecodeError:
                        # 文件内容为空或不是有效JSON，则初始化为空字典
                        config = {}
            config[key] = value
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return ''
        except Exception as e:
            print(f"写入配置文件失败 {path}: {e}")
            return ''
    
    def _image_func(self, url: str):
        """图片函数"""
        return f'[CQ:image,file={url}]'
    
    def _gif_func(self, url: str):
        """动图函数"""
        return f'[CQ:image,file={url}]'
    
    def _flash_image_func(self, url: str):
        """闪照函数"""
        return f'[CQ:image,file={url},type=flash]'
    
    def _voice_func(self, duration: str, url: str):
        """语音函数"""
        return f'[CQ:record,file={url}]'
    
    def _emoji_func(self, emoji_id: str):
        """表情函数"""
        return f'[CQ:face,id={emoji_id}]'
    
    def _super_emoji_func(self, emoji_id: str):
        """超级表情函数"""
        return f'[CQ:face,id={emoji_id}]'
    
    def _send_func(self, *args):
        """发送函数"""
        # 简化实现，实际应该调用发送接口
        return ''
    
    def _new_message_func(self, msg_id: str):
        """新建消息函数"""
        self.global_variables[f'msg_{msg_id}'] = {}
        return ''
    
    def _add_message_func(self, *args):
        """添加消息函数"""
        # 简化实现
        return ''
    
    def _send_message_func(self, msg_id: str, result_var: str = ''):
        """发送消息函数"""
        # 简化实现
        return ''
    
    def _exists_message_func(self, tag: str):
        """检查消息是否存在"""
        return tag in self.message_context
    
    def _get_message_func(self, *args):
        """获取消息函数"""
        if len(args) == 1:
            return self.message_context.get(args[0], '')
        elif len(args) == 2:
            return self.message_context.get(args[0], args[1])
        return ''
    
    def _is_group_message_func(self):
        """判断是否为群聊消息"""
        return 1 if self.message_context.get('message_type') == 'group' else 0
    
    def _is_friend_message_func(self):
        """判断是否为好友消息"""
        return 1 if self.message_context.get('message_type') == 'private' else 0
    
    def _is_temp_message_func(self):
        """判断是否为临时消息"""
        return 0  # 简化实现
    
    def _is_system_message_func(self):
        """判断是否为系统消息"""
        return 0  # 简化实现
    
    def _is_unauthorized_func(self):
        """判断是否未授权"""
        return 0  # 简化实现