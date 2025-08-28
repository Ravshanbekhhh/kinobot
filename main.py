import asyncio, logging, sys, json, os
from aiogram import Bot, Dispatcher, html, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, Update
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from datetime import datetime, timedelta
from buttons import start_btn, Categories
from aiohttp import web
load_dotenv()

TOKEN = "8305141782:AAF5qyfXs1XVxDDFVfF_GUOn_vK76Kbb348"
WEBHOOK_HOST = "https://ravshanbek1808.alwaysdata.net"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
bot = Bot(token=TOKEN)


# Kanal ID'lar
CHANNELS = {
    "scary": -1002507262411,
    "multfilm": -1002717456380,
    "boevik": -1002834167173,
    "fantastik": -1002667445705,
    "uzbek": -1002593091032
}

DATA_FILE = "data.json"
CHANNELS_FILE = "channels.json"

dp = Dispatcher()

Login = "temirqol"
Password = ("darrax"
            "")

# Default qiymatlar
code_counters = {
    "scary": {"prefix": "Q", "counter": 100},
    "multfilm": {"prefix": "M", "counter": 100},
    "boevik": {"prefix": "B", "counter": 100},
    "fantastik": {"prefix": "F", "counter": 100},
    "uzbek": {"prefix": "U", "counter": 100},
}
movies = {}
views_log = {}  # {"kod": ["2025-08-01", "2025-08-02", ...]}

# Webhook handler
async def handle_webhook(request):
    data = await request.json()
    update = Update.to_object(data)
    await dp.feed_update(bot, update)
    return web.Response()


async def on_startup(app):
    # Eski webhookni o‘chirib, yangisini o‘rnatamiz
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(app):
    await bot.session.close()



# ---------- JSON FAYL FUNKSIYALARI ----------
def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("channels", [])
    return []

def save_channels(channels_list):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump({"channels": channels_list}, f, ensure_ascii=False, indent=4)

def load_data():
    global code_counters, movies, views_log
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            code_counters.update(data.get("code_counters", {}))
            movies.update(data.get("movies", {}))
            views_log.update(data.get("views_log", {}))
            print("📂 Ma'lumotlar yuklandi.")
    else:
        save_data()

def save_data():
    data = {
        "code_counters": code_counters,
        "movies": movies,
        "views_log": views_log
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("💾 Ma'lumotlar saqlandi.")

# ---------- STATE'LAR ----------
class AdminAuth(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

class MovieUpload(StatesGroup):
    waiting_for_movie = State()
    waiting_for_movie_name = State()

class SearchByCode(StatesGroup):
    waiting_for_code = State()

# ---------- KOMANDALAR ----------

# Admin kanallar qo‘shishi
@dp.message(F.text == "➕ Kanal qo‘shish")
async def add_channel(msg: Message):
    channels = load_channels()
    await msg.answer("🔗 Kanal username yoki ID yuboring:")

    @dp.message()
    async def receive_channel(m: Message):
        ch_id = m.text.strip()
        if ch_id not in channels:
            channels.append(ch_id)
            save_channels(channels)
            await m.answer("✅ Kanal qo‘shildi.")
        else:
            await m.answer("⚠️ Bu kanal allaqachon ro‘yxatda bor.")



# Admin kanallarni o‘chirish
@dp.message(F.text == "❌ Kanal o‘chirish")
async def delete_channel_list(msg: Message):
    channels = load_channels()
    if not channels:
        await msg.answer("⚠️ Hozircha ro‘yxatda kanal yo‘q.")
        return

    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.row(InlineKeyboardButton(
            text=ch,
            callback_data=f"del_channel:{ch}"
        ))

    await msg.answer("🗑 O‘chirmoqchi bo‘lgan kanalingizni tanlang:", reply_markup=kb.as_markup())


# Callback orqali kanal o‘chirish
@dp.callback_query(F.data.startswith("del_channel:"))
async def delete_channel_cb(callback: CallbackQuery):

    username = callback.data.split(":", 1)[1]
    channels = load_channels()
    new_channels = [ch for ch in channels if ch != username]
    save_channels(new_channels)

    await callback.answer("✅ Kanal o‘chirildi.", show_alert=True)
    await callback.message.edit_text(f"🗑 {username} kanali o‘chirildi.")

@dp.message(Command(commands="start"))
async def start(message: Message,state:FSMContext) -> None:
    await state.clear()
    await message.answer(f"Salom, {html.bold(message.from_user.full_name)}!\nMenulardan birini tanla.", reply_markup=start_btn)



@dp.message(F.text == "Bot haqida")
async def about_bot(msg: Message):
    await msg.answer("""KinoBot\n🎥 Maxfiy kinolarni faqat kod orqali oching.\nInstagramda rolik → Telegramda to‘liq film.\n🔐 Sirli. Tez. Faqat siz uchun.""")

@dp.message(F.text == "Orqaga⬅️")
async def back_to_menu(msg: Message):
    await msg.answer("Bosh menyu.", reply_markup=start_btn)

@dp.message(F.text == "Admin Login")
async def login(msg: Message, state: FSMContext):
    await msg.answer("Loginni kirit:")
    await state.set_state(AdminAuth.waiting_for_login)

@dp.message(AdminAuth.waiting_for_login)
async def get_login(msg: Message, state: FSMContext):
    await state.update_data(login=msg.text)
    await msg.answer("🔒 Endi parolni kiriting:")
    await state.set_state(AdminAuth.waiting_for_password)

@dp.message(AdminAuth.waiting_for_password)
async def get_password(msg: Message, state: FSMContext):
    user_data = await state.get_data()
    login = user_data.get("login")
    password = msg.text

    if str(login).lower() == Login.lower() and password.lower() == Password.lower():
        await msg.answer("✅ Hush kelibsiz, Temirqol! Siz admin sifatida tizimga kirdingiz.", reply_markup=Categories)
    else:
        await msg.answer("❌ Login yoki parol noto‘g‘ri.")

    await state.clear()

# ----------- CATEGORY HANDLERS -----------

async def start_upload(msg: Message, state: FSMContext, genre: str, text: str):
    await state.update_data(genre=genre)
    await msg.answer(f"🎬 {text} kino faylini yuboring:")
    await state.set_state(MovieUpload.waiting_for_movie)

@dp.message(F.text == "👻 Qo‘rqinchli")
async def scary_category(msg: Message, state: FSMContext):
    await start_upload(msg, state, "scary", "Qo‘rqinchli")

@dp.message(F.text == "🐭 Multfilmlar")
async def cartoon_category(msg: Message, state: FSMContext):
    await start_upload(msg, state, "multfilm", "Multfilm")

@dp.message(F.text == "🧨 Boevik / Ekshen")
async def boevik_category(msg: Message, state: FSMContext):
    await start_upload(msg, state, "boevik", "Boevik / Ekshen")

@dp.message(F.text == "🎬Fantastik")
async def fantastik_category(msg: Message, state: FSMContext):
    await start_upload(msg, state, "fantastik", "Fantastik")

@dp.message(F.text == "🇺🇿 O‘zbek kinolari")
async def uzbek_category(msg: Message, state: FSMContext):
    await start_upload(msg, state, "uzbek", "O'zbek kino")

# ----------- MOVIE UPLOAD -----------

@dp.message(MovieUpload.waiting_for_movie)
async def receive_movie_file(msg: Message, state: FSMContext):
    if msg.video or msg.document:
        await state.update_data(movie_file=msg)
        await msg.answer("📛 Kino nomini kiriting:")
        await state.set_state(MovieUpload.waiting_for_movie_name)
    else:
        await msg.answer("❗Iltimos, video yoki fayl yuboring.")

@dp.message(MovieUpload.waiting_for_movie_name)
async def receive_movie_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    genre = data.get("genre", "scary")
    movie_file = data["movie_file"]       # bu Message obyekti
    movie_name = msg.text.strip()

    last_number = code_counters[genre]["counter"]
    new_number = last_number + 1
    code_counters[genre]["counter"] = new_number

    prefix = code_counters[genre]["prefix"]
    code = f"{prefix}{new_number}"

    # Fayl id (hozircha saqlab turamiz, lekin asosiy narsa - channel post ID)
    file_id = movie_file.video.file_id if movie_file.video else movie_file.document.file_id

    channel_id = CHANNELS[genre]
    caption = f"🎥 Kino nomi: {movie_name}\n🔢 Kod: {code}\n🎬 Janr: {genre.title()}"

    # KANALGA KO'CHIRISH va qaytgan channel xabarini olish
    sent_msg = await movie_file.copy_to(chat_id=channel_id, caption=caption)

    # Muhim: kanal postining manbasini saqlaymiz
    movies[code] = {
        "file_id": file_id,  # fallback uchun turaversin
        "movie_name": movie_name,
        "genre": genre,
        "origin_chat_id": channel_id,
        "origin_message_id": sent_msg.message_id
    }

    save_data()

    await msg.answer(
        f"✅ Kino '{movie_name}' yuklandi.\n📮 Kanalga yuborildi.\n🔢 Kodi: {code}"
    )
    await state.clear()

# ----------- SEARCH -----------

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def check_subscriptions(user_id, bot: Bot):
    channels = load_channels()
    not_subscribed = []

    for ch in channels:
        try:
            # t.me/ yoki https://t.me/ bo‘lsa, faqat nomini olamiz
            if str(ch).startswith("http"):
                ch = ch.split("/")[-1]

            # Agar raqam bo‘lsa, ID sifatida ishlatamiz
            if str(ch).lstrip('-').isdigit():
                chat_id = int(ch)
            else:
                # username bo‘lsa, @ belgisi bo‘lishi shart
                if not str(ch).startswith("@"):
                    ch = f"@{ch}"
                chat_id = ch

            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                not_subscribed.append(ch)
        except Exception as e:
            logging.warning(f"Obuna tekshirishda xato: {e}")
            not_subscribed.append(ch)

    return not_subscribed


@dp.message(F.text == "Kino kodi orqali izlash🔎")
async def search_by_code(msg: Message, state: FSMContext):
    await msg.answer("🔎 Kodini kiriting:")
    await state.set_state(SearchByCode.waiting_for_code)


@dp.message(SearchByCode.waiting_for_code)
async def send_movie_by_code(msg: Message, state: FSMContext):
    not_subs = await check_subscriptions(msg.from_user.id, msg.bot)
    if not_subs:
        kb = InlineKeyboardBuilder()
        for ch in not_subs:
            if str(ch).startswith("-100"):
                url = f"https://t.me/c/{str(ch)[4:]}"
            else:
                url = f"https://t.me/{str(ch).replace('@', '')}"
            kb.row(InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url=url))
        kb.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs"))

        await msg.answer("❗ Iltimos, quyidagi kanallarga obuna bo‘ling:", reply_markup=kb.as_markup())
        # ❌ bu yerda clear qilmaymiz!
        return

    code = msg.text.strip().upper()
    info = movies.get(code)

    if not info:
        await msg.answer("❌ Bunday kod topilmadi.")
        # ❌ clear emas, yana state o‘sha joyida qoladi
        return

    today = datetime.now().strftime("%Y-%m-%d")
    views_log.setdefault(code, []).append(today)
    save_data()

    try:
        if "origin_chat_id" in info and "origin_message_id" in info:
            sent = await msg.bot.copy_message(
                chat_id=msg.chat.id,
                from_chat_id=info["origin_chat_id"],
                message_id=info["origin_message_id"],
                protect_content=True,
            )
        else:
            sent = await msg.bot.send_video(
                chat_id=msg.chat.id,
                video=info["file_id"],
                caption=f"🎥 {info['movie_name']} (Kodi: {code})",
                protect_content=True
            )

        asyncio.create_task(delete_later(msg.bot, msg.chat.id, sent.message_id, 86400))
        await msg.answer("⏳ Kino 24 soat davomida mavjud.")

    except TelegramBadRequest as e:
        if "wrong file identifier" in str(e).lower():
            await msg.answer("⛔ Bu kino eski bot orqali yuklangan. Iltimos, admin uni qayta yuklasin.")
        else:
            raise

    # ✅ Yana qidirishga ruxsat berish
    await state.set_state(SearchByCode.waiting_for_code)


@dp.callback_query(F.data == "check_subs")
async def recheck_subs(callback, state: FSMContext):
    not_subs = await check_subscriptions(callback.from_user.id, callback.bot)
    if not_subs:
        await callback.answer("❌ Hali ham obuna bo‘lmagansiz!", show_alert=True)
    else:
        await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)

# ----------- TOP 1 OYLIK -----------


@dp.message(F.text == "Top 1 kino oy uchun📈")
async def monthly_top(msg: Message):
    today = datetime.now()
    last_30_days = today - timedelta(days=30)

    stats = {}
    for code, dates in views_log.items():
        count = sum(1 for d in dates if datetime.strptime(d, "%Y-%m-%d") >= last_30_days)
        if count > 0:
            stats[code] = count

    if not stats:
        await msg.answer("❌ Oxirgi 30 kunda hech qanday ko‘rish qayd etilmagan.")
        return

    top_code = max(stats, key=stats.get)
    info = movies.get(top_code)

    if info:
        await msg.bot.send_video(
            chat_id=msg.chat.id,
            video=info["file_id"],
            caption=f"🏆 Oylik TOP 1 kino:\n🎥 {info['movie_name']}\n🔢 Kod: {top_code}\n📊 Ko‘rishlar soni: {stats[top_code]}",
            protect_content=True
        )
    else:
        await msg.answer("❌ Ma'lumot topilmadi.")

async def delete_later(bot: Bot, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)

async def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=8080)  # Alwaysdata 8080 portda ishlatadi


if __name__ == "__main__":
    asyncio.run(main())
