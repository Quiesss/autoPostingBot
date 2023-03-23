import asyncio
import os
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Union

from aiogram import Bot, Dispatcher, F, types, BaseMiddleware

from aiogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    TelegramObject,
    FSInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from conf import API_KEY, CHANNEL

CHAT_ID_TO_SEND = CHANNEL
DEFAULT_DELAY = 0.6


async def main():
    class MediaGroupMiddleware(BaseMiddleware):
        ALBUM_DATA: Dict[str, List[Message]] = {}

        def __init__(self, delay: Union[int, float] = DEFAULT_DELAY):
            self.delay = delay

        async def __call__(
                self,
                handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                event: Message,
                data: Dict[str, Any],
        ) -> Any:
            if not event.media_group_id:
                return await handler(event, data)

            try:
                self.ALBUM_DATA[event.media_group_id].append(event)
                return  # Don't propagate the event
            except KeyError:
                self.ALBUM_DATA[event.media_group_id] = [event]
                await asyncio.sleep(self.delay)
                data["album"] = self.ALBUM_DATA.pop(event.media_group_id)

            return await handler(event, data)

    bot = Bot(API_KEY, parse_mode="HTML")
    dp = Dispatcher()
    dp.message.middleware(MediaGroupMiddleware())

    @dp.message(F.media_group_id)
    async def handle_albums(message: Message, album: List[Message]):
        """This handler will receive a complete album of any type."""
        group_elements = []
        for element in album:
            print(element.caption)
            caption_kwargs = {"caption": element.caption, "caption_entities": element.caption_entities}
            if element.photo:
                input_media = InputMediaPhoto(media=element.photo[-1].file_id, **caption_kwargs, parse_mode=None)
            elif element.video:
                input_media = InputMediaVideo(media=element.video.file_id, **caption_kwargs, parse_mode=None)
            elif element.document:
                input_media = InputMediaDocument(media=element.document.file_id, **caption_kwargs, parse_mode=None)
            elif element.audio:
                input_media = InputMediaAudio(media=element.audio.file_id, **caption_kwargs)
            else:
                return message.answer("This media type isn't supported!")

            group_elements.append(input_media)
        await message.reply('Отправил альбом в канал, ожидайте')

        return await bot.send_media_group(CHAT_ID_TO_SEND, media=group_elements)

    @dp.message(F.voice)
    async def send_audio(message: Message):
        message_split = message.caption.split('#') if message.caption else None
        if message_split and len(message_split) == 2:
            builder = InlineKeyboardBuilder()
            button_split = message_split[1].split('\n')
            for button in button_split:
                parse_inline_button = button.split('|')
                if len(parse_inline_button) == 2:
                    builder.row(types.InlineKeyboardButton(
                        text=parse_inline_button[0].strip(),
                        url=parse_inline_button[1].strip()
                    ))
            await bot.send_voice(
                CHANNEL,
                voice=message.voice.file_id,
                reply_markup=builder.as_markup(),
                caption=(message_split[0])
            )
        else:
            await bot.send_voice(
                CHANNEL,
                voice=message.voice.file_id,
                caption=(message.caption if message.caption else '')
            )

    @dp.message(F.video)
    async def send_video_note(message: Message):
        message_split = message.caption.split('%') if message.caption else None
        builder = InlineKeyboardBuilder()
        if message_split and len(message_split) == 2:
            button_split = message_split[1].split('\n')
            for button in button_split:
                parse_inline_button = button.split('|')
                if len(parse_inline_button) == 2:
                    builder.row(types.InlineKeyboardButton(
                        text=parse_inline_button[0].strip(),
                        url=parse_inline_button[1].strip()
                    ))
        if message.caption and message.caption.__contains__('/v'):
            caption = message_split[0].replace('/v', '')
            await bot.send_video(
                CHANNEL,
                video=message.video.file_id,
                caption=caption,
                reply_markup=builder.as_markup()
            )
            await message.reply('Отправил видео в канал')
        else:
            file = await bot.get_file(message.video.file_id)
            uniq_name = str(uuid.uuid4()) + '.mp4'
            await bot.download_file(file.file_path, uniq_name)
            await bot.send_video_note(
                CHANNEL,
                video_note=FSInputFile(uniq_name),
                reply_markup=builder.as_markup()
            )
            await message.reply('Отправил кружок в канал')
            os.remove(uniq_name)

    @dp.message(F.text)
    async def send_text(message: Message):
        message_split = message.text.split('%') if message.text else None
        if message_split and len(message_split) == 2:

            builder = InlineKeyboardBuilder()
            button_split = message_split[1].split('\n')
            for button in button_split:
                parse_inline_button = button.split('|')
                if len(parse_inline_button) == 2:
                    builder.row(types.InlineKeyboardButton(
                        text=parse_inline_button[0].strip(),
                        url=parse_inline_button[1].strip()
                    ))
            await bot.send_message(CHANNEL, message_split[0], entities=message.entities,
                                   reply_markup=builder.as_markup())
        else:
            await bot.send_message(CHANNEL, message.text, entities=message.entities)
        await message.reply('Отправил пост в канал')

    @dp.message(F.photo)
    async def send_photo(message: Message):
        message_split = message.caption.split('%') if message.caption else None
        if message_split and len(message_split) == 2:
            builder = InlineKeyboardBuilder()
            button_split = message_split[1].split('\n')
            for button in button_split:
                parse_inline_button = button.split('|')
                if len(parse_inline_button) == 2:
                    builder.row(types.InlineKeyboardButton(
                        text=parse_inline_button[0].strip(),
                        url=parse_inline_button[1].strip()
                    ))
            await bot.send_photo(CHANNEL, photo=message.photo[-1].file_id, caption=message_split[0],
                                 reply_markup=builder.as_markup())
        else:
            await bot.send_photo(CHANNEL, photo=message.photo[-1].file_id, caption=message.caption)
        await message.reply('Отправил фото в канал')

    @dp.message(F.sticker)
    async def send_sticker(message: Message):
        await bot.send_sticker(CHANNEL, sticker=message.sticker.file_id)
        await message.reply('Отправил стикер в канал')

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
