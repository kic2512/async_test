from time import sleep

import pika

list_urls = [
        'https://cdn.photographylife.com/wp-content/uploads/2014/02/Sunset-Sunflower.jpg',
        'https://beautyty.org/wp-content/uploads/2019/01/8809240761304_1.jpg',
        'https://beautyty.org/wp-content/uploads/2019/01/8809240761304_2.jpg',
        'https://beautyty.org/wp-content/uploads/2019/01/8809240761304_3.jpg',
        'https://beautyty.org/wp-content/uploads/2019/01/8809240761304_4.jpg',
        'https://beautyty.org/wp-content/uploads/2019/01/8809240761304_44.jpg',
        'https://static.photocdn.pt/images/articles/2018/03/07/articles/2017_8/landscape_photography_lighting.jpg',
        'https://www.thesun.co.uk/wp-content/uploads/2019/07/NINTCHDBPICT000506209482.jpg'
    ]

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672))
    channel = connection.channel()
    channel.queue_declare(queue='download_stream', durable=True)
    try:
        while True:
            for url in list_urls:
                channel.basic_publish(exchange='', routing_key='download_stream', body=bytes(url, 'utf8'))
                print('urls pack was send')
            sleep(20)
    finally:
        connection.close()

