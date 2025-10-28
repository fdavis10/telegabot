from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    full_name = State()
    age = State()
    city = State()
    phone = State()
    email = State()
    document_photo = State()
    waiting_code = State()  