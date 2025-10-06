import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
import re


URL_POLITICS = "https://ria.ru/politics/"
URL_SCIENCE = "https://ria.ru/science/"
URL_HEALTH = "https://ria.ru/health/"


"""
{
  'news': [
      {
          'title': 'Заголовок новости',
          'date': 'ДД.ММ.ГГГГ' или 'ГГГГ-ММ-ДД',
          'time': 'ЧЧ:ММ' или '',
          'image': 'URL картинки или относительный путь',
          'link': 'URL полной версии новости'
      },
      ...
  ]
}

!!!! ФУНКЦИИ 


- parse_latest_news_politics(url=URL_POLITICS): принимает url раздела о политике РИА новостей ria.ru/politics/, возвращает словарь news (см. выше)

- get_full_article_text_politics(url): принимает URL полной версии новости с ria.ru/politics/, возвращает строку с полным текстом статьи.

- get_article_preview_politics(url, preview_length=300): Принимает максимальную длину превью и url полной версии новости с ria.ru/politics/,
  возвращает строку с кратким текстовым превью статьи
	



- parse_latest_news_science(url=URL_SCIENCE): принимает url раздела о науке РИА новостей ria.ru/science/, возвращает словарь news (см. выше)

- get_full_article_text_science(url): принимает URL полной версии новости с ria.ru/science/, возвращает строку с полным текстом статьи.

- get_article_preview_science(url, preview_length=300): Принимает максимальную длину превью и url полной версии новости с ria.ru/science/,
  возвращает строку с кратким текстовым превью статьи




- parse_latest_news_health(url=URL_HEALTH): принимает url раздела о здоровье РИА новостей ria.ru/health/, возвращает словарь news (см. выше)

- get_full_article_text_health(url): принимает URL полной версии новости с ria.ru/health/, возвращает строку с полным текстом статьи.

- get_article_preview_health(url, preview_length=300): Принимает максимальную длину превью и url полной версии новости с ria.ru/health/,
  возвращает строку с кратким текстовым превью статьи



!!!! КЛАСС 
 
class NewsParser:   ///   Универсальный парсер новостей с RIA.ru


!!!!  МЕТОД   ///   что делает               


get_today_date(self) -> str:   ///   Возвращает сегодняшнюю дату в формате ДД.ММ.ГГГГ

_make_request(self, url: str) -> Optional[BeautifulSoup]:   ///   Выполняет HTTP запрос и возвращает BeautifulSoup объект

_extract_time_from_text(self, time_text: str) -> str:   ///   Извлекает время из текста в формате ЧЧ:ММ

_parse_date_time(self, item) -> tuple[str, str]:   ///   Парсит дату и время из элемента новости

_extract_image_url(self, item) -> str:   ///   Извлекает URL изображения из элемента новости

_extract_link(self, item) -> Optional[str]:   ///   Извлекает и нормализует ссылку на новость

_extract_title(self, item) -> Optional[str]:   ///   Извлекает заголовок новости

parse_latest_news(self, url: str, category: str = "general") -> Dict[str, List]:   ///   Основная функция парсинга новостей

_is_table_of_contents(self, text: str) -> bool:   ///   Определяет, является ли текст оглавлением

_extract_news_preview(self, text: str, preview_length: int = 300) -> str:   ///   Извлекает превью новости, пропуская оглавление

get_full_article_text(self, url: str, preserve_formatting: bool = True) -> str:   ///   Получает полный текст статьи с сохранением форматирования

get_article_preview(self, url: str, preview_length: int = 300) -> str:   ///   Получает превью статьи без оглавления

_extract_formatted_text(self, content_div) -> str:   ///   Извлекает текст с сохранением форматирования и переносов строк

"""


class NewsParser:
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_today_date(self) -> str:
        return datetime.now().strftime("%d.%m.%Y")
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = self.session.get(url)
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'lxml')
        except Exception:
            return None
    
    def _extract_time_from_text(self, time_text: str) -> str:
        time_clean = ''
        colon_found = False
        digits_after_colon = 0
        
        for char in time_text:
            if char == ':':
                colon_found = True
                time_clean += char
            elif char.isdigit():
                if colon_found:
                    digits_after_colon += 1
                    if digits_after_colon <= 2:
                        time_clean += char
                    else:
                        break
                else:
                    time_clean += char
            else:
                break
        
        return time_clean
    
    def _parse_date_time(self, item) -> tuple[str, str]:
        date, time = '', ''
        
        date_selectors = ['.cell-info__date', '[data-type="date"]', '.list-item__info']
        date_element = None
        
        for selector in date_selectors:
            date_element = item.select_one(selector)
            if date_element:
                break
        
        if not date_element:
            return date, time
        
        date_text = date_element.get_text().strip()
        
        if ',' in date_text:
            parts = date_text.split(',', 1)
            if len(parts) == 2:
                date_part, time_part = parts
                date = date_part.strip()
                
                if time_part and any(c.isdigit() for c in time_part):
                    time = self._extract_time_from_text(time_part.strip())
        else:
            if ':' in date_text:
                time = self._extract_time_from_text(date_text)
                date = 'Сегодня' if time else ''
            else:
                date = date_text
        
        # Если есть время, но нет даты - ставим "Сегодня"
        if time and not date:
            date = 'Сегодня'
            
        return date, time
    
    def _extract_image_url(self, item) -> str:
        image = ''
        
        # Поиск в специализированных контейнерах для science
        img_container = item.select_one('.cell-list__item-img')
        if img_container:
            img_tag = img_container.select_one('img')
            if img_tag:
                image = img_tag.get('src') or img_tag.get('data-src') or ''
        
        # Поиск в обычных img тегах
        if not image:
            img_tag = item.select_one('img')
            if img_tag:
                image = img_tag.get('src') or img_tag.get('data-src') or ''
        
        # Поиск в background-image стилях
        if not image:
            div_with_bg = item.select_one('[style*="background-image"]')
            if div_with_bg and div_with_bg.get('style'):
                style = div_with_bg['style']
                if 'url(' in style:
                    start = style.find('url(')
                    end = style.find(')', start)
                    if start != -1 and end != -1:
                        image = style[start+4:end].strip('"\'')
        
        # Нормализация URL изображения
        if image:
            if image.startswith('//'):
                image = 'https:' + image
            elif image.startswith('/'):
                image = 'https://ria.ru' + image
        
        return image
    
    def _extract_link(self, item) -> Optional[str]:
        link = item.get('href', '')
        
        if not link:
            link_tag = item.select_one('a[href]')
            if link_tag:
                link = link_tag.get('href', '')
        
        if not link:
            return None
        
        # Нормализация URL
        if link.startswith('/'):
            link = 'https://ria.ru' + link
        elif link.startswith('//'):
            link = 'https:' + link
        
        return link
    
    def _extract_title(self, item) -> Optional[str]:
        title_selectors = [
            '.cell-list__item-title', 
            '.list-item__title', 
            'h2', 
            'h3',
            '.news-item__title'
        ]
        
        title_tag = None
        for selector in title_selectors:
            title_tag = item.select_one(selector)
            if title_tag:
                break
        
        if not title_tag:
            title_tag = item
        
        title = title_tag.get_text().strip()
        return title if title and len(title) >= 10 else None
    
    def parse_latest_news(self, url: str, category: str = "general") -> Dict[str, List]:
        soup = self._make_request(url)
        if not soup:
            return {'news': []}
        
        news_dict = {'news': []}
        seen_links = set()
        
        # Селекторы для элементов новостей
        item_selectors = ['.cell-list__item', '.list-item', '.news-item', '[data-type="news"]']
        items = []
        
        for selector in item_selectors:
            found_items = soup.select(selector)
            if found_items:
                items.extend(found_items)
        
        for item in items:
            try:
                # Извлечение заголовка
                title = self._extract_title(item)
                if not title:
                    continue
                
                # Извлечение и проверка ссылки
                link = self._extract_link(item)
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                
                # Парсинг даты и времени
                date, time = self._parse_date_time(item)
                
                # Извлечение изображения
                image = self._extract_image_url(item)
                
                # Добавление новости в результат
                news_dict['news'].append({
                    'title': title,
                    'date': date,
                    'time': time,
                    'image': image,
                    'link': link
                })
                
            except Exception:
                continue
        
        return news_dict
    
    def _is_table_of_contents(self, text: str) -> bool:
        toc_indicators = [
            'оглавление', 'содержание', 'содержит', 'в статье', 
            'читайте также', 'table of contents', 'toc',
            'введение', 'заголовок', 'раздел', 'часть', 'глава'
        ]
        
        text_lower = text.lower().strip()
        if len(text_lower) < 50:  # Слишком короткий текст для содержания
            return False
            
        # Проверяем наличие маркеров оглавления
        for indicator in toc_indicators:
            if indicator in text_lower:
                return True
        
        # Проверяем паттерны типа "1. Заголовок", "Раздел 1" и т.д.
        toc_patterns = [
            r'^\d+\.\s',  # "1. Текст"
            r'^[ivx]+\.\s',  # "I. Текст", "II. Текст"
            r'^раздел\s+\d+',  # "Раздел 1"
            r'^часть\s+\d+',  # "Часть 1"
            r'^глава\s+\d+',  # "Глава 1"
        ]
        
        first_line = text_lower.split('\n')[0] if '\n' in text_lower else text_lower
        for pattern in toc_patterns:
            if re.search(pattern, first_line):
                return True
        
        return False
    
    def _extract_news_preview(self, text: str, preview_length: int = 300) -> str:
        lines = text.split('\n')
        news_lines = []
        
        # Пропускаем оглавление и находим начало новости
        skip_toc = True
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if skip_toc:
                if self._is_table_of_contents(line):
                    continue
                # Если нашли строку, которая не является оглавлением, начинаем собирать новость
                if len(line) > 50 and not self._is_table_of_contents(line):
                    skip_toc = False
                    news_lines.append(line)
            else:
                news_lines.append(line)
        
        # Если все строки были оглавлением, используем оригинальный текст
        if not news_lines:
            news_lines = [line.strip() for line in lines if line.strip()]
        
        # Формируем превью
        preview_text = ' '.join(news_lines)
        
        # Обрезаем до нужной длины, но не обрезаем середину слова
        if len(preview_text) > preview_length:
            preview_text = preview_text[:preview_length]
            last_space = preview_text.rfind(' ')
            if last_space > preview_length * 0.7:  # Обрезаем только если есть подходящее место
                preview_text = preview_text[:last_space]
            preview_text += '...'
        
        return preview_text
    
    def get_full_article_text(self, url: str, preserve_formatting: bool = True) -> str:
        soup = self._make_request(url)
        if not soup:
            return ''
        
        content_selectors = [
            'div.article__body',
            'div.article__text',
            'article',
            '.content',
            '.post-content',
            '[class*="article"]',
            '[class*="content"]'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Удаление ненужных элементов
                unwanted_selectors = [
                    'script', 'style', '.ad', '.banner', '.social', '.share',
                    '.article__info', '.article__meta', '.article__tags',
                    '.recommended', '.related', '.comments', '.advertisement'
                ]
                
                for unwanted in unwanted_selectors:
                    for elem in content_div.select(unwanted):
                        elem.decompose()
                
                if preserve_formatting:
                    # Сохранение форматирования с переносами строк
                    return self._extract_formatted_text(content_div)
                else:
                    # Старый метод (простой текст)
                    text = content_div.get_text().strip()
                    if len(text) > 100:
                        return text
        
        return ''
    
    def get_article_preview(self, url: str, preview_length: int = 300) -> str:
        full_text = self.get_full_article_text(url, preserve_formatting=True)
        if not full_text:
            return ''
        
        return self._extract_news_preview(full_text, preview_length)
    
    def _extract_formatted_text(self, content_div) -> str:
        # Временная копия для работы
        temp_div = BeautifulSoup(content_div.prettify(), 'lxml')
        
        # Обработка заголовков - добавляем переносы строк
        for tag in temp_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            tag.insert_after('\n\n')
            tag.insert_before('\n\n')
        
        # Обработка параграфов - добавляем переносы строк
        for tag in temp_div.find_all('p'):
            tag.insert_after('\n\n')
        
        # Обработка списков
        for tag in temp_div.find_all(['ul', 'ol']):
            tag.insert_after('\n')
            for li in tag.find_all('li'):
                li.insert_after('\n')
        
        # Обработка div'ов с контентом
        for tag in temp_div.find_all('div'):
            if tag.get_text(strip=True):
                # Проверяем, не является ли div контейнером для нескольких элементов
                child_tags = tag.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol'])
                if not child_tags:
                    tag.insert_after('\n')
        
        # Получаем текст и очищаем его
        text = temp_div.get_text()
        
        # Очистка лишних пробелов и нормализация переносов
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line:  # пропускаем пустые строки
                lines.append(line)
        
        # Объединяем с правильными переносами
        formatted_text = '\n'.join(lines)
        
        # Убираем множественные переносы (больше 2 подряд)
        formatted_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted_text)
        
        return formatted_text.strip()


parser = NewsParser()

"""
===============================
===       POLITICS       ===
===============================
"""

def parse_latest_news_politics(url=URL_POLITICS):
    return parser.parse_latest_news(url, "politics")

def get_full_article_text_politics(url):
    return parser.get_full_article_text(url)

def get_article_preview_politics(url, preview_length=300):
    return parser.get_article_preview(url, preview_length)


"""
===============================
===      SCIENCE       ===
===============================
"""


def parse_latest_news_science(url=URL_SCIENCE):
    return parser.parse_latest_news(url, "science")

def get_full_article_text_science(url):
    return parser.get_full_article_text(url)

def get_article_preview_science(url, preview_length=300):
    return parser.get_article_preview(url, preview_length)


"""
===============================
===       HEALTH      ===
===============================
"""


def parse_latest_news_health(url=URL_HEALTH):
    return parser.parse_latest_news(url, "health")

def get_full_article_text_health(url):
    return parser.get_full_article_text(url)

def get_article_preview_health(url, preview_length=300):
    return parser.get_article_preview(url, preview_length)


