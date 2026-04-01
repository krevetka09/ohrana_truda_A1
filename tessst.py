import sys
import os
import csv
import json
import random
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QListWidgetItem, QRadioButton, QButtonGroup, 
                             QMessageBox, QDialog, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Глобальные переменные согласно заданию
TOTAL_QUESTIONS = 20
PASS_THRESHOLD = 15

RESULTS_FILE = 'results.csv'
STATISTIC_FILE = 'statistic.csv'

# Генерация пула вопросов для демонстрации
QUESTIONS_POOL = []
for i in range(1, 51):
    QUESTIONS_POOL.append({
        "id": i,
        "text": f"Текст вопроса №{i}\n(Здесь может быть длинное описание сути вопроса для тестирования)",
        "options": [f"Вариант ответа 1 для вопроса {i}", 
                    f"Вариант ответа 2 для вопроса {i}", 
                    f"Вариант ответа 3 для вопроса {i}", 
                    f"Вариант ответа 4 для вопроса {i}"],
        "correct": random.randint(0, 3) # Случайный правильный ответ
    })

class DataManager:
    """Класс для управления сохранением и загрузкой данных в CSV"""
    @staticmethod
    def init_files():
        if not os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['test_id', 'date', 'passed', 'details'])
        
        if not os.path.exists(STATISTIC_FILE):
            with open(STATISTIC_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['metric', 'value'])

    @staticmethod
    def save_test_result(passed, details):
        tests = DataManager.get_all_results()
        test_id = len(tests) + 1
        date_str = datetime.now().strftime("%d.%m.%y %H:%M")
        
        with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([test_id, date_str, int(passed), json.dumps(details)])
        
        DataManager.update_statistics(passed, details)

    @staticmethod
    def get_all_results():
        results = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['test_id'] = int(row['test_id'])
                    row['passed'] = bool(int(row['passed']))
                    row['details'] = json.loads(row['details'])
                    results.append(row)
        return results

    @staticmethod
    def update_statistics(passed, details):
        stats = DataManager.get_statistics()
        
        # Инициализация базовых метрик
        stats['total_answers'] = stats.get('total_answers', 0)
        stats['correct_answers'] = stats.get('correct_answers', 0)
        stats['passed_tests'] = stats.get('passed_tests', 0)
        stats['total_tests'] = stats.get('total_tests', 0)
        
        stats['total_tests'] += 1
        if passed:
            stats['passed_tests'] += 1
            
        for q_id_str, data in details.items():
            stats['total_answers'] += 1
            if data['is_correct']:
                stats['correct_answers'] += 1
            else:
                wrong_key = f"wrong_q_{q_id_str}"
                stats[wrong_key] = stats.get(wrong_key, 0) + 1

        with open(STATISTIC_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['metric', 'value'])
            for k, v in stats.items():
                writer.writerow([k, v])

    @staticmethod
    def get_statistics():
        stats = {}
        if os.path.exists(STATISTIC_FILE):
            with open(STATISTIC_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats[row['metric']] = int(row['value'])
        return stats

    @staticmethod
    def get_uniform_questions():
        """Выбирает вопросы равномерно, отдавая приоритет тем, которые выпадали реже"""
        stats = DataManager.get_statistics()
        results = DataManager.get_all_results()
        
        # Подсчет, сколько раз выпадал каждый вопрос
        q_usage = {q['id']: 0 for q in QUESTIONS_POOL}
        for res in results:
            for q_id_str in res['details'].keys():
                q_id = int(q_id_str)
                if q_id in q_usage:
                    q_usage[q_id] += 1
        
        # Сортируем вопросы по частоте использования (по возрастанию), затем перемешиваем группы с одинаковой частотой
        pool_with_usage = [(q, q_usage[q['id']]) for q in QUESTIONS_POOL]
        random.shuffle(pool_with_usage) # Перемешиваем, чтобы не брались одни и те же при равном счетчике
        pool_with_usage.sort(key=lambda x: x[1])
        
        selected_questions = [item[0] for item in pool_with_usage[:TOTAL_QUESTIONS]]
        random.shuffle(selected_questions) # Перемешиваем итоговый билет
        return selected_questions

class TestingWindow(QDialog):
    def __init__(self, parent=None, is_readonly=False, test_data=None):
        super().__init__(parent)
        self.setWindowTitle("Окно тестирования")
        self.resize(1000, 600)
        
        self.is_readonly = is_readonly
        self.test_data = test_data
        
        if self.is_readonly and self.test_data:
            # Режим просмотра пройденного теста
            self.questions = []
            for q_id_str in self.test_data['details'].keys():
                q_id = int(q_id_str)
                for q in QUESTIONS_POOL:
                    if q['id'] == q_id:
                        self.questions.append(q)
                        break
        else:
            # Режим нового теста
            self.questions = DataManager.get_uniform_questions()
            
        self.answers = {} # Формат: {q_id: {"selected": int, "is_correct": bool}}
        if self.is_readonly:
            self.answers = {int(k): v for k, v in self.test_data['details'].items()}
            
        self.current_q_index = 0
        self.init_ui()
        self.load_question(0)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Левая панель с номерами вопросов
        left_panel = QVBoxLayout()
        self.question_list = QListWidget()
        self.question_list.currentRowChanged.connect(self.load_question)
        
        for i in range(len(self.questions)):
            item = QListWidgetItem(f"Вопрос №{i+1}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(QColor("#FFFFFF"))
            
            if self.is_readonly:
                q_id = self.questions[i]['id']
                is_correct = self.answers[q_id]['is_correct']
                item.setBackground(QColor("#32CD32") if is_correct else QColor("#DC143C"))
                
            self.question_list.addItem(item)
            
        left_panel.addWidget(self.question_list)
        
        if not self.is_readonly:
            self.btn_finish = QPushButton("Завершить тестирование")
            self.btn_finish.setStyleSheet("background-color: #64B5F6; font-weight: bold; padding: 10px;")
            self.btn_finish.clicked.connect(self.finish_testing)
            left_panel.addWidget(self.btn_finish)
            
        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setFixedWidth(250)
        main_layout.addWidget(left_container)
        
        # Правая панель с текущим вопросом
        right_panel = QVBoxLayout()
        
        # Текст вопроса
        self.lbl_question_text = QLabel("Текст вопроса")
        self.lbl_question_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_question_text.setFont(QFont("Arial", 14))
        self.lbl_question_text.setWordWrap(True)
        self.lbl_question_text.setStyleSheet("border: 1px solid gray; padding: 20px; background-color: white;")
        right_panel.addWidget(self.lbl_question_text)
        
        # Радио-кнопки
        self.radio_group = QButtonGroup(self)
        self.radio_buttons = []
        options_layout = QVBoxLayout()
        options_layout.setSpacing(15)
        options_layout.setContentsMargins(50, 30, 50, 30)
        
        for i in range(4):
            rb = QRadioButton(f"Вариант ответа {i+1}")
            rb.setFont(QFont("Arial", 12))
            self.radio_group.addButton(rb, i)
            self.radio_buttons.append(rb)
            options_layout.addWidget(rb)
            
        right_panel.addLayout(options_layout)
        right_panel.addStretch()
        
        # Кнопки управления (Очистить, Навигация, Подтвердить)
        controls_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton(f"🡸")
        self.btn_prev.setFixedSize(60, 40)
        self.btn_prev.clicked.connect(lambda: self.question_list.setCurrentRow(max(0, self.current_q_index - 1)))
        
        self.btn_confirm = QPushButton("Подтвердить\nответ")
        self.btn_confirm.setFixedSize(120, 50)
        self.btn_confirm.clicked.connect(self.confirm_answer)
        
        self.btn_next = QPushButton(f"🡺")
        self.btn_next.setFixedSize(60, 40)
        self.btn_next.clicked.connect(lambda: self.question_list.setCurrentRow(min(len(self.questions)-1, self.current_q_index + 1)))
        
        self.btn_clear = QPushButton("Очистить\nвыбор")
        self.btn_clear.setFixedSize(100, 50)
        self.btn_clear.clicked.connect(self.clear_selection)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_confirm)
        controls_layout.addWidget(self.btn_next)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_clear)
        
        if self.is_readonly:
            self.btn_confirm.hide()
            self.btn_clear.hide()
            for rb in self.radio_buttons:
                rb.setEnabled(False)
                
        right_panel.addLayout(controls_layout)
        
        right_container = QWidget()
        right_container.setLayout(right_panel)
        main_layout.addWidget(right_container)

    def load_question(self, index):
        if index < 0 or index >= len(self.questions):
            return
            
        self.current_q_index = index
        q = self.questions[index]
        
        self.lbl_question_text.setText(q['text'])
        for i, rb in enumerate(self.radio_buttons):
            rb.setText(q['options'][i])
            
        # Восстановление состояния радио-кнопок
        self.radio_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
        self.radio_group.setExclusive(True)
        
        if not self.is_readonly:
            for rb in self.radio_buttons:
                rb.setEnabled(True)
            self.btn_confirm.setEnabled(True)
            self.btn_clear.setEnabled(True)
            
        q_id = q['id']
        if q_id in self.answers:
            selected_idx = self.answers[q_id]['selected']
            if selected_idx is not None and selected_idx >= 0:
                self.radio_buttons[selected_idx].setChecked(True)
                
            # Если ответ был подтвержден в текущем тесте, блокируем кнопки
            if not self.is_readonly and 'is_correct' in self.answers[q_id]:
                for rb in self.radio_buttons:
                    rb.setEnabled(False)
                self.btn_confirm.setEnabled(False)
                self.btn_clear.setEnabled(False)

    def confirm_answer(self):
        selected_id = self.radio_group.checkedId()
        if selected_id == -1:
            return
            
        q = self.questions[self.current_q_index]
        is_correct = (selected_id == q['correct'])
        
        self.answers[q['id']] = {
            "selected": selected_id,
            "is_correct": is_correct
        }
        
        # Обновление цвета в списке
        item = self.question_list.item(self.current_q_index)
        item.setBackground(QColor("#32CD32") if is_correct else QColor("#DC143C"))
        
        # Блокировка
        for rb in self.radio_buttons:
            rb.setEnabled(False)
        self.btn_confirm.setEnabled(False)
        self.btn_clear.setEnabled(False)

    def clear_selection(self):
        self.radio_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
        self.radio_group.setExclusive(True)

    def finish_testing(self):
        unanswered = []
        for i, q in enumerate(self.questions):
            if q['id'] not in self.answers or 'is_correct' not in self.answers[q['id']]:
                unanswered.append(str(i + 1))
                
        if unanswered:
            msg = f"Вы не подтвердили ответ на следующие вопросы:\n{', '.join(unanswered)}"
            reply = QMessageBox.warning(self, "Предупреждение", msg, 
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            # В задании сказано: "есть две кнопки Ок и Отмена". Если Ок, то просто закрываем окно предупреждения.
            return
            
        reply = QMessageBox.question(self, "Завершение", "Вы дали ответы на все вопросы, хотите завершить тестирование?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            correct_count = sum(1 for ans in self.answers.values() if ans['is_correct'])
            passed = correct_count >= PASS_THRESHOLD
            
            DataManager.save_test_result(passed, self.answers)
            
            self.accept()
            
            status_msg = f"Тестирование пройдено!\nПравильных ответов: {correct_count} из {TOTAL_QUESTIONS}" if passed else \
                         f"Тестирование не пройдено.\nПравильных ответов: {correct_count} из {TOTAL_QUESTIONS}. Нужно минимум {PASS_THRESHOLD}."
            
            QMessageBox.information(self.parent(), "Результат", status_msg, QMessageBox.StandardButton.Ok)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное меню")
        self.resize(1100, 700)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Левая панель - список тестов
        left_panel = QVBoxLayout()
        self.tests_list = QListWidget()
        self.tests_list.itemClicked.connect(self.open_readonly_test)
        self.populate_tests_list()
        left_panel.addWidget(self.tests_list)
        
        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setFixedWidth(280)
        main_layout.addWidget(left_container)
        
        # Центральная панель
        center_panel = QVBoxLayout()
        
        # Заголовок статистики
        lbl_stat_title = QLabel("Статистика")
        lbl_stat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_stat_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        center_panel.addWidget(lbl_stat_title)
        
        # Горизонтальный блок: Круговая диаграмма + Текстовая статистика
        stat_content_layout = QHBoxLayout()
        
        # Настройка matplotlib
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        stat_content_layout.addWidget(self.canvas)
        
        # Текстовая статистика
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
        
        # Кнопка начать тест
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
            item.setBackground(QColor("#32CD32") if res['passed'] else QColor("#DC143C"))
            # Сохраняем данные в элементе для открытия по клику
            item.setData(Qt.ItemDataRole.UserRole, res)
            self.tests_list.addItem(item)

    def update_statistics_view(self):
        stats = DataManager.get_statistics()
        
        correct = stats.get('correct_answers', 0)
        total_ans = stats.get('total_answers', 0)
        incorrect = total_ans - correct
        total_tests = stats.get('total_tests', 0)
        passed_tests = stats.get('passed_tests', 0)
        
        # Отрисовка круговой диаграммы
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if total_ans > 0:
            ax.pie([correct, incorrect], labels=['Правильные', 'Неправильные'], 
                   autopct='%1.1f%%', startangle=90, colors=['#81C784', '#E57373'])
            ax.set_title("Соотношение ответов")
        else:
            ax.text(0.5, 0.5, 'Нет данных', horizontalalignment='center', verticalalignment='center')
            ax.axis('off')
        self.canvas.draw()
        
        # Обновление текстовых меток
        avg_correct = (correct / total_tests) if total_tests > 0 else 0
        self.lbl_avg_correct.setText(f"Среднее количество правильных ответов: {avg_correct:.1f}")
        self.lbl_total_answers.setText(f"Общее количество данных ответов: {total_ans}")
        self.lbl_passed_tests.setText(f"Количество успешно сданных тестов: {passed_tests} из {total_tests}")
        
        # Поиск самого сложного вопроса
        hardest_q_id = "Нет данных"
        max_wrong = 0
        for k, v in stats.items():
            if k.startswith('wrong_q_') and v > max_wrong:
                max_wrong = v
                hardest_q_id = k.replace('wrong_q_', '')
                
        self.lbl_hardest_q.setText(f"Вопрос на который чаще всего даётся неправильный ответ: №{hardest_q_id}")

    def start_new_test(self):
        test_window = TestingWindow(self)
        if test_window.exec():
            self.populate_tests_list()
            self.update_statistics_view()

    def open_readonly_test(self, item):
        test_data = item.data(Qt.ItemDataRole.UserRole)
        test_window = TestingWindow(self, is_readonly=True, test_data=test_data)
        test_window.exec()

if __name__ == '__main__':
    DataManager.init_files()
    app = QApplication(sys.argv)
    
    # Глобальный стиль приложения
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())