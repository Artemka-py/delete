import asyncio
from datetime import datetime, timedelta

import aioschedule
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import db

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


@   dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    global status
    id = str(message.from_user.id)
    res = db.fetchall('instructors_instructor', ["telegram_id", "approved", "reg_finish"], f" where telegram_id='{id}'")
    if len(res):
        for re in res:
            if re['reg_finish'] is None and re['approved'] is None:
                await message.reply(
                    "В прошлый раз вы не закончили регистрацию! http://tripwego.ru/instructors/?teleg_id=" + id)
                return
            if re['approved'] is None:
                await message.reply('Вы были зарегистрированны, но ваш статус не подтвержден, пожалуйста обратитесь в '
                                    'поддержку по номеру телефона +7(985)269-46-64')
                return
            elif re['approved'] is False:
                await message.reply('Вас не подтвердили, обратитесть пожалуйста в поддержку +7(985)269-46-64. '
                                    'Возможно оператор запросит ваш индетификационный номер: ' + id + '.')
                return
        await message.reply("Вы уже были зарегистрированы в нашем боте и сайте.")
        return
    await message.reply("Приветствуем нового инсруктора TripWeGo! Для дальнейшего нашего сотрудничества пройдите по "
                        "ссылке и зарегистрируйтесь! http://tripwego.ru/instructors/?teleg_id=" + id)
    db.insert_single_value('instructors_instructor', "telegram_id, created_at, updated_at",
                           f"{id}, '{datetime.now()}', '{datetime.now()}'")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Данный бот предназначен для инструкторов сервиса TripWeGo! В данном боте можно "
                        "зарегистрироваться, после чего получать заявки и зарабатывать бабки)))")


# @dp.message_handler()
# async def echo_message(msg: types.Message):
#     await bot.send_message(msg.from_user.id, str(msg.from_user.id))


async def zayavka():
    global inline_btn_1
    global order_id
    res = db.fetchall("orders_order", ["id", "resort_id", "service_id", "date_time"], """where finish = false and instructor_id IS
    NULL and date_time > now()""")
    all_users = []

    for re in res:
        duplicate = db.fetchall("instructors_fortelegrambot", ["instructors_fortelegrambot.order_id"], f"""where
        instructors_fortelegrambot.order_id = '{re["id"]}'""")
        if len(duplicate): continue
        inline_btn_1 = types.InlineKeyboardButton(f'Принять заявку!', callback_data=f'button {re["id"]}',
                                                  data_id=re["id"])
        # all_users = db.fetchall("instructors_instructor", ["telegram_id"],
        #                         f""" left join instructors_instructor_resorts
        #     on instructors_instructor.id = instructors_instructor_resorts.instructor_id
        #                 left join instructors_instructor_services on instructors_instructor.id =
        #     instructors_instructor_services.instructor_id
        #             where instructors_instructor.approved = true and instructors_instructor.reg_finish = true and
        #     instructors_instructor_resorts.resort_id = {re["resort_id"]} and instructors_instructor_services.service_id = {re[
        #                             "service_id"]}""")
        all_users = db.fetchall("instructors_instructor", ["telegram_id"],
                                f"""

left join instructors_instructor_resorts
            on instructors_instructor.id = instructors_instructor_resorts.instructor_id
                        left join instructors_instructor_services on instructors_instructor.id =
            instructors_instructor_services.instructor_id
    left join instructors_instructor_levels on instructors_instructor.id = instructors_instructor_levels.instructor_id
            left join instructors_level on instructors_instructor_levels.level_id = instructors_level.id
                    where instructors_instructor.approved = true and instructors_instructor.reg_finish = true and
        instructors_instructor_resorts.resort_id = {re["resort_id"]} and 
instructors_instructor_services.service_id = {re["service_id"]} and (select level_num from orders_order
            inner join instructors_level on instructors_level.id = orders_order.level_id
            where orders_order.id = {re["id"]} ) <= level_num
""")

        for user in all_users:
            inline_kb1 = types.InlineKeyboardMarkup().add(inline_btn_1)
            text_order = db.fetchall("orders_order", ["orders_order.date_time", "orders_resort.title",
                                                      "instructors_service.price", "instructors_service.title",
                                                      "instructors_servicecategory.title"],
                                     f"""
                                        inner join orders_messenger on orders_messenger.id = orders_order.messenger_id
                                    inner join instructors_service on orders_order.service_id = instructors_service.id
                                        inner join instructors_servicecategory on instructors_service.category_id = 
                        instructors_servicecategory.id 
                                        inner join orders_resort on orders_order.resort_id = orders_resort.id
                                            where orders_order.id = {re["id"]}
                        """)
            for text in text_order:
                print(text)
                text_date = str(text["orders_order.date_time"])
                print(str(text["orders_order.date_time"]))
                date = datetime.strptime(text_date[0:19], '%Y-%m-%d %H:%M:%S')
                date2 = datetime.strftime(date, '%d.%m.%Y %H:%M')

                res2 = db.fetchall("orders_order", ["telegram_id"], f"""
                                             inner join instructors_instructor ii on ii.id = orders_order.instructor_id
                    where telegram_id = '{user["telegram_id"]}' 
and '[{date - timedelta(hours=2, minutes=30)},  {date + timedelta(hours=2, minutes=30)})'
::tsrange @> date_time::timestamp
                                            """)
                print(res2)
                if len(res2): continue

                msg_id = await bot.send_message(user['telegram_id'], f"""
                Занятие: {text["instructors_servicecategory.title"]}/{text["instructors_service.title"]}.
Место: {text["orders_resort.title"]}.
Время: {date2} 
Цена: {text["instructors_service.price"]}""", reply_markup=inline_kb1)
            db.insert_single_value("instructors_fortelegrambot", "msg_id, order_id, teleg_id",
                                   f"'{str(msg_id.message_id)}', '{str(re['id'])}', '{str(user['telegram_id'])}'")
            print(msg_id.message_id)


def parse_int(data):
    b = data.split()
    c = []
    for i in b:
        if i.isdigit():
            c.append(int(i))
    return c


@dp.callback_query_handler(lambda c: c.data.__contains__('button'))
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = parse_int(callback_query.data)

    print(order_id[0])  # delete
    print(callback_query)

    res = db.fetchall("orders_order", ["instructor_id"], f"  inner join instructors_instructor ii on ii.id = "
                                                         f"orders_order.instructor_id where telegram_id = "
                                                         f"'{callback_query.from_user.id}' and orders_order.id = "
                                                         f"{order_id[0]}")

    print(res)  # delete

    if len(res):
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
        return await bot.send_message(callback_query.from_user.id, 'Извините, но заявку уже забрали!')

    user_order = db.fetchall("orders_order", ["date_time"], f" where id = {order_id[0]}")
    text_date = str(user_order[0]['date_time'])
    date = datetime.strptime(text_date[0:19], '%Y-%m-%d %H:%M:%S')
    res2 = db.fetchall("orders_order", ["telegram_id"], f"""
                                         inner join instructors_instructor ii on ii.id = orders_order.instructor_id
                        where telegram_id = '{callback_query.from_user.id}' 
    and '[{date - timedelta(hours=2, minutes=30)},  {date + timedelta(hours=2, minutes=30)})'
    ::tsrange @> date_time::timestamp
                                                """)
    print(res2)
    if len(res2):
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
        return await bot.send_message(callback_query.from_user.id, 'Извините, но у вас есть заявка на это время в '
                                                                   'пределах +- двух с половиной часов!')

    ids = db.fetchall("instructors_instructor", ["id"], f" where telegram_id = '{callback_query.from_user.id}'")
    for id in ids:
        db.update_single_value("orders_order", "instructor_id", f"{id['id']}", order_id[0])

    await delete_messages(order_id[0])
    text_order = db.fetchall("orders_order", ["orders_order.date_time", "orders_resort.title",
                                              "instructors_service.price", "instructors_service.title",
                                              "instructors_servicecategory.title", "users_customer.fio",
                                              "instructors_level.title", "users_customer.phone_num",
                                              "orders_messenger.title"],
                             f"""
                    inner join orders_messenger on orders_messenger.id = orders_order.messenger_id
                    inner join instructors_service on orders_order.service_id = instructors_service.id
                inner join instructors_servicecategory on instructors_service.category_id =
instructors_servicecategory.id
                inner join orders_resort on orders_order.resort_id = orders_resort.id
                inner join users_customer on orders_order.customer_id = users_customer.id
                inner join instructors_level on orders_order.level_id = instructors_level.id
                        where orders_order.id = {order_id[0]}
    """)
    for text in text_order:
        text_date = str(text["orders_order.date_time"])
        date = datetime.strptime(text_date[0:19], '%Y-%m-%d %H:%M:%S')
        date2 = datetime.strftime(date, '%d.%m.%Y %H:%M')
        await bot.send_message(callback_query.from_user.id, f"""
    Вы приняли заявку №{order_id[0]}!
Занятие: {text["instructors_servicecategory.title"]}/{text["instructors_service.title"]}.
Место: {text["orders_resort.title"]}.
Время: {date2} 
Цена: {text["instructors_service.price"]}
Информация о покупателе:
ФИО: {text["users_customer.fio"]}.
Уровень катания: {text["instructors_level.title"]}.
Номер телефона: {text["users_customer.phone_num"]}.
Связываться через мессенджер: {text["orders_messenger.title"]}.
    """)


async def delete_messages(order_id):
    res = db.fetchall("instructors_fortelegrambot", ["msg_id", "teleg_id"], f" where order_id = '{order_id}'")
    for re in res:
        try:
            await bot.delete_message(chat_id=re["teleg_id"], message_id=re["msg_id"])
        except:
            print("Ошибка в удалении сообщений после принятия заявки!")


async def scheduler():
    aioschedule.every(10).seconds.do(zayavka)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_register(x):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_register)
