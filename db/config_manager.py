#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
统一管理数据库配置和导出配置
"""

import json
import os
from typing import Dict, Any, Optional, List
from .logger import get_logger
from .exceptions import ValidationError, handle_error

logger = get_logger()


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_FILE = "db_config.json"
    CONFIG_VERSION = "1.0"

    def __init__(self, config_file: str = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认使用db_config.json
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"配置已加载: {self.config_file}")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {str(e)}，使用默认配置")
                self.config = self._get_default_config()
        else:
            logger.info("配置文件不存在，使用默认配置")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": self.CONFIG_VERSION,
            "db_type": "mysql",
            "host": "localhost",
            "port": 3306,
            "user": "",
            "password": "",
            "database": "",
            "export": {
                "csv_dir": "data_dictionary",
                "excel_dir": "excel_output",
                "modules": {
                    "user": ["nm_user*", "sys_user*", "ob_user*"],
                    "order": ["cp_*", "ob_call*"],
                    "product": ["fi_prod*", "rob_*"],
                    "business": ["cti_*", "t_*"]
                }
            }
        }

    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False

    def get_db_config(self) -> Dict[str, Any]:
        """获取数据库配置
        
        Returns:
            Dict: 数据库连接配置
        """
        return {
            "db_type": self.config.get("db_type", "mysql"),
            "host": self.config.get("host", "localhost"),
            "port": self.config.get("port", 3306),
            "user": self.config.get("user", ""),
            "password": self.config.get("password", ""),
            "database": self.config.get("database", "")
        }

    def set_db_config(self, db_type: str = None, host: str = None, 
                     port: int = None, user: str = None, 
                     password: str = None, database: str = None) -> None:
        """设置数据库配置
        
        Args:
            db_type: 数据库类型
            host: 主机地址
            port: 端口
            user: 用户名
            password: 密码
            database: 数据库名
        """
        if db_type is not None:
            self.config["db_type"] = db_type
        if host is not None:
            self.config["host"] = host
        if port is not None:
            self.config["port"] = port
        if user is not None:
            self.config["user"] = user
        if password is not None:
            self.config["password"] = password
        if database is not None:
            self.config["database"] = database

    def get_export_config(self) -> Dict[str, Any]:
        """获取导出配置
        
        Returns:
            Dict: 导出配置
        """
        return self.config.get("export", self._get_default_config()["export"])

    def validate_config(self) -> tuple:
        """验证配置是否完整和有效
        
        Returns:
            tuple: (是否有效, 错误信息列表)
        """
        errors = []
        
        if not self.config.get("db_type"):
            errors.append("数据库类型不能为空")
        
        if not self.config.get("host"):
            errors.append("主机地址不能为空")
        
        if not self.config.get("port"):
            errors.append("端口不能为空")
        
        if not self.config.get("user"):
            errors.append("用户名不能为空")
        
        if not self.config.get("database"):
            errors.append("数据库名不能为空")
        
        is_valid = len(errors) == 0
        return is_valid, errors

    def has_config(self) -> bool:
        """检查配置文件是否存在
        
        Returns:
            bool: 配置文件是否存在
        """
        return os.path.exists(self.config_file)


class ExportOptions:
    """导出选项"""

    def __init__(self):
        self.export_csv: bool = True
        self.export_excel: bool = True
        self.selected_tables: Optional[List[str]] = None
        self.output_csv_dir: str = "data_dictionary"
        self.output_excel_dir: str = "excel_output"
        self.module_mapping: Optional[Dict[str, List[str]]] = None
        self.show_confirmation: bool = True

    @classmethod
    def from_config(cls, config_manager: ConfigManager) -> 'ExportOptions':
        """从配置管理器创建导出选项
        
        Args:
            config_manager: 配置管理器
        
        Returns:
            ExportOptions: 导出选项对象
        """
        options = cls()
        export_config = config_manager.get_export_config()
        
        options.output_csv_dir = export_config.get("csv_dir", "data_dictionary")
        options.output_excel_dir = export_config.get("excel_dir", "excel_output")
        options.module_mapping = export_config.get("modules", {})
        
        return options

    def __str__(self) -> str:
        parts = []
        parts.append(f"导出CSV: {'是' if self.export_csv else '否'}")
        parts.append(f"导出Excel: {'是' if self.export_excel else '否'}")
        if self.selected_tables:
            parts.append(f"选中表数量: {len(self.selected_tables)}")
        else:
            parts.append("选中表: 全部")
        parts.append(f"CSV输出目录: {self.output_csv_dir}")
        parts.append(f"Excel输出目录: {self.output_excel_dir}")
        return ", ".join(parts)