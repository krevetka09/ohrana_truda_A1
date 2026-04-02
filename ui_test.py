from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QListWidgetItem, QCheckBox, 
                             QMessageBox, QWidget, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from data_manager import DataManager
import config

class OptionWidget(QWidget):
    """Виджет варианта ответа на базе QCheckBox"""
    def __init__(self, parent=None, on_toggle_callback=None):
        super().__init__(parent)
        self.on_toggle_callback = on_toggle_callback
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox = QCheckBox()
        self.checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.checkbox.stateChanged.connect(self._on_state_changed)
        
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Arial", 12))
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label)
        self.label.mousePressEvent = self._label_clicked
        
    def _on_state_changed(self, state):
        if self.on_toggle_callback:
            self.on_toggle_callback()

    def _label_clicked(self, event):
        if self.checkbox.isEnabled():
            self.checkbox.setChecked(not self.checkbox.isChecked())
            
    def setText(self, text):
        self.label.setText(text)
        
    def setEnabled(self, enabled):
        self.checkbox.setEnabled(enabled)
        
    def setChecked(self, checked):
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)

    def isChecked(self):
        return self.checkbox.isChecked()

class TestingWindow(QDialog):
    def __init__(self, parent=None, is_readonly=False, test_data=None):
        super().__init__(parent)
        self.setWindowTitle("Окно тестирования")
        self.resize(1000, 600)
        
        self.is_readonly = is_readonly
        self.test_data = test_data
        self.all_questions_pool = DataManager.load_questions()
        self.start_time = None if self.is_readonly else datetime.now()
        
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
        self.option_widgets = []
        self.init_ui()
        
        if self.questions:
            self.load_question(0)
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить вопросы.")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        left_panel = QVBoxLayout()
        self.question_list = QListWidget()
        self.question_list.currentRowChanged.connect(self.load_question)
        
        for i in range(len(self.questions)):
            item = QListWidgetItem(f"Вопрос №{i+1}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(QColor("#FFFFFF"))
            if self.is_readonly:
                q_id = self.questions[i]['id']
                score = self.answers.get(q_id, {}).get('score', 0)
                if score >= 1.0:
                    item.setBackground(QColor(config.COLOR_CORRECT))
                elif score > 0:
                    item.setBackground(QColor("#FFF176")) # Желтый для частичных
                else:
                    item.setBackground(QColor(config.COLOR_INCORRECT))
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
        
        right_panel = QVBoxLayout()
        self.lbl_question_text = QLabel()
        self.lbl_question_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_question_text.setFont(QFont("Arial", 14))
        self.lbl_question_text.setWordWrap(True)
        self.lbl_question_text.setStyleSheet("border: 1px solid gray; padding: 20px; background-color: white;")
        right_panel.addWidget(self.lbl_question_text)
        
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_layout.setContentsMargins(50, 20, 50, 20)
        right_panel.addLayout(self.options_layout)
        
        self.lbl_correct_info = QLabel("")
        self.lbl_correct_info.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.lbl_correct_info.setStyleSheet(f"color: {config.COLOR_CORRECT}; padding: 10px; border: 1px dashed {config.COLOR_CORRECT}; border-radius: 5px;")
        self.lbl_correct_info.setWordWrap(True)
        self.lbl_correct_info.hide()
        right_panel.addWidget(self.lbl_correct_info)
        
        right_panel.addStretch()
        
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

    def update_selection_limit(self):
        """Ограничивает выбор: нельзя выбрать больше, чем есть правильных ответов"""
        if self.is_readonly: return
        
        q = self.questions[self.current_q_index]
        max_allowed = len(q['correct_indices'])
        checked_count = sum(1 for w in self.option_widgets if w.isVisible() and w.isChecked())
        
        for w in self.option_widgets:
            if not w.isChecked():
                w.setEnabled(checked_count < max_allowed)

    def load_question(self, index):
        if index < 0 or index >= len(self.questions): return
        self.current_q_index = index
        q = self.questions[index]
        self.lbl_question_text.setText(q['text'])
        
        if self.is_readonly:
            q_id = q['id']
            ans_data = self.answers.get(q_id, {})
            if ans_data.get('score', 0) < 1.0:
                correct_texts = [q['options'][i] for i in q['correct_indices']]
                self.lbl_correct_info.setText(f"Правильные ответы: \n{'\n'.join(correct_texts)}")
                self.lbl_correct_info.show()
            else:
                self.lbl_correct_info.hide()

        for w in self.option_widgets: w.hide()
        
        q_id = q['id']
        is_confirmed = q_id in self.answers and self.answers[q_id].get('confirmed', False)

        for i, opt_text in enumerate(q['options']):
            if i < len(self.option_widgets):
                w = self.option_widgets[i]
                w.show()
            else:
                w = OptionWidget(on_toggle_callback=self.update_selection_limit)
                self.options_layout.addWidget(w)
                self.option_widgets.append(w)
            
            w.setText(opt_text)
            w.setEnabled(not self.is_readonly and not is_confirmed)
            
            selected_list = self.answers.get(q_id, {}).get('selected', [])
            w.setChecked(i in selected_list)

        self.update_selection_limit()
        self.btn_confirm.setEnabled(not self.is_readonly and not is_confirmed)
        self.btn_clear.setEnabled(not self.is_readonly and not is_confirmed)

    def confirm_answer(self):
        selected_indices = [i for i, w in enumerate(self.option_widgets) if w.isVisible() and w.isChecked()]
        if not selected_indices: return
            
        q = self.questions[self.current_q_index]
        correct_indices = q['correct_indices']
        
        # Расчет баллов: 1 / кол-во_правильных за каждый верный выбор
        points_per_one = 1.0 / len(correct_indices)
        correct_selected = sum(1 for idx in selected_indices if idx in correct_indices)
        
        score = round(correct_selected * points_per_one, 2)
        if score > 0.98: score = 1.0 # Округление до целого при всех верных
        
        self.answers[q['id']] = {
            "selected": selected_indices,
            "score": score,
            "status": 'correct' if score >= 1.0 else 'incorrect',
            "confirmed": True
        }
        
        item = self.question_list.item(self.current_q_index)
        if score >= 1.0:
            item.setBackground(QColor(config.COLOR_CORRECT))
        elif score > 0:
            item.setBackground(QColor("#FFF176"))
        else:
            item.setBackground(QColor(config.COLOR_INCORRECT))
        
        next_idx = self.current_q_index + 1
        if next_idx < len(self.questions):
            self.question_list.setCurrentRow(next_idx)
        else:
            self.load_question(self.current_q_index)

    def clear_selection(self):
        for w in self.option_widgets:
            w.setChecked(False)
            w.setEnabled(True)

    def finish_testing(self):
        unanswered_indices = []
        for i, q in enumerate(self.questions):
            if q['id'] not in self.answers or not self.answers[q['id']].get('confirmed', False):
                unanswered_indices.append(i)
                
        if unanswered_indices:
            msg = f"Вы не подтвердили ответ на некоторые вопросы. Завершить?"
            if QMessageBox.warning(self, "Предупреждение", msg, QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Cancel:
                return

        final_details = {}
        total_score = 0.0
        
        for i, q in enumerate(self.questions):
            q_id = q['id']
            if q_id in self.answers and self.answers[q_id].get('confirmed', False):
                final_details[q_id] = self.answers[q_id]
                total_score += self.answers[q_id]['score']
            else:
                final_details[q_id] = {"selected": [], "score": 0.0, "status": "unanswered", "confirmed": True}
                
        duration_str = "00:00"
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            mins, secs = divmod(int(elapsed.total_seconds()), 60)
            duration_str = f"{mins:02d}:{secs:02d}"

        passed = total_score >= config.PASS_THRESHOLD
        DataManager.save_test_result(passed, final_details, duration_str)
        self.accept()
        
        status_text = "пройдено" if passed else "не пройдено"
        QMessageBox.information(self.parent(), "Результат", f"Тестирование {status_text}!\nНабрано баллов: {round(total_score, 2)} из {len(self.questions)}\nВремя: {duration_str}")