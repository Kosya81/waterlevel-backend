import requests
from bs4 import BeautifulSoup
import json
import urllib3
import re
from urllib.parse import quote
import time
from datetime import datetime
import sys
import os

# Добавляем родительскую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal
from app import models

# Отключаем предупреждения о небезопасных запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def preprocess_js_object(js_str):
    # Remove any trailing commas before closing braces/brackets
    js_str = re.sub(r',(\s*[}\]])', r'\1', js_str)
    # Replace single quotes with double quotes for JSON compatibility
    js_str = re.sub(r"'", '"', js_str)
    # Remove any comments
    js_str = re.sub(r'//.*?\n', '\n', js_str)
    # Add quotes around property names
    js_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', js_str)
    return js_str

def generate_graph_url(station_id, station_name, days=14):
    """Generate URL for station graph"""
    base_url = "https://www.meteo.co.me/Hidrologija/aws-graph-h.php"
    encoded_name = quote(station_name)
    return f"{base_url}?s={station_id}&d={days}d&name={encoded_name}"

def get_station_data(station_id, station_name, days=14):
    """Get water level and temperature data from station graph page"""
    try:
        graph_url = generate_graph_url(station_id, station_name, days)
        response = requests.get(graph_url, verify=False)
        response.raise_for_status()
        
        # Ищем данные в JavaScript-коде
        data_matches = re.findall(r'var\s+Data_m\s*=\s*(\{.*?\});', response.text, re.DOTALL)
        data_h_matches = re.findall(r'var\s+Data_h\s*=\s*(\{.*?\});', response.text, re.DOTALL)
        
        data = {
            'water_level': [],
            'temperature': [],
            'timestamps': []
        }
        
        # Обрабатываем данные из Data_m (минутные данные)
        if data_matches:
            data_m_str = preprocess_js_object(data_matches[0])
            try:
                data_m = json.loads(data_m_str)
                if 'G1' in data_m and 'V' in data_m['G1'] and 'Tv' in data_m['G1']:
                    # Собираем данные о температуре
                    for point in data_m['G1']['Tv']:
                        if len(point) >= 2:
                            timestamp = datetime.fromtimestamp(point[0]/1000)
                            temperature = point[1] if point[1] is not None else None
                            data['timestamps'].append(timestamp)
                            data['temperature'].append(temperature)
                    
                    # Собираем данные об уровне воды
                    for point in data_m['G1']['V']:
                        if len(point) >= 2:
                            timestamp = datetime.fromtimestamp(point[0]/1000)
                            water_level = point[1] if point[1] is not None else None
                            data['timestamps'].append(timestamp)
                            data['water_level'].append(water_level)
            except json.JSONDecodeError as e:
                print(f"Error parsing Data_m JSON for station {station_id}: {e}")
                print("Problematic string:", data_m_str)
        
        # Обрабатываем данные из Data_h (часовые данные)
        if data_h_matches:
            data_h_str = preprocess_js_object(data_h_matches[0])
            try:
                data_h = json.loads(data_h_str)
                if 'G1' in data_h and 'V' in data_h['G1'] and 'Tv' in data_h['G1']:
                    # Добавляем часовые данные, если минутные отсутствуют
                    if not data['timestamps']:
                        for point in data_h['G1']['Tv']:
                            if len(point) >= 2:
                                timestamp = datetime.fromtimestamp(point[0]/1000)
                                temperature = point[1] if point[1] is not None else None
                                data['timestamps'].append(timestamp)
                                data['temperature'].append(temperature)
                        
                        for point in data_h['G1']['V']:
                            if len(point) >= 2:
                                timestamp = datetime.fromtimestamp(point[0]/1000)
                                water_level = point[1] if point[1] is not None else None
                                data['timestamps'].append(timestamp)
                                data['water_level'].append(water_level)
            except json.JSONDecodeError as e:
                print(f"Error parsing Data_h JSON for station {station_id}: {e}")
                print("Problematic string:", data_h_str)
        
        return data
    except requests.RequestException as e:
        print(f"Error fetching station data for {station_id}: {e}")
        return None

def get_station_links():
    url = "https://www.meteo.co.me/Hidrologija/aws_h.php"
    
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все теги <script>
        scripts = soup.find_all('script')
        all_stations = []
        
        for script in scripts:
            script_text = script.string
            if script_text:
                # Ищем объект staniceH
                staniceH_match = re.search(r'var\s+staniceH\s*=\s*(\{.*?\});', script_text, re.DOTALL)
                if staniceH_match:
                    staniceH_str = staniceH_match.group(1)
                    # Preprocess the JavaScript object string
                    staniceH_str = preprocess_js_object(staniceH_str)
                    try:
                        staniceH = json.loads(staniceH_str)
                        # Combine all stations into a single list
                        if 'jadranski' in staniceH:
                            for station in staniceH['jadranski']:
                                station.append(generate_graph_url(station[0], station[5]))
                            all_stations.extend(staniceH['jadranski'])
                        if 'crnomorski' in staniceH:
                            for station in staniceH['crnomorski']:
                                station.append(generate_graph_url(station[0], station[5]))
                            all_stations.extend(staniceH['crnomorski'])
                        break
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
                        print("Problematic string:", staniceH_str)
                        continue
        
        if all_stations:
            # Сохраняем базовую информацию о станциях
            with open('station_links.json', 'w', encoding='utf-8') as f:
                json.dump(all_stations, f, ensure_ascii=False, indent=4)
            print(f"Все станции найдены и сохранены в station_links.json")
            
            # Получаем данные для каждой станции
            station_data = {}
            for station in all_stations:
                station_id = station[0]
                station_name = station[5]
                
                print(f"Получение данных для станции {station_name} ({station_id})...")
                data = get_station_data(station_id, station_name)
                if data:
                    station_data[station_id] = {
                        'name': station_name,
                        'data': data
                    }
                time.sleep(1)  # Задержка между запросами
            
            # Сохраняем данные станций
            with open('station_data.json', 'w', encoding='utf-8') as f:
                json.dump(station_data, f, ensure_ascii=False, indent=4, default=str)
            print("Данные станций сохранены в station_data.json")
            
            return all_stations
        else:
            print("Станции не найдены")
            return []
            
    except requests.RequestException as e:
        print(f"Ошибка при получении данных: {e}")
        return []

def fill_stations_table():
    """Fill stations table with data from the website"""
    db = SessionLocal()
    try:
        stations = get_station_links()
        if not stations:
            print("Станции не найдены")
            return
        
        for station in stations:
            # station: [id, '-', lat, lon, height, name, type, river, 1, graph_url]
            station_data = {
                'name': station[5],
                'code': station[0],
                'river': station[7] if len(station) > 7 else None,
                'region': station[6] if len(station) > 6 else None,
                'coordinates': f"{station[2]},{station[3]}" if station[2] and station[3] else None,
                'graph_url': station[9] if len(station) > 9 else None
            }
            
            # Проверяем, существует ли станция
            existing_station = db.query(models.Station).filter(models.Station.code == station_data['code']).first()
            if existing_station:
                # Обновляем существующую станцию
                for key, value in station_data.items():
                    setattr(existing_station, key, value)
            else:
                # Создаем новую станцию
                new_station = models.Station(**station_data)
                db.add(new_station)
            
            print(f"Станция обработана: {station_data['name']} ({station_data['code']})")
        
        db.commit()
        print("Все станции добавлены/обновлены в базе данных.")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при заполнении таблицы станций: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fill_stations_table() 