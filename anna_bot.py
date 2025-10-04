from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Проверка токенов
if not BOT_TOKEN or not DEEPSEEK_API_KEY:
    raise ValueError("Не найдены необходимые токены в переменных окружения!")

# Инициализация клиента DeepSeek
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# Состояния разговора
LANG, MAIN_MENU, TOPIC_DETAIL = range(3)

# Структура меню и текстов
MENU_STRUCTURE = {
    'en': {
        'main_menu_title': 'Main Menu',
        'topics': {
            '🤖 About Qubic': ['What is Qubic?', 'Project Vision', 'Key Features'],
            '⚡ Technology': ['Useful Proof of Work', 'Aigarth AI', 'Quorum Consensus'],
            '🌍 Community': ['Join Community', 'Resources', 'Development'],
            '🚀 Get Started': ['How to Begin', 'Mining Guide', 'Developer Docs']
        },
        'phrases': {
            'main_menu_prompt': 'Please choose a topic to explore:',
            'subtopic_prompt': 'What would you like to know about this topic?',
            'back_to_main': '🔙 Back to Main Menu',
            'restart': '🔄 Restart',
            'wait_generation': '🔄 Generating response...',
            'choose_language': 'Please choose your language:',
            'welcome': "Hello! I'm Anna, your intelligent assistant for the Qubic project!",
            'error': 'Sorry, I encountered an error. Please try again.',
            'restarting': '🔄 Restarting conversation...'
        }
    },
    'ru': {
        'main_menu_title': 'Главное меню',
        'topics': {
            '🤖 О Qubic': ['Что такое Qubic?', 'Видение проекта', 'Ключевые особенности'],
            '⚡ Технологии': ['Useful Proof of Work', 'ИИ Aigarth', 'Консенсус Quorum'],
            '🌍 Сообщество': ['Присоединиться', 'Ресурсы', 'Разработка'],
            '🚀 Начать': ['Как начать', 'Гайд по майнингу', 'Документация']
        },
        'phrases': {
            'main_menu_prompt': 'Выберите тему для изучения:',
            'subtopic_prompt': 'Что бы вы хотели узнать по этой теме?',
            'back_to_main': '🔙 Назад в меню',
            'restart': '🔄 Начать заново',
            'wait_generation': '🔄 Генерирую ответ...',
            'choose_language': 'Пожалуйста, выберите язык:',
            'welcome': "Привет! Я Анна, ваш интеллектуальный помощник по проекту Qubic!",
            'error': 'Извините, произошла ошибка. Пожалуйста, попробуйте снова.',
            'restarting': '🔄 Перезапускаю разговор...'
        }
    }
}

async def get_ai_response(prompt: str, language: str) -> str:
    """Получение ответа от DeepSeek API"""
    try:
        system_message = {
            'en': "You are Anna, a helpful assistant for Qubic project. Provide clear, engaging answers about Qubic's decentralized AI platform, Useful Proof of Work, Aigarth AI, and related technologies. Keep responses informative but concise. Respond in English.",
            'ru': "Ты Анна, помощник проекта Qubic. Давай четкие и увлекательные ответы о децентрализованной платформе ИИ Qubic, Useful Proof of Work, ИИ Aigarth и связанных технологиях. Будь информативной, но лаконичной. Отвечай на русском."
        }
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message[language]},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return None

async def start(update: Update, context: CallbackContext) -> int:
    """Начало разговора - выбор языка"""
    keyboard = [
        [KeyboardButton("🇺🇸 English"), KeyboardButton("🇷🇺 Русский")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "👋 Hello! I'm Anna, your intelligent assistant for the Qubic project!\n\n"
        "Please choose your preferred language:",
        reply_markup=reply_markup
    )
    return LANG

async def choose_language(update: Update, context: CallbackContext) -> int:
    """Обработка выбора языка"""
    user_choice = update.message.text
    
    if "Русский" in user_choice:
        context.user_data['lang'] = 'ru'
        welcome_text = MENU_STRUCTURE['ru']['phrases']['welcome']
    else:
        context.user_data['lang'] = 'en'
        welcome_text = MENU_STRUCTURE['en']['phrases']['welcome']
    
    await update.message.reply_text(welcome_text)
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: CallbackContext) -> int:
    """Показать главное меню"""
    lang = context.user_data.get('lang', 'en')
    phrases = MENU_STRUCTURE[lang]['phrases']
    topics = MENU_STRUCTURE[lang]['topics']
    
    # Создаем клавиатуру с темами + кнопка перезапуска
    keyboard = []
    for topic in topics.keys():
        keyboard.append([KeyboardButton(topic)])
    
    keyboard.append([KeyboardButton(phrases['restart'])])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(phrases['main_menu_prompt'], reply_markup=reply_markup)
    
    return MAIN_MENU

async def handle_main_menu(update: Update, context: CallbackContext) -> int:
    """Обработка выбора темы в главном меню"""
    lang = context.user_data.get('lang', 'en')
    chosen_topic = update.message.text
    topics = MENU_STRUCTURE[lang]['topics']
    phrases = MENU_STRUCTURE[lang]['phrases']
    
    # Проверяем, не выбрана ли кнопка перезапуска
    if chosen_topic == phrases['restart']:
        return await restart_bot(update, context)
    
    # Проверяем, есть ли выбранная тема в структуре меню
    current_topic = None
    for topic, subtopics in topics.items():
        if topic == chosen_topic:
            current_topic = topic
            break
    
    if not current_topic:
        await update.message.reply_text(phrases['error'])
        return await show_main_menu(update, context)
    
    context.user_data['current_topic'] = current_topic
    
    # Создаем клавиатуру с подтемами
    subtopics = topics[current_topic]
    keyboard = []
    for subtopic in subtopics:
        keyboard.append([KeyboardButton(subtopic)])
    keyboard.append([KeyboardButton(phrases['back_to_main'])])
    keyboard.append([KeyboardButton(phrases['restart'])])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(phrases['subtopic_prompt'], reply_markup=reply_markup)
    
    return TOPIC_DETAIL

async def handle_topic_detail(update: Update, context: CallbackContext) -> int:
    """Обработка выбора подтемы и генерация ответа"""
    lang = context.user_data.get('lang', 'en')
    chosen_subtopic = update.message.text
    phrases = MENU_STRUCTURE[lang]['phrases']
    current_topic = context.user_data.get('current_topic')
    
    # Проверяем, не выбрана ли кнопка перезапуска
    if chosen_subtopic == phrases['restart']:
        return await restart_bot(update, context)
    
    # Проверяем, не хочет ли пользователь вернуться в главное меню
    if chosen_subtopic == phrases['back_to_main']:
        return await show_main_menu(update, context)
    
    # Показываем сообщение о генерации
    wait_message = await update.message.reply_text(phrases['wait_generation'])
    
    # Формируем промпт для AI
    prompt = f"Topic: {current_topic}. Question: {chosen_subtopic}. Provide detailed but concise information about this aspect of Qubic project."
    
    # Получаем ответ от DeepSeek
    ai_response = await get_ai_response(prompt, lang)
    
    # Удаляем сообщение о генерации
    await wait_message.delete()
    
    if ai_response:
        # Создаем клавиатуру для продолжения диалога
        topics_dict = MENU_STRUCTURE[lang]['topics']
        subtopics_list = topics_dict[current_topic]
        
        keyboard = []
        for subtopic in subtopics_list:
            keyboard.append([KeyboardButton(subtopic)])
        keyboard.append([KeyboardButton(phrases['back_to_main'])])
        keyboard.append([KeyboardButton(phrases['restart'])])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Отправляем ответ
        await update.message.reply_text(ai_response, reply_markup=reply_markup)
    else:
        # Резервный ответ если API не работает
        fallback_responses = {
            'en': {
                'What is Qubic?': '🤖 **Qubic** is a decentralized platform for creating Artificial General Intelligence (AGI) that uses Useful Proof of Work instead of wasteful computations.',
                'Useful Proof of Work': '⚡ **Useful Proof of Work (uPoW)** is an innovative consensus mechanism that performs meaningful computations instead of energy-wasting mining operations.',
                'Aigarth AI': '🧠 **Aigarth** is the advanced artificial intelligence system developed by the Qubic project, designed to operate in a decentralized environment.',
                'Join Community': '🌍 Join our growing community! Connect with developers and enthusiasts through our Telegram groups and Discord server.'
            },
            'ru': {
                'Что такое Qubic?': '🤖 **Qubic** - это децентрализованная платформа для создания искусственного общего интеллекта (AGI), использующая Useful Proof of Work вместо бесполезных вычислений.',
                'Useful Proof of Work': '⚡ **Useful Proof of Work (uPoW)** - это инновационный механизм консенсуса, который выполняет полезные вычисления вместо энергозатратного майнинга.',
                'ИИ Aigarth': '🧠 **Aigarth** - это продвинутая система искусственного интеллекта, разработанная проектом Qubic для работы в децентрализованной среде.',
                'Присоединиться': '🌍 Присоединяйтесь к нашему растущему сообществу! Общайтесь с разработчиками и энтузиастами через наши группы в Telegram и Discord.'
            }
        }
        
        fallback_response = fallback_responses[lang].get(chosen_subtopic, phrases['error'])
        
        keyboard = []
        topics_dict = MENU_STRUCTURE[lang]['topics']
        subtopics_list = topics_dict[current_topic]
        for subtopic in subtopics_list:
            keyboard.append([KeyboardButton(subtopic)])
        keyboard.append([KeyboardButton(phrases['back_to_main'])])
        keyboard.append([KeyboardButton(phrases['restart'])])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(fallback_response, reply_markup=reply_markup)
    
    return TOPIC_DETAIL

async def restart_bot(update: Update, context: CallbackContext) -> int:
    """Перезапуск бота"""
    lang = context.user_data.get('lang', 'en')
    phrases = MENU_STRUCTURE[lang]['phrases']
    
    await update.message.reply_text(phrases['restarting'])
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    keyboard = [
        [KeyboardButton("🇺🇸 English"), KeyboardButton("🇷🇺 Русский")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    welcome_text = "👋 Hello! I'm Anna, your intelligent assistant for the Qubic project!\n\nPlease choose your preferred language:"
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return LANG

async def cancel(update: Update, context: CallbackContext) -> int:
    """Завершение разговора"""
    lang = context.user_data.get('lang', 'en')
    goodbye_text = "Thank you for chatting with me! Use /start to begin again." if lang == 'en' else "Спасибо за беседу! Используйте /start чтобы начать снова."
    
    await update.message.reply_text(goodbye_text)
    return ConversationHandler.END

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Обработка ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")

def main() -> None:
    """Запуск бота"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Настройка ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
                MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
                TOPIC_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topic_detail)],
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        
        application.add_handler(conv_handler)
        
        # Запуск бота
        print("🤖 Бот Anna успешно запущен...")
        print("📍 Используется современный API python-telegram-bot")
        print("🔑 DeepSeek API ключ:", DEEPSEEK_API_KEY[:10] + "..." + DEEPSEEK_API_KEY[-5:])
        print("⏹ Для остановки нажмите Ctrl+C")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        print("💡 Проверьте токен бота и подключение к интернету")

if __name__ == '__main__':
    main()