    
from playwright.sync_api import sync_playwright, expect
import pandas as pd
import logging
from datetime import datetime
import time
import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='drug_automation.log',
    encoding='utf-8'
)

# 当前时间和默认用户
CURRENT_TIME = "2025-04-30 10:27:46"
DEFAULT_USERNAME = "lengxiaohua123"
DEFAULT_PASSWORD = "test123"

class DrugAutomation:
    def __init__(self, url="http://localhost:5000", message_queue=None):
        self.url = url
        self.current_time = CURRENT_TIME
        self.message_queue = message_queue
        self.setup_browser()
        
    def log_message(self, message, level="info"):
        """发送日志消息到队列"""
        if self.message_queue:
            self.message_queue.put((level, message))
        if level == "info":
            logging.info(message)
        elif level == "error":
            logging.error(message)
    
    def setup_browser(self):
        """初始化 Playwright"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,  # 显示浏览器界面
            )
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.log_message("Playwright 初始化成功")
        except Exception as e:
            self.log_message(f"Playwright 初始化失败: {str(e)}", "error")
            raise
        
    def login(self, username, password):
        """登录系统"""
        try:
            self.page.goto(self.url)
            
            # 填写登录表单
            self.page.fill("#username", username)
            self.page.fill("#password", password)
            
            # 提交表单
            self.page.click('button[type="submit"]')
            
            # 等待页面加载完成（等待查询按钮出现）
            self.page.wait_for_selector(".search-btn")
            
            self.log_message(f"登录成功: {username}")
            return True
            
        except Exception as e:
            self.log_message(f"登录失败: {str(e)}", "error")
            return False

    def search_drug(self, drug_name):
        """搜索药品并返回是否存在"""
        try:
            # 清空搜索框并输入药品名称
            search_input = self.page.locator("#drug_search")
            search_input.clear()
            search_input.fill(drug_name)
            
            # 点击搜索按钮
            self.page.click(".search-btn")
            
            # 等待表格更新
            self.page.wait_for_timeout(1000)
            
            # 检查结果
            rows = self.page.query_selector_all("#drug-table-body tr")
            for row in rows:
                name_cell = row.query_selector("td")
                if name_cell and drug_name in name_cell.inner_text():
                    self.log_message(f"找到药品: {drug_name}")
                    return True
            
            self.log_message(f"未找到药品: {drug_name}")
            return False
            
        except Exception as e:
            self.log_message(f"搜索药品失败: {str(e)}", "error")
            return False
    
    def add_drug(self, drug_name, specification):
        """添加新药品"""
        try:
            # 点击添加按钮
            self.page.click(".add-btn")
            
            # 等待模态框出现并填写表单
            self.page.wait_for_selector("#drugModal")
            
            self.page.fill("#drug_name", drug_name)
            self.page.fill("#specification", specification)
            
            # 提交表单
            self.page.click(".submit-btn")
            
            # 等待模态框消失
            self.page.wait_for_selector("#drugModal", state="hidden")
            
            self.log_message(f"成功添加药品: {drug_name}")
            return True
            
        except Exception as e:
            self.log_message(f"添加药品失败: {str(e)}", "error")
            return False
    
    def process_drug(self, drug_name, specification):
        """处理单个药品：先查询，不存在则添加"""
        try:
            # 先查询药品是否存在
            exists = self.search_drug(drug_name)
            
            if not exists:
                # 药品不存在，添加新药品
                if self.add_drug(drug_name, specification):
                    self.log_message(f"成功添加新药品: {drug_name}")
                    return True
                else:
                    self.log_message(f"添加药品失败: {drug_name}", "error")
                    return False
            else:
                self.log_message(f"药品已存在，无需添加: {drug_name}")
                return True
                
        except Exception as e:
            self.log_message(f"处理药品失败: {drug_name}, 错误: {str(e)}", "error")
            return False
    
    def batch_process_from_excel(self, excel_file):
        """从Excel文件批量处理药品"""
        try:
            df = pd.read_excel(excel_file)
            total = len(df)
            success = 0
            
            for index, row in df.iterrows():
                if self.process_drug(row['通用名'], row['规格']):
                    success += 1
                # 添加延迟避免太快
                self.page.wait_for_timeout(1000)
            
            self.log_message(f"批量处理完成，成功: {success}/{total}")
            return success
            
        except Exception as e:
            self.log_message(f"批量处理失败: {str(e)}", "error")
            return 0
    
    def close(self):
        """关闭浏览器"""
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            self.log_message("浏览器已关闭")
        except Exception as e:
            self.log_message(f"关闭浏览器失败: {str(e)}", "error")

class AutomationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("药品字典管理自动化")
        self.root.geometry("800x700")  # 增加窗口高度以适应新的登录字段
        
        self.message_queue = queue.Queue()
        self.automation = None
        
        self.create_widgets()
        self.update_log()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 登录区域
        login_frame = ttk.LabelFrame(main_frame, text="登录信息", padding="5")
        login_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # URL输入
        ttk.Label(login_frame, text="系统URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_var = tk.StringVar(value="http://localhost:5000")
        ttk.Entry(login_frame, textvariable=self.url_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # 用户名输入
        ttk.Label(login_frame, text="用户名:").grid(row=1, column=0, sticky=tk.W)
        self.username_var = tk.StringVar(value=DEFAULT_USERNAME)
        ttk.Entry(login_frame, textvariable=self.username_var).grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # 密码输入
        ttk.Label(login_frame, text="密码:").grid(row=2, column=0, sticky=tk.W)
        self.password_var = tk.StringVar(value=DEFAULT_PASSWORD)
        ttk.Entry(login_frame, textvariable=self.password_var, show="*").grid(row=2, column=1, sticky=(tk.W, tk.E))
        
        # 登录按钮
        ttk.Button(login_frame, text="登录系统", command=self.start_automation).grid(row=1, column=2, rowspan=2, padx=5)
        
        # 显示当前时间和用户信息
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(info_frame, text=f"当前时间: {CURRENT_TIME}").grid(row=0, column=0, sticky=tk.W)
        
        # 单个药品添加区域
        single_frame = ttk.LabelFrame(main_frame, text="添加单个药品", padding="5")
        single_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(single_frame, text="药品名称:").grid(row=0, column=0, sticky=tk.W)
        self.drug_name_var = tk.StringVar()
        ttk.Entry(single_frame, textvariable=self.drug_name_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(single_frame, text="规格:").grid(row=1, column=0, sticky=tk.W)
        self.spec_var = tk.StringVar()
        ttk.Entry(single_frame, textvariable=self.spec_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        ttk.Button(single_frame, text="添加", command=self.add_single_drug).grid(row=1, column=2, padx=5)
        
        # 批量导入区域
        batch_frame = ttk.LabelFrame(main_frame, text="批量导入", padding="5")
        batch_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(batch_frame, text="选择Excel文件", command=self.select_excel).grid(row=0, column=0, sticky=tk.W)
        self.file_label = ttk.Label(batch_frame, text="未选择文件")
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Button(batch_frame, text="开始导入", command=self.start_batch_import).grid(row=0, column=2, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置权重使日志区域可扩展
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
    def start_automation(self):
        """启动自动化实例"""
        try:
            username = self.username_var.get()
            password = self.password_var.get()
            
            if not username or not password:
                self.log_text.insert(tk.END, "请输入用户名和密码\n")
                return
                
            self.automation = DrugAutomation(self.url_var.get(), self.message_queue)
            if self.automation.login(username, password):
                self.log_text.insert(tk.END, f"系统登录成功 - 用户: {username}\n")
            else:
                self.log_text.insert(tk.END, "系统登录失败\n")
        except Exception as e:
            self.log_text.insert(tk.END, f"启动失败: {str(e)}\n")

    def add_single_drug(self):
        """添加单个药品"""
        if not self.automation:
            self.log_text.insert(tk.END, "请先登录系统\n")
            return
        
        drug_name = self.drug_name_var.get()
        spec = self.spec_var.get()
        
        if not drug_name or not spec:
            self.log_text.insert(tk.END, "请输入药品名称和规格\n")
            return
        
        threading.Thread(target=self._add_single_drug, args=(drug_name, spec)).start()
    
    def _add_single_drug(self, drug_name, spec):
        """在新线程中添加药品"""
        self.automation.process_drug(drug_name, spec)
        
    def select_excel(self):
        """选择Excel文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx;*.xls")],
            title="选择药品数据Excel文件"
        )
        if file_path:
            self.file_label.config(text=file_path)
            self.excel_file = file_path
    
    def start_batch_import(self):
        """开始批量导入"""
        if not hasattr(self, 'excel_file'):
            self.log_text.insert(tk.END, "请先选择Excel文件\n")
            return
        
        if not self.automation:
            self.log_text.insert(tk.END, "请先登录系统\n")
            return
        
        threading.Thread(target=self._batch_import).start()
    
    def _batch_import(self):
        """在新线程中执行批量导入"""
        self.automation.batch_process_from_excel(self.excel_file)
    
    def update_log(self):
        """更新日志显示"""
        try:
            while True:
                level, message = self.message_queue.get_nowait()
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.update_log)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = AutomationGUI()
    gui.run()
    
    
