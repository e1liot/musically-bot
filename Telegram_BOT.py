from fuzzywuzzy import fuzz
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.callback_data import CallbackData
import logging, config, random, psycopg2

logging.basicConfig(level=logging.INFO)

BOT = Bot(token=config.TOKEN)
dp = Dispatcher(BOT)

conn = psycopg2.connect(
   database="d5n5h5pc213re6", user="maqdmqbshrzaxg", 
   password="3dc6278794f20f0f306b06c4a0fde8ec8b42e86a9c932319245d86dc65a797ae", host="ec2-54-246-67-245.eu-west-1.compute.amazonaws.com", port="5432"
   )
   
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS music_db(
      Song TEXT,
      File_id TEXT
)''')

@dp.message_handler(commands=['start'])
async def start_function(message: types.Message):
   if message.chat.last_name != None:
      await message.answer("Glad to see you, %s %s!" % (message.chat.first_name, message.chat.last_name))
      await message.answer_animation(animation=random.choice(config.STICKER_ID)) 
   else:
      await message.answer("Glad to see you, %s!" % (message.chat.first_name))
      await message.answer_animation(animation=random.choice(config.STICKER_ID))

@dp.message_handler(content_types=['audio'])
async def insert_audio_into_db(message):
   c.execute(f'''INSERT INTO music_db VALUES ($${message.audio.performer + " - " + message.audio.title}$$, $${message.audio.file_id}$$)''')
   conn.commit()

index_message = 0 

@dp.message_handler(content_types=['text']) 
async def message_with_text(message):
   await result_searching_in_database(message.text, message)

async def result_searching_in_database(message_text, message=None):
   level = 1 
   result_searching = await search_in_database(message_text)
   if result_searching != None:
      await get_keyboard(level, result_searching, message)

async def delete_the_previous_table(message):
   global index_message
   try:
      await BOT.delete_message(message.chat.id, message_id=index_message + 1) # удаление сообщения от inline клавиатуры
      await BOT.edit_message_reply_markup(message.chat.id, message_id=index_message + 1, reply_markup=None) # удаление inline клавиатуры
   except:
      pass

async def get_keyboard(level, result_searching, message=None):
   keyboard = await make_keyboard(result_searching, level)
   await send_message(level, keyboard, message)

async def send_message(level, keyboard, message=None):
   global index_message
   await delete_the_previous_table(message)
   await BOT.send_animation(chat_id = message.chat.id, animation=random.choice(config.GIF_ID), reply_markup=keyboard)
   index_message = message.message_id

async def search_in_database(message):
   global dictionary 
   dictionary = {} 
   message_text = message.split()
   c.execute('''SELECT song FROM music_db''')
   for song_name in c.fetchall(): 
      if fuzz.WRatio(message, song_name) >= 90 or (fuzz.WRatio(message_text[0], song_name[0].split()[0]) >= 90 
      and fuzz.WRatio(message_text[len(message_text) - 1], song_name[0].split()[len(song_name[0].split()) - 1]) >= 90):
         c.execute(f'''SELECT file_id FROM music_db WHERE song=$${song_name[0]}$$''')
         for file_id in c.fetchone(): 
            if len(dictionary) < 25: 
               dictionary[song_name[0]] = file_id 
            else:
              break

   if bool(dictionary) == True: # проверка на заполняемость словаря
      return dictionary
   else: 
      pass

async def make_keyboard(dictionary, level):
   index = 0 
   keyboard = types.InlineKeyboardMarkup()
   for i in range(level * 5 - 5, level * 5): 
      try:
         keyboard.add(types.InlineKeyboardButton(text=list(dictionary.keys())[i], 
         callback_data=await make_callback_data(level=level, number=index))) 
      except IndexError:
         if level == 1:
            return keyboard
         else:
            keyboard.add(types.InlineKeyboardButton(text="<<", callback_data=await make_callback_data(level=level, number="back")))
            return keyboard
      index += 1 
   keyboard.add(types.InlineKeyboardButton(text="<<", callback_data=await make_callback_data(level=level, number="back")), 
   types.InlineKeyboardButton(text=">>", callback_data=await make_callback_data(level=level, number="next")))
   return keyboard

callback = CallbackData("music", "level", "number")

async def make_callback_data(level, number):
   return callback.new(level=level, number=number)

@dp.callback_query_handler(callback.filter())
async def inline_callback(call:types.CallbackQuery, callback_data:dict):
   level = int(callback_data.get("level"))
   if callback_data.get("number") == "0":
      await BOT.send_audio(call.message.chat.id, audio=list(dictionary.values())[level * 5 - 5])
   elif callback_data.get("number") == "1":
      await BOT.send_audio(call.message.chat.id, audio=list(dictionary.values())[level * 5 - 4])
   elif callback_data.get("number") == "2":
      await BOT.send_audio(call.message.chat.id, audio=list(dictionary.values())[level * 5 - 3])
   elif callback_data.get("number") == "3":
      await BOT.send_audio(call.message.chat.id, audio=list(dictionary.values())[level * 5 - 2])
   elif callback_data.get("number") == "4":
      await BOT.send_audio(call.message.chat.id, audio=list(dictionary.values())[level * 5 - 1])
   elif callback_data.get("number") == "next":
      if int(callback_data.get("level")) != 5:
         keyboard = await make_keyboard(dictionary, level=int(callback_data.get("level")) + 1)   
         await BOT.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
      else:
         pass
   elif callback_data.get("number") == "back":
      if int(callback_data.get("level")) != 1:
         keyboard = await make_keyboard(dictionary, level=int(callback_data.get("level")) - 1)
         await BOT.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
      else:
         pass

if __name__ == "__main__":
   executor.start_polling(dp, skip_updates=True)