import requests
from bs4 import BeautifulSoup
import os

URL = 'https://ria.ru/'

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 YaBrowser/21.11.1.932 Yowser/2.5 Safari/537.36',
    'accept': '*/*'
}

def get_html(url):
    return requests.get(url, headers=HEADERS)

def get_latest_article(url):
    html = get_html(url)
    if html.status_code == 200:
        soup = BeautifulSoup(html.text, 'html.parser')
        article = soup.find('div', class_='list-item') or soup.find('div', class_='cell-list__item')
        if article:
            data = article.find('a')
            title = data.get_text(strip=True)
            link = data.get('href')
            if not link.startswith('http'):
                link = 'https://ria.ru' + link
            date = article.find('time')
            date_text = date.get('datetime') if date else 'NO DATE'
            text, image_path = get_text_and_image(link)
            return {'title': title, 'date': date_text, 'text': text, 'media': image_path, 'url': link}
    return None

def get_text_and_image(link):
    html = get_html(link)
    soup = BeautifulSoup(html.text, 'html.parser')
    content = soup.find_all('div', class_="article__text")
    text = 'NO TEXT'
    image_path = None

    if content:
        paragraphs = []
        for div in content:
            paragraphs.append(div.get_text(strip=True))
        

        text = ' '.join(paragraph for paragraph in paragraphs)

    image_div = soup.find('div', class_='photoview__open')
    if image_div:
        img_tag = image_div.find('img')
        if img_tag and img_tag.get('src'):
            image_url = img_tag['src']
            image_path = save_image(image_url)

    return text, image_path

def save_image(image_url):
    response = requests.get(image_url, headers=HEADERS)
    if response.status_code == 200:
        if not os.path.exists('media'):
            os.makedirs('media')
        image_path = os.path.join('media', 'ria.png')
        with open(image_path, 'wb') as file:
            file.write(response.content)
        return image_path
    return 'NO IMAGE'



