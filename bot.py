import logging
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# Введите ваш токен Telegram API и API-ключ Binance
TELEGRAM_API_TOKEN = "5683212966:AAFROD7629pEwgVHLOGyWap0vtKdxN3EdHE"
BINANCE_API_KEY = "zX6iKEIMBXY9dJyyz2a1etoKCEYcVtrAI4JqPrvc0ihVQWxGDCZyNYBpMiGOR66w"
OPERATOR_CHAT_ID = "358968367" # Замените на идентификатор чата оператора

# Реквизиты банков
BANK_DETAILS = {
    "sberbank": {
        "name": "Сбербанк",
        "card_number": "1234 5678 9012 3456",
    },
    "tinkoff": {
        "name": "Тинькофф",
        "card_number": "2345 6789 0123 4567",
    },
    "qiwi": {
        "name": "Qiwi кошелек",
        "card_number": "3456 7890 1234 5678",
    },
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Функция для получения актуального курса BTC
def get_btc_rate():
    url = f"https://api.binance.com/api/v3/ticker/price?symbol=BTCRUB"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    response = requests.get(url, headers=headers)
    response_data = response.json()
    btc_rate = float(response_data["price"])
    return btc_rate

# Функция для конвертации суммы с учетом наценки
def convert_with_markup(amount, rate, markup):
    return amount * rate * (1 + markup)

# Функция обработки команды /start
def start(update, context):
    chat_id = update.effective_chat.id
    welcome_message = "Добро пожаловать! Я бот, который поможет вам с обменом криптовалюты. Выберите действие:"
    keyboard = [
        [
            InlineKeyboardButton("Купить BTC", callback_data="buy_btc"),
            InlineKeyboardButton("Продать BTC", callback_data="sell_btc"),
            InlineKeyboardButton("Поддержка", callback_data="support"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text=welcome_message, reply_markup=reply_markup)

# Функции обработки коллбэков для кнопок
def handle_buy_btc(update, context):
    chat_id = update.effective_chat.id
    message = (
        "Укажите сумму в BTC или RUB:\n\n"
        "Пример: 0.1 или 0,01 или 3940\n\n"
        "Минимальная сумма 1000 рублей в BTC по текущему курсу BTC (1000 рублей)\n"
        "Курс: 1 BTC = актуальный курс btc + 15% наценка"
    )
    context.bot.send_message(chat_id=chat_id, text=message)
    context.user_data["action"] = "buy_btc"

def handle_sell_btc(update, context):
    chat_id = update.effective_chat.id
    message = "Эта функция находится в разработке. Пожалуйста, попробуйте позже."
    context.bot.send_message(chat_id=chat_id, text=message)

def handle_support(update, context):
    chat_id = update.effective_chat.id
    message = "Если у вас возникли вопросы или проблемы, пожалуйста, свяжитесь с оператором @Pav_Glash."
    context.bot.send_message(chat_id=chat_id, text=message)

def handle_amount_message(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text

    if "action" not in context.user_data or context.user_data["action"] != "buy_btc":
        return

def main():
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    action = query.data

    if action.startswith("buy"):
        handle_payment_method_selection(update, context, action)
    elif action.startswith("confirm"):
        handle_payment_confirmation(update, context, action)
    elif action.startswith("paid"):
        handle_payment_paid(update, context)
    elif action == "cancel":
        start(update, context)
    dp.add_handler(CallbackQueryHandler(handle_callback_query))
    dp.add_handler(MessageHandler(Filters.text, handle_amount_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

def parse_amount(text):
    text = text.replace(",", ".")
    try:
        amount = float(text)
        return amount
    except ValueError:
        return None

def handle_amount_message(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text

    if "action" not in context.user_data or context.user_data["action"] != "buy_btc":
        return

    amount = parse_amount(text)
    if amount is None:
        context.bot.send_message(chat_id=chat_id, text="Неверный формат суммы. Попробуйте еще раз.")
        return

    btc_rate = get_btc_rate()
    markup = 0.15

    if amount < 1000:
        amount_btc = amount / btc_rate
    else:
        amount_btc = amount

    amount_rub = convert_with_markup(amount_btc, btc_rate, markup)

    context.user_data["amount_btc"] = amount_btc
    context.user_data["amount_rub"] = amount_rub

    message = f"Вы получите: {amount_btc:.8f} BTC\n\nДля продолжения выберите способ оплаты:"
    keyboard = [
        [
            InlineKeyboardButton(f"{BANK_DETAILS['sberbank']['name']} {amount_rub:.2f} RUB", callback_data="pay_sberbank"),
            InlineKeyboardButton(f"{BANK_DETAILS['tinkoff']['name']} {amount_rub:.2f} RUB", callback_data="pay_tinkoff"),
            InlineKeyboardButton(f"{BANK_DETAILS['qiwi']['name']} {amount_rub:.2f} RUB", callback_data="pay_qiwi"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

def handle_callback_query(update, context):
    query = update.callback_query
    query_data = query.data

    if query_data == "buy_btc":
        handle_buy_btc(update, context)
    elif query_data == "sell_btc":
        handle_sell_btc(update, context)
    elif query_data == "support":
        handle_support(update, context)
    elif query_data.startswith("pay_"):
        handle_payment_choice(update, context, query_data[4:])
    elif query_data == "paid":
        handle_payment_paid(update, context)

def handle_payment_paid(update, context):
    chat_id = update.effective_chat.id
    username = update.effective_user.username

    amount_btc = context.user_data["amount_btc"]
    amount_rub = context.user_data["amount_rub"]
    wallet = context.user_data["wallet"]
    payment_method = context.user_data["payment_method"]

    bank_info = BANK_DETAILS[payment_method]

    message_to_operator = (
        f"Пользователь @{username} сказал, что перевел {amount_rub:.2f} RUB на указанные реквизиты.\n\n"
        f"Сумма BTC: {amount_btc:.8f}\n"
        f"Реквизиты: {bank_info['card_number']}\n"
        f"Банк: {bank_info['bank_name']}\n"
        f"Кошелек BTC: {wallet}"
    )
    context.bot.send_message(chat_id=OPERATOR_CHAT_ID, text=message_to_operator)

    message_to_user = (
        "Спасибо за оплату! Мы проверим вашу оплату и свяжемся с вами в ближайшее время."
    )
    context.bot.send_message(chat_id=chat_id, text=message_to_user)

    del context.user_data["action"]
    del context.user_data["amount_btc"]
    del context.user_data["amount_rub"]
    del context.user_data["wallet"]
    del context.user_data["payment_method"]


def handle_payment_choice(update, context, payment_method):
    chat_id = update.effective_chat.id
    amount_btc = context.user_data.get("amount_btc")
    amount_rub = context.user_data.get("amount_rub")

    message = (
        f"Напишите боту BTC кошелек, на который нужно зачислить криптовалюту.\n\n"
        f"Внимание! Убедитесь, что указанный кошелек действительно принадлежит вам и "
        f"имеет правильный формат. В случае ошибки монеты могут быть потеряны."
    )
    context.bot.send_message(chat_id=chat_id, text=message)

    context.user_data["action"] = "enter_wallet"
    context.user_data["payment_method"] = payment_method

def handle_wallet_message(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text

    if "action" not in context.user_data or context.user_data["action"] != "enter_wallet":
        return

    wallet = text.strip()
    # Здесь можно добавить проверку на валидность BTC кошелька, если требуется

    context.user_data["wallet"] = wallet

    message = (
        f"Время на оплату заявки 20 минут!\n\n"
        f"Итого к оплате: {context.user_data['amount_rub']:.2f} RUB\n\n"
        f"После оплаты средства будут переведены на кошелек: {wallet}\n\n"
        f"Если у вас возникли проблемы с оплатой, напишите оператору @Pav_Glash"
    )
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data="cancel"), InlineKeyboardButton("Согласен", callback_data="confirm")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

def main():
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_callback_query))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_amount_message))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_wallet_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

def handle_confirm_payment(update, context):
    chat_id = update.effective_chat.id
    payment_method = context.user_data["payment_method"]
    bank_info = BANK_DETAILS[payment_method]

    message = (
        f"Номер карты банка: {bank_info['card_number']}\n\n"
        f"Имя получателя: {bank_info['recipient_name']}\n\n"
        f"После перевода нажмите кнопку 'Оплатил', и мы проверим вашу оплату."
    )
    keyboard = [[InlineKeyboardButton("Оплатил", callback_data="paid")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

    context.user_data["action"] = "confirm_payment"


def handle_cancel_payment(update, context):
    chat_id = update.effective_chat.id

    message = "Операция отменена. Возвращаемся в главное меню."
    send_main_menu(context.bot, chat_id)

    del context.user_data["action"]
    del context.user_data["amount_btc"]
    del context.user_data["amount_rub"]
    del context.user_data["wallet"]
    del context.user_data["payment_method"]

def send_btc_transaction(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if not text.startswith("Перевёл BTC пользователю"):
        return

    cash_number = text.split(" ")[-1]

    message = (
        f"BTC были отправлены на ваш счёт. Вот кэш-номер транзакции: {cash_number}\n\n"
        f"Рады сотрудничать!"
    )
    context.bot.send_message(chat_id=chat_id, text=message)

def handle_text(update, context):
    if context.user_data.get("action") == "confirm_payment":
        handle_wallet_input(update, context)
    elif update.message.text.startswith("Перевёл BTC пользователю"):
        send_btc_transaction(update, context)

dp.add_handler(MessageHandler(Filters.text, handle_text))
