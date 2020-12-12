import asyncio
import aioschedule
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from config import TOKEN
# import keyboard as kb

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет это заглушка!")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Напиши мне что-нибудь, и я отпрпавлю этот текст тебе в ответ!")


@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, str(msg.from_user.id))


test = ["844543391"]


# , "355649830"


async def zayavka():
    for user_telega_id in test:
# тут попытки передать данные в краце мне нужно передать message_id и там данные заявки из бд пока все в черновом варианте
        inline_btn_1 = types.InlineKeyboardButton('Первая кнопка!', callback_data='button1 ' + str(test2.message_id))
        inline_kb1 = types.InlineKeyboardMarkup().add(inline_btn_1)
        test2 = await bot.send_message(user_telega_id, 'Привет это заявка', reply_markup=inline_kb1)
        print(test2.message_id)

# тут обработка кнопки ну думаю ты знаешь
@dp.callback_query_handler(lambda c: c.data.__contains__('button1'))
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    print(callback_query.data)
    await bot.send_message(callback_query.from_user.id, 'Нажата первая кнопка!')


async def scheduler():
    aioschedule.every(5).seconds.do(zayavka)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_register(x):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_register)
