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
    filename='drug_automation.log'
)

class DrugAutomation:
    def __init__(self, url="http://localhost:5000"):
        self.url = url
        self.current_time = "2025-04-30 09:47:49"
        self.username = "lengxiaohua123"
        self.setup_browser()

    def setup_browser(self):
        """初始化 Playwright"""
        try:
            self.playwright = sync_playwright().start()

            # 配置浏览器选项
            browser_options = {
                "headless": False,  # 设置为 True 则不显示浏览器界面
                "args": [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--ignore-certificate-errors',  # 忽略证书错误
                ]
            }

            # 尝试启动 Chromium
            try:
                self.browser = self.playwright.chromium.launch(**browser_options)
            except Exception as e:
                logging.warning(f"无法启动 Chromium，尝试使用系统 Chrome: {str(e)}")
                # 如果 Chromium 启动失败，尝试使用系统 Chrome
                browser_options["channel"] = "chrome"
                self.browser = self.playwright.chromium.launch(**browser_options)

            self.context = self.browser.new_context(ignore_https_errors=True)
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

    def search_drug(self, drug_name="", operator="", status="all", date_from="", date_to=""):
        """搜索药品"""
        try:
            # 填写搜索条件
            self.page.fill("#drug_search", drug_name)
            self.page.fill("#operator", operator)

            if status != "all":
                self.page.select_option("#status", status)

            if date_from:
                self.page.fill("#date_from", date_from)
            if date_to:
                self.page.fill("#date_to", date_to)

            # 点击搜索按钮
            self.page.click(".search-btn")

            # 等待结果加载
            self.page.wait_for_timeout(1000)  # 等待1秒

            logging.info(f"搜索完成: {drug_name}")
            return True

        except Exception as e:
            logging.error(f"搜索失败: {str(e)}")
            return False

    def toggle_drug_status(self, drug_name):
        """切换药品状态"""
        try:
            # 先搜索药品
            self.search_drug(drug_name)

            # 找到对应行的状态按钮并点击
            rows = self.page.query_selector_all("#drug-table-body tr")
            for row in rows:
                name_cell = row.query_selector("td")
                if name_cell and drug_name in name_cell.inner_text():
                    status_btn = row.query_selector(".status-btn")
                    if status_btn:
                        status_btn.click()
                        break

            # 等待操作完成
            self.page.wait_for_timeout(1000)

            logging.info(f"成功切换药品状态: {drug_name}")
            return True

        except Exception as e:
            logging.error(f"切换状态失败: {str(e)}")
            return False

    def edit_drug(self, old_drug_name, new_drug_name, new_specification):
        """编辑药品信息"""
        try:
            # 先搜索药品
            self.search_drug(old_drug_name)

            # 找到对应行的编辑按钮并点击
            rows = self.page.query_selector_all("#drug-table-body tr")
            for row in rows:
                name_cell = row.query_selector("td")
                if name_cell and old_drug_name in name_cell.inner_text():
                    edit_btn = row.query_selector(".edit-btn")
                    if edit_btn:
                        edit_btn.click()
                        break

            # 等待模态框出现并填写新信息
            self.page.wait_for_selector("#drugModal")

            self.page.fill("#drug_name", new_drug_name)
            self.page.fill("#specification", new_specification)

            # 提交修改
            self.page.click(".submit-btn")

            # 等待模态框消失
            self.page.wait_for_selector("#drugModal", state="hidden")

            logging.info(f"成功编辑药品: {old_drug_name} -> {new_drug_name}")
            return True

        except Exception as e:
            logging.error(f"编辑药品失败: {str(e)}")
            return False

    def batch_add_drugs_from_excel(self, excel_file):
        """从Excel文件批量添加药品"""
        try:
            df = pd.read_excel(excel_file)
            success_count = 0

            for index, row in df.iterrows():
                if self.add_drug(row['通用名'], row['规格']):
                    success_count += 1
                # 添加延迟避免太快
                self.page.wait_for_timeout(1000)

            logging.info(f"批量添加完成，成功添加 {success_count}/{len(df)} 条记录")
            return success_count

        except Exception as e:
            logging.error(f"批量添加失败: {str(e)}")
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
    # 示例用法
    automation = DrugAutomation()

    try:
        # 登录系统
        if not automation.login():
            raise Exception("登录失败")

        # 准备测试数据
        test_drugs = [
            {"name": "琥珀安神丸", "spec": "3ml:300IU/瓶提纯剂/支/盒"},
            {"name": "牡蛎丸", "spec": "10g:0.1g/支/盒"},
            {"name": "维生素B12片", "spec": "25μg*100片/瓶"}
        ]

        # 添加测试数据
        for drug in test_drugs:
            automation.add_drug(drug["name"], drug["spec"])

        # 搜索示例
        automation.search_drug(
            drug_name="维生素",
            operator="lengxiaohua123",
            status="enabled"
        )

        # 编辑示例
        automation.edit_drug(
            "维生素B12片",
            "维生素B12片",
            "25μg*100片/瓶"
        )

        # 切换状态示例
        automation.toggle_drug_status("维生素B12片")

        # 从Excel文件批量导入（如果有文件的话）
        # automation.batch_add_drugs_from_excel("drug_data.xlsx")

    except Exception as e:
        logging.error(f"自动化过程出错: {str(e)}")

    finally:
        automation.close()

if __name__ == "__main__":
    main()