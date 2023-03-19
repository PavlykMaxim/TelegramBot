from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import FileIsTooBig
import datetime
import re
import asyncio
import time
import os
from videoDownloader import VideoDownload
from videoCropper import VideoCropper
from audioUtils import AudioExtractor

API_TOKEN = ''
CLEAR_FOLDERS_TIMER = 60

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
downloader = VideoDownload()
cropper = VideoCropper()
audioExtractor = AudioExtractor()

print('Bot_started')

class WaitingStates(StatesGroup):
    waiting_for_file_circle = State()
    waiting_for_file_audio = State()


@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    button2 = InlineKeyboardButton(text="/circle")
    button3 = InlineKeyboardButton(text='/audio')
    kb.add(button2, button3)
    await bot.send_message(chat_id=msg.chat.id, text='Привет!👋\nЭтот бот позволяет превратить любое видео в кружочек ТГ.\n'
                                                    'Всё что нужно сделать - выбрать режим работы и после получения готового кружочка, нажать переслать.\n' 
                                                    'Отправлять можно отключив автора!\n\n'
                                                    'Выбери, какой вариант загрузки видео ты хочешь:\n'
                                                    '/circle - твое видео в кружочек (не дольше 1 минуты и не тяжелее 20мб!)\n'
                                                    '/audio - твое видео в голосовое сообщение (не дольше 2 минут и не тяжелее 20мб!)', reply_markup=kb)


@dp.message_handler(commands=['circle'])
async def circle(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id, text='Пришли мне ссылку или видео!')

    await WaitingStates.waiting_for_file_circle.set()


@dp.message_handler(commands=['audio'])
async def audio(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id, text='Пришли ссылку или файл!')

    await WaitingStates.waiting_for_file_audio.set()


@dp.message_handler(state=WaitingStates.waiting_for_file_circle, content_types=types.ContentType.ANY)
async def process_circle(msg: types.Message, state: FSMContext):
    if msg.content_type != 'video' and not re.search(r'(http|https)://[^\s]+', msg.text):
        await msg.reply(text='Это не ссылка и не видео!')
        await state.finish()
        return
    else:
        pass

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    current_time = datetime.datetime.now()
    time_str = current_time.strftime('%d_%m_%y_%H_%M_%S')

    if msg.content_type == 'video':
        file_id = msg.video.file_id
        duration = msg.video.duration
        filename = f'{file_id}_{time_str}.mp4'

        if duration > 60:
            await msg.reply(text='Длительность видео превышает 1 минуту!')
            await state.finish()
            return
        else:
            pass

        try:
            file = await bot.get_file(file_id)
        except FileIsTooBig:
            await msg.reply(text='Файл весит больше 20мб!')
            await state.finish()
            return
        
        await bot.download_file(file_path=file.file_path, destination = f'data/users/{user_id}/downloaded/{filename}')
        bot_msg = await msg.reply(text='Видео обрабатывается! Это может занять пару минут!')
        msg_id = bot_msg.message_id
        cropper.cropping(filename=filename, user_id=user_id)
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        await circle_sender(chat_id, user_id, filename)
        await state.finish()
        await clear_folders(user_id=user_id)

    else:
        url = msg.text
        domain = url.split("//")[-1].split("www.")[-1].split(".")[0]
        filename = f'{user_id}_{time_str}.mp4'

        if domain != 'youtube' and domain != 'youtu':
            await msg.reply(text='Ссылка должна быть только на YouTube')
            await state.finish()
            return

        bot_msg = await msg.reply(text='Скачиваем и обрабатываем видео!\nЭто может занять пару минут!')
        msg_id = bot_msg.message_id
        downloaded = downloader.video_dowloader(url, filename, user_id=user_id, mode='circle')

        if downloaded == True:
            cropper.cropping(filename=filename, user_id=user_id)
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            await circle_sender(chat_id, user_id, filename)
            await state.finish()
            await clear_folders(user_id=user_id)
        else:
            await msg.reply(text='Что-то пошло не так. Попробуйте снова! \n(Возможно вы ввели неверную ссылку или длительность видео превышет 60 секунд!)')
            await state.finish()
            return


@dp.message_handler(state=WaitingStates.waiting_for_file_audio, content_types=types.ContentType.ANY)
async def process_audio(msg: types.Message, state: FSMContext):
    if msg.content_type != 'video' and not re.search(r'(http|https)://[^\s]+', msg.text):
        await msg.reply(text='Это не ссылка и не видео!')
        await state.finish()
        return
    else:
        pass

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    current_time = datetime.datetime.now()
    time_str = current_time.strftime('%d_%m_%y_%H_%M_%S')

    if msg.content_type == 'video':
        file_id = msg.video.file_id
        duration = msg.video.duration
        filename = f'{file_id}_{time_str}.mp4'

        if duration > 120:
            await msg.reply(text='Длительность видео превышает 2 минуты!')
            await state.finish()
            return
        else:
            pass

        try:
            file = await bot.get_file(file_id)
        except FileIsTooBig:
            await msg.reply(text='Файл весит больше 20мб!')
            await state.finish()
            return
        
        await bot.download_file(file_path=file.file_path, destination = f'data/users/{user_id}/downloaded/{filename}')
        bot_msg = await msg.reply(text='Видео обрабатывается! Это может занять пару минут!')
        msg_id = bot_msg.message_id

        audio_checker = audioExtractor.audioExtractor(filename=filename, user_id=user_id)

        if audio_checker == True:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            await audio_sender(chat_id, user_id, filename)
            await state.finish()
            await clear_folders(user_id=user_id)
        else:
            msg.reply(text='Что-то пошло не так. Попробуйте снова! \n(Возможно длительность видео превышет 60 секунд!)')
            await state.finish()
            return

    else:
        url = msg.text
        domain = url.split("//")[-1].split("www.")[-1].split(".")[0]
        filename = f'{user_id}_{time_str}.mp4'

        if domain != 'youtube' and domain != 'youtu':
            await msg.reply(text='Ссылка должна быть только на YouTube')
            await state.finish()
            return

        bot_msg = await msg.reply(text='Скачиваем и обрабатываем видео!\nЭто может занять пару минут!')
        msg_id = bot_msg.message_id
        downloaded = downloader.video_dowloader(url, filename, user_id=user_id, mode='audio')
        if downloaded == True:
            audioExtractor.audioExtractor(filename=filename, user_id=user_id)
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            await audio_sender(chat_id, user_id, filename)
            await state.finish()
            await clear_folders(user_id=user_id)
        else:
            await msg.reply(text='Что-то пошло не так. Попробуйте снова! \n(Возможно вы ввели неверную ссылку или длительность видео превышет 120 секунд!)')
            await state.finish()
            return


@dp.message_handler(content_types=types.ContentType.ANY)
async def echo(msg: types.Message):
    await msg.reply('Я не знаю, что с этим делать. 🤷‍♂️')


async def audio_sender(chat_id, user_id, filename):
    await bot.send_chat_action(user_id, action="RECORD_VOICE")
    await asyncio.sleep(1)
    new_filename = filename[:len(filename)-4]
    await bot.send_voice(chat_id=chat_id,
                        voice=open(f'data/users/{user_id}/audio/{new_filename}_audio.ogg', 'rb'))
    

async def circle_sender(chat_id, user_id, filename):
    await bot.send_chat_action(user_id, action='RECORD_VIDEO_NOTE')
    await asyncio.sleep(1)
    new_filename = filename[:len(filename)-4]
    await bot.send_video_note(chat_id=chat_id,
                            video_note=open(f'data/users/{user_id}/cropped/{new_filename}_final.mp4', 'rb'))


async def clear_folders(user_id):
    folder_path = f'data/users/{user_id}'
    created_before = time.time() - 120

    for sub_dir in ['audio', 'cropped', 'downloaded']:
        sub_dir_path = os.path.join(folder_path, sub_dir)

        for filename in os.listdir(sub_dir_path):
            file_path = os.path.join(sub_dir_path, filename)

            if os.path.isfile(file_path):
                if os.stat(file_path).st_ctime < created_before:

                    try:
                        os.remove(file_path)

                    except Exception as e:
                        print(f'Файл {file_path} не удалось удалить!')

                    else:
                        print(f'Файл {file_path} успешно удален!')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)