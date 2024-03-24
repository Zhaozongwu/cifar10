import sys
import traceback
from urllib import parse
import pymysql
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QDate
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QMenu,
                             QAction, QPlainTextEdit, QStyle, QFileDialog,
                             QMessageBox, QComboBox, QTreeWidgetItem, QTableWidgetItem, QPushButton, QCheckBox,
                             QHBoxLayout)
from pymysql import Connection
from sqlalchemy import create_engine, text
from taosrest import connect, cursor
from ui.main_page import Ui_MainPage
from ui.eval_task import Ui_EvalTask
from ui.report_out import Ui_ReportOut
from ui.Basic1 import Ui_Basic_info
from ui.Eval_Choose import Ui_Eval_Choose
from Dao.read_db import OperateTD

#EVAL_PROJECTE_NAME = show_confirmation_dialog(self)
class BasicInformation(QWidget, Ui_Basic_info):
    """
        基础配置页面
    """
    def __init__(self):
        super(BasicInformation, self).__init__()
        self.db = self.connect_to_database()
        self.setupUi(self)
        self.page_ini()
        self.search_database()  # 页面初始化时调用，展示所有项目
        self.is_edit_mode = True
        self.selected_project_name = ""
        self.project_name = ""
        self.history_database()
        # self.update_textedit()

    def page_ini(self):
        self.controller()
        # self.search_database()  # 默认展示查询所有内容

    def controller(self):
        """
        定义槽函数
        :return:
        """
        self.history.clicked.connect(self.switch)
        self.pushButton_5.clicked.connect(self.switch)
        self.choose.clicked.connect(self.search_database)  # 关键词筛选
        self.key.returnPressed.connect(self.search_database)  # 回车键触发搜索
        self.textEdit.itemClicked.connect(self.update_panel_with_project)  # 选择项目时更新
        self.lineEdit_6.dateTimeChanged.connect(self.on_datetime_changed)  # 筛选日期-吊装时间 selected_date = datetime.date()
        self.lineEdit_7.dateTimeChanged.connect(self.on_datetime_changed)  # 筛选日期-并网时间
        self.textEdit.cellClicked.connect(self.handle_cell_clicked)  #

        self.next11.clicked.connect(self.enable_edit_model)  # 点击编辑按钮时，可更改信息
        self.builditems.clicked.connect(self.handle_new_project)  # 点击新建项目，填写信息
        self.start_eval.clicked.connect(self.show_confirmation_dialog)  # 点击开始评估跳出弹窗

        self.choose2.clicked.connect(self.history_database)  # 关键词筛选
        self.key2.returnPressed.connect(self.history_database)  # 回车键触发搜索
        self.textEdit_2.itemClicked.connect(self.update_textedit)  # 选择项目时更新
        self.textEdit_2.itemClicked.connect(self.on_project_selected)


    def engine_conn(self):
        psw = parse.quote_plus('fenxizu#user')
        engine = create_engine("mysql+pymysql://fenxizu:{0}@192.168.0.61:3306/post_eval?charset=utf8".format(psw))
        return engine

    def connect_to_database(self):
        try:
            db = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                password='123456',
                database='post_eval'
            )
            return db
        except Exception as e:
            print("连接数据库时出现错误：", str(e))
            return None

    def switch(self):
        """
        项目信息配置 & 历史项目总览 交互
        :return:
        """
        sender = self.sender().objectName()
        index = {
            "history": 1,
            "pushButton_5": 0
        }
        if sender in index:
            print(f"sender = {sender} index[sender] = {index[sender]}")
            self.stackedWidget.setCurrentIndex(index[sender])
            if index[sender] == 1:
                total_count, completed, plan = self.update_eval_item_operation()
                self.lineEdit_13.setText(str(total_count))
                self.lineEdit_14.setText(str(completed))
                self.lineEdit_15.setText(str(plan))
                self.fill_table()

    def resizeEvent(self, event):
        """
        使表格大小自适应窗口大小
        :param event:
        :return:
        """
        window_width = self.width()
        col_widths = [int(window_width * factor) for factor in [1]]
        for col, width in enumerate(col_widths):
            self.textEdit.setColumnWidth(col, width)
            self.textEdit_2.setColumnWidth(col, width)

    def on_datetime_changed(self, datetime):
        """
        筛选日期
        """
        selected_date = datetime.date()
        print(f"selected date:{selected_date}")

    def save_project_to_database(self):
        """
        写入数据库，更新表eval_item_operation
        :return:
        """
        eval_project_name = self.lineEdit_2.text()  # 项目名称
        eval_project_id = self.lineEdit_3.text()  # 项目编号
        try:
            with self.db.cursor() as cursor:
                query = "SELECT * FROM eval_item_operation_copy WHERE eval_project_name = %s AND eval_project_id = %s"
                cursor.execute(query, (eval_project_name, eval_project_id))
                existing_project = cursor.fetchone()

                if not existing_project:
                    cursor.execute("SELECT * FROM eval_item_list")
                    all_rows = cursor.fetchall()

                    for row in all_rows:
                        eval_sys = row[1]
                        eval_sys_node = row[2]
                        eval_list = row[3]
                        eval_list_node = row[4]
                        eval_item = row[5]
                        eval_item_node = row[6]
                        eval_content = row[7]
                        eval_content_node = row[8]
                        eval_std = row[9]
                        eval_department = row[10]
                        eval_person = row[11]
                        review_person = row[12]
                        insert_subitem_query = "INSERT INTO eval_item_operation_copy (eval_project_id, eval_project_name, eval_sys, eval_sys_node, eval_list, eval_list_node, eval_item, eval_item_node," \
                                       "eval_content, eval_content_node, eval_std,eval_department,eval_person,review_person)" \
                                                   " VALUES  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s)"
                        cursor.execute(insert_subitem_query, (eval_project_id, eval_project_name,eval_sys, eval_sys_node,eval_list, eval_list_node, eval_item, eval_item_node,
                                                              eval_content, eval_content_node, eval_std,eval_department,eval_person,review_person))
                    self.db.commit()
                    print("Project added successfuly")
                else:
                    print("Project already exists")
        except Exception as e:
            print("Error:", e)
            self.db.rollback()


    def search_database(self):
        """
        根据条件查询项目类别信息
        连接搜索按钮
        """
        try:
            search_query = self.key.text()
            cursor = self.db.cursor()
            # 清空表格中的所有行
            self.textEdit.clearContents()
            self.textEdit.setRowCount(0)

            # 处理查询结果
            if not search_query:
                query_all = "select project_name from post_basic_information"
                cursor.execute(query_all)
                result_list_all = [str(row[0]) for row in cursor.fetchall()]
                for row, project_name in enumerate(result_list_all):
                    self.textEdit.insertRow(row)  # 插入新行
                    item = QTableWidgetItem(project_name)  # 创建单元格项目
                    self.textEdit.setItem(row, 0, item)  # 将项目名称添加到表格中
            else:
                query_match = f"select project_name from post_basic_information where project_name like '%{search_query}%'"
                cursor.execute(query_match)
                result_list_match = [str(row[0]) for row in cursor.fetchall()]
                for row, project_name in enumerate(result_list_match):
                    self.textEdit.insertRow(row)  # 插入新行
                    item = QTableWidgetItem(project_name)  # 创建单元格项目
                    self.textEdit.setItem(row, 0, item)  # 将项目名称添加到表格中
        except Exception as e:
            print(f"Error in search_database: {str(e)}")
        finally:
            cursor.close()

    def handle_cell_clicked(self,row, column):
        """
        从数据库获取项目名称
        :param row:
        :param column:
        :return:
        """
        project_name_item = self.textEdit.item(row, column)
        if project_name_item:
            selected_project = project_name_item.text()
            self.update_panel_with_project(selected_project)

    def get_detailed_info_from_database(self, selected_project):
        """
        从数据库中获取项目详细信息
        """
        self.db.ping(reconnect=True)
        cursor = self.db.cursor()
        query = f"select * " \
                f"from post_basic_information " \
                f" where project_name like '%{selected_project}%'"
        cursor.execute(query)

        # 获取查询结果
        row = cursor.fetchone()
        detailed_info = {f: str(row[i]) if row and len(row) > i else "" for i, f in enumerate([
            "project_name", "project_number", "lifting_time", "connection_time", "assessment_period", "farm_location",
             "wind_configuration", "assessment_status", "project_manager", "sample_number"
        ], start=1)}
        cursor.close()
        return detailed_info

    def update_panel_with_project(self, selected_project):
        """
        填充项目右侧详细信息,未点击编辑按钮，此处为灰，且不可修改
        :param selected_project:
        :return:
        """
        if selected_project:
            detailed_info = self.get_detailed_info_from_database(selected_project)
            # 更新QlineEdit内容
            if hasattr(self, 'lineEdit_2'):
                self.selected_project_name = detailed_info.get("project_name", "")  # 存储项目名称
                self.lineEdit_2.setText(detailed_info.get("project_name", ""))  # 项目名称
                self.lineEdit_2.setEnabled(False)
                self.lineEdit_2.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_3'):
                self.lineEdit_3.setText(detailed_info.get("project_number", ""))  # 项目编号
                self.lineEdit_3.setEnabled(False)
                self.lineEdit_3.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_6'):
                lifting_time = detailed_info.get("lifting_time", "")
                lifting_time_format = "yyyy-mm-dd"
                lifting_time1 = QDateTime.fromString(lifting_time, lifting_time_format)
                self.lineEdit_6.setDateTime(lifting_time1)  # 吊装时间
                self.lineEdit_6.setEnabled(False)
                self.lineEdit_6.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_7'):
                connection_time = detailed_info.get("connection_time", "")
                connection_time_format = "yyyy-mm-dd"
                connection_time1 = QDateTime.fromString(connection_time, connection_time_format)
                self.lineEdit_7.setDateTime(connection_time1)  # 并网时间
                self.lineEdit_7.setEnabled(False)
                self.lineEdit_7.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_8'):
                self.lineEdit_8.setText(detailed_info.get("assessment_period", ""))  # 评估周期
                self.lineEdit_8.setEnabled(False)
                self.lineEdit_8.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_9'):
                self.lineEdit_9.setText(detailed_info.get("farm_location", ""))  # 风场位置
                self.lineEdit_9.setEnabled(False)
                self.lineEdit_9.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_10'):
                self.lineEdit_10.setText(detailed_info.get("wind_configuration", ""))  # 风机配置
                self.lineEdit_10.setEnabled(False)
                self.lineEdit_10.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_11'):
                assessment_status = detailed_info.get("assessment_status", "")  # 评估状态
                self.lineEdit_11.setEnabled(False)
                self.lineEdit_11.setStyleSheet("color: gray;")
                if assessment_status == "完成":
                    self.lineEdit_11.setCurrentText("完成")
                elif assessment_status == "计划":
                    self.lineEdit_11.setCurrentText("计划")
                elif assessment_status == "进行":
                    self.lineEdit_11.setCurrentText("进行")
                else:
                    self.lineEdit_11.setCurrentText("null")
            if hasattr(self, 'lineEdit_4'):
                self.lineEdit_4.setText(detailed_info.get("project_manager", ""))  # 项目经理
                self.lineEdit_4.setEnabled(False)
                self.lineEdit_4.setStyleSheet("color: gray;")
            if hasattr(self, 'lineEdit_5'):
                self.lineEdit_5.setText(detailed_info.get("sample_number", ""))  # 样机编号
                self.lineEdit_5.setEnabled(False)
                self.lineEdit_5.setStyleSheet("color: gray;")
        else:
            editable_widgets = [self.lineEdit_2, self.lineEdit_3, self.lineEdit_6, self.lineEdit_7, self.lineEdit_8,
                                self.lineEdit_9, self.lineEdit_10, self.lineEdit_11, self.lineEdit_4, self.lineEdit_5]
            for widget in editable_widgets:
                widget.clear()

    def enable_edit_model(self):
        """
        启用所有需要编辑的部件并将字体颜色设置为黑色
        编辑完成以后变成确认
        :return:
        """
        editable_widgets = [self.lineEdit_2, self.lineEdit_3, self.lineEdit_6, self.lineEdit_7, self.lineEdit_8,
                                self.lineEdit_9, self.lineEdit_10, self.lineEdit_11, self.lineEdit_4, self.lineEdit_5]
        # 循环处理所有需要编辑的部件
        for widget in editable_widgets:
            if self.is_edit_mode:  # 如果当前为编辑状态
                widget.setEnabled(True)  # 启用部件
                widget.setStyleSheet("color: black;")  # 设置字体颜色为黑色
            else:  # 否则当前为确认状态
                widget.setEnabled(False)  # 禁用部件
                widget.setStyleSheet("color: gray;")  # 设置字体颜色为灰色

        # 切换编辑按钮文本为“确认”或“编辑”
        if self.is_edit_mode:
            self.next11.setText("确认")
        else:
            self.next11.setText("编辑")

        # 如果当前为确认状态，则保存数据到数据库
        if not self.is_edit_mode:
            self.save_project_details_to_database()
            self.save_project_to_database()

        # 切换标志，实现循环
        self.is_edit_mode = not self.is_edit_mode
    def handle_new_project(self):
        """
        新建项目时处理
        :return:
        """
        self.is_edit_mode = True

        # 清空时间控件
        default_datetime = QtCore.QDateTime()
        self.lineEdit_6.setDateTime(default_datetime)
        self.lineEdit_7.setDateTime(default_datetime)

        # 清空所有文本框
        editable_widgets = [self.lineEdit_2, self.lineEdit_3, self.lineEdit_6, self.lineEdit_7, self.lineEdit_8,
                            self.lineEdit_9, self.lineEdit_10, self.lineEdit_11, self.lineEdit_4, self.lineEdit_5]
        for widget in editable_widgets:
            widget.clear()

        # 循环处理所有需要编辑的部件
        self.enable_edit_model()

    def show_confirmation_dialog(self):
        """
        弹窗
        :return:
        """
        confirmation_dialog = QMessageBox()
        confirmation_dialog.setIcon(QMessageBox.Question)
        confirmation_dialog.setText(f"您确定要开始评估项目 '{self.lineEdit_2.text()}' 吗？")
        confirmation_dialog.setWindowTitle("确认开始评估")
        confirmation_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirmation_dialog.setDefaultButton(QMessageBox.No)
        confirmation_dialog.buttonClicked.connect(self.handle_confirmation_response)
        confirmation_dialog.exec_()

    def handle_confirmation_response(self, clicked_button):
        """
        处理确认框的响应
        """
        if clicked_button.text() == "Yes":
            # 用户点击了确认按钮，执行开始评估的操作
            self.start_evaluation()
        else:
            # 用户点击了取消按钮，不执行任何操作或者显示相应提示信息
            pass

    def save_project_details_to_database(self):
        """
        获取用户在界面输入的项目详情信息
        :return:
        """
        project_name = self.lineEdit_2.text()
        project_number = self.lineEdit_3.text()
        lifting_time = self.lineEdit_6.date().toString("yyyy-MM-dd")
        connection_time = self.lineEdit_7.date().toString("yyyy-MM-dd")
        assessment_period = self.lineEdit_8.text()
        farm_location = self.lineEdit_9.text()
        wind_configuration = self.lineEdit_10.text()
        assessment_status = self.lineEdit_11.currentText()
        project_manager = self.lineEdit_4.text()
        sample_number = self.lineEdit_5.text()

        # 检查项目名称是否存在于数据库中
        if self.check_project_exists(project_name):
            # 项目名称存在，执行更新操作
            success = self.update_project_in_database(project_name, project_number, lifting_time, connection_time, assessment_period,
                                                      farm_location, wind_configuration, assessment_status, project_manager, sample_number)
            if success:
                QMessageBox.information(self, "成功", "项目信息更新成功！")
            else:
                QMessageBox.warning(self, "错误", "项目信息更新失败，请重试或检查输入信息！")
        else:
            # 项目名称不存在，执行新建操作
            success = self.insert_new_project_to_database(project_name, project_number, lifting_time, connection_time, assessment_period,
                                                          farm_location, wind_configuration, assessment_status, project_manager, sample_number)
            if success:
                QMessageBox.information(self, "成功", "新建项目成功！")
            else:
                QMessageBox.warning(self, "错误", "新建项目失败，请重试或检查输入信息！")

    def check_project_exists(self, project_name):
        """
        检查项目名称是否存在于数据库中
        """
        cursor = self.db.cursor()
        sql = "SELECT * FROM post_basic_information WHERE project_name = %s"
        cursor.execute(sql, (project_name,))
        result = cursor.fetchone()
        return result is not None

    def update_project_in_database(self,  project_name, project_number, lifting_time, connection_time, assessment_period,
                                   farm_location, wind_configuration, assessment_status, project_manager, sample_number):
        """
        更新项目信息到数据库中
        """
        try:
            cursor = self.db.cursor()
            sql = "UPDATE post_basic_information SET project_number = %s, lifting_time= %s, connection_time= %s, " \
                  "assessment_period= %s, farm_location= %s, wind_configuration= %s, assessment_status= %s, project_manager= %s, sample_number= %s " \
                  "WHERE project_name = %s"
            cursor.execute(sql, (project_number, lifting_time, connection_time, assessment_period,
                                 farm_location, wind_configuration,assessment_status,project_manager,sample_number,project_name))
            self.db.commit()
            return True
        except Exception as e:
            print("Error:", e)
            self.db.rollback()
            return False

    def insert_new_project_to_database(self, project_name, project_number, lifting_time, connection_time, assessment_period,
                                       farm_location, wind_configuration,assessment_status,project_manager,sample_number):
        """
        插入新建项目信息到数据库中
        """
        try:
            cursor = self.db.cursor()
            sql = "INSERT INTO post_basic_information (project_name, project_number, lifting_time, connection_time, assessment_period, " \
                  "farm_location, wind_configuration,assessment_status,project_manager,sample_number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (project_name, project_number, lifting_time, connection_time, assessment_period,
                                 farm_location, wind_configuration,assessment_status,project_manager,sample_number))
            self.db.commit()
            return True
        except Exception as e:
            print("Error:", e)
            self.db.rollback()
            return False

    ###########历史项目总览子页面

    def update_eval_item_operation(self):
        """
        生成汇总表
        """
        total_count = 0
        completed = 0
        plan = 0
        try:
            self.db.ping(reconnect=True)
            cursor =self.db.cursor()
            query = " SELECT COUNT(project_name) AS total_count, SUM(CASE WHEN assessment_status = '完成' THEN 1 ELSE 0 END) AS completed," \
                    " SUM(CASE WHEN assessment_status != '完成' THEN 1 ELSE 0 END) AS plan" \
                    " FROM post_basic_information"
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                total_count = result[0]
                completed = result[1]
                plan = result[2]
        except Exception as e:
            print("Error:", e)
            self.db.rollback()
        finally:
            cursor.close()
        return total_count, completed, plan

    def history_database(self):
        """
        根据条件查询项目类别信息
        连接搜索按钮
        """
        try:
            search_query = self.key2.text()
            cursor =self.db.cursor()

            # 清空表格中的所有行
            self.textEdit_2.clearContents()
            self.textEdit_2.setRowCount(0)

            # 处理查询结果
            if not search_query:
                query_all = "select distinct eval_project_id from eval_item_summary"
                cursor.execute(query_all)
                result_list_all = [str(row[0]) for row in cursor.fetchall()]
                for row, eval_project_id in enumerate(result_list_all):
                    self.textEdit_2.insertRow(row)  # 插入新行
                    item = QTableWidgetItem(eval_project_id)  # 创建单元格项目
                    self.textEdit_2.setItem(row, 0, item)  # 将项目名称添加到表格中
            else:
                query_match = f"select distinct eval_project_id from eval_item_summary where eval_project_id like '%{search_query}%'"
                cursor.execute(query_match)
                result_list_match = [str(row[0]) for row in cursor.fetchall()]
                for row, eval_project_id in enumerate(result_list_match):
                    self.textEdit_2.insertRow(row)  # 插入新行
                    item = QTableWidgetItem(eval_project_id)  # 创建单元格项目
                    self.textEdit_2.setItem(row, 0, item)  # 将项目名称添加到表格中
        except Exception as e:
            print(f"Error in search_database: {str(e)}")
        finally:
            cursor.close()
    def handle_cell_clicked_history(self,row, column):
        """
        从数据库获取项目名称
        """
        project_name_item = self.textEdit_2.item(row, column)
        if project_name_item:
            eval_project_id = project_name_item.text()
            self.update_textedit(eval_project_id)

    def on_project_selected(self, item):
        """
        更新标签文本
        """
        project_name = item.text()
        self.label_14.setText(f"{project_name}项目后评估审核概况")

    def update_textedit(self, eval_project_id):
        """
        更新所有textedit控件中的内容
        """
        if eval_project_id:
            department_info_list = self.get_department_info_list(eval_project_id)
            for idx, (eval_department, total_count, completed) in enumerate(department_info_list):
                textedit = getattr(self, f"department_{idx + 1}")
                self.fill_textedit(textedit, eval_department, total_count, completed)

    def get_department_info_list(self, eval_project_id):
        """
        从数据库中获取部门信息列表
        """
        department_info_list = []
        try:
            with self.db.cursor() as cursor:
                sql = "SELECT eval_department, total_count, completed FROM eval_item_summary"
                cursor.execute(sql)
                result = cursor.fetchall()
            for row in result:
                eval_department, total_count, completed = row
                department_info_list.append((eval_department, total_count, completed))
        except Exception as e:
            print("Error:", e)
        finally:
            return department_info_list

    def on_table_item_clicked(self, item, column):
        """
        从数据库获取项目
        """
        row = item.row()
        eval_project_id = self.textEdit_2.item(row, column)
        if eval_project_id:
            select = eval_project_id.text()
            self.update_textedit(select)

    def clear_all_textedit(self):
        """
        清空所有文本编辑
        """
        for idx in range(1, 14):
            textedit = getattr(self, f"department_{idx}")
            if textedit:
                textedit.clear()

    def fill_textedit(self, textedit, department,total_count, completed ):
        """
        从表中读取数据，并填充到textedit控件中
        """
        if textedit:
            textedit.clear()
            textedit.append(f"{department}")
            in_progress = total_count - completed
            textedit.append(f"进行中：({in_progress})")
            textedit.append(f"完成：({completed})")

    def fill_table(self):
        """
        填充表格，仅展示 completed < total_count 的项目
        """
        try:
            with self.db.cursor() as cursor:
                sql = """
                        SELECT eval_project_id, SUM(completed) AS completed, SUM(total_count) AS total_count
                        FROM eval_item_summary
                        GROUP BY eval_project_id
                        """
                cursor.execute(sql)
                result = cursor.fetchall()

                # 清空表格中的所有行
                self.tableWidget_2.clearContents()
                self.tableWidget_2.setRowCount(0)

                # 填充表格
                for row_idx, row_data in enumerate(result):
                    eval_project_id, completed, total_count = row_data
                    completion_rate = completed / total_count if total_count != 0 else 0

                    # 仅展示 completed < total_count 的项目
                    if completed < total_count:
                        self.tableWidget_2.insertRow(row_idx)
                        item_eval_project_id = QTableWidgetItem(eval_project_id)
                        item_completion_rate = QTableWidgetItem(f"已完成 ({completed}) / 总评估项数 ({total_count})")

                        self.tableWidget_2.setItem(row_idx, 0, item_eval_project_id)
                        self.tableWidget_2.setItem(row_idx, 1, item_completion_rate)

        except Exception as e:
            print("Error:", e)

class EvalChoose(QWidget, Ui_Eval_Choose):
    """
        评估选择页面
    """
    dataEdited = pyqtSignal(dict)
    def __init__(self):
        super(EvalChoose, self).__init__()
        self.db = self.connect_to_database()   # 连接到数据库
        self.setupUi(self)
        self.page_ini()
        self.tree_dict = {}
        self.read_data_from_database()  # 初始化时读取数据
        self.lineEdit.setText("")  ##
        self.row_data_list = [] # 存储每行的数据
        self.row_current_list = []     #存储要编辑修改那一行
        self.row_index = 0
        self.columns_to_display = [5, 7, 11, 13, 14]

    def page_ini(self):
        self.controller()

    def controller(self):
        self.pushButton.clicked.connect(self.on_checkbox_state_changed1)  # 写入数据库
        # self.pushButton.clicked.connect(self.switch)
        # self.textEdit.itemClicked.connect(self.on_tree_item_click)
        self.textEdit.itemClicked.connect(self.update_table_based_on_tree_selection)
        self.pushButton_2.clicked.connect(self.on_return_and_save_button_clicked)  # 点击返回跳转到上一页
        self.dataEdited.connect(self.update_table)
        # self.comboBox.currentIndexChanged.connect(self.update_table_based_on_department)  # 部门筛选


    def connect_to_database(self):
        try:
            db = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                password='123456',
                database='post_eval'
            )
            return db
        except Exception as e:
            print("连接数据库时出现错误：", str(e))
            return None

    def resizeEvent(self, event):
        """
        使表格大小自适应窗口大小
        """
        window_width = self.width()
        col_widths = [int(window_width * factor) for factor in [0.07, 0.07, 0.32, 0.09, 0.05, 0.05, 0.05]]
        for col, width in enumerate(col_widths):
            self.tableWidget.setColumnWidth(col, width)

    def on_return_and_save_button_clicked(self):
        """
        返回加确认
        """
        self.on_return_button_clicked()
        self.save_data_and_emit_signal()

    def on_return_button_clicked(self):
        """
        点击返回跳转到上一页
        """
        self.stackedWidget.setCurrentIndex(0)

    def close_database_connection(self):
        if self.connection:
            self.connection.close()

    def read_data_from_database(self):
        try:
            with self.db.cursor() as cursor:
                query = "SELECT Distinct eval_sys, eval_list, eval_department FROM eval_item_operation_copy"
                cursor.execute(query)
                result = cursor.fetchall()
                # 创建一个字典用于存储一级结构和对应的子项
                tree_dict = {}
                # 遍历结果，构建字典
                for row in result:
                    eval_sys = str(row[0])
                    eval_list = str(row[1])
                    if eval_sys not in tree_dict:
                        tree_dict[eval_sys] = []
                    tree_dict[eval_sys].append(eval_list)
                # 创建树状结构
                for eval_sys, eval_list_items in tree_dict.items():
                    eval_sys_item = QTreeWidgetItem(self.textEdit, [eval_sys])

                    for eval_list in eval_list_items:
                        eval_list_item = QTreeWidgetItem(eval_sys_item, [eval_list])

                #### 填充部门下拉按钮
                departments = self.get_departments_from_database()
                self.comboBox.addItems(departments)

        except Exception as e:
            print(f"Error: {e}")

    def update_table_based_on_department(self):
        """
        按照部门更新右侧表格
        """
        selected_department = self.comboBox.currentText()
        self.populate_table(selected_department)

    def get_departments_from_database(self):
        departments =[]
        try:
            with self.db.cursor() as cursor:
                query = "SELECT Distinct eval_department FROM eval_item_operation_copy"
                cursor.execute(query)
                result = cursor.fetchall()
                departments = [row[0] for row in result]
        except Exception as e:
            print("Error:", e)
        return departments

    def get_data_for_department(self,category, department):
        data = []
        try:
            with self.db.cursor() as cursor:
                query = "SELECT * FROM eval_item_operation_copy WHERE eval_sys = %s and eval_department = %s"
                cursor.execute(query, (category,  department,))
                data = cursor.fetchall()
        except Exception as e:
            print("Error:", e)
        return data

    def populate_tree_structure(self, selected_department):
        """
        根据选择的部门，填充树状结构
        """
        self.textEdit.clear()  # 清空树状结构
        categories = self.get_categories_for_department(selected_department)  # 获取该部门的项目类别
        for category in categories:
            eval_sys_item = QTreeWidgetItem(self.textEdit, [category])
            eval_list_items = self.get_lists_for_category(category, selected_department)
            for eval_list in eval_list_items:
                eval_list_item = QTreeWidgetItem(eval_sys_item, [eval_list])

    def update_table_based_on_tree_selection(self, item, column):
        """
        根据树状结构的选择更新右侧表格数据
        """
        if item.parent() is None:  # 如果点击的是一级结构
            selected_category = item.text(0)  # 获取点击的项目类别
            selected_department = self.comboBox.currentText()  # 获取当前选择的部门
            self.populate_table(selected_category, selected_department)  # 更新表格数据

    def populate_table(self, category, selected_department):
        """
        根据树状结构，展示对应的评估内容
        :param category:
        :return:
        """
        self.tableWidget.setRowCount(0)  # 清空表格
        data = self.get_data_for_department(category,selected_department)
        self.row_data_list = data  # 存储数据

        for row_position, item in enumerate(data):
            self.tableWidget.insertRow(row_position)
            for display_column, column_index in enumerate(self.columns_to_display):
                value = item[column_index]
                self.tableWidget.setItem(row_position, display_column, QTableWidgetItem(str(value)))

            # 获取列数
            num_columns = self.tableWidget.columnCount()

            # 在编辑列添加按钮
            edit_button = QPushButton("编辑")
            # edit_button.setFixedSize(60, 30)
            edit_button.clicked.connect(lambda state, row=row_position: self.on_edit_button_clicked(row))
            edit_button.setStyleSheet("background-color: transparent; color: blue; border: none;")
            # self.tableWidget.setCellWidget(row_position, len(item), edit_button)
            self.tableWidget.setCellWidget(row_position, num_columns - 2, edit_button)

            # 清空最后一列的单元格
            self.tableWidget.setItem(row_position, num_columns - 1, QTableWidgetItem(""))
            # 创建复选框
            checkbox = QCheckBox()
            self.tableWidget.setCellWidget(row_position, num_columns - 1, checkbox)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, checkbox=checkbox, lineEdit=self.lineEdit_4: self.on_checkbox_state_changed(state,checkbox, lineEdit))
            self.on_checkbox_state_changed(Qt.Checked, checkbox, self.lineEdit_4)

        self.tableWidget.resizeRowsToContents()


    def on_edit_button_clicked(self, row_position):
        """
        当编辑按钮被点击时，获取该行的数据，并执行相应的操作，跳转到详情编辑页面page_2
        """
        row_data = self.row_data_list[row_position]
        self.row_index = row_position
        self.row_current_list = row_data
        self.lineEdit.setText(str(row_data[1]))
        self.lineEdit_2.setText(str(row_data[5]))
        self.lineEdit_3.setText(str(row_data[7]))
        self.lineEdit_5.setText(str(row_data[13]))
        self.lineEdit_6.setText(str(row_data[14]))
        self.lineEdit_7.setText(str(row_data[12]))
        self.textEdit_2.setText(str(row_data[11]))
        self.stackedWidget.setCurrentIndex(1)
    def on_checkbox_state_changed(self, state, checkbox, lineEdit):
        """
        根据复选框状态填入编辑详情页的是否合适
        """
        checkbox.status = state == Qt.Checked
        if checkbox.status:
            lineEdit.setText("适合")
        else:
            lineEdit.setText("不适合")

    def on_tree_item_click(self, item, row_position):
        # 获取点击的一级结构
        if item.parent() is None:
            category = item.text(0)
            # 在右侧表格中显示相应的子项
            selected_department = self.comboBox.currentText()
            self.populate_table(selected_department,category)

    def save_data_and_emit_signal(self):
        """
        编辑页需要更改的信息
        :return:
        """
        try:
            edited_data = {
                '评估标准': self.textEdit_2.toPlainText(),
                '评估人': self.lineEdit_5.text(),
                '复核人': self.lineEdit_6.text()
            }
            print(self.row_current_list[1])
            print(self.row_current_list[10])
            print(self.row_current_list[12])
            print(self.row_current_list)
            # 执行更新数据库操作
            with self.db.cursor() as cursor:
                query = """
                    UPDATE eval_item_operation_copy
                    SET eval_std = %s, eval_person = %s, review_person = %s
                    where id = %s 
                    """
                cursor.execute(query, (
                    edited_data['评估标准'],
                    edited_data['评估人'],
                    edited_data['复核人'],
                    self.row_current_list[0],
                    # self.row_current_list[10],
                    # self.row_current_list[12]
                ))
                self.dataEdited.emit(edited_data)
                self.db.commit()
                print("Data updated this row successfully")
                return True
        except Exception as e:
            print("an error occurred in save_data_and_emit_signal()", e)

    def update_table(self, edited_data):
        """
        根据编辑页的修改，更新数据表中对应的行数据
        """
        self.tableWidget.setItem(self.row_index, 2, QTableWidgetItem(edited_data['评估标准']))
        self.tableWidget.setItem(self.row_index, 3, QTableWidgetItem(edited_data['评估人']))
        self.tableWidget.setItem(self.row_index, 4, QTableWidgetItem(edited_data['复核人']))

    def on_checkbox_state_changed1(self, state, checkbox):
        """
        适用记为1，否则记为0
        """
        row = self.tableWidget.indexAt(checkbox.pos()).row()
        print(row)
        eval_content_node = self.columns_to_display[11]
        if state == Qt.Checked:
            value = 1
        else:
            value = 0
        self.update_is_use_in_database(value,eval_content_node)
        #更新到数据库
        try:
            with self.db.cursor() as cursor:
                query = "UPDATE eval_item_operation_copy SET eval_is_use = %s where eval_content_node = %s"
                cursor.execute(query, (value,eval_content_node))
                self.db.commit()
                print("is_use updated successfully")
        except Exception as e:
            print(f"Error: {e}")
            self.db.rollback()
        finally:
            cursor.close()
    def update_is_use_in_database(self,value,eval_content_node):
        """
        更新到数据库
        """
        try:
            with self.db.cursor() as cursor:
                query = "UPDATE eval_item_operation_copy SET eval_is_use = %s where eval_content_node = %s"
                cursor.execute(query, (value,eval_content_node))
                self.db.commit()
                print("is_use updated successfully")
        except Exception as e:
            print(f"Error: {e}")
            self.db.rollback()
        finally:
            cursor.close()

class EvalTask(QWidget, Ui_EvalTask):
    def __init__(self):
        super(EvalTask, self).__init__()
        self.setupUi(self)
        self.page_ini()

    def page_ini(self):
        pages = self.stackedWidget.count()
        self.controller()


    def controller(self):
        self.edit_btn.clicked.connect(self.switch)
        self.return_btn_page2.clicked.connect(self.switch)

    def switch(self):
        sender = self.sender().objectName()
        index = {
            "edit_btn": 1,
            "return_btn_page2": 0
        }
        if sender in index:
            print(f"sender = {sender} index[sender] = {index[sender]}")
            self.stackedWidget.setCurrentIndex(index[sender])

class ReportOut(QWidget, Ui_ReportOut):
    def __init__(self):
        super(ReportOut, self).__init__()
        self.setupUi(self)
        self.page_ini()

    def page_ini(self):
        self.controller()

    def controller(self):
        # self.edit_btn.clicked.connect(self.switch)
        pass

class MainPage(QWidget, Ui_MainPage):
    def __init__(self):
        super(MainPage, self).__init__()

        self.setupUi(self)
        self.resize(1800, 1600)
        self.page_init()

    def btn_transparent(self):
        btns = [self.base_info_btn, self.eval_choice_btn, self.eval_task_btn,
                self.report_out_btn, self.set_btn, self.about_btn, self.user_btn, self.exit_btn]
        for btn in btns:
            btn.setStyleSheet('background-color: transparent;')

    def page_init(self):
        # 实例化子界面并添加
        self.btn_transparent()
        self.base_info= BasicInformation()
        self.stackedWidget.addWidget(self.base_info)

        self.eval_choice = EvalChoose()
        self.stackedWidget.addWidget(self.eval_choice)

        self.eval_task = EvalTask()
        self.stackedWidget.addWidget(self.eval_task)

        self.report_out = ReportOut()
        self.stackedWidget.addWidget(self.report_out)

        # self.base_info.next11.clicked.connect(self.switch_to_choose_page)  # 页面1的跳转功能
        # 控制函数
        self.controller()

        # 显示初始页面
        self.stackedWidget.setCurrentIndex(2)
    def switch_to_choose_page(self):
        self.stackedWidget.setCurrentIndex(3)

    def controller(self):
        self.base_info_btn.clicked.connect(self.switch)
        self.eval_choice_btn.clicked.connect(self.switch)
        self.eval_choice_btn.clicked.connect(self.base_info.show_confirmation_dialog)  # 评估选择弹窗
        self.eval_task_btn.clicked.connect(self.switch)
        self.report_out_btn.clicked.connect(self.switch)

        self.set_btn.clicked.connect(self.cfg)
        self.about_btn.clicked.connect(self.cfg)
        self.user_btn.clicked.connect(self.cfg)
        self.exit_btn.clicked.connect(self.cfg)


    def switch(self):
        self.btn_transparent()
        sender = self.sender().objectName()
        sender_btn = self.sender()
        sender_btn.setStyleSheet('background-color: #007bff; color: white;')
        index = {
            "base_info_btn": 0,
            "eval_choice_btn": 1,
            "eval_task_btn": 2,
            "report_out_btn": 3
        }
        if sender in index:
            print(f"sender = {sender} index[sender] = {index[sender]}")
            self.stackedWidget.setCurrentIndex(index[sender] + 2  )

    def cfg(self):
        self.btn_transparent()
        sender_btn = self.sender()
        sender_btn.setStyleSheet('background-color: #007bff; color: white;')
        if sender_btn.objectName() == "exit_btn":
            QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./resource/time-5-48.ico"))
    window = MainPage()
    window.show()
    sys.exit(app.exec())


