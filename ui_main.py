from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import config
from data_manager import DataManager
from ui_test import TestingWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное меню тестирования")
        self.resize(1100, 700)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        left_panel = QVBoxLayout()
        self.tests_list = QListWidget()
        self.tests_list.itemClicked.connect(self.open_readonly_test)
        self.populate_tests_list()
        left_panel.addWidget(self.tests_list)
        
        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setFixedWidth(280)
        main_layout.addWidget(left_container)
        
        center_panel = QVBoxLayout()
        
        lbl_stat_title = QLabel("Статистика")
        lbl_stat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_stat_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        center_panel.addWidget(lbl_stat_title)
        
        stat_content_layout = QHBoxLayout()
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        stat_content_layout.addWidget(self.canvas)
        
        text_stat_layout = QVBoxLayout()
        self.lbl_avg_correct = QLabel()
        self.lbl_total_answers = QLabel()
        self.lbl_passed_tests = QLabel()
        self.lbl_hardest_q = QLabel()
        
        for lbl in [self.lbl_avg_correct, self.lbl_total_answers, self.lbl_passed_tests, self.lbl_hardest_q]:
            lbl.setStyleSheet("border: 1px solid gray; padding: 10px; background-color: white;")
            lbl.setWordWrap(True)
            text_stat_layout.addWidget(lbl)
            
        stat_content_layout.addLayout(text_stat_layout)
        center_panel.addLayout(stat_content_layout)
        
        self.btn_start = QPushButton("Начать новое тестирование")
        self.btn_start.setStyleSheet("background-color: #42A5F5; color: white; font-weight: bold; padding: 15px; font-size: 14px;")
        self.btn_start.clicked.connect(self.start_new_test)
        center_panel.addWidget(self.btn_start, alignment=Qt.AlignmentFlag.AlignCenter)
        
        center_container = QWidget()
        center_container.setLayout(center_panel)
        main_layout.addWidget(center_container)
        
        self.update_statistics_view()

    def populate_tests_list(self):
        self.tests_list.clear()
        results = DataManager.get_all_results()
        for res in results:
            item = QListWidgetItem(f"Тестирование №{res['test_id']} от {res['date']}")
            item.setBackground(QColor(config.COLOR_CORRECT) if res['passed'] else QColor(config.COLOR_INCORRECT))
            item.setData(Qt.ItemDataRole.UserRole, res)
            self.tests_list.addItem(item)

    def update_statistics_view(self):
        stats = DataManager.get_statistics()
        
        correct = stats.get('correct_answers', 0)
        unanswered = stats.get('unanswered', 0)
        total_ans = stats.get('total_answers', 0)
        incorrect = total_ans - correct - unanswered
        total_tests = stats.get('total_tests', 0)
        passed_tests = stats.get('passed_tests', 0)
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if total_ans > 0:
            labels = ['Правильные', 'Неправильные', 'Без ответа']
            sizes = [correct, incorrect, unanswered]
            colors = ['#81C784', '#E57373', '#FFF176']
            
            # Фильтруем нулевые значения, чтобы на диаграмме не было пустых секторов
            labels_f, sizes_f, colors_f = [], [], []
            for l, s, c in zip(labels, sizes, colors):
                if s > 0:
                    labels_f.append(l)
                    sizes_f.append(s)
                    colors_f.append(c)
            
            ax.pie(sizes_f, labels=labels_f, autopct='%1.1f%%', startangle=90, colors=colors_f)
            ax.set_title("Соотношение ответов")
        else:
            ax.text(0.5, 0.5, 'Нет данных', horizontalalignment='center', verticalalignment='center')
            ax.axis('off')
        self.canvas.draw()
        
        avg_correct = (correct / total_tests) if total_tests > 0 else 0
        self.lbl_avg_correct.setText(f"Среднее количество правильных ответов: {avg_correct:.1f}")
        self.lbl_total_answers.setText(f"Общее количество заданных вопросов: {total_ans}")
        self.lbl_passed_tests.setText(f"Количество успешно сданных тестов: {passed_tests} из {total_tests}")
        
        hardest_q_id = "Нет данных"
        max_wrong = 0
        for k, v in stats.items():
            if k.startswith('wrong_q_') and v > max_wrong:
                max_wrong = v
                hardest_q_id = k.replace('wrong_q_', '')
                
        self.lbl_hardest_q.setText(f"Вопрос с наибольшим числом ошибок: №{hardest_q_id}")

    def start_new_test(self):
        test_window = TestingWindow(self)
        if test_window.exec():
            self.populate_tests_list()
            self.update_statistics_view()

    def open_readonly_test(self, item):
        test_data = item.data(Qt.ItemDataRole.UserRole)
        test_window = TestingWindow(self, is_readonly=True, test_data=test_data)
        test_window.exec()