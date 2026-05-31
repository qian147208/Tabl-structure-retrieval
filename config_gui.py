import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from db.factory import DatabaseConnectionFactory

class DatabaseConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("数据库连接配置")
        self.root.geometry("500x400")
        self.root.resizable(True, True)

        # 配置文件路径
        self.config_file = "db_config.json"

        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 数据库类型选择
        self.db_type_var = tk.StringVar(value="mysql")

        # 创建界面元素
        self.create_widgets()

        # 加载配置
        self.load_config()

    def create_widgets(self):
        # 标题
        title = ttk.Label(self.main_frame, text="数据库连接配置", font=("SimHei", 16, "bold"))
        title.pack(pady=10)

        # 数据库类型选择
        db_type_frame = ttk.LabelFrame(self.main_frame, text="数据库类型", padding="10")
        db_type_frame.pack(fill=tk.X, pady=5)

        db_types = ["mysql", "postgresql", "oracle"]
        for i, db_type in enumerate(db_types):
            ttk.Radiobutton(
                db_type_frame,
                text=db_type.capitalize(),
                variable=self.db_type_var,
                value=db_type
            ).grid(row=0, column=i, padx=10)

        # 连接参数
        params_frame = ttk.LabelFrame(self.main_frame, text="连接参数", padding="10")
        params_frame.pack(fill=tk.X, pady=5)

        # 主机
        ttk.Label(params_frame, text="主机:", width=10).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar(value="localhost")
        ttk.Entry(params_frame, textvariable=self.host_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)

        # 端口
        ttk.Label(params_frame, text="端口:", width=10).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value="3306")
        ttk.Entry(params_frame, textvariable=self.port_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=5)

        # 用户名
        ttk.Label(params_frame, text="用户名:", width=10).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.user_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.user_var, width=30).grid(row=2, column=1, sticky=tk.W, pady=5)

        # 密码
        ttk.Label(params_frame, text="密码:", width=10).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.password_var, show="*", width=30).grid(row=3, column=1, sticky=tk.W, pady=5)

        # 数据库名
        ttk.Label(params_frame, text="数据库名:", width=10).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.database_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.database_var, width=30).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Schema (仅PostgreSQL)
        ttk.Label(params_frame, text="Schema:", width=10).grid(row=5, column=0, sticky=tk.W, pady=5)
        self.schema_var = tk.StringVar(value="public")
        self.schema_entry = ttk.Entry(params_frame, textvariable=self.schema_var, width=30)
        self.schema_entry.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 测试连接按钮
        ttk.Button(
            button_frame,
            text="测试连接",
            command=self.test_connection
        ).pack(side=tk.LEFT, padx=5)

        # 保存配置按钮
        ttk.Button(
            button_frame,
            text="保存配置",
            command=self.save_config
        ).pack(side=tk.LEFT, padx=5)

        # 加载配置按钮
        ttk.Button(
            button_frame,
            text="加载配置",
            command=self.load_config
        ).pack(side=tk.LEFT, padx=5)

        # 退出按钮
        ttk.Button(
            button_frame,
            text="退出",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=5)

    def _validate_port(self):
        """验证端口号是否为有效数字"""
        try:
            port = int(self.port_var.get())
            if port < 1 or port > 65535:
                messagebox.showerror("参数错误", "端口必须在1-65535之间")
                return None
            return port
        except ValueError:
            messagebox.showerror("参数错误", "端口必须是数字")
            return None

    def get_connection_params(self):
        """获取连接参数"""
        port = self._validate_port()
        if port is None:
            raise ValueError("端口参数无效")

        params = {
            "host": self.host_var.get(),
            "port": port,
            "user": self.user_var.get(),
            "password": self.password_var.get(),
            "database": self.database_var.get(),
            "schema": self.schema_var.get()
        }
        return params

    def test_connection(self):
        """测试数据库连接"""
        try:
            db_type = self.db_type_var.get()
            params = self.get_connection_params()

            # 创建连接对象
            connection = DatabaseConnectionFactory.create_connection(db_type, **params)

            # 测试连接
            connection.connect()
            connection.disconnect()

            messagebox.showinfo("测试成功", "数据库连接测试成功！")
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
        except Exception as e:
            messagebox.showerror("测试失败", f"连接测试失败: {str(e)}")

    def save_config(self):
        """保存配置到文件"""
        port = self._validate_port()
        if port is None:
            return

        config = {
            "db_type": self.db_type_var.get(),
            "host": self.host_var.get(),
            "port": port,
            "user": self.user_var.get(),
            "password": self.password_var.get(),
            "database": self.database_var.get(),
            "schema": self.schema_var.get()
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存成功", "配置已成功保存！")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存配置失败: {str(e)}")

    def load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # 设置数据库类型
                self.db_type_var.set(config.get("db_type", "mysql"))

                # 设置连接参数
                self.host_var.set(config.get("host", "localhost"))
                self.port_var.set(str(config.get("port", 3306)))
                self.user_var.set(config.get("user", ""))
                self.password_var.set(config.get("password", ""))
                self.database_var.set(config.get("database", ""))
                self.schema_var.set(config.get("schema", "public"))

                messagebox.showinfo("加载成功", "配置已成功加载！")
            except Exception as e:
                messagebox.showerror("加载失败", f"加载配置失败: {str(e)}")
        else:
            messagebox.showinfo("提示", "配置文件不存在，使用默认配置")

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseConfigGUI(root)
    root.mainloop()
