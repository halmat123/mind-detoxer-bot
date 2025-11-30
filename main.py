import asyncio
import logging
import sqlite3

from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


BOT_TOKEN = "8565396330:AAGzrdr97yxJVJl8eQM0i1pbqt8TbVrXJXY"

logging.basicConfig(level=logging.INFO)
router = Router()


class Diary(StatesGroup):
    waiting_day = State()
    q1 = State()
    q2 = State()
    q3 = State()


def init_db():
    con = sqlite3.connect("diary.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            positive INTEGER,
            created_at TEXT
        )
    """)
    con.commit()
    con.close()


def clear_memories(user_id: int):
    con = sqlite3.connect("diary.db")
    cur = con.cursor()
    cur.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
    con.commit()
    con.close()


def save_positive_memory(user_id: int, text: str):
    con = sqlite3.connect("diary.db")
    cur = con.cursor()
    cur.execute(
        "INSERT INTO memories (user_id, text, positive, created_at) VALUES (?, ?, 1, ?)",
        (user_id, text, datetime.utcnow().isoformat())
    )
    con.commit()
    con.close()


def get_last_positive_memory(user_id: int):
    con = sqlite3.connect("diary.db")
    cur = con.cursor()
    cur.execute(
        "SELECT text FROM memories WHERE user_id=? AND positive=1 ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row else None


POSITIVE = {
    "хорошо", "отлично", "прекрасно", "замечательно", "великолепно",
    "рад", "рада", "радостно", "радость", "счастлив", "счастлива", "счастливо",
    "классно", "круто", "кайф", "кайфово", "здорово", "весело",
    "веселый", "веселая", "веселило", "веселье",
    "приятно", "приятный", "приятная", "приятное",
    "легко", "легкость", "легкий", "легкая",
    "получилось", "удалось", "успех", "удачно", "повезло",
    "спасибо", "благодарен", "благодарна", "благодарность",
    "люблю", "нравится", "понравилось", "по кайфу",
    "спокойно", "спокойствие", "умиротворенно", "умиротворение",
    "вдохновила", "вдохновил", "вдохновило", "вдохновение",
    "мотивирован", "мотивирована", "мотивация",
    "красиво", "красота", "миленько",
    "тепло", "уютно", "уют", "домашне",
    "хорошенько", "вкусно", "обожаю",
    "доволен", "довольна", "довольно",
    "ярко", "яркий", "яркая",
    "интересно", "интересный", "интересная",
    "полезно", "полезный", "полезная",
    "волшебно", "чудесно", "чудо",
    "супер", "класс", "огонь", "замечательный"
}
NEGATIVE = {
    "плохо", "ужасно", "грустно", "тревожно", "стресс", "злюсь", "злость",
    "устал", "устала", "измотан", "измотана", "выгорел", "выгорела",
    "раздражен", "раздражена", "раздражало", "раздражение",
    "тяжело", "тяжкий", "тяжелый", "тяжёлая", "тяжёло",
    "печально", "обидно", "обида", "обиделась", "обиделся",
    "не получилось", "сломалось", "проблемы", "проблема",
    "потеряла", "потерял", "потерялась", "потерянно",
    "страшно", "испуган", "испугана", "паника", "паниковала",
    "неприятно", "неприятный", "неприятная",
    "сложно", "сложный", "сложная",
    "тревога", "паническое",
    "одиноко", "одиночество", "одинокая", "одинокий",
    "подавленно", "подавленный", "подавленная",
    "хуже", "плохой", "плохая",
    "плакала", "плакал", "плач", "ревела",
    "больно", "болезненно",
    "напряженно", "напряжение", "напрягло",
    "разочарование", "разочарована", "разочарован",
    "жалко", "жалость",
    "нехорошо", "мерзко"
}

def analyze(text: str):
    t = text.lower().split()
    pos = sum(1 for w in t if w in POSITIVE)
    neg = sum(1 for w in t if w in NEGATIVE)

    if pos + neg == 0:
        return "neutral"
    if pos / (pos + neg) > 0.5:
        return "positive"
    if neg / (pos + neg) > 0.5:
        return "negative"
    return "neutral"


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    clear_memories(message.from_user.id)
    await state.clear()
    await message.answer("Привет! Рад тебя видеть! Расскажи, как прошел твой день?")
    await state.set_state(Diary.waiting_day)


@router.message(
    F.text.lower().in_([
        "привет",
        "hi",
        "hello",
        "расскажу про день",
        "расскажу про свой день",
        "расскажу как прошел мой день",
        "я расскажу про день",
        "я расскажу про свой день",
        "я расскажу как прошел мой день",
        "хай"
    ])
)
async def greet(message: Message, state: FSMContext):
    clear_memories(message.from_user.id)
    await start(message, state)


@router.message(Diary.waiting_day)
async def day_text(message: Message, state: FSMContext):
    text = message.text
    mood = analyze(text)
    user_id = message.from_user.id

    if mood == "positive":
        reply = "Я рад, что твой день прошел хорошо! Спасибо, что поделился этим со мной. 💛"
        save_positive_memory(user_id, text)
    elif mood == "negative":
        reply = "Мне очень жаль, что сегодняшний день был непростым. Ты справишься со всеми трудностями, и я рад, что ты нашел силы поделиться этим со мной. 💙"
    else:
        reply = "Спасибо, что рассказал о своем дне. Давай вместе его немного осмыслим? 🤍"

    await message.answer(reply)
    await message.answer("1️⃣ Какую эмоцию ты чувствовал сегодня ярче всего?")
    await state.set_state(Diary.q1)


@router.message(Diary.q1)
async def q1(message: Message, state: FSMContext):
    await message.answer("2️⃣ Был ли момент, когда ты почувствовал себя уверенно/спокойно/радостно?")
    await state.set_state(Diary.q2)


@router.message(Diary.q2)
async def q2(message: Message, state: FSMContext):
    await message.answer("3️⃣ Что бы ты хотел сделать иначе, если мог бы изменить один момент?")
    await state.set_state(Diary.q3)


@router.message(Diary.q3)
async def q3(message: Message, state: FSMContext):
    await message.answer("Спасибо за честные ответы 💚 Давай немного подышим вместе…")

    await asyncio.sleep(2)
    await message.answer("Вдох… (4 сек)")
    await asyncio.sleep(4)

    await message.answer("Задержка… (4 сек)")
    await asyncio.sleep(4)

    await message.answer("Выдох… (6 сек)")
    await asyncio.sleep(6)

    mem = get_last_positive_memory(message.from_user.id)
    if mem:
        await message.answer(
            f"Помнишь, недавно ты говорил(а):\n\n«{mem}»\n\nПопробуй вновь почувствовать то приятное ощущение 💛"
        )
    else:
        await message.answer("Надеюсь, завтрашний день принесет тебе больше светлых моментов! ✨")

    await asyncio.sleep(1)
    await message.answer("Спокойной ночи 🌙 Ты сегодня отлично поработал над собой 💖")
    await state.clear()


async def main():
    init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())