import csv
import json
import random
import os
from datetime import datetime
from config import RESULTS_FILE, STATISTIC_FILE, QUESTIONS_FILE, TOTAL_QUESTIONS

class DataManager:
    @staticmethod
    def init_files():
        if not os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['test_id', 'date', 'passed', 'details', 'duration'])
        
        if not os.path.exists(STATISTIC_FILE):
            with open(STATISTIC_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['metric', 'value'])

    @staticmethod
    def load_questions():
        questions = []
        if not os.path.exists(QUESTIONS_FILE):
            return questions

        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            for idx, row in enumerate(reader):
                if not row or len(row) < 2:
                    continue
                
                q_text = row[0]
                options = []
                correct_indices = []
                
                raw_options = row[1:]
                for i, opt in enumerate(raw_options):
                    opt = opt.strip()
                    if not opt:
                        continue
                    if opt.startswith('_'):
                        correct_indices.append(i)
                        opt = opt[1:]
                    options.append(opt)
                    
                questions.append({
                    "id": idx + 1,
                    "text": q_text,
                    "options": options,
                    "correct_indices": correct_indices
                })
        return questions

    @staticmethod
    def save_test_result(passed, details, duration="00:00"):
        tests = DataManager.get_all_results()
        test_id = len(tests) + 1
        date_str = datetime.now().strftime("%d.%m.%y %H:%M")
        
        with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([test_id, date_str, int(passed), json.dumps(details), duration])
        
        DataManager.update_statistics(passed, details)

    @staticmethod
    def get_all_results():
        results = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                next(reader, None)
                for row in reader:
                    if len(row) < 4: continue
                    results.append({
                        'test_id': int(row[0]),
                        'date': row[1],
                        'passed': bool(int(row[2])),
                        'details': json.loads(row[3]),
                        'duration': row[4] if len(row) > 4 else "Неизвестно"
                    })
        return results

    @staticmethod
    def update_statistics(passed, details):
        stats = DataManager.get_statistics()
        
        # Инициализация базовых метрик
        for key in ['total_answers', 'correct_answers_sum', 'unanswered', 'passed_tests', 'total_tests']:
            if key not in stats: stats[key] = 0.0
        
        stats['total_tests'] += 1
        if passed:
            stats['passed_tests'] += 1
            
        for q_id_str, data in details.items():
            stats['total_answers'] += 1
            status = data.get('status')
            score = data.get('score', 0.0)
            
            if status == 'unanswered':
                stats['unanswered'] += 1
            else:
                stats['correct_answers_sum'] = round(stats['correct_answers_sum'] + score, 2)
                if score < 1.0: # Если не полный балл, считаем как ошибку для анти-рейтинга
                    wrong_key = f"wrong_q_{q_id_str}"
                    stats[wrong_key] = stats.get(wrong_key, 0) + 1

        with open(STATISTIC_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['metric', 'value'])
            for k, v in stats.items():
                writer.writerow([k, v])

    @staticmethod
    def get_statistics():
        stats = {}
        if os.path.exists(STATISTIC_FILE):
            with open(STATISTIC_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        stats[row['metric']] = float(row['value'])
                    except:
                        stats[row['metric']] = 0.0
        return stats

    @staticmethod
    def get_uniform_questions():
        questions_pool = DataManager.load_questions()
        if len(questions_pool) < TOTAL_QUESTIONS:
            return questions_pool
        results = DataManager.get_all_results()
        q_usage = {q['id']: 0 for q in questions_pool}
        for res in results:
            for q_id_str in res['details'].keys():
                qid = int(q_id_str)
                if qid in q_usage: q_usage[qid] += 1
        pool = [(q, q_usage[q['id']]) for q in questions_pool]
        random.shuffle(pool)
        pool.sort(key=lambda x: x[1])
        selected = [item[0] for item in pool[:TOTAL_QUESTIONS]]
        random.shuffle(selected)
        return selected