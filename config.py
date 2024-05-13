MAX_USERS = 3  # максимальное кол-во пользователей
MAX_GPT_TOKENS = 120  # максимальное кол-во токенов в ответе GPT
COUNT_LAST_MSG = 4  # кол-во последних сообщений из диалога

# лимиты для пользователя
MAX_USER_STT_BLOCKS = 10  # 10 аудиоблоков
MAX_USER_TTS_SYMBOLS = 5_000  # 5 000 символов (сколько можно перевести из текста в голос)
MAX_USER_GPT_TOKENS = 2_000  # 2 000 токенов (столько токенов может сгенерировать нейросеть при ответах одному
# пользователю суммарно)

SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. '
                                            'Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. '
                                            'Изображай человека'}]  # список с системным промтом

<<<<<<< HEAD
HOME_DIR = '../YP_Python_Final'
=======
HOME_DIR = '/home/student/aa'  # путь к папке с проектом
>>>>>>> 5c25e83f7c2362876f5daeb5e53c881baab855fe
LOGS = f'{HOME_DIR}/logs.txt'  # файл для логов
DB_FILE = f'{HOME_DIR}/messages.db'  # файл для базы данных

IAM_TOKEN_PATH = f'{HOME_DIR}/iam_token.txt'  # файл для хранения iam_token
FOLDER_ID_PATH = f'{HOME_DIR}/folder_id.txt'  # файл для хранения folder_id
BOT_TOKEN_PATH = f'{HOME_DIR}/API_TOKEN.txt'  # файл для хранения bot_token
