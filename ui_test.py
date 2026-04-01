from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QListWidgetItem, QRadioButton, 
                             QButtonGroup, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from data_manager import DataManager
import config

class TestingWindow(QDialog):
    def __init__(self, parent=None, is_readonly=False, test_data=None):
        super().__init__(parent)
        self.setWindowTitle("Окно тестирования")
        self.resize(1000, 600)
        
        self.is_readonly = is_readonly
        self.test_data = test_data
        self.all_questions_pool = DataManager.load_questions()
        
        if self.is_readonly and self.test_data:
            self.questions = []
            details = self.test_data['details']
            for q_id_str in details.keys():
                q_id = int(q_id_str)
                for q in self.all_questions_pool:
                    if q['id'] == q_id:
                        self.questions.append(q)
                        break
        else:
            self.questions = DataManager.get_uniform_questions()
            
        self.answers = {}
        if self.is_readonly:
            self.answers = {int(k): v for k, v in self.test_data['details'].items()}
            
        self.current_q_index = 0
        self.radio_buttons = []
        self.init_ui()
        
        if self.questions:
            self.load_question(0)
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить вопросы.")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Список вопросов
        left_panel = QVBoxLayout()
        self.question_list = QListWidget()
        self.question_list.currentRowChanged.connect(self.load_question)
        
        for i in range(len(self.questions)):
            item = QListWidgetItem(f"Вопрос №{i+1}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(QColor("#FFFFFF"))
            
            if self.is_readonly:
                q_id = self.questions[i]['id']
                status = self.answers.get(q_id, {}).get('status')
                if status == 'correct':
                    item.setBackground(QColor(config.COLOR_CORRECT))
                elif status == 'incorrect':
                    item.setBackground(QColor(config.COLOR_INCORRECT))
                else:
                    item.setBackground(QColor(config.COLOR_UNANSWERED))
                
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
        
        # Область вопроса
        right_panel = QVBoxLayout()
        self.lbl_question_text = QLabel("Текст вопроса")
        self.lbl_question_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_question_text.setFont(QFont("Arial", 14))
        self.lbl_question_text.setWordWrap(True)
        self.lbl_question_text.setStyleSheet("border: 1px solid gray; padding: 20px; background-color: white;")
        right_panel.addWidget(self.lbl_question_text)
        
        # Контейнер для вариантов ответов
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_layout.setContentsMargins(50, 20, 50, 20)
        self.radio_group = QButtonGroup(self)
        right_panel.addLayout(self.options_layout)
        
        # Информационная метка для правильного ответа (режим просмотра)
        self.lbl_correct_info = QLabel("")
        self.lbl_correct_info.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.lbl_correct_info.setStyleSheet(f"color: {config.COLOR_CORRECT}; padding: 10px; border: 1px dashed {config.COLOR_CORRECT}; border-radius: 5px;")
        self.lbl_correct_info.setWordWrap(True)
        self.lbl_correct_info.hide()
        right_panel.addWidget(self.lbl_correct_info)
        
        right_panel.addStretch()
        
        # Кнопки управления
        controls_layout = QHBoxLayout()
        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(60, 40)
        self.btn_prev.clicked.connect(lambda: self.question_list.setCurrentRow(max(0, self.current_q_index - 1)))
        
        self.btn_confirm = QPushButton("Подтвердить\nответ")
        self.btn_confirm.setFixedSize(120, 50)
        self.btn_confirm.clicked.connect(self.confirm_answer)
        
        self.btn_next = QPushButton(">")
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
        
        # Управление видимостью правильного ответа
        if self.is_readonly:
            q_id = q['id']
            ans_status = self.answers.get(q_id, {}).get('status')
            if ans_status in ['incorrect', 'unanswered']:
                correct_text = q['options'][q['correct']]
                self.lbl_correct_info.setText(f"Правильный ответ: {correct_text}")
                self.lbl_correct_info.show()
            else:
                self.lbl_correct_info.hide()
        else:
            self.lbl_correct_info.hide()

        # Обновление радио-кнопок
        for rb in self.radio_buttons:
            rb.hide()
            self.radio_group.removeButton(rb)
        
        for i, opt_text in enumerate(q['options']):
            if i < len(self.radio_buttons):
                rb = self.radio_buttons[i]
                rb.show()
            else:
                rb = QRadioButton()
                rb.setFont(QFont("Arial", 12))
                self.options_layout.addWidget(rb)
                self.radio_buttons.append(rb)
            
            rb.setText(opt_text)
            self.radio_group.addButton(rb, i)
            
            q_id = q['id']
            is_confirmed = q_id in self.answers and self.answers[q_id].get('confirmed', False)
            rb.setEnabled(not self.is_readonly and not is_confirmed)

        self.radio_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
        self.radio_group.setExclusive(True)
        
        q_id = q['id']
        if q_id in self.answers:
            sel_idx = self.answers[q_id]['selected']
            if sel_idx != -1 and sel_idx < len(q['options']):
                self.radio_buttons[sel_idx].setChecked(True)
        
        can_edit = not self.is_readonly and not (q_id in self.answers and self.answers[q_id].get('confirmed', False))
        self.btn_confirm.setEnabled(can_edit)
        self.btn_clear.setEnabled(can_edit)

    def confirm_answer(self):
        selected_id = self.radio_group.checkedId()
        if selected_id == -1:
            return
            
        q = self.questions[self.current_q_index]
        is_correct = (selected_id == q['correct'])
        status = 'correct' if is_correct else 'incorrect'
        
        self.answers[q['id']] = {
            "selected": selected_id,
            "status": status,
            "confirmed": True
        }
        
        item = self.question_list.item(self.current_q_index)
        item.setBackground(QColor(config.COLOR_CORRECT) if is_correct else QColor(config.COLOR_INCORRECT))
        
        # Автоматический переход к следующему вопросу
        next_idx = self.current_q_index + 1
        if next_idx < len(self.questions):
            self.question_list.setCurrentRow(next_idx)
        else:
            # Если это последний вопрос, просто обновляем текущий вид
            self.load_question(self.current_q_index)

    def clear_selection(self):
        self.radio_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
        self.radio_group.setExclusive(True)

    def finish_testing(self):
        unanswered_indices = []
        for i, q in enumerate(self.questions):
            if q['id'] not in self.answers or not self.answers[q['id']].get('confirmed', False):
                unanswered_indices.append(i)
                
        if unanswered_indices:
            q_nums = ", ".join([str(i + 1) for i in unanswered_indices])
            msg = f"Вы не подтвердили ответ на следующие вопросы:\n{q_nums}\n\nЗавершить тестирование?"
            reply = QMessageBox.warning(self, "Предупреждение", msg, 
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Cancel:
                return
        else:
            msg = "Вы дали ответы на все вопросы, хотите завершить тестирование?"
            reply = QMessageBox.question(self, "Завершение", msg,
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        final_details = {}
        correct_count = 0
        
        for i, q in enumerate(self.questions):
            q_id = q['id']
            if q_id in self.answers and self.answers[q_id].get('confirmed', False):
                final_details[q_id] = self.answers[q_id]
                if self.answers[q_id]['status'] == 'correct':
                    correct_count += 1
            else:
                final_details[q_id] = {"selected": -1, "status": "unanswered", "confirmed": True}
                self.question_list.item(i).setBackground(QColor(config.COLOR_UNANSWERED))
                
        passed = correct_count >= config.PASS_THRESHOLD
        DataManager.save_test_result(passed, final_details)
        
        self.accept()
        
        status_text = "пройдено" if passed else "не пройдено"
        QMessageBox.information(self.parent(), "Результат", 
                                f"Тестирование {status_text}!\nПравильных ответов: {correct_count} из {len(self.questions)}")