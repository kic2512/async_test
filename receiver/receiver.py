import asyncio
import logging
import os
from asyncio import BaseEventLoop
from typing import Optional, BinaryIO, Awaitable

import aiohttp
import aiofiles

import async_timeout
import pika

logger = logging.getLogger(__name__)


async def save_file(file_name: str, data: Awaitable[BinaryIO]) -> str:
    """
    Save file to local file system
    :param file_name: file name
    :param data: file binary data
    :return: path to file
    """
    async with aiofiles.open(file_name, 'wb') as f:
        i = 0
        while True:
            chunk = await data.read(1024)
            if not chunk:
                await f.flush()
                logger.info('saved: {}'.format(file_name))
                return os.path.abspath(file_name)
            i += 1
            logger.info('{}: chunk {}'.format(file_name, i))
            await f.write(chunk)


async def download_image(url: str, loop: 'BaseEventLoop', messages_part: int) -> Optional[str]:
    """
    Download image asynchronously by url
    :param url: file url
    :param loop: current event loop
    :param messages_part: number of file part
    :return: Successfully downloaded file url
    """
    logger.info('start download: {}'.format(url))
    try:
        with async_timeout.timeout(5):
            async with aiohttp.ClientSession(loop=loop).get(url) as response:
                if response.status == 200:
                    content = response.content
                    file_name = '{}-'.format(messages_part) + url.split('/')[-1]
                    await save_file(file_name, content)
                    response.close()
                else:
                    logger.info('Bad response for image: {}'.format(url))
                    return None
    except asyncio.TimeoutError:
        logger.info('Cant download image: {}'.format(url))
        return None
    else:
        logger.error('end download: {}'.format(url), exc_info=True)
        return url


async def main(aio_loop: 'BaseEventLoop') -> None:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672))
    channel = connection.channel()
    channel.queue_declare(queue='download_stream', durable=True)
    channel.basic_qos(prefetch_count=1)

    list_urls = []
    n = 0
    while True:
        method_frame, header_frame, body = channel.basic_get(queue='download_stream')
        if not method_frame:
            continue
        elif method_frame.NAME == 'Basic.GetEmpty':
            pass
        else:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            list_urls.append('{}'.format(body.decode("utf-8")))

        if len(list_urls) >= 5:
            n += 1
            tasks = [aio_loop.create_task(download_image(url, aio_loop, n)) for url in list_urls]
            done, pending = await asyncio.wait(tasks, loop=aio_loop, return_when=asyncio.ALL_COMPLETED)

            list_urls = []

            for future in pending:
                logger.info('future was canceled')
                future.cancel()

            for future in done:
                logger.info('future was done')
                logger.info('result: {}'.format(future.result()))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop))
    finally:
        loop.close()
