from aiogram import Router, types
from aiogram.types import FSInputFile
from keyboard.inline import start_keyboard

router = Router()

@router.message(lambda message: message.text == "/start")
async def cmd_start(message: types.Message):
    photo = FSInputFile("assets/welcome.jpg")
    await message.answer_photo(
        photo=photo,
        caption="Ласкаво просимо!\n\n" \
        "Цей бот створений для подачі заявок на отримання портативних зарядних станцій та автономних джерел живлення від бренду EcoFlow.\n" \
        "\n" \
        "\n" \
        "Ця ініціатива реалізується в рамках спільної програми АТ «Укренерго» та Товариства Червоного Хреста України за фінансової підтрими Європейского Союзу.\n" \
        "\n" \
        "\n" \
        "Мета програми — надати українцям доступ до альтернативних джерел енергії під час тривалих відключень електропостачання, спричинених російською агресією.\n" \
        "\n" \
        "\n" \
        "Щоб подати заявку на отримання допомоги, натисніть кнопку «Почати».",
        reply_markup=start_keyboard()
    )
