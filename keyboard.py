from aiogram import types

inline_btn_1 = types.InlineKeyboardButton('Первая кнопка!', callback_data='button1' + btn_id + 'номер_заявки')
inline_kb1 = types.InlineKeyboardMarkup().add(inline_btn_1)
