import requests
from bs4 import BeautifulSoup


URL_SPORT = "https://www.sport.ru"
URL_EDUCATION = "https://k-obr.spb.ru/o-komitete/news/"
URL_IT = "https://habr.com/ru/news/top/daily/"

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

- parse_latest_news_sport(url): принимает URL sport.ru (URL_SPORT), возвращает словарь news (см. выше)
- get_full_article_text_sport(url): принимает URL полной версии новости с Sport.ru, возвращает строку с полным текстом статьи.

- parse_latest_news_education(url): принимает URL раздела новостей k-obr.spb.ru (URL_EDUCATION), возвращает словарь news (см. выше)
- get_full_article_text_education(url): принимает URL конкретной новости k-obr.spb.ru, возвращает строку с полным текстом статьи.

- parse_latest_news_it(url): принимает URL ленты статей Habr (URL_IT), возвращает словарь news (см. выше)
- get_full_article_text_it(url): принимает URL статьи Habr, возвращает строку с полным текстом статьи.
"""


"""
===============================
===          SPORT          ===
===============================
"""

def parse_main_news_sport(url):
    response = requests.get(url)
    response.encoding = 'windows-1251'
    soup = BeautifulSoup(response.text, 'lxml')

    news_dict = {'news': []}
    articles = soup.select('div.articles-item.articles-item-large')

    for article in articles:
        title_tag = article.select_one('h3 a')
        date_tag = article.select_one('span.date')
        img_tag = article.select_one('div.articles-item-image a img')
        link_tag = article.select_one('div.articles-item-image a')

        if not (title_tag and date_tag and img_tag and link_tag):
            continue

        date_time_str = date_tag.text.strip()
        if ',' in date_time_str:
            date, time = map(str.strip, date_time_str.split(',', 1))
        else:
            date, time = date_time_str, ''

        news_dict['news'].append({
            'title': title_tag.text.strip(),
            'date': date,
            'time': time,
            'image': img_tag['src'],
            'link': link_tag['href']
        })

    return news_dict

def parse_latest_news_sport(url):
    response = requests.get(url)
    response.encoding = 'windows-1251'
    soup = BeautifulSoup(response.text, 'lxml')

    news_dict = {'news': []}
    wrappers = soup.select('div.lst-itm, div.lst-itm.lst-itm-hid')

    for wrapper in wrappers:
        article = wrapper.select_one('div.articles-item.articles-item-large')
        if not article:
            continue

        title_tag = article.select_one('h3 a')
        date_tag = article.select_one('span.date')
        img_tag = article.select_one('div.articles-item-image a img')
        link_tag = article.select_one('div.articles-item-image a')

        if not (title_tag and date_tag and img_tag and link_tag):
            continue

        date_time_str = date_tag.text.strip()
        if ',' in date_time_str:
            date, time = map(str.strip, date_time_str.split(',', 1))
        else:
            date, time = date_time_str, ''

        news_dict['news'].append({
            'title': title_tag.text.strip(),
            'date': date,
            'time': time,
            'image': img_tag['src'],
            'link': link_tag['href']
        })

    return news_dict

def get_full_article_text_sport(url):
    response = requests.get(url)
    response.encoding = 'windows-1251'
    soup = BeautifulSoup(response.text, 'lxml')

    content_div = soup.find('div', class_='article-text clearfix')
    if not content_div:
        return ''

    article_text = content_div.get_text().strip()
    return article_text[39:]

"""
===============================
===        EDUCATION        ===
===============================
"""

RU_MONTHS = {
    'января': '01',
    'февраля': '02',
    'марта': '03',
    'апреля': '04',
    'мая': '05',
    'июня': '06',
    'июля': '07',
    'августа': '08',
    'сентября': '09',
    'октября': '10',
    'ноября': '11',
    'декабря': '12',
}

def parse_latest_news_education(url_base):
    response = requests.get(url_base)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')

    news_dict = {'news': []}
    items = soup.select('div.news__item.card')

    for item in items:
        title_tag = item.select_one('h2.news__title a')
        link_tag = item.select_one('a.news__link')
        date_parts = item.select('div.news__date .d-inline')

        if not (title_tag and link_tag and date_parts and len(date_parts) >= 3):
            continue

        day = date_parts[0].get_text(strip=True)
        month_ru = date_parts[1].get_text(strip=True).lower()
        year = date_parts[2].get_text(strip=True)
        month = RU_MONTHS.get(month_ru, '01')
        date = f'{day.zfill(2)}.{month}.{year}'

        style = link_tag.get('style', '')
        image = ''
        if "background-image" in style:
            start = style.find("url(")
            end = style.find(")", start + 4)
            if start != -1 and end != -1:
                image = style[start + 4:end].strip().strip('"').strip("'")

        news_dict['news'].append({
            'title': title_tag.get_text(strip=True),
            'date': date,
            'time': '',
            'image': image,
            'link': title_tag['href']
        })

    return news_dict

def get_full_article_text_education(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')

    container = soup.find('article', class_='article mb-32')
    if not container:
        return ''

    text = container.get_text().strip()
    return text

"""
===============================
===            IT           ===
===============================
"""

def parse_latest_news_it(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')

    news = {'news': []}
    items = soup.select('article.tm-articles-list__item, article.tm-articles-listitem')

    for item in items:
        title_tag = item.select_one('h2.tm-title a.tm-title__link, h2.tm-title a.tm-titlelink')
        time_tag = item.select_one('a.tm-article-datetime-published time, time.tm-article-datetime-published')
        img_tag = item.select_one('img.tm-article-snippet__lead-image, img.tm-article-snippetlead-image')
        if not title_tag:
            # Альтернативная разметка карточки
            title_tag = item.select_one('a[data-test-id="article-snippet-title-link"]')
        if not (title_tag and time_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = title_tag.get('href', '')
        if link and link.startswith('/'):
            # Habr: относительная ссылка
            link = 'https://habr.com' + link

        # Время берём из атрибута title или datetime
        date = ''
        time = ''
        dt_title = time_tag.get('title')
        dt_attr = time_tag.get('datetime')
        dt_text = (dt_title or dt_attr or '').strip()
        if dt_text:
            # Форматы типа "2025-10-01, 07:13" или ISO
            if ',' in dt_text:
                d, t = dt_text.split(',', 1)
                date, time = d.strip(), t.strip()
            elif 'T' in dt_text and 'Z' in dt_text:
                # ISO: 2025-10-01T07:13:26.000Z
                iso = dt_text.replace('Z', '')
                parts = iso.split('T', 1)
                if len(parts) == 2:
                    date, time = parts[0], parts[1][:5]
            else:
                date = dt_text

        image = ''
        if img_tag and img_tag.get('src'):
            image = img_tag['src']
            if image.startswith('//'):
                image = 'https:' + image

        news['news'].append({
            'title': title,
            'date': date,
            'time': time,
            'image': image,
            'link': link
        })

    return news

def get_full_article_text_it(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')

    container = soup.select_one('#post-content-body .article-formatted-body, .article-formatted-body')
    if not container:
        container = soup.select_one('div.article-body, article.tm-article-presenter__content')

    if not container:
        return ''

    text = container.get_text().strip()
    return text


# arr = parse_latest_news_it(URL_IT)
# print(arr)
# print(get_full_article_text_it(arr["news"][0]["link"]))
