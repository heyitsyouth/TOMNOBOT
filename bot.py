import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Папка для сохранения скриншотов
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Простой список участников розыгрыша (можно сохранять в JSON)
PARTICIPANTS_FILE = "participants.txt"
if not os.path.exists(PARTICIPANTS_FILE):
    open(PARTICIPANTS_FILE, 'w').close()

# Состояния
class PresaveState(StatesGroup):
    waiting_screenshot = State()

# Клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ сделать пресейв и получить награды")]],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "приветы! ты на пути к крутым призам за то, что ты крутой, а еще в честь EP «ТОМНО».\n\n"
        "🎁 за это получишь два полных трека и участвуешь в розыгрыше 1000 рубликов",
        reply_markup=main_kb
    )

@dp.message(F.text == "✅ сделать пресейв и получить награды")
async def ask_screenshot(message: types.Message, state: FSMContext):
    await state.set_state(PresaveState.waiting_screenshot)
    await message.answer(
		"1️⃣ сделай пресейв по ссылке band.link/tomno (нужно отключить VPN!)\n"
		"2️⃣ как сделал:а, отправь скриншот, где видно, что пресейвы есть\n\n"
		"жду скриншот следующим соо: после него ты автоматом получишь треки и будешь участвовать в розыгрыше!",
		reply_markup=types.ReplyKeyboardRemove()
	)

@dp.message(PresaveState.waiting_screenshot, F.photo)
async def save_screenshot(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    # Скачиваем фото
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_extension = file.file_path.split('.')[-1] if '.' in file.file_path else 'jpg'
    file_name = f"{user_id}_{int(message.date.timestamp())}.{file_extension}"
    file_path = os.path.join(SCREENSHOT_DIR, file_name)
    await bot.download_file(file.file_path, file_path)

    # Сохраняем участника в список для розыгрыша
    with open(PARTICIPANTS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{user_id}|{message.from_user.full_name}|{message.from_user.username}|{file_name}\n")

    # Отправляем треки (они должны лежать в папке бота)
    track1 = FSInputFile("для меня беспредел — sunday sunrise.mp3")
    track2 = FSInputFile("солнце пахнет зимой — sunday sunrise.mp3")
    await message.answer_audio(track1, caption="сексуальный трек один")
    await message.answer_audio(track2, caption="грустный сексуальный трек два")
    await message.answer(
        "треки твои! ты также участвуешь в розыгрыше 1000₽\n"
        "результаты объявим 15 мая в тгешке sunday sunrise\n"
        "спасибо за поддержку EP «ТОМНО»!!! целую !!"
    )
    await state.clear()

@dp.message(PresaveState.waiting_screenshot)
async def wrong_input(message: types.Message):
    await message.answer("пожалуйста, отправь именно скриншот (фото). если не можешь – напиши мне в лс @heyitsyouthh.")

# Админская команда для просмотра участников (доступ только для вас)
ADMIN_ID = 513528979  # замени на свой Telegram ID
@dp.message(Command("participants"))
async def show_participants(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("нет прав ))")
        return
    with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        await message.answer("пока нет участников")
        return

    # Отправим общее количество
    await message.answer(f"📋 Всего участников: {len(lines)}")

    # Отправим каждого участника с его скриншотом
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) < 4:
            continue
        user_id, full_name, username, screenshot_filename = parts[0], parts[1], parts[2], parts[3]
        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)
        caption = (
            f"👤 {full_name}\n"
            f"🆔 @{username}\n"
            f"📸 {screenshot_filename}"
        )
        if os.path.exists(screenshot_path):
            photo = FSInputFile(screenshot_path)
            await message.answer_photo(photo, caption=caption)
        else:
            await message.answer(f"{caption}\n⚠️ Файл скриншота не найден")
        # Небольшая пауза, чтобы не спамить слишком быстро
        await asyncio.sleep(0.5)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
