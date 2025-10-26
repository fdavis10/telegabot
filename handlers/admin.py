from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import add_admin, is_admin
from config import ADMIN_PASSWORD

router = Router()

class AdminAuth(StatesGroup):
    waiting_password = State()

@router.message(lambda message: message.text == "/apanel")
async def admin_panel_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверяем, авторизован ли уже пользователь
    if is_admin(user_id):
        await message.answer(
            "✅ Ви вже авторизовані як адміністратор.\n\n"
            "Вам будуть приходити сповіщення про нові анкети."
        )
        return
    
    # Запрашиваем пароль
    await state.set_state(AdminAuth.waiting_password)
    await message.answer("🔐 Введіть пароль для доступу до адміністраторської панелі:")

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
            "✅ <b>Авторизація успішна!</b>\n\n"
            "Ви тепер адміністратор. Вам будуть приходити сповіщення про нові анкети з можливістю підтвердження або відхилення кодів."
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Невірний пароль. Спробуйте ще раз або зверніться до головного адміністратора."
        )
        await state.clear()