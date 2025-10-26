from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Почати", callback_data="continue_form")]
    ])

def next_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Почати", callback_data="next_question")]
    ])

def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Так, підтверджую", callback_data="confirm_sms")]
    ])
