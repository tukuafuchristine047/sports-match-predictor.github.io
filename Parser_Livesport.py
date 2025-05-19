import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import schedule
import json
import os

def get_flag_url(country_name):
    """Ищет URL флага для страны на worldometers.info"""
    try:
        if country_name == 'USA':
            country_name = 'United States'
        
        url = 'https://www.worldometers.info/geography/flags-of-the-world/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        flag_img = soup.find('img', class_='w-[120px] h-[80px] object-contain', alt=country_name)
        if flag_img and 'src' in flag_img.attrs:
            flag_path = flag_img['src']
            return f'https://www.worldometers.info{flag_path}'
        return 'N/A'
    except Exception as e:
        print(f"Ошибка при поиске флага для {country_name}: {e}")
        return 'N/A'

def parse_livesport_matches(url, sport_name):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--user-data-dir=/tmp/chrome_profile')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        match_blocks = soup.find_all('div', class_='event__match')
        
        if not match_blocks:
            print(f"[{sport_name}] Блоки матчей не найдены. Проверьте класс 'event__match' или структуру страницы.")
            print(f"[{sport_name}] Первые 500 символов HTML для диагностики:")
            print(str(soup)[:500])
            return []
        
        matches = []
        for match in match_blocks:
            time_elem = match.find('div', class_='event__time')
            match_time = time_elem.text.strip() if time_elem else 'N/A'
            
            # Специальная логика для футбола
            if sport_name == 'Soccer':
                participant1_elem = match.find('div yüksel, class_='event__homeParticipant')
                participant2_elem = match.find('div', class_='event__awayParticipant')
                
                if participant1_elem:
                    participant1_img = participant1_elem.find('img')
                    participant1_name = participant1_img['alt'] if participant1_img and 'alt' in participant1_img.attrs else 'N/A'
                    participant1_logo = participant1_img['src'] if participant1_img and 'src' in participant1_img.attrs else None
                else:
                    participant1_name = 'N/A'
                    participant1_logo = None
                
                if participant2_elem:
                    participant2_img = participant2_elem.find('img')
                    participant2_name = participant2_img['alt'] if participant2_img and 'alt' in participant2_img.attrs else 'N/A'
                    participant2_logo = participant2_img['src'] if participant2_img and 'src' in participant2_img.attrs else None
                else:
                    participant2_name = 'N/A'
                    participant2_logo = None
            else:
                # Проверяем парный формат для других видов спорта
                participant1_home1 = match.find('div', class_='event__participant--home1')
                participant1_home2 = match.find('div', class_='event__participant--home2')
                participant2_away1 = match.find('div', class_='event__participant--away1')
                participant2_away2 = match.find('div', class_='event__participant--away2')
                
                if participant1_home1 and participant1_home2:
                    participant1_name = f"{participant1_home1.text.strip()} / {participant1_home2.text.strip()}"
                else:
                    participant1_elem = match.find('div', class_='event__participant--home')
                    participant1_name = participant1_elem.text.strip() if participant1_elem else 'N/A'
                
                if participant2_away1 and participant2_away2:
                    participant2_name = f"{participant2_away1.text.strip()} / {participant2_away2.text.strip()}"
                else:
                    participant2_elem = match.find('div', class_='event__participant--away')
                    participant2_name = participant2_elem.text.strip() if participant2_elem else 'N/A'
                
                participant1_logo_elem = match.find('img', class_='event__logo--home')
                participant2_logo_elem = match.find('img', class_='event__logo--away')
                
                participant1_logo = participant1_logo_elem['src'] if participant1_logo_elem and 'src' in participant1_logo_elem.attrs else None
                participant2_logo = participant2_logo_elem['src'] if participant2_logo_elem and 'src' in participant2_logo_elem.attrs else None
            
            # Обработка логотипов для всех видов спорта
            if not participant1_logo:
                participant1_span1 = match.find('span', class_='event__logo--home1')
                participant1_span2 = match.find('span', class_='event__logo--home2')
                if participant1_span1 and 'title' in participant1_span1.attrs:
                    country_name = participant1_span1['title']
                    participant1_logo = get_flag_url(country_name)
                elif participant1_span2 and 'title' in participant1_span2.attrs:
                    country_name = participant1_span2['title']
                    participant1_logo = get_flag_url(country_name)
                else:
                    participant1_span = match.find('span', class_='event__logo--home')
                    participant1_logo = get_flag_url(participant1_span['title']) if participant1_span and 'title' in participant1_span.attrs else 'N/A'
            
            if not participant2_logo:
                participant2_span1 = match.find('span', class_='event__logo--away1')
                participant2_span2 = match.find('span', class_='event__logo--away2')
                if participant2_span1 and 'title' in participant2_span1.attrs:
                    country_name = participant2_span1['title']
                    participant2_logo = get_flag_url(country_name)
                elif participant2_span2 and 'title' in participant2_span2.attrs:
                    country_name = participant2_span2['title']
                    participant2_logo = get_flag_url(country_name)
                else:
                    participant2_span = match.find('span', class_='event__logo--away')
                    participant2_logo = get_flag_url(participant2_span['title']) if participant2_span and 'title' in participant2_span.attrs else 'N/A'
            
            matches.append({
                'time': match_time,
                'team1': participant1_name,
                'team2': participant2_name,
                'logo1': participant1_logo,
                'logo2': participant2_logo
            })
        
        return matches
    
    except Exception as e:
        print(f"[{sport_name}] Ошибка при парсинге: {e}")
        return []

def send_to_api(matches, sport_name, api_url):
    try:
        # API key (in production, load from environment variable)
        API_KEY = os.getenv('API_KEY', 'x7k9mPqT3vL8nRwY2cF5bZ6tJ4hD0gN1aE3uW8iQ2oX9lS7yV')  # Replace 'your-secret-api-key' with default for testing
        
        # Подготовка данных в формате JSON
        filtered_matches = [
            {
                'time': match['time'],
                'team1': match['team1'],
                'team2': match['team2'],
                'logo1': match['logo1'] if match['logo1'] != 'N/A' else 'https://www.pinclipart.com/picdir/big/488-4885392_gray-shield-badge-with-black-ribbon-ribbon-banner.png',
                'logo2': match['logo2'] if match['logo2'] != 'N/A' else 'https://www.pinclipart.com/picdir/big/488-4885392_gray-shield-badge-with-black-ribbon-ribbon-banner.png'
            }
            for match in matches if match['time'] != 'N/A'
        ]
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Удаление старых данных
        try:
            response = requests.delete(api_url, headers=headers, timeout=10)
            if response.status_code not in [200, 204]:
                print(f"[{sport_name}] Предупреждение: Не удалось удалить старые данные с {api_url}. Код ответа: {response.status_code}")
        except requests.RequestException as e:
            print(f"[{sport_name}] Ошибка при удалении старых данных с {api_url}: {e}")
        
        # Отправка новых данных
        response = requests.post(api_url, headers=headers, data=json.dumps(filtered_matches), timeout=10)
        response.raise_for_status()
        print(f"[{sport_name}] Данные успешно отправлены на {api_url}")
    except requests.RequestException as e:
        print(f"[{sport_name}] Ошибка при отправке данных на {api_url}: {e}")

def update_all_sports():
    sports = [
        {'name': 'Basketball', 'url': 'https://www.livesport.com/en/basketball/', 'api': 'https://your-website.com/basketball/api'},
        {'name': 'Tennis', 'url': 'https://www.livesport.com/en/tennis/', 'api': 'https://your-website.com/tennis/api'},
        {'name': 'Soccer', 'url': 'https://www.livesport.com/en/soccer/', 'api': 'https://your-website.com/soccer/api'},
        {'name': 'Hockey', 'url': 'https://www.livesport.com/en/hockey/', 'api': 'https://your-website.com/hockey/api'},
        {'name': 'Baseball', 'url': 'https://www.livesport.com/en/baseball/', 'api': 'https://your-website.com/baseball/api'},
        {'name': 'Rugby', 'url': 'https://www.livesport.com/en/rugby-union/', 'api': 'https://your-website.com/rugby/api'},
        {'name': 'Volleyball', 'url': 'https://www.livesport.com/en/volleyball/', 'api': 'https://your-website.com/volleyball/api'},
        {'name': 'Badminton', 'url': 'https://www.livesport.com/en/badminton/', 'api': 'https://your-website.com/badminton/api'},
        {'name': 'Boxing', 'url': 'https://www.livesport.com/en/boxing/', 'api': 'https://your-website.com/boxing/api'}
    ]
    
    for sport in sports:
        sport_name = sport['name']
        url = sport['url']
        api_url = sport['api']
        
        print(f"Парсинг {sport_name}...")
        matches = parse_livesport_matches(url, sport_name)
        
        if matches:
            send_to_api(matches, sport_name, api_url)
        else:
            print(f"[{sport_name}] Не удалось получить данные о матчах")

def main():
    # Запускаем обновление сразу при старте
    update_all_sports()
    
    # Планируем обновление каждые 10 минут
    schedule.every(10).minutes.do(update_all_sports)
    
    print("Скрипт запущен. Обновление данных каждые 10 минут...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту

if __name__ == "__main__":
    main()