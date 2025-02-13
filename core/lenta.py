import requests
import datetime
import user_agent
from bs4 import BeautifulSoup
import os
from PIL import Image
from io import BytesIO

class Lenta_Parser:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.host = "https://lenta.ru"
        self.media_dir = "media"
        os.makedirs(self.media_dir, exist_ok=True)

    def get_request(self, url: str) -> str:
        self.session.headers.update(user_agent.generate_navigator())
        return self.session.get(url).text

    def download_media(self, url: str) -> str:
        try:
            response = self.session.get(url, stream=True)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                filename = os.path.join(self.media_dir, "image.png")
                image.save(filename, format="PNG")
                return filename
            return ""
        except Exception:
            return ""

    def parse_latest_post(self) -> None:
        try:
            soup = BeautifulSoup(self.get_request(self.host), "html.parser")
            latest_news = soup.find("a", class_="card-mini")

            if latest_news:
                news_url = self.host + latest_news.get("href")
                news_soup = BeautifulSoup(self.get_request(news_url), "html.parser")

                title = news_soup.find("h1").get_text(strip=True)
                content = news_soup.find("div", class_="topic-body__content").get_text(strip=True)
                date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                media_files = []
                image_container = news_soup.find("div", class_="topic-body__title-image")
                if image_container:
                    img_tag = image_container.find("img")
                    if img_tag:
                        src = img_tag.get("src") or img_tag.get("data-src")
                        if src:
                            if src.startswith("//"):
                                src = "https:" + src
                            elif src.startswith("/"):
                                src = self.host + src
                            media_files.append(src)
                        else:
                            print("Image source not found.")

                return {
                    "title": title,
                    "text": content,
                    "date": date,
                    "media": src,
                    "url": news_url
                }

        except Exception as e:
            print(f"Ошибка парсинга последнего поста: {e}")
