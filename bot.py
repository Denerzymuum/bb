import telebot
from config import *
from speechkit import speech_to_text, text_to_speech
from validators import *  # модуль для валидации
from gpt import ask_gpt  # модуль для работы с GPT
from database import create_database, add_message, select_n_last_messages
from creds import get_bot_token  # модуль для получения bot_token

bot = telebot.TeleBot(get_bot_token())  # создаём объект бота

create_database()


@bot.message_handler(commands=['debug'])
def debug(message):
    with open("logs.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(commands=['start'])
def starter(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Привет. я бот, который поможет с твоими вопросами. Задать их мне ты можешь '
                              'как в текстовом виде, так и голосовым сообщением. Я отвечу тебе так же. '
                              'У тебя так же есть лимиты. Узнать больше можно используя команду /help '
                              'Чтобы вступить в режим диалога с ботом - используйте команду /dialog')


@bot.message_handler(commands=['help'])
def helper(message):
    bot.send_message(message.chat.id, f"Это тестовая версия бота собеседника с возможностью голосового общения"
                                      ". В ней есть определенные ограничения: \n"
                                      f"Всего бот позволит использовать себя {MAX_USERS} пользователям \n"
                                      f"Отправить ГС вы можете не больше {MAX_USER_STT_BLOCKS} штук, если они длиною "
                                      f"до 15 секунд. ГС более 15 секунд считаются за 2. более 30 секунд отправлять "
                                      f"нельзя. Ответы бота так же ограничены {MAX_GPT_TOKENS} токенами. "
                                      f"И суммарно все ответы ограничены {MAX_USER_GPT_TOKENS} токенами"
                                      f"Максимальное число символов, которые могут быть "
                                      f"озвучены нейросетью - {MAX_USER_TTS_SYMBOLS}"
                                      f"При этом нейросеть помнит {COUNT_LAST_MSG} "
                                      f"ваших последних сообщений из диалога")


@bot.message_handler(commands=['dialog'])
def dialoger(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Привет. Какая у тебя проблема?')
    bot.register_next_step_handler(message, dialoger_two)


def dialoger_two(message):
    if message.text:
        texter(message)
    elif message.voice:
        devoicer(message)
    else:
        bot.send_message(message.chat.id, f"я не могу это видеть")
    bot.register_next_step_handler(message, dialoger_two)


def texter(message):
    try:
        user_id = message.from_user.id

        # ВАЛИДАЦИЯ: проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)  # мест нет =(
            return

        # БД: добавляем сообщение пользователя и его роль в базу данных
        full_user_message = [message.text, 'user', 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)

        # ВАЛИДАЦИЯ: считаем количество доступных пользователю GPT-токенов
        # получаем последние 4 (COUNT_LAST_MSG) сообщения и количество уже потраченных токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, error_message)
            return

        # GPT: отправляем запрос к GPT
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        # GPT: обрабатываем ответ от GPT
        if not status_gpt:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, answer_gpt)
            return
        # сумма всех потраченных токенов + токены в ответе GPT
        total_gpt_tokens += tokens_in_answer

        # БД: добавляем ответ GPT и потраченные токены в базу данных
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение")


# Декоратор для обработки голосовых сообщений, полученных ботом
def devoicer(message):
    user_id = message.from_user.id  # Идентификатор пользователя, который отправил сообщение
    try:
        # Проверка на максимальное количество пользователей
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return
        # Проверка на доступность аудиоблоков
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:


            bot.send_message(user_id, error_message)
            return
        # Обработка голосового сообщения
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return
        # Запись в БД
        add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])

        # Проверка на доступность GPT-токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        # Запрос к GPT и обработка ответа
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer
        # Проверка на лимит символов для SpeechKit
        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)

        # Запись ответа GPT в БД
        add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # Преобразование ответа в аудио и отправка
        status_tts, voice_response = text_to_speech(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)

    except Exception as e:
        logging.error(e)
        bot.send_message(user_id, "Не получилось ответить. Попробуй записать другое сообщение")


bot.polling()
