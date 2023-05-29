import datetime
import requests
import logging
import aiogram.utils.markdown as md
from aiogram.utils import executor
from aiogram.types import ParseMode
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)


API_TOKEN = '6132416977:AAETP87KsVRXIjztDLDdqr9FwNXjTOzYe14'
bot = Bot(token=API_TOKEN)


# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    name = State()
    phone = State()
    master = State()
    procedure = State()
    day = State()
    time = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.name.set()
    await message.reply("Введите ваше имя: ")


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()
    await message.reply("Введите номер телефона: ")


@dp.message_handler(lambda message: message.text, state=Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    # Update state and data
    await Form.next()
    await state.update_data(phone=message.text)

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Татьяна", "Светлана")
    markup.add("Марина", "Виолетта")

    await message.reply("Выберите мастера?", reply_markup=markup)


@dp.message_handler(lambda message: message.text, state=Form.master)
async def process_master(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(master=message.text)

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Покраска волос")
    markup.add("Мэйкап")
    markup.add("Мелирование")

    await message.reply("Выберите услугу?", reply_markup=markup)


@dp.message_handler(lambda message: message.text, state=Form.procedure)
async def process_procedure(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(procedure=message.text)

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Сегодня")
    markup.add("Завтра")
    markup.add("Послезавтра")

    await message.reply("Выберите день: ", reply_markup=markup)


@dp.message_handler(lambda message: message.text, state=Form.day)
async def process_day(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(day=message.text)

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("13:00:00", "14:30:00")
    markup.add("15:00:00", "16:30:00")

    await message.reply("Выберите время: ", reply_markup=markup)
    
    

@dp.message_handler(state=Form.time)
async def process_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = message.text

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()


        day = data['day']
        if day == 'Сегодня':
            day = datetime.date.today()
        elif day == 'Завтра':
            delta = datetime.timedelta(days=1)
            day = datetime.date.today() + delta
        else:
            delta = datetime.timedelta(days=2)
            day = datetime.date.today() + delta
        
        day = day.strftime("%Y-%m-%d")
        time = data['time']
        full_datetime = f'{day} {time}'


    # Create appointment record in DB:
    payload = {
        'client_name': data['name'],
        'client_phone': data['phone'],
        'master': data['master'],
        'service': data['procedure'],
        'datetime': full_datetime,
    }
 
    res = requests.post('http://localhost:8000/api/appointment/', data=payload)
    print(res.text)


    await bot.send_message(
                message.chat.id,
                md.text(
                    md.text('Запись----------->>>'),
                    md.text('Имя', md.bold(data['name'])),
                    md.text('Телефон:', md.code(data['phone'])),
                    md.text('Мастер:', data['master']),
                    md.text('Процедура:', data['procedure']),
                    md.text('День:', day),
                    md.text('Время:', time),
                    md.text('---------------------------'),
                    md.text(md.bold('Успешно добавлена')),
                    sep='\n',
                ),
                reply_markup=markup,
                parse_mode=ParseMode.MARKDOWN,
    )
    # Finish conversation
    await state.finish()
    await cmd_start(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
