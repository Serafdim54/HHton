import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
import feedparser
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import json
from bs4 import XMLParsedAsHTMLWarning
import warnings

# Подавляем предупреждение о парсинге XML как HTML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# URL для РИА Новостей
URL_POLITICS = "https://ria.ru/politics/"
URL_SCIENCE = "https://ria.ru/science/"
URL_HEALTH = "https://ria.ru/health/"

class AdvancedNewsParser:
    """
    Усовершенствованный парсер новостей с оптимизированными источниками
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_session()
        self.selenium_driver = None
        
    def setup_session(self):
        """Настройка сессии с рандомными User-Agent"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_selenium_driver(self):
        """Инициализация Selenium драйвера"""
        if not self.selenium_driver:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={self.ua.random}")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.selenium_driver = webdriver.Chrome(options=chrome_options)
            self.selenium_driver.set_page_load_timeout(30)
        
        return self.selenium_driver
    
    def close_selenium(self):
        """Закрытие Selenium драйвера"""
        if self.selenium_driver:
            self.selenium_driver.quit()
            self.selenium_driver = None
    
    def _make_request(self, url: str, use_selenium: bool = False) -> Optional[BeautifulSoup]:
        """
        Улучшенный запрос с поддержкой Selenium для динамического контента
        """
        try:
            if use_selenium:
                print(f"🔄 Используем Selenium для: {url}")
                driver = self.get_selenium_driver()
                driver.get(url)
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                time.sleep(3)
                html = driver.page_source
                return BeautifulSoup(html, 'html.parser')
            else:
                print(f"🌐 Стандартный запрос: {url}")
                time.sleep(random.uniform(1, 3))
                self.session.headers['User-Agent'] = self.ua.random
                
                response = self.session.get(url, timeout=15)
                response.encoding = 'utf-8'
                print(f"✅ Статус: {response.status_code}")
                
                # Определяем, XML это или HTML
                if any(xml_indicator in url.lower() for xml_indicator in ['rss', 'xml', 'feed', 'export']):
                    print("📄 Используем XML парсер для RSS")
                    return BeautifulSoup(response.content, 'xml')
                else:
                    return BeautifulSoup(response.text, 'html.parser')
                    
        except Exception as e:
            print(f"❌ Ошибка запроса {url}: {e}")
            return None

    def parse_with_fallback_strategy(self, url: str, source_type: str) -> List[Dict]:
        """
        Многоуровневая стратегия парсинга с приоритетом для РИА Новостей
        """
        print(f"🎯 Запускаем каскадный парсинг для: {url}")
        
        # Для РИА Новостей используем специализированный парсер
        if 'ria.ru' in url and not ('rss' in url or 'export' in url):
            print("🔍 Используем специализированный парсер для РИА Новостей")
            return self._parse_ria_news_advanced(url, source_type)
        
        # Приоритет 1: Парсинг RSS
        if any(rss_indicator in url.lower() for rss_indicator in ['rss', 'export', 'feed']):
            news = self._parse_rss_feed_advanced(url)
            if news:
                print(f"✅ RSS успешно: {len(news)} новостей")
                return news
        
        # Приоритет 2: Статический HTML парсинг
        soup_static = self._make_request(url, use_selenium=False)
        if soup_static:
            news = self._extract_news_advanced(soup_static, url, source_type)
            if news:
                print(f"✅ Статический парсинг успешен: {len(news)} новостей")
                return news
        
        # Приоритет 3: Динамический парсинг через Selenium
        print("🔄 Переходим к динамическому парсингу...")
        soup_dynamic = self._make_request(url, use_selenium=True)
        if soup_dynamic:
            news = self._extract_news_advanced(soup_dynamic, url, source_type)
            if news:
                print(f"✅ Динамический парсинг успешен: {len(news)} новостей")
                return news
        
        print("❌ Все методы парсинга не дали результатов")
        return []

    # ===== СПЕЦИАЛИЗИРОВАННЫЙ ПАРСЕР ДЛЯ РИА НОВОСТЕЙ =====
    
    def _parse_ria_news_advanced(self, url: str, category: str) -> List[Dict]:
        """Специализированный парсер для РИА Новостей"""
        print(f"🔍 Парсим РИА Новости: {url}")
        soup = self._make_request(url, use_selenium=False)
        if not soup:
            return []
        
        news_items = []
        seen_links = set()
        
        # Селекторы для элементов новостей РИА
        item_selectors = ['.cell-list__item', '.list-item', '.news-item', '[data-type="news"]']
        items = []
        
        for selector in item_selectors:
            found_items = soup.select(selector)
            if found_items:
                items.extend(found_items)
        
        for item in items:
            try:
                # Извлечение заголовка
                title = self._extract_ria_title(item)
                if not title:
                    continue
                
                # Извлечение и проверка ссылки
                link = self._extract_ria_link(item)
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                
                # Парсинг даты и времени
                date, time = self._parse_ria_date_time(item)
                
                # Извлечение изображения
                image = self._extract_ria_image_url(item)
                
                news_item = {
                    'title': title,
                    'date': date,
                    'time': time,
                    'image': image,
                    'link': link,
                    'source': 'RIA.ru'
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                print(f"⚠️ Ошибка обработки элемента РИА: {e}")
                continue
        
        print(f"✅ РИА Новости: собрано {len(news_items)} новостей")
        return news_items
    
    def _extract_ria_title(self, item) -> Optional[str]:
        """Извлечение заголовка для РИА"""
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
    
    def _extract_ria_link(self, item) -> Optional[str]:
        """Извлечение ссылки для РИА"""
        link = item.get('href', '')
        
        if not link:
            link_tag = item.select_one('a[href]')
            if link_tag:
                link = link_tag.get('href', '')
        
        if not link:
            return None
        
        # Нормализация URL для РИА
        if link.startswith('/'):
            link = 'https://ria.ru' + link
        elif link.startswith('//'):
            link = 'https:' + link
        
        return link
    
    def _parse_ria_date_time(self, item) -> tuple[str, str]:
        """Парсинг даты и времени для РИА"""
        date, time = '', ''
        
        date_selectors = ['.cell-info__date', '[data-type="date"]', '.list-item__info']
        date_element = None
        
        for selector in date_selectors:
            date_element = item.select_one(selector)
            if date_element:
                break
        
        if not date_element:
            return self.get_today_date(), ''
        
        date_text = date_element.get_text().strip()
        
        if ',' in date_text:
            parts = date_text.split(',', 1)
            if len(parts) == 2:
                date_part, time_part = parts
                date = date_part.strip()
                time = self._extract_time_from_text(time_part.strip())
        else:
            if ':' in date_text:
                time = self._extract_time_from_text(date_text)
                date = 'Сегодня' if time else ''
            else:
                date = date_text
        
        if time and not date:
            date = 'Сегодня'
            
        return date or self.get_today_date(), time
    
    def _extract_ria_image_url(self, item) -> str:
        """Извлечение изображения для РИА"""
        image = ''
        
        img_container = item.select_one('.cell-list__item-img')
        if img_container:
            img_tag = img_container.select_one('img')
            if img_tag:
                image = img_tag.get('src') or img_tag.get('data-src') or ''
        
        if not image:
            img_tag = item.select_one('img')
            if img_tag:
                image = img_tag.get('src') or img_tag.get('data-src') or ''
        
        if not image:
            div_with_bg = item.select_one('[style*="background-image"]')
            if div_with_bg and div_with_bg.get('style'):
                style = div_with_bg['style']
                if 'url(' in style:
                    start = style.find('url(')
                    end = style.find(')', start)
                    if start != -1 and end != -1:
                        image = style[start+4:end].strip('"\'')
        
        if image:
            if image.startswith('//'):
                image = 'https:' + image
            elif image.startswith('/'):
                image = 'https://ria.ru' + image
        
        return image
    
    def _extract_time_from_text(self, time_text: str) -> str:
        """Извлекает время из текста в формате ЧЧ:ММ"""
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

    # ===== УНИВЕРСАЛЬНЫЙ ПАРСЕР ДЛЯ ДРУГИХ ИСТОЧНИКОВ =====
    
    def _parse_rss_feed_advanced(self, rss_url: str) -> List[Dict]:
        """Улучшенный парсинг RSS с обработкой разных форматов"""
        print(f"📡 Парсим RSS: {rss_url}")
        news_items = []
        
        try:
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                print("⚠️ RSS feed пуст или недоступен")
                return []
            
            print(f"📊 Найдено RSS записей: {len(feed.entries)}")
            
            for i, entry in enumerate(feed.entries[:20]):
                try:
                    pub_date = self._parse_rss_date(entry)
                    image_url = self._extract_rss_image(entry)
                    
                    news_item = {
                        'title': entry.title,
                        'date': pub_date,
                        'time': self._extract_time_from_rss(entry),
                        'image': image_url,
                        'link': entry.link,
                        'source': self._extract_source_name(rss_url),
                        'description': getattr(entry, 'description', '')[:200] + '...' if hasattr(entry, 'description') else ''
                    }
                    news_items.append(news_item)
                    
                    if i < 3:
                        print(f"   ✅ {i+1}. {entry.title[:60]}...")
                        
                except Exception as e:
                    print(f"   ⚠️ Ошибка обработки RSS элемента: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Критическая ошибка RSS парсинга: {e}")
        
        return news_items
    
    def _parse_rss_date(self, entry) -> str:
        """Парсинг даты из RSS в унифицированном формате"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6])
                return dt.strftime("%d.%m.%Y")
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                dt = datetime(*entry.updated_parsed[:6])
                return dt.strftime("%d.%m.%Y")
        except:
            pass
        
        return self.get_today_date()
    
    def _extract_rss_image(self, entry) -> str:
        """Извлечение изображения из RSS записи"""
        image_url = ''
        
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('type', '').startswith('image/'):
                    image_url = link.href
                    break
                elif link.get('rel', '') == 'enclosure':
                    image_url = link.href
                    break
        
        if not image_url and hasattr(entry, 'content'):
            for content in entry.content:
                if content.get('type', '').startswith('image/'):
                    image_url = content.get('url', '')
                    break
        
        if not image_url and hasattr(entry, 'media_thumbnail'):
            image_url = entry.media_thumbnail[0]['url']
        
        return image_url
    
    def _extract_news_advanced(self, soup: BeautifulSoup, url: str, source_type: str) -> List[Dict]:
        """
        Улучшенный парсинг HTML для ТАСС, Интерфакс и Доктор Питер
        """
        news_items = []
        source_name = self._extract_source_name(url)
        
        print(f"🔍 Извлекаем новости для {source_name}")
        
        # Специфичные стратегии для каждого источника
        extraction_methods = {
            'tass.ru': self._extract_tass_news,
            'interfax.ru': self._extract_interfax_news,
            'doctorpiter.ru': self._extract_doctorpiter_news
        }
        
        method = extraction_methods.get(source_name, self._extract_generic_news)
        news_items = method(soup, url)
        
        return news_items
    
    def _extract_tass_news(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Специфичный парсинг для TASS"""
        news_items = []
        
        selectors = [
            '.news-line__item',
            '.news-list__item', 
            '.content-big-newslist__item',
            '.b-material-list__item',
            'article'
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                print(f"✅ TASS: найдены элементы по селектору '{selector}': {len(articles)}")
                
                for article in articles[:20]:
                    try:
                        title_elem = article.select_one('.news-line__title, .news-list__title, .b-material-list__title, h2, h3, h4, a')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        if len(title) < 5:
                            continue
                        
                        link_elem = article.select_one('a[href]')
                        if not link_elem:
                            continue
                            
                        link = self._normalize_url(link_elem.get('href'), 'tass.ru')
                        if not link:
                            continue
                        
                        image_url = self._extract_tass_image(article)
                        
                        news_item = {
                            'title': title[:100] + "..." if len(title) > 100 else title,
                            'date': self.get_today_date(),
                            'time': '',
                            'image': image_url,
                            'link': link,
                            'source': 'TASS'
                        }
                        
                        news_items.append(news_item)
                        
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки элемента TASS: {e}")
                        continue
                
                if news_items:
                    break
        
        return news_items
    
    def _extract_interfax_news(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Парсинг для Интерфакс - надежный источник с хорошей структурой"""
        news_items = []
        
        # Селекторы для Интерфакс
        selectors = [
            '.newsPage__list .timeline__item',
            '.newsList .newsItem',
            '.main-newslist .news-item',
            '.news-feed-list .news-feed-item',
            'article',
            '.news'
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                print(f"✅ Интерфакс: найдены элементы по селектору '{selector}': {len(articles)}")
                
                for article in articles[:20]:
                    try:
                        # Селекторы заголовков для Интерфакс
                        title_elem = article.select_one(
                            '.timeline__item-title, .newsItem__title, '
                            '.news-item__title, h3, h4, .title, a'
                        )
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        if len(title) < 10 or len(title) > 300:
                            continue
                        
                        link_elem = article.select_one('a[href]')
                        if not link_elem:
                            continue
                            
                        link = self._normalize_url(link_elem.get('href'), 'interfax.ru')
                        if not link or 'interfax.ru' not in link:
                            continue
                        
                        image_url = self._extract_interfax_image(article)
                        
                        news_item = {
                            'title': title[:100] + "..." if len(title) > 100 else title,
                            'date': self.get_today_date(),
                            'time': '',
                            'image': image_url,
                            'link': link,
                            'source': 'Интерфакс'
                        }
                        
                        news_items.append(news_item)
                        
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки элемента Интерфакс: {e}")
                        continue
                
                if len(news_items) >= 5:
                    break
        
        return news_items
    
    def _extract_doctorpiter_news(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Парсинг для Доктор Питер - надежный медицинский портал"""
        news_items = []
        
        # Селекторы для Доктор Питер
        selectors = [
            '.news-item',
            '.article-preview',
            '.news-list-item',
            '.item-news',
            'article.news',
            '.b-news-item'
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                print(f"✅ Доктор Питер: найдены элементы по селектору '{selector}': {len(articles)}")
                
                for article in articles[:20]:
                    try:
                        # Селекторы заголовков для Доктор Питер
                        title_elem = article.select_one(
                            '.news-item__title, .article-preview__title, '
                            '.news-list-item__title, .item-news__title, '
                            'h2, h3, h4, .title, a'
                        )
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        if len(title) < 10 or len(title) > 300:
                            continue
                        
                        link_elem = article.select_one('a[href]')
                        if not link_elem:
                            continue
                            
                        link = self._normalize_url(link_elem.get('href'), 'doctorpiter.ru')
                        if not link or 'doctorpiter.ru' not in link:
                            continue
                        
                        image_url = self._extract_doctorpiter_image(article)
                        
                        news_item = {
                            'title': title[:100] + "..." if len(title) > 100 else title,
                            'date': self.get_today_date(),
                            'time': '',
                            'image': image_url,
                            'link': link,
                            'source': 'Доктор Питер'
                        }
                        
                        news_items.append(news_item)
                        
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки элемента Доктор Питер: {e}")
                        continue
                
                if len(news_items) >= 5:
                    break
        
        return news_items
    
    def _extract_interfax_image(self, article) -> str:
        """Извлечение изображения для Интерфакс"""
        img_selectors = [
            'img',
            '.timeline__item-img img',
            '.newsItem__image img',
            '.news-item__image img',
            '[data-src]'
        ]
        
        for selector in img_selectors:
            img_elem = article.select_one(selector)
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src:
                    return self._normalize_url(src, 'interfax.ru')
        return ''
    
    def _extract_doctorpiter_image(self, article) -> str:
        """Извлечение изображения для Доктор Питер"""
        img_selectors = [
            'img',
            '.news-item__image img',
            '.article-preview__image img',
            '.news-list-item__image img',
            '.item-news__image img',
            '[data-src]'
        ]
        
        for selector in img_selectors:
            img_elem = article.select_one(selector)
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src:
                    return self._normalize_url(src, 'doctorpiter.ru')
        return ''
    
    def _extract_tass_image(self, article) -> str:
        """Извлечение изображения для TASS"""
        img_selectors = [
            'img',
            '.news-line__image img',
            '.b-material-list__image img',
            '[data-src]'
        ]
        
        for selector in img_selectors:
            img_elem = article.select_one(selector)
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src:
                    return self._normalize_url(src, 'tass.ru')
        return ''
    
    def _extract_generic_news(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Универсальный парсинг для неизвестных источников"""
        news_items = []
        
        universal_selectors = [
            'article',
            '.news-item',
            '.item',
            '.card',
            '.post',
            '[class*="news"]',
            '[class*="article"]',
            '.news'
        ]
        
        for selector in universal_selectors:
            articles = soup.select(selector)
            if articles:
                print(f"🌐 Универсальный парсинг: найдено {len(articles)} элементов по селектору '{selector}'")
                
                for article in articles[:15]:
                    try:
                        title_elem = article.select_one('h1, h2, h3, h4, h5, .title, .heading, [class*="title"], [class*="heading"]')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        if len(title) < 5 or len(title) > 500:
                            continue
                        
                        link_elem = article.select_one('a[href]')
                        if not link_elem:
                            continue
                            
                        link = link_elem.get('href')
                        if not link or link.startswith('javascript:'):
                            continue
                            
                        if link.startswith('/'):
                            base_domain = re.findall(r'https?://[^/]+', url)[0]
                            link = base_domain + link
                        elif not link.startswith('http'):
                            link = url + link
                        
                        img_elem = article.select_one('img')
                        image_url = img_elem.get('src') if img_elem else ''
                        
                        news_item = {
                            'title': title[:100] + "..." if len(title) > 100 else title,
                            'date': self.get_today_date(),
                            'time': '',
                            'image': image_url,
                            'link': link,
                            'source': self._extract_source_name(url)
                        }
                        
                        news_items.append(news_item)
                        
                    except Exception as e:
                        continue
                
                if news_items:
                    break
        
        return news_items
    
    def _normalize_url(self, url: str, source_name: str) -> str:
        """Нормализация URL в зависимости от источника"""
        if not url or url.startswith('javascript:'):
            return ''
        
        url = url.strip()
        
        source_domains = {
            'ria.ru': 'https://ria.ru',
            'tass.ru': 'https://tass.ru', 
            'interfax.ru': 'https://www.interfax.ru',
            'doctorpiter.ru': 'https://doctorpiter.ru'
        }
        
        base_domain = source_domains.get(source_name, '')
        
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return base_domain + url
        elif not url.startswith('http'):
            return base_domain + '/' + url
        
        return url
    
    def _extract_time_from_rss(self, entry) -> str:
        """Извлечение времени из RSS"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6])
                return dt.strftime("%H:%M")
        except:
            pass
        return ''
    
    def _extract_source_name(self, url: str) -> str:
        """Извлечение имени источника из URL"""
        if 'ria.ru' in url:
            return 'RIA.ru'
        elif 'tass.ru' in url:
            return 'TASS'
        elif 'interfax.ru' in url:
            return 'Интерфакс'
        elif 'doctorpiter.ru' in url:
            return 'Доктор Питер'
        else:
            domain = re.findall(r'https?://([^/]+)', url)
            return domain[0] if domain else 'Unknown'
    
    def get_today_date(self) -> str:
        return datetime.now().strftime("%d.%m.%Y")
    
    # ===== ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ПОЛНОГО ТЕКСТА И ПРЕВЬЮ =====
    
    def _is_table_of_contents(self, text: str) -> bool:
        """Определяет, является ли текст оглавлением"""
        toc_indicators = [
            'оглавление', 'содержание', 'содержит', 'в статье', 
            'читайте также', 'table of contents', 'toc',
            'введение', 'заголовок', 'раздел', 'часть', 'глава'
        ]
        
        text_lower = text.lower().strip()
        if len(text_lower) < 50:
            return False
            
        for indicator in toc_indicators:
            if indicator in text_lower:
                return True
        
        toc_patterns = [
            r'^\d+\.\s',
            r'^[ivx]+\.\s',
            r'^раздел\s+\d+',
            r'^часть\s+\d+',
            r'^глава\s+\d+',
        ]
        
        first_line = text_lower.split('\n')[0] if '\n' in text_lower else text_lower
        for pattern in toc_patterns:
            if re.search(pattern, first_line):
                return True
        
        return False
    
    def _extract_news_preview(self, text: str, preview_length: int = 300) -> str:
        """Извлекает превью новости, пропуская оглавление"""
        lines = text.split('\n')
        news_lines = []
        
        skip_toc = True
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if skip_toc:
                if self._is_table_of_contents(line):
                    continue
                if len(line) > 50 and not self._is_table_of_contents(line):
                    skip_toc = False
                    news_lines.append(line)
            else:
                news_lines.append(line)
        
        if not news_lines:
            news_lines = [line.strip() for line in lines if line.strip()]
        
        preview_text = ' '.join(news_lines)
        
        if len(preview_text) > preview_length:
            preview_text = preview_text[:preview_length]
            last_space = preview_text.rfind(' ')
            if last_space > preview_length * 0.7:
                preview_text = preview_text[:last_space]
            preview_text += '...'
        
        return preview_text
    
    def get_full_article_text(self, url: str, preserve_formatting: bool = True) -> str:
        """Получает полный текст статьи с сохранением форматирования"""
        print(f"📖 Получаем полный текст: {url}")
        
        # Для РИА Новостей используем специализированный метод
        if 'ria.ru' in url:
            return self._get_ria_full_article_text(url, preserve_formatting)
        
        # Для других источников используем общий метод
        soup = self._make_request(url, use_selenium=False)
        if not soup:
            soup = self._make_request(url, use_selenium=True)
        
        if not soup:
            return ''
        
        content_selectors = [
            'div.article__body',
            'div.article-text',
            'div.b-text',
            'article',
            'div.content',
            'div.post-content',
            '[class*="article"]',
            '[class*="content"]'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                unwanted_selectors = [
                    'script', 'style', '.ad', '.banner', '.social', '.share',
                    '.article__info', '.article__meta', '.article__tags',
                    '.recommended', '.related', '.comments', '.advertisement'
                ]
                
                for unwanted in unwanted_selectors:
                    for elem in content_div.select(unwanted):
                        elem.decompose()
                
                if preserve_formatting:
                    return self._extract_formatted_text(content_div)
                else:
                    text = content_div.get_text().strip()
                    if len(text) > 200:
                        return self._clean_text(text)
        
        return ''
    
    def _get_ria_full_article_text(self, url: str, preserve_formatting: bool = True) -> str:
        """Специализированный метод для получения полного текста РИА"""
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
                unwanted_selectors = [
                    'script', 'style', '.ad', '.banner', '.social', '.share',
                    '.article__info', '.article__meta', '.article__tags',
                    '.recommended', '.related', '.comments', '.advertisement'
                ]
                
                for unwanted in unwanted_selectors:
                    for elem in content_div.select(unwanted):
                        elem.decompose()
                
                if preserve_formatting:
                    return self._extract_formatted_text(content_div)
                else:
                    text = content_div.get_text().strip()
                    if len(text) > 100:
                        return text
        
        return ''
    
    def get_article_preview(self, url: str, preview_length: int = 300) -> str:
        """Получает превью статьи без оглавления"""
        full_text = self.get_full_article_text(url, preserve_formatting=True)
        if not full_text:
            return ''
        
        return self._extract_news_preview(full_text, preview_length)
    
    def _extract_formatted_text(self, content_div) -> str:
        """Извлекает текст с сохранением форматирования и переносов строк"""
        temp_div = BeautifulSoup(content_div.prettify(), 'html.parser')
        
        for tag in temp_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            tag.insert_after('\n\n')
            tag.insert_before('\n\n')
        
        for tag in temp_div.find_all('p'):
            tag.insert_after('\n\n')
        
        for tag in temp_div.find_all(['ul', 'ol']):
            tag.insert_after('\n')
            for li in tag.find_all('li'):
                li.insert_after('\n')
        
        for tag in temp_div.find_all('div'):
            if tag.get_text(strip=True):
                child_tags = tag.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol'])
                if not child_tags:
                    tag.insert_after('\n')
        
        text = temp_div.get_text()
        
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                lines.append(line)
        
        formatted_text = '\n'.join(lines)
        formatted_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted_text)
        
        return formatted_text.strip()
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних пробелов"""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines)
    
    # ===== ОСНОВНЫЕ ФУНКЦИИ ПАРСИНГА ПО КАТЕГОРИЯМ =====
    
    def parse_category_news(self, category: str) -> Dict[str, List]:
        """
        Основная функция парсинга с оптимизированными источниками
        """
        print(f"\n{'='*60}")
        print(f"🚀 ЗАПУСК ПАРСИНГА: {category.upper()}")
        print(f"{'='*60}")
        
        # Оптимизированная конфигурация источников
        sources_config = {
            'politics': [
                # РИА Новости (специализированный парсер)
                ('https://ria.ru/politics/', 'HTML'),
                
                # ТАСС (RSS + HTML) - надежный источник для политики
                ('https://tass.ru/rss/v2.xml', 'RSS'),
                ('https://tass.ru/politika', 'HTML'),
                
                # Интерфакс (RSS + HTML) - отличный источник для политики
                ('https://www.interfax.ru/rss.asp', 'RSS'),
                ('https://www.interfax.ru/politics/', 'HTML')
                
                # Lenta.ru удалена из политики из-за проблем с парсингом
            ],
            'science': [
                # РИА Новости
                ('https://ria.ru/science/', 'HTML'),
                
                # ТАСС для науки
                ('https://tass.ru/rss/v2.xml', 'RSS'),
                ('https://tass.ru/nauka', 'HTML'),
                
                # Интерфакс для науки
                ('https://www.interfax.ru/rss.asp', 'RSS'),
                ('https://www.interfax.ru/science/', 'HTML')
            ],
            'health': [
                # РИА Новости
                ('https://ria.ru/health/', 'HTML'),
                
                # Доктор Питер (RSS + HTML) - специализированный медицинский источник
                ('https://doctorpiter.ru/rss/', 'RSS'),
                ('https://doctorpiter.ru/news/', 'HTML'),
                
                # Интерфакс для здоровья
                ('https://www.interfax.ru/rss.asp', 'RSS'),
                ('https://www.interfax.ru/health/', 'HTML')
                
                # Lenta.ru заменена на Доктор Питер
            ]
        }
        
        if category not in sources_config:
            return {'news': [], 'statistics': {'error': 'Unknown category'}}
        
        all_news = []
        source_stats = {}
        successful_sources = []
        
        # Парсим все источники с улучшенной стратегией
        for url, parser_type in sources_config[category]:
            source_name = self._extract_source_name(url)
            source_key = f"{source_name}_{parser_type}"
            
            print(f"\n🔍 Обрабатываем: {source_key}")
            print(f"   URL: {url}")
            
            try:
                news_from_source = self.parse_with_fallback_strategy(url, category)
                count = len(news_from_source)
                source_stats[source_key] = count
                
                if count > 0:
                    successful_sources.append(source_key)
                    all_news.extend(news_from_source)
                    print(f"✅ УСПЕХ: {count} новостей")
                else:
                    print(f"❌ НОВОСТЕЙ НЕ НАЙДЕНО")
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
                source_stats[source_key] = 0
        
        self.close_selenium()
        
        # Удаляем дубликаты
        unique_news = []
        seen_titles = set()
        seen_links = set()
        
        for news in all_news:
            title_key = news['title'].strip().lower()[:50]
            link_key = news['link']
            
            if title_key not in seen_titles and link_key not in seen_links:
                seen_titles.add(title_key)
                seen_links.add(link_key)
                unique_news.append(news)
        
        # Статистика
        print(f"\n{'='*60}")
        print(f"📊 ИТОГИ КАТЕГОРИИ: {category.upper()}")
        print(f"{'='*60}")
        
        total_collected = sum(source_stats.values())
        total_unique = len(unique_news)
        
        print(f"📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего собрано: {total_collected}")
        print(f"   Уникальных новостей: {total_unique}")
        print(f"   Работающих источников: {len(successful_sources)}/{len(sources_config[category])}")
        
        print(f"\n📋 ДЕТАЛЬНАЯ СТАТИСТИКА ПО ИСТОЧНИКАМ:")
        for source, count in source_stats.items():
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {source}: {count} новостей")
        
        return {
            'news': unique_news[:25],
            'statistics': {
                'total_collected': total_collected,
                'total_unique': total_unique,
                'successful_sources': len(successful_sources),
                'total_sources': len(sources_config[category]),
                'sources': source_stats
            }
        }


# Создаем экземпляр парсера
advanced_parser = AdvancedNewsParser()

# ===== ФАБРИЧНЫЕ ФУНКЦИИ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ =====

"""
===============================
===       POLITICS       ===
===============================
"""

def parse_latest_news_politics():
    return advanced_parser.parse_category_news('politics')

def get_full_article_text_politics(url):
    return advanced_parser.get_full_article_text(url)

def get_article_preview_politics(url, preview_length=300):
    return advanced_parser.get_article_preview(url, preview_length)


"""
===============================
===      SCIENCE       ===
===============================
"""

def parse_latest_news_science():
    return advanced_parser.parse_category_news('science')

def get_full_article_text_science(url):
    return advanced_parser.get_full_article_text(url)

def get_article_preview_science(url, preview_length=300):
    return advanced_parser.get_article_preview(url, preview_length)


"""
===============================
===       HEALTH      ===
===============================
"""

def parse_latest_news_health():
    return advanced_parser.parse_category_news('health')

def get_full_article_text_health(url):
    return advanced_parser.get_full_article_text(url)

def get_article_preview_health(url, preview_length=300):
    return advanced_parser.get_article_preview(url, preview_length)
