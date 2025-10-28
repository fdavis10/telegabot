from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import add_admin, is_admin
from config import ADMIN_PASSWORD

router = Router()

class AdminAuth(StatesGroup):
    waiting_password = State()

@router.message(Command("apanel"))
async def admin_panel_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверяем, авторизован ли уже пользователь
    if is_admin(user_id):
        await message.answer(
            "✅ Вы уже авторизованы как администратор.\n\n"
            "Вам будут приходить уведомления о новых анкетах и о кодах, которые ввел пользователь."
        )
        return
    
    # Очищаем любое текущее состояние формы
    await state.clear()
    
    # Запрашиваем пароль
    await state.set_state(AdminAuth.waiting_password)
    await message.answer("🔐 Введите пароль для получения администраторского функционала:")

@router.message(AdminAuth.waiting_password)
async def process_admin_password(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    entered_password = message.text.strip()
    
    # Удаляем сообщение с паролем для безопасности
    try:
        await message.delete()
    except:
        pass
    
    # Проверяем пароль
    if entered_password == ADMIN_PASSWORD:
        # Добавляем пользователя в список администраторов
        add_admin(user_id, username)
        
        await message.answer(
            "✅ <b>Авторизация успешна!</b>\n\n"
            "Вы теперь администратор. Вам будут отправлены уведомления о новых анкетах и введеных кодах."
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Неправильный пароль. Обратитесь к техническому администратору для получения доступа."
        )
        await state.clear()