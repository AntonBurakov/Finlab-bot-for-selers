from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Каталог')],
                                     [KeyboardButton(text='Корзина')],
                                     [KeyboardButton(text='Контакты'), KeyboardButton(text='О нас')]],
                                     resize_keyboard=True,
                                     input_field_placeholder='Выберите Пункт меню')

catalog = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='джинсы', callback_data='jeans')],
                                                [InlineKeyboardButton(text='майки', callback_data='shirts')],
                                                [InlineKeyboardButton(text='трусы', callback_data='pants')]])

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер', 
                                                           request_contact=True)]],
                                                           resize_keyboard=True)