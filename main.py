import asyncio
import os
import uuid

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import FSInputFile, input_file

from aiogram.types import (
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from conf import API_KEY, CHANNEL

CHAT_ID_TO_SEND = CHANNEL


async def main():
    bot = Bot(API_KEY, parse_mode="HTML")
    dp = Dispatcher()

    @dp.message(F.video)
    async def send_video_note(message: Message):
        builder = InlineKeyboardBuilder()
        if message.caption is not None:
            inline = message.caption.split('|')
            if len(inline) == 2:
                builder.row(types.InlineKeyboardButton(
                    text=inline[0].strip(),
                    url=inline[1].strip()
                ))
        file = await bot.get_file(message.video.file_id)
        uniq_name = str(uuid.uuid4()) + '.mp4'
        await bot.download_file(file.file_path, uniq_name)
        await bot.send_video_note(
            CHANNEL,
            video_note=FSInputFile(uniq_name),
            reply_markup=builder.as_markup()
        )
        await message.reply('Отправил кружок в чат')
        os.remove(uniq_name)

    @dp.message(F.text)
    async def send_video_note(message: Message):
        message_split = message.text.split('%')
        if len(message_split) == 2:

            builder = InlineKeyboardBuilder()
            button_split = message_split[1].split('\n')
            for button in button_split:
                parse_inline_button = button.split('|')
                print(parse_inline_button)
                if len(parse_inline_button) == 2:
                    builder.row(types.InlineKeyboardButton(
                        text=parse_inline_button[0].strip(),
                        url=parse_inline_button[1].strip()
                    ))
            await bot.send_message(CHANNEL, message_split[0], entities=message.entities, reply_markup=builder.as_markup())
        else:
            await bot.send_message(CHANNEL, message.text, entities=message.entities)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
