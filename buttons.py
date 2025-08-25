from aiogram.types import KeyboardButton,ReplyKeyboardMarkup

start_btn= ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="Kino kodi orqali izlash🔎"),
    ],
    [
        KeyboardButton(text="Top 1 kino oy uchun📈"),
    ],
    [
        KeyboardButton(text="Bot haqida"),
        KeyboardButton(text="Admin Login"),
    ],
],
    resize_keyboard=True,
    one_time_keyboard=True
)



back_btn=ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="Orqaga🔙")
    ]
],
    resize_keyboard=True
)



Categories= ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="🧨 Boevik / Ekshen"),
        KeyboardButton(text="👻 Qo‘rqinchli"),
    ],
    [
        KeyboardButton(text="🎬Fantastik"),
        KeyboardButton(text="🇺🇿 O‘zbek kinolari")
    ],

    [
        KeyboardButton(text="🐭 Multfilmlar"),
        KeyboardButton(text="➕ Kanal qo‘shish"),
    ],
    [
        KeyboardButton(text="❌ Kanal o‘chirish"),
        KeyboardButton(text="Orqaga⬅️")
    ]
],
    resize_keyboard=True
)