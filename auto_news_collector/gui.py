"""
汽车产业资讯采集工具 - 主界面 v3.0
参考原型样式：浅色背景 + 蓝色主题 + Office365商务风格
"""

import sys
import os
import json
import threading
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QCheckBox, QComboBox, QLabel, QPushButton,
    QTextEdit, QProgressBar, QButtonGroup, QRadioButton, QFileDialog,
    QMessageBox, QSystemTrayIcon, QMenu, QAction, QSpinBox, QFrame,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPropertyAnimation, QSize
from PyQt5.QtGui import QFont, QColor, QPalette

from config import DOMAINS, TIME_RANGE_OPTIONS, DEFAULT_OUTPUT_DIR, DEFAULT_CACHE_DIR
# from collector.browser_agent import GasgooCollector, AutoinfoCollector  # TODO: 修复导入
from exporter import WordExporter


class Communicate(QObject):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)


class MainWindow(QMainWindow):
    
    # Office 365 配色方案
    ACCENT_BLUE = "#0078D4"
    ACCENT_BLUE_HOVER = "#106EBE"
    ACCENT_BLUE_LIGHT = "#E8F4FD"
    BG_LIGHT = "#F3F6F9"
    BG_WHITE = "#FFFFFF"
    BG_CARD = "#FFFFFF"
    TEXT_DARK = "#323130"
    TEXT_MID = "#605E5C"
    TEXT_LIGHT = "#A19F9D"
    BORDER_COLOR = "#EDEBE9"
    BORDER_HOVER = "#0078D4"
    SUCCESS_GREEN = "#107C10"
    ERROR_RED = "#D13438"
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("汽车产业资讯采集工具")
        self.setGeometry(300, 50, 900, 780)
        self.setMinimumSize(800, 700)
        
        # 应用浅色主题
        self.setStyleSheet(f"""
            QMainWindow, QMainWindow > QWidget {{
                background-color: {self.BG_LIGHT};
            }}
            QWidget {{
                background-color: {self.BG_LIGHT};
                color: {self.TEXT_DARK};
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
                font-size: 9pt;
            }}
            QLabel {{
                background-color: {self.BG_LIGHT};
            }}
            
            /* 分组标题样式 */
            QGroupBox {{
                background-color: {self.BG_WHITE};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 8px;
                margin-top: 12px;
                padding: 20px 12px 12px 12px;
                font-size: 10pt;
                font-weight: 600;
                color: {self.TEXT_DARK};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 8px;
                color: {self.ACCENT_BLUE};
            }}
            
            /* 标签 */
            QLabel {{
                color: {self.TEXT_DARK};
                background-color: transparent;
            }}
            QLabel.section-title {{
                font-size: 11pt;
                font-weight: 600;
                color: {self.TEXT_DARK};
            }}
            QLabel.hint {{
                font-size: 8pt;
                color: {self.TEXT_LIGHT};
            }}
            
            /* 按钮样式 */
            QPushButton {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 9pt;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{
                border-color: {self.BORDER_HOVER};
                background-color: {self.ACCENT_BLUE_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {self.ACCENT_BLUE_LIGHT};
            }}
            QPushButton:disabled {{
                background-color: {self.BG_LIGHT};
                color: {self.TEXT_LIGHT};
                border-color: {self.BORDER_COLOR};
            }}
            
            /* 主要按钮（蓝色） */
            QPushButton.primary {{
                background-color: {self.ACCENT_BLUE};
                color: {self.BG_WHITE};
                border: none;
                font-weight: 600;
            }}
            QPushButton.primary:hover {{
                background-color: {self.ACCENT_BLUE_HOVER};
            }}
            
            /* 次要按钮 */
            QPushButton.secondary {{
                background-color: {self.BG_LIGHT};
                color: {self.TEXT_MID};
            }}
            
            /* 复选框 */
            QCheckBox {{
                color: {self.TEXT_DARK};
                spacing: 8px;
                font-size: 9pt;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid {self.BORDER_COLOR};
                background-color: {self.BG_WHITE};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.ACCENT_BLUE};
                border-color: {self.ACCENT_BLUE};
                image: none;
            }}
            QCheckBox:hover {{
                color: {self.ACCENT_BLUE};
            }}
            
            /* 单选框 */
            QRadioButton {{
                color: {self.TEXT_DARK};
                spacing: 8px;
                font-size: 9pt;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid {self.BORDER_COLOR};
                background-color: {self.BG_WHITE};
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.ACCENT_BLUE};
                border-color: {self.ACCENT_BLUE};
            }}
            
            /* 下拉框 */
            QComboBox {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 4px;
                padding: 7px 12px;
                min-width: 100px;
                font-size: 9pt;
            }}
            QComboBox:hover {{
                border-color: {self.BORDER_HOVER};
            }}
            QComboBox:focus {{
                border-color: {self.ACCENT_BLUE};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {self.TEXT_MID};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
                border: 1px solid {self.BORDER_COLOR};
                selection-background-color: {self.ACCENT_BLUE_LIGHT};
                padding: 4px;
            }}
            
            /* 数字输入框 */
            QSpinBox {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 9pt;
            }}
            QSpinBox:hover {{
                border-color: {self.BORDER_HOVER};
            }}
            QSpinBox:focus {{
                border-color: {self.ACCENT_BLUE};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {self.BG_LIGHT};
                border-radius: 2px;
                width: 20px;
            }}
            QSpinBox::up-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid {self.TEXT_MID};
            }}
            QSpinBox::down-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {self.TEXT_MID};
            }}
            
            /* 进度条 */
            QProgressBar {{
                background-color: {self.BG_LIGHT};
                border: none;
                border-radius: 4px;
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.ACCENT_BLUE};
                border-radius: 4px;
            }}
            
            /* 文本编辑器 */
            QTextEdit {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 6px;
                padding: 10px;
                font-family: "Consolas", "Microsoft YaHei UI", monospace;
                font-size: 8pt;
            }}
            QTextEdit:focus {{
                border-color: {self.ACCENT_BLUE};
            }}
            
            /* 滚动条 */
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.TEXT_LIGHT};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.TEXT_MID};
            }}
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 8px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {self.TEXT_LIGHT};
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar:horizontal:hover {{
                background-color: {self.TEXT_MID};
            }}
            
            /* 消息框 */
            QMessageBox {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
            }}
            QMessageBox QLabel {{
                color: {self.TEXT_DARK};
                font-size: 9pt;
                padding: 4px;
                background-color: transparent;
            }}
            QMessageBox QPushButton {{
                background-color: {self.ACCENT_BLUE};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                font-size: 9pt;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {self.ACCENT_BLUE_HOVER};
            }}
            QMessageBox QPushButton:enabled {{
                background-color: {self.ACCENT_BLUE};
                color: white;
            }}
            QMessageBox QPushButton:default {{
                background-color: {self.ACCENT_BLUE};
                color: white;
                font-weight: bold;
            }}
            
            /* 对话框 */
            QDialog {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
            }}
            
            /* 所有子控件继承背景 */
            QMessageBox QWidget {{
                background-color: {self.BG_WHITE};
            }}
            QDialog QWidget {{
                background-color: {self.BG_WHITE};
            }}
        """)

        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        os.makedirs(DEFAULT_CACHE_DIR, exist_ok=True)

        self.comm = Communicate()
        self.is_collecting = False
        self.stop_flag = False
        self.collection_results = {}

        self.init_ui()

        self.comm.log_signal.connect(self.append_log)
        self.comm.progress_signal.connect(self.update_progress)
        self.comm.finished_signal.connect(self.on_collection_finished)
        self.comm.error_signal.connect(self.on_error)

        self.setup_tray()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet(f"QWidget#centralWidget {{ background-color: {self.BG_LIGHT}; }}")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # ========== 顶部标题栏 ==========
        header = QWidget()
        header.setStyleSheet("""
            background-color: #FFFFFF;
            border: 1px solid #EDEBE9;
            border-radius: 6px;
            padding: 10px 14px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 8, 14, 8)
        
        title = QLabel("汽车产业资讯采集工具")
        title.setStyleSheet(f"""
            font-size: 14pt;
            font-weight: 600;
            color: {self.TEXT_DARK};
        """)
        header_layout.addWidget(title)
        
        version = QLabel("v3.0")
        version.setStyleSheet(f"""
            font-size: 9pt;
            color: {self.TEXT_LIGHT};
            background-color: {self.BG_LIGHT};
            padding: 2px 8px;
            border-radius: 4px;
        """)
        header_layout.addWidget(version, 0, Qt.AlignRight | Qt.AlignVCenter)
        
        main_layout.addWidget(header)

        # ========== 内容区（无滚动） ==========
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 2, 0, 2)
        content_layout.setSpacing(10)

        # ---- 第一行：时间范围 + 输出目录 ----
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        
        time_card = self.make_card("⏰ 时间范围", self.build_time_section())
        row1.addWidget(time_card, 1)
        
        output_card = self.make_card("📁 输出设置", self.build_output_section())
        row1.addWidget(output_card, 2)
        
        content_layout.addLayout(row1)

        # ---- 领域选择卡片 ----
        domain_card = self.make_card("📂 采集领域（可多选）", self.build_domain_section())
        content_layout.addWidget(domain_card)

        # ---- 定时任务卡片 ----
        schedule_card = self.make_card("📅 定时任务", self.build_schedule_section())
        content_layout.addWidget(schedule_card)
        
        main_layout.addWidget(content, 1)

        # ========== 进度条 ==========
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # ========== 日志卡片 ==========
        log_card = QWidget()
        log_card.setStyleSheet("""
            background-color: #FFFFFF;
            border: 1px solid #EDEBE9;
            border-radius: 6px;
        """)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(10, 8, 10, 8)
        log_layout.setSpacing(6)
        
        log_title = QLabel("📋 执行日志")
        log_title.setStyleSheet(f"color: {self.ACCENT_BLUE}; font-weight: 600; font-size: 9pt;")
        log_layout.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(360)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.BG_LIGHT};
                color: {self.TEXT_DARK};
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 8pt;
            }}
        """)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_card)

        # ========== 操作按钮 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.start_btn = QPushButton("▶ 开始采集")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ACCENT_BLUE};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 28px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.ACCENT_BLUE_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {self.TEXT_LIGHT};
            }}
        """)
        self.start_btn.clicked.connect(self.start_collection)
        btn_layout.addWidget(self.start_btn)

        self.export_btn = QPushButton("📄 生成Word")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.BG_WHITE};
                color: {self.TEXT_DARK};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 4px;
                padding: 8px 24px;
                font-size: 9pt;
                font-weight: 500;
            }}
            QPushButton:hover {{
                border-color: {self.ACCENT_BLUE};
                background-color: {self.ACCENT_BLUE_LIGHT};
            }}
            QPushButton:disabled {{
                color: {self.TEXT_LIGHT};
            }}
        """)
        self.export_btn.clicked.connect(self.export_to_word)
        btn_layout.addWidget(self.export_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.BG_WHITE};
                color: {self.ERROR_RED};
                border: 1px solid {self.ERROR_RED};
                border-radius: 4px;
                padding: 8px 24px;
                font-size: 9pt;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #FEF0F0;
            }}
            QPushButton:disabled {{
                color: {self.TEXT_LIGHT};
                border-color: {self.BORDER_COLOR};
            }}
        """)
        self.stop_btn.clicked.connect(self.stop_collection)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def make_card(self, title, content_widget):
        """创建卡片容器"""
        card = QWidget()
        card.setStyleSheet(f"""
            background-color: #FFFFFF;
            border: 1px solid #EDEBE9;
            border-radius: 6px;
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self.ACCENT_BLUE};
            font-size: 9pt;
            font-weight: 600;
        """)
        layout.addWidget(title_label)
        layout.addWidget(content_widget)
        
        return card

    def build_time_section(self):
        """时间范围区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.time_combo = QComboBox()
        self.time_combo.addItems(TIME_RANGE_OPTIONS.keys())
        self.time_combo.setCurrentText("近一周（周六→周五）")
        self.time_combo.setFixedWidth(180)
        layout.addWidget(self.time_combo)
        
        self.custom_days = QSpinBox()
        self.custom_days.setRange(1, 365)
        self.custom_days.setValue(7)
        self.custom_days.setSuffix(" 天")
        self.custom_days.setFixedWidth(110)
        self.custom_days.setVisible(False)
        layout.addWidget(self.custom_days)
        
        layout.addStretch()
        
        self.time_combo.currentTextChanged.connect(self.on_time_range_changed)
        
        return widget

    def build_output_section(self):
        """输出目录区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.output_path = QLabel("点击右侧「浏览」选择输出目录")
        self.output_path.setStyleSheet(f"color: {self.TEXT_LIGHT}; font-size: 9pt;")
        layout.addWidget(self.output_path, 1)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self.browse_output_dir)
        layout.addWidget(self.browse_btn)
        
        return widget

    def build_domain_section(self):
        """领域选择区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 全选/取消按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ACCENT_BLUE_LIGHT};
                color: {self.ACCENT_BLUE};
                border: none;
                border-radius: 4px;
                padding: 5px 14px;
                font-size: 9pt;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.ACCENT_BLUE};
                color: white;
            }}
        """)
        self.select_all_btn.clicked.connect(self.select_all_domains)
        btn_row.addWidget(self.select_all_btn)
        
        self.clear_all_btn = QPushButton("取消全选")
        self.clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.BG_LIGHT};
                color: {self.TEXT_MID};
                border: none;
                border-radius: 4px;
                padding: 5px 14px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {self.ACCENT_BLUE_LIGHT};
                color: {self.ACCENT_BLUE};
            }}
        """)
        self.clear_all_btn.clicked.connect(self.clear_all_domains)
        btn_row.addWidget(self.clear_all_btn)
        btn_row.addStretch()
        
        layout.addLayout(btn_row)
        
        # 领域复选框网格
        self.domain_checkboxes = {}
        domains = list(DOMAINS.keys())
        
        grid = QGridLayout()
        grid.setSpacing(6)
        
        for i, domain in enumerate(domains):
            row = i // 2
            col = i % 2
            
            cb = QCheckBox(f"{domain}")
            cb.setChecked(True)
            cb.setFixedHeight(24)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {self.TEXT_DARK};
                    spacing: 6px;
                    font-size: 9pt;
                    padding: 3px 8px;
                    background-color: {self.BG_LIGHT};
                    border-radius: 4px;
                }}
                QCheckBox:hover {{
                    background-color: {self.ACCENT_BLUE_LIGHT};
                }}
                QCheckBox:checked {{
                    color: {self.ACCENT_BLUE};
                    background-color: {self.ACCENT_BLUE_LIGHT};
                }}
                QCheckBox::indicator {{
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid {self.BORDER_COLOR};
                    background-color: {self.BG_WHITE};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {self.ACCENT_BLUE};
                    border-color: {self.ACCENT_BLUE};
                }}
            """)
            self.domain_checkboxes[domain] = cb
            grid.addWidget(cb, row, col)
        
        layout.addLayout(grid)
        
        return widget

    def build_schedule_section(self):
        """定时任务区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        self.schedule_group = QButtonGroup()
        
        self.no_schedule_rb = QRadioButton("关闭")
        self.no_schedule_rb.setChecked(True)
        self.schedule_group.addButton(self.no_schedule_rb, 1)
        layout.addWidget(self.no_schedule_rb)
        
        self.daily_schedule_rb = QRadioButton("每天定时")
        self.schedule_group.addButton(self.daily_schedule_rb, 2)
        layout.addWidget(self.daily_schedule_rb)
        
        self.schedule_time = QComboBox()
        for h in range(24):
            for m in [0, 30]:
                self.schedule_time.addItem(f"{h:02d}:{m:02d}")
        self.schedule_time.setCurrentText("11:30")
        self.schedule_time.setFixedWidth(80)
        layout.addWidget(self.schedule_time)
        
        self.custom_schedule_rb = QRadioButton("自定义周期")
        self.schedule_group.addButton(self.custom_schedule_rb, 3)
        layout.addWidget(self.custom_schedule_rb)
        
        self.custom_interval = QSpinBox()
        self.custom_interval.setRange(1, 24)
        self.custom_interval.setValue(12)
        self.custom_interval.setSuffix(" 小时")
        self.custom_interval.setFixedWidth(110)
        layout.addWidget(self.custom_interval)
        
        layout.addStretch()
        
        return widget

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        tray_menu = QMenu()
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        collect_action = QAction("立即采集", self)
        collect_action.triggered.connect(self.start_collection)
        tray_menu.addAction(collect_action)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(sys.exit)
        tray_menu.addAction(exit_action)
        self.tray.setContextMenu(tray_menu)
        self.tray.show()

    def on_time_range_changed(self, text):
        self.custom_days.setVisible(text == "自定义")

    def get_selected_domains(self):
        return [d for d, cb in self.domain_checkboxes.items() if cb.isChecked()]

    def select_all_domains(self):
        for cb in self.domain_checkboxes.values():
            cb.setChecked(True)

    def clear_all_domains(self):
        for cb in self.domain_checkboxes.values():
            cb.setChecked(False)

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录", DEFAULT_OUTPUT_DIR)
        if dir_path:
            self.output_path.setText(dir_path)
            self.output_path.setStyleSheet(f"color: {self.TEXT_DARK}; font-size: 9pt;")

    def get_week_range(self):
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7
        this_friday = today + timedelta(days=days_until_friday)
        last_saturday = this_friday - timedelta(days=6)
        return last_saturday, this_friday

    def get_two_week_range(self):
        last_saturday, this_friday = self.get_week_range()
        return last_saturday - timedelta(days=7), this_friday

    def get_month_range(self):
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7
        this_friday = today + timedelta(days=days_until_friday)
        first_day_this_month = today.replace(day=1)
        if first_day_this_month.weekday() == 6:
            first_day_this_month = first_day_this_month - timedelta(days=1)
        last_month_start = first_day_this_month - timedelta(days=first_day_this_month.weekday() + 1)
        return last_month_start, this_friday

    def get_date_range(self):
        text = self.time_combo.currentText()
        if text == "近一周（周六→周五）":
            return self.get_week_range()
        elif text == "近两周":
            return self.get_two_week_range()
        elif text == "近一个月":
            return self.get_month_range()
        elif text == "自定义":
            days = self.custom_days.value()
            end_date = datetime.now()
            return end_date - timedelta(days=days), end_date
        return self.get_week_range()

    def start_collection(self):
        selected_domains = self.get_selected_domains()
        if not selected_domains:
            QMessageBox.warning(self, "提示", "请至少选择一个采集领域！")
            return

        if self.is_collecting:
            return

        self.is_collecting = True
        self.stop_flag = False
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)

        start_date, end_date = self.get_date_range()

        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] 开始采集...")
        self.append_log(f"时间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        self.append_log(f"领域: {', '.join(selected_domains)}")

        thread = threading.Thread(target=self._collect_worker, args=(selected_domains, start_date, end_date))
        thread.daemon = True
        thread.start()

    def _collect_worker(self, domains, start_date, end_date):
        try:
            results = {}
            # 计算总步数：URL数量 + 领域7/8的API采集 + pcauto单独算1步
            total_steps = 0
            for d in domains:
                if "urls" in DOMAINS[d]:
                    total_steps += len(DOMAINS[d]["urls"])
                elif d in ["政策法规"]:
                    total_steps += 1
                else:
                    total_steps += 1
                # 新车上市需要额外加pcauto步骤
                if d == "新车上市":
                    total_steps += 1
            current_step = 0

            for domain in domains:
                # 检查停止标志
                if self.stop_flag:
                    self.comm.log_signal.emit(f"\n⏹ 用户停止，退出采集")
                    break
                    
                self.comm.log_signal.emit(f"\n--- {domain} ---")
                domain_config = DOMAINS[domain]
                domain_results = []

                if "sub_domains" in domain_config:
                    # 按分领域分别存储
                    sub_domain_results = {}
                    
                    # 宏观经济政策使用专门的MacroCollector
                    if domain == "宏观经济政策":
                        try:
                            from collector.browser_agent import MacroCollector
                            macro = MacroCollector()
                            macro_results = macro.collect(start_date, end_date, domain_config["sub_domains"])
                            for sub_name, news in macro_results.items():
                                sub_domain_results[sub_name] = news
                                domain_results.extend(news)
                                self.comm.log_signal.emit(f"  ✓ {sub_name}: {len(news)}条")
                        except Exception as e:
                            self.comm.log_signal.emit(f"  宏观经济政策采集失败: {e}")
                    else:
                        for sub_name, sub_config in domain_config["sub_domains"].items():
                            if self.stop_flag:
                                break
                            try:
                                self.comm.log_signal.emit(f"  → {sub_name}")
                                from collector.gasgoo import GasgooCollector
                                collector = GasgooCollector(sub_config["url"])
                                news = collector.collect(
                                    start_date=start_date, end_date=end_date,
                                    max_count=sub_config.get("max_count", 10),
                                    include_keywords=sub_config.get("include_keywords", []),
                                    exclude_keywords=domain_config.get("exclude_keywords", []),
                                    fetch_content=True,
                                    stop_if_enough=True,
                                    current_total=0  # 每个子领域独立判断，互不影响
                                )
                                sub_domain_results[sub_name] = news
                                domain_results.extend(news)  # 保留原始列表用于兼容
                                with_content = sum(1 for n in news if n.get('content'))
                                self.comm.log_signal.emit(f"    ✓ {len(news)}条（含正文{with_content}条）")
                            except Exception as e:
                                self.comm.log_signal.emit(f"  {sub_name}: 失败")

                        current_step += 1
                        self.comm.progress_signal.emit(int(current_step / total_steps * 100))
                    
                    # 保存分领域结果用于导出
                    results[f"{domain}_分领域"] = sub_domain_results
                else:
                    for url in domain_config.get("urls", []):
                        # 检查停止标志
                        if self.stop_flag:
                            break
                            
                        # 检查是否已采集够10条
                        if len(domain_results) >= 10:
                            self.comm.log_signal.emit(f"  ✓ 已达上限，停止采集剩余频道")
                            break
                        
                        try:
                            self.comm.log_signal.emit(f"  → {url[-40:]}")
                            from collector.gasgoo import GasgooCollector
                            collector = GasgooCollector(url)
                            
                            if domain == "企业要闻":
                                # 企业要闻：逐条判断，满足则采集，直到够10条
                                news = collector.collect(
                                    start_date=start_date, end_date=end_date,
                                    max_count=10,  # 直接采10条，逐条判断，不多采
                                    include_keywords=domain_config.get("include_keywords", []),
                                    exclude_keywords=domain_config.get("exclude_keywords", []),
                                    brand_categories=domain_config.get("brand_categories", []),
                                    fetch_content=True,
                                    stop_if_enough=True,  # 够数后停止翻页
                                    current_total=0
                                )
                            else:
                                news = collector.collect(
                                    start_date=start_date, end_date=end_date,
                                    max_count=domain_config.get("max_count", 10),
                                    include_keywords=domain_config.get("include_keywords", []),
                                    exclude_keywords=domain_config.get("exclude_keywords", []),
                                    fetch_content=True,
                                    stop_if_enough=True,
                                    current_total=len(domain_results)
                                )
                            domain_results.extend(news)
                            
                            # 统计有正文的数量
                            with_content = sum(1 for n in news if n.get('content'))
                            self.comm.log_signal.emit(f"    ✓ {len(news)}条（含正文{with_content}条）")
                        except Exception as e:
                            self.comm.log_signal.emit(f"  {url[-30:]}: 失败 - {str(e)}")

                        current_step += 1
                        self.comm.progress_signal.emit(int(current_step / total_steps * 100))

                if domain == "政策法规":
                    try:
                        from collector.autoinfo import AutoinfoCollector
                        autoinfo = AutoinfoCollector()
                        policy_news = autoinfo.collect(
                            start_date=start_date, end_date=end_date,
                            max_count=domain_config.get("max_count", 10)
                        )
                        domain_results.extend(policy_news)
                        self.comm.log_signal.emit(f"  政策API: +{len(policy_news)}条")
                    except Exception as e:
                        self.comm.log_signal.emit(f"  政策API: 失败 - {e}")

                if domain == "新车上市":
                    try:
                        from collector.pcauto import PcautoCollector
                        pcauto = PcautoCollector()
                        pcauto_news = pcauto.collect(
                            start_date=start_date, end_date=end_date,
                            max_count=domain_config.get("max_count", 10)
                        )
                        domain_results.extend(pcauto_news)
                        self.comm.log_signal.emit(f"  太平洋汽车: +{len(pcauto_news)}条")
                    except Exception as e:
                        self.comm.log_signal.emit(f"  太平洋汽车: 失败 - {str(e)}")

                    current_step += 1
                    self.comm.progress_signal.emit(int(current_step / total_steps * 100))

                results[domain] = domain_results

            # 检查是否因停止而退出
            if self.stop_flag:
                self.collection_results = results
                self._save_cache(results)
                self.comm.progress_signal.emit(0)
                self.comm.log_signal.emit("\n⏹ 已停止采集")
                return

            # ========== 领域1（行业动态）最终处理：合并所有频道结果，排序取前10 ==========
            if "行业动态" in results and len(results["行业动态"]) > 0:
                all_news = results["行业动态"]
                # 按日期排序（由近到远）
                all_news.sort(key=lambda x: x.get('date', ''), reverse=True)
                # 取前10条
                results["行业动态"] = all_news[:10]
                self.comm.log_signal.emit(f"\n📊 行业动态共{len(all_news)}条，已按时间取最新10条")

            # ========== 领域2（企业要闻）最终处理：品牌分类 ==========
            if "企业要闻" in results and len(results["企业要闻"]) > 0:
                all_news = results["企业要闻"]
                # 按日期排序（由近到远）
                all_news.sort(key=lambda x: x.get('date', ''), reverse=True)
                # 取前10条
                all_news = all_news[:10]
                
                # 获取品牌分类配置
                enterprise_config = DOMAINS.get("企业要闻", {})
                brands = enterprise_config.get("brands", {})
                
                # 分类
                categorized = {
                    "豪华品牌车企": [],
                    "合资品牌车企": [],
                    "自主品牌车企": [],
                    "造车新势力及其他": []
                }
                
                for news in all_news:
                    text = news.get('title', '') + news.get('content', '')
                    assigned = False
                    for category, brand_list in brands.items():
                        for brand in brand_list:
                            if brand in text:
                                categorized[category].append(news)
                                assigned = True
                                break
                        if assigned:
                            break
                    if not assigned:
                        # 未匹配到任何品牌，归入"造车新势力及其他"
                        categorized["造车新势力及其他"].append(news)
                
                # 记录分类统计
                stats = {cat: len(items) for cat, items in categorized.items()}
                self.comm.log_signal.emit(f"\n📊 企业要闻共{len(all_news)}条，分类: {stats}")
                
                # 保存分类结果（用于导出）
                results["企业要闻_分类"] = categorized
                
                # 保留原始数据也保存一份
                results["企业要闻"] = all_news

            # ========== 领域5（新技术/新趋势）最终处理：分领域统计 ==========
            if "新技术/新趋势" in results and len(results["新技术/新趋势"]) > 0:
                # 分领域结果已经在采集时保存在 results["新技术/新趋势_分领域"]
                if "新技术/新趋势_分领域" in results:
                    stats = {cat: len(items) for cat, items in results["新技术/新趋势_分领域"].items() if items}
                    self.comm.log_signal.emit(f"\n📊 新技术/新趋势共{len(results['新技术/新趋势'])}条，分类: {stats}")

            self.collection_results = results
            self._save_cache(results)
            self.comm.progress_signal.emit(100)
            self.comm.finished_signal.emit(results)

        except Exception as e:
            self.comm.error_signal.emit(str(e))

    def _save_cache(self, results):
        # 清理旧缓存文件（只保留最新的3个）
        try:
            cache_files = sorted(
                [f for f in os.listdir(DEFAULT_CACHE_DIR) if f.startswith('cache_') and f.endswith('.json')],
                reverse=True
            )
            for old_file in cache_files[3:]:
                os.remove(os.path.join(DEFAULT_CACHE_DIR, old_file))
        except:
            pass
        
        # 保存新缓存
        cache_file = os.path.join(DEFAULT_CACHE_DIR, f"cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except:
            pass

    def append_log(self, text):
        self.log_text.append(text)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_collection_finished(self, results):
        self.is_collecting = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.export_btn.setEnabled(True)

        # 排除分类数据，只统计新闻列表
        news_results = {k: v for k, v in results.items() if not k.endswith("_分类")}
        total = 0
        with_content = 0
        for k, v in results.items():
            if k.endswith("_分类") or k.endswith("_分领域"):
                continue
            if isinstance(v, list):
                total += len(v)
                for n in v:
                    if isinstance(n, dict) and n.get('content'):
                        with_content += 1
        self.append_log(f"\n✅ 采集完成，共{total}条资讯（含正文{with_content}条）")
        QMessageBox.information(self, "采集完成", f"共获取 {total} 条资讯\n其中 {with_content} 条已获取正文\n点击「生成Word」导出报告")

    def on_error(self, error_msg):
        self.is_collecting = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.append_log(f"\n❌ 错误: {error_msg}")
        QMessageBox.critical(self, "错误", str(error_msg))

    def stop_collection(self):
        self.is_collecting = False
        self.stop_flag = True
        self.append_log("\n⏹ 已停止")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def export_to_word(self):
        if not self.collection_results:
            QMessageBox.warning(self, "提示", "请先执行采集！")
            return

        output_dir = self.output_path.text() if "点击" not in self.output_path.text() else DEFAULT_OUTPUT_DIR
        start_date, end_date = self.get_date_range()
        filename = f"汽车产业资讯简报_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}.docx"
        filepath = os.path.join(output_dir, filename)

        try:
            self.append_log(f"\n📝 正在生成Word文档...")
            exporter = WordExporter()
            exporter.export(results=self.collection_results, start_date=start_date, end_date=end_date, output_path=filepath)
            self.append_log(f"✅ 已生成: {filename}")
            QMessageBox.information(self, "导出成功", f"Word文档已保存至:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def closeEvent(self, event):
        if self.is_collecting:
            reply = QMessageBox.question(self, '提示', "正在采集中，确定要退出吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
