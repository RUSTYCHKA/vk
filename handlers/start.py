import vk_api
import requests
import json
import asyncio
import tempfile
import os
from aiogram import Bot, Router, F

from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from telethon import TelegramClient, functions, errors


from config import TOKEN, GEMINI_API_KEY, hashtags, BOT_TOKEN

from core.functions import ProxyFromUrl
from core.lenta import Lenta_Parser
from core.states import States
from core.ria import get_latest_article
from Levenshtein import ratio

import core.kb as kb

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

CHANNELS_FILE = "channels.txt"
GROUP_FILE = "vk_group.txt"

tg_client = TelegramClient(
    "session/tg",
    proxy=ProxyFromUrl("http://zMVPkGG3bb:EBYiNK1WdL@107.175.69.226:52117"),
    api_id=2040,
    api_hash="b18441a1ff607e10a989891a5462e627",
    auto_reconnect=True,
    system_version="4.16.30-vxCUSTOM"
)

vk_session =  vk_api.VkApi(
    token=TOKEN, api_version='5.131', scope=1073737727)

vk_client = vk_session.get_api()

upload = vk_api.VkUpload(vk_session)

handlers_router = Router()


async def call_gemini_api(gemini_api_key, prompt):
    print("Запрос к ИИ...")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    proxy = "http://zMVPkGG3bb:EBYiNK1WdL@107.175.69.226:52117"
    response = requests.post(url, headers=headers, data=json.dumps(data), params={
                             "key": gemini_api_key}, proxies={"http": proxy, "https": proxy})
    f = response.json()
    return f['candidates'][0]['content']['parts'][0]['text']



@handlers_router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(f"Привет {message.from_user.first_name}", reply_markup=kb.menu)

@handlers_router.callback_query(F.data == "add_vk_group")
async def add_vk_group(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите ссылку на ВК группу, в которую бот должен делать посты.")
    await state.set_state(States.vk_group)

@handlers_router.message(States.vk_group)
async def save_vk_group(message: Message, state: FSMContext):
    with open(GROUP_FILE, "w") as f:
        f.write(message.text.strip())
    await message.answer("Ссылка на ВК группу сохранена.", reply_markup=kb.menu)
    await state.clear()

@handlers_router.callback_query(F.data == "add_channels")
async def add_channels(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите список ТГ каналов, за которыми нужно следить, через запятую.")
    await state.set_state(States.tg_channels)

@handlers_router.message(States.tg_channels)
async def save_channels(message: Message, state: FSMContext):
    with open(CHANNELS_FILE, "w") as f:
        f.write("\n".join(message.text.split(",")))
    await message.answer("Список ТГ каналов сохранён.", reply_markup=kb.menu)
    await state.clear()

@handlers_router.callback_query(F.data.startswith("start="))
async def start_callback(call: CallbackQuery) -> None:
    act = call.data.split("=")[1]
    if act == "settings":
        await call.message.edit_text("Выберите настройку:", reply_markup=kb.settings)
    else:
        with open(CHANNELS_FILE, "r") as f:
                urls = f.read().splitlines()

        with open(GROUP_FILE, "r") as f:
            group = f.read().strip()

        ids = {}
        ids['lenta'] = ['']
        ids['ria'] = ['']
        for url in urls:
            ids[url] = []
        
        while True:
            try:
                

                
                groupname = group.replace("https://vk.com/", "")

                group_id = vk_client.utils.resolveScreenName(screen_name=groupname)['object_id']
                
                
                for url in urls:
                    
                    
                    await call.message.answer(f"Начинаю собирать данные с тг чата {url}...")
                    await tg_client.connect()

                    try:
                        full = await tg_client(functions.channels.GetFullChannelRequest(url))
                    except (errors.rpcerrorlist.ChannelPrivateError,
                            errors.rpcerrorlist.TimeoutError,
                            errors.rpcerrorlist.ChannelPublicGroupNaError):

                        return None, "У вас нет доступа к чату"
                    except (ValueError):

                        return None, "Чат не существует"

                    full_channel = full.full_chat
                    chat_id = full_channel.id
                    
                    async for msg in tg_client.iter_messages(chat_id, limit=1):
                        
                        if msg.id in ids[url]:
                            continue
                        
                        ids[url].append(msg.id)
                        
                        if msg.video:
                            ad_check_prompt = f"Определи, является ли этот текст рекламным. Ответь строго: 'Реклама есть' или 'Реклама нет'. Текст: {
                                msg.text.replace('📱[Дмитрий Никотин. Подписаться!](https://t.me/+pJOV7FvOs4U0NTgy)', '')}"
                            ad_check_result = await call_gemini_api(GEMINI_API_KEY, ad_check_prompt)
                            if "Реклама нет" in ad_check_result:
                                await tg_client.download_media(msg.video, "video.mp4")
                            
                                video = upload.video(
                                    video_file='video.mp4')
                                vk_video_url = 'https://vk.com/video{}_{}'.format(
                                    video['owner_id'], video['video_id'])
                                video = vk_video_url.replace('https://vk.com/', '')
                                # Переформулировка текста
                                rephrase_prompt = f"Переформулируй следующий текст, сохраняя его суть: {
                                    msg.text}"
                                rephrased_text = await call_gemini_api(GEMINI_API_KEY, rephrase_prompt)

                                vk_client.wall.post(
                                    owner_id=-group_id, from_group=1, message=rephrased_text+hashtags, attachments=video)
                                await call.message.answer("Пост с тг был спаршен и отправлен в группу")
                            else:
                                await call.message.answer("Пост с тг был спаршен, но не был отправлен в группу, так как нашел рекламу")
                            
                        elif msg.photo:
                            
                            await tg_client.download_media(msg.photo, "photo.jpg")

                            foto = upload.photo(
                                'photo.jpg', album_id="306470339")
                            vk_photo_url = 'https://vk.com/photo{}_{}'.format(
                                foto[0]['owner_id'], foto[0]['id'])
                            photo = vk_photo_url.replace('https://vk.com/', '')
                            # Проверка на рекламу
                            ad_check_prompt = f"Определи, является ли этот текст рекламным. Ответь строго: 'Реклама есть' или 'Реклама нет'. Текст: {
                                msg.text.replace('📱[Дмитрий Никотин. Подписаться!](https://t.me/+pJOV7FvOs4U0NTgy)', '')}"
                            ad_check_result = await call_gemini_api(GEMINI_API_KEY, ad_check_prompt)

                            if "Реклама нет" in ad_check_result:
                                # Переформулировка текста
                                rephrase_prompt = f"Переформулируй следующий текст, сохраняя его суть: {
                                    msg.text}"
                                rephrased_text = await call_gemini_api(GEMINI_API_KEY, rephrase_prompt)

                                vk_client.wall.post(
                                    owner_id=-group_id, from_group=1, message=rephrased_text+hashtags, attachments=photo)
                                await call.message.answer("Пост с тг был спаршен и отправлен в группу")
                            else:
                                await call.message.answer("Пост с тг был спаршен, но не был отправлен в группу, так как нашел рекламу")
                        elif msg.text:
                            
                            # Проверка на рекламу
                            ad_check_prompt = f"Определи, является ли этот текст рекламным. Ответь строго: 'Реклама есть' или 'Реклама нет'. Текст: {
                                msg.text.replace('📱[Дмитрий Никотин. Подписаться!](https://t.me/+pJOV7FvOs4U0NTgy)', '')}"
                            ad_check_result = await call_gemini_api(GEMINI_API_KEY, ad_check_prompt)

                            if "Реклама нет" in ad_check_result:
                                # Переформулировка текста
                                rephrase_prompt = f"Переформулируй следующий текст, сохраняя его суть: {
                                    msg.text}"
                                rephrased_text = await call_gemini_api(GEMINI_API_KEY, rephrase_prompt)

                                vk_client.wall.post(owner_id=-group_id,
                                                    from_group=1, message=rephrased_text+hashtags)
                                await call.message.answer("Пост с тг был спаршен и отправлен в группу")
                            else:
                                await call.message.answer("Пост с тг был спаршен, но не был отправлен в группу, так как нашел рекламу")
                    await tg_client.disconnect()
                
                lenta = Lenta_Parser()
                post = lenta.parse_latest_post()
                
                if post:
                    # Инициализируем переменную для прикрепления (если медиа отсутствует, передадим пустую строку)
                    photo = ""
                    # Если новость отличается от предыдущей (порог схожести можно настроить)
                    if ratio(post["text"], ids['lenta'][-1]) < 0.5:
                        ids['lenta'].append(post["text"])
                        if post["media"]:
                            # Скачиваем изображение по URL в уникальный временный файл
                            response = requests.get(post["media"])
                            if response.status_code == 200:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                                    tmp_file.write(response.content)
                                    tmp_filename = tmp_file.name
                                # Загружаем фото в ВК
                                media = upload.photo(tmp_filename, album_id="306470339")
                                os.remove(tmp_filename)  # удаляем временный файл после загрузки
                                vk_photo_url = 'https://vk.com/photo{}_{}'.format(
                                    media[0]['owner_id'], media[0]['id'])
                                photo = vk_photo_url.replace('https://vk.com/', '')
                            else:
                                # Если не удалось скачать фото, можно обработать ошибку или оставить photo пустым
                                photo = ""
                        # Проверяем, является ли текст рекламным
                        ad_check_prompt = (
                            f"Определи, является ли этот текст рекламным. "
                            f"Ответь строго: 'Реклама есть' или 'Реклама нет'. Текст: {post['text']}"
                        )
                        ad_check_result = await call_gemini_api(GEMINI_API_KEY, ad_check_prompt)

                        if "Реклама нет" in ad_check_result:
                            # Переформулировка текста
                            rephrase_prompt = f"Переформулируй следующий текст, сохраняя его суть: {post['text']}"
                            rephrased_text = await call_gemini_api(GEMINI_API_KEY, rephrase_prompt)
                            vk_client.wall.post(
                                owner_id=-group_id,
                                from_group=1,
                                message=rephrased_text + f"\n\nИсточник: {post['url']}" + hashtags,
                                attachments=photo  # Если photo пустое, можно передавать None или вовсе не указывать attachments
                            )
                            await call.message.answer("Пост с ленты ру был спаршен и отправлен в группу")
                            
                
                latest_article = get_latest_article('https://ria.ru/lenta/')
                if latest_article:
                    if ratio(latest_article["text"], ids['ria'][-1]) < 0.5:
                        ids["ria"].append(latest_article["text"])
                        if latest_article["media"]:
                            media = upload.photo(
                                latest_article["media"], album_id="306470339")
                            vk_photo_url = 'https://vk.com/photo{}_{}'.format(
                                media[0]['owner_id'], media[0]['id'])
                            photo = vk_photo_url.replace('https://vk.com/', '')
                            
                        ad_check_prompt = f"Определи, является ли этот текст рекламным. Ответь строго: 'Реклама есть' или 'Реклама нет'. Текст: {latest_article["text"]}"
                        ad_check_result = await call_gemini_api(GEMINI_API_KEY, ad_check_prompt)

                        if "Реклама нет" in ad_check_result:

                            rephrase_prompt = f"Переформулируй следующий текст, сохраняя его суть: {latest_article["text"]}"
                            rephrased_text = await call_gemini_api(GEMINI_API_KEY, rephrase_prompt)
                            vk_client.wall.post(owner_id=-group_id,from_group=1, message=rephrased_text+f"\n\nИсточник: {latest_article['url']}"+hashtags, attachments=photo)
                            await call.message.answer("Пост с риа ру был спаршен и отправлен в группу")
                
                await asyncio.sleep(60)
            except Exception as e:
                print(e)
        