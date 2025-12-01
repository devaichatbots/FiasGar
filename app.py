from flask import Flask, render_template, request, jsonify
import csv
import os
from functools import lru_cache

app = Flask(__name__)

# Конфигурация
CSV_FILE = 'export-reestrmkd-50-20251201.csv'
ENCODING = 'utf-8-sig'
DELIMITER = ';'

def load_data():
    """Загружает данные из CSV файла в список словарей"""
    data = []
    if not os.path.exists(CSV_FILE):
        print(f"Файл {CSV_FILE} не найден!")
        return data
    
    try:
        with open(CSV_FILE, 'r', encoding=ENCODING) as file:
            reader = csv.DictReader(file, delimiter=DELIMITER)
            
            for row in reader:
                cleaned_row = {k: (v if v and v.strip() != '' else None) for k, v in row.items()}
                data.append(cleaned_row)
        
        print(f"Загружено {len(data)} записей из CSV")
        return data
    except Exception as e:
        print(f"Ошибка при чтении CSV: {e}")
        return []

@lru_cache(maxsize=1)
def get_cached_data():
    """Кеширует загруженные данные для быстрого доступа"""
    return load_data()

def search_addresses(query):
    """Ищет адреса по введенному запросу"""
    if not query or len(query.strip()) < 2:
        return []
    
    data = get_cached_data()
    query_lower = query.strip().lower()
    results = []
    
    for item in data:
        address = item.get('address', '')
        if address and query_lower in address.lower():
            results.append({
                'address': address,
                'houseguid': item.get('houseguid', ''),
                'short': address[:100] + '...' if len(address) > 100 else address
            })
    
    results.sort(key=lambda x: len(x['address']))
    return results[:50]

def get_address_info(houseguid):
    """Получает полную информацию об адресе по houseguid"""
    data = get_cached_data()
    
    for item in data:
        if item.get('houseguid') == houseguid:
            return {
                'address': item.get('address', 'Не указан'),
                'houseguid': item.get('houseguid', 'Не указан'),
                'built_year': item.get('built_year', 'Не указан'),
                'area_total': item.get('area_total', 'Не указан'),
                'foundation_type': item.get('foundation_type', 'Не указан'),
                'wall_material': item.get('wall_material', 'Не указан'),
                'heating_type': item.get('heating_type', 'Не указан'),
                'hot_water_type': item.get('hot_water_type', 'Не указан'),
                'gas_type': item.get('gas_type', 'Не указан')
            }
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = search_addresses(query)
    return jsonify({'results': results})

@app.route('/address/<houseguid>', methods=['GET'])
def get_address(houseguid):
    info = get_address_info(houseguid)
    if info:
        return jsonify(info)
    else:
        return jsonify({'error': 'Адрес не найден'}), 404

@app.route('/stats', methods=['GET'])
def stats():
    """Статистика загруженных данных"""
    data = get_cached_data()
    return jsonify({
        'total_records': len(data),
        'has_data': len(data) > 0,
        'file_exists': os.path.exists(CSV_FILE)
    })

# Ошибки
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Загрузка данных при старте
print("=" * 50)
print("Инициализация приложения...")
print("=" * 50)
data = load_data()
print(f"Загружено записей: {len(data)}")
if data:
    print("Пример первой записи:")
    print(f"  Адрес: {data[0].get('address', 'Нет')}")
    print(f"  Код ФИАС: {data[0].get('houseguid', 'Нет')}")
print("=" * 50)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
