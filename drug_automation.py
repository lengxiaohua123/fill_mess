from playwright.sync_api import sync_playwright, expect
import pandas as pd
import logging
from datetime import datetime
import time
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='drug_automation.log',
    encoding='utf-8'
)

class DrugAutomation:
    def __init__(self, url="http://localhost:5000"):
        self.url = url
        self.current_time = "2025-04-30 10:10:55"
        self.username = "lengxiaohua123"
        self.setup_browser()
        
    def setup_browser(self):
        """初始化 Playwright"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,  # 显示浏览器界面
            )
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            logging.info("Playwright 初始化成功")
        except Exception as e:
            logging.error(f"Playwright 初始化失败: {str(e)}")
            raise
        
    def login(self, username="lengxiaohua123", password="test123"):
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
            
            logging.info(f"登录成功: {username}")
            return True
            
        except Exception as e:
            logging.error(f"登录失败: {str(e)}")
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
                    logging.info(f"找到药品: {drug_name}")
                    return True
            
            logging.info(f"未找到药品: {drug_name}")
            return False
            
        except Exception as e:
            logging.error(f"搜索药品失败: {str(e)}")
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
            
            logging.info(f"成功添加药品: {drug_name}")
            return True
            
        except Exception as e:
            logging.error(f"添加药品失败: {str(e)}")
            return False
    
    def process_drug(self, drug_name, specification):
        """处理单个药品：先查询，不存在则添加"""
        try:
            # 先查询药品是否存在
            exists = self.search_drug(drug_name)
            
            if not exists:
                # 药品不存在，添加新药品
                if self.add_drug(drug_name, specification):
                    logging.info(f"成功添加新药品: {drug_name}")
                    return True
                else:
                    logging.error(f"添加药品失败: {drug_name}")
                    return False
            else:
                logging.info(f"药品已存在，无需添加: {drug_name}")
                return True
                
        except Exception as e:
            logging.error(f"处理药品失败: {drug_name}, 错误: {str(e)}")
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
            
            logging.info(f"批量处理完成，成功: {success}/{total}")
            return success
            
        except Exception as e:
            logging.error(f"批量处理失败: {str(e)}")
            return 0
    
    def close(self):
        """关闭浏览器"""
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            logging.info("浏览器已关闭")
        except Exception as e:
            logging.error(f"关闭浏览器失败: {str(e)}")

def main():
    # 示例数据
    test_drugs = [
        {"name": "琥珀安神丸", "spec": "3ml:300IU/瓶提纯剂/支/盒"},
        {"name": "牡蛎丸", "spec": "10g:0.1g/支/盒"},
        {"name": "维生素B12片", "spec": "25μg*100片/瓶"}
    ]
    
    automation = DrugAutomation()
    
    try:
        # 登录系统
        if not automation.login():
            raise Exception("登录失败")
        
        # 处理测试数据
        for drug in test_drugs:
            automation.process_drug(drug["name"], drug["spec"])
        
        # 如果有 Excel 文件，也可以批量处理
        # automation.batch_process_from_excel("drug_data.xlsx")
        
    except Exception as e:
        logging.error(f"自动化过程出错: {str(e)}")
    
    finally:
        automation.close()

if __name__ == "__main__":
    main()