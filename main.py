import json

import requests

from datetime import datetime


class VkUser:
    # Класс собирает информацию о фото в соц.сети ВКонтакте по id пользователя и сохраняет в json-файл
    url = 'https://api.vk.com/method/'

    def __init__(self, version='5.130'):
        # Инициализация экземпляра класса
        self.token = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
        self.version = version
        self.params = {
            'access_token': self.token,
            'v': self.version
        }

    def get_numbers_of_photo(self):
        # Метод запрашивает у пользователя количество скачиваемых фотографий
        while True:
            try:
                count_photo = input(f'Сколько фотографий Вы хотите скачать (по-умолчанию 5 штук, '
                                        f'максимальное количество 1000 штук)?\n')
                if count_photo == '':
                    count_photo = 5
                count_photo = int(count_photo)
            except ValueError:
                print(f'Ошибка! Неверный ввод!\n')
            else:
                break
        return count_photo

    def get_vk_user_id(self):
        # метод принимает идентификатор (user_id) или короткое имя (screen_name) пользователя и возвращает
        # его id для дальнейшей обработки
        user_url = self.url + 'users.get'
        user_id = input(f'Введите короткое имя или id пользователя социальной сети "ВКонтакте":\n')
        user_params = {
            'user_ids': user_id,
        }
        res = requests.get(user_url, params={**self.params, **user_params})
        vk_user_id = res.json()['response'][0]['id']
        return vk_user_id

    def get_photos(self):
        # метод сохраняет в json-файл служебную информацию о фото, для последующего использования этой
        # информации во время загрузки фото в Яндекс.Диск. Также другой json-файл сохраняется на жесткий диск
        # и содержит информацию о фото в требуемом по заданию виде
        photos_url = self.url + 'photos.get'
        user_id = self.get_vk_user_id()
        count_photo = self.get_numbers_of_photo()
        photos_params = {
            'count': count_photo,
            'user_id': user_id,
            'photo_sizes': '1',
            'album_id': 'profile',
            'extended': '1'
        }
        res = requests.get(photos_url, params={**self.params, **photos_params})
        photos = res.json()['response']['items']

        json_data_file = []
        json_data_upload_yadisc = []

        # итерируем фотографии
        for photo in photos:

            file_path = 'vk_photo.json'

            # создаем на жестком диске json-файл с информацией о фото
            with open(file_path, 'w') as f:
                sizes = photo['sizes']
                max_size_list = list()

                # запоминаем кол-во лайков текущего фото
                photo_likes = photo['likes']['count']

                # запоминаем дату создания текущего фото (преобразуем дату/время из формата timestamp unix)
                photo_date = datetime.fromtimestamp(int(photo['date'])).strftime('%Y.%m.%d_%H-%M-%S')

                # итерируем размеры фото внутри одной фотографии
                for size in sizes:
                    if size['width'] >= size['height']:
                        max_size_list.append(size['width'])
                    else:
                        max_size_list.append(size['height'])
                    max_size_photo = max(max_size_list)
                if size['width'] == max_size_photo or size['height'] == max_size_photo:
                    temp_dict = {}
                    temp_name = str(photo_likes) + '.jpg'
                    temp_dict['filename'] = temp_name

                    # сохраняем информацию о фото в json-файл на жестком диске в требуемом по заданию виде
                    for name in json_data_file:
                        if temp_name in name.values():
                            temp_dict['filename'] = str(photo_likes) + '_' + str(photo_date) + '.jpg'
                        else:
                            temp_dict['filename'] = temp_name
                    temp_dict['size'] = size['type']
                    json_data_file.append(temp_dict)

                    # заполняем json-файл для загрузки фото в Яндекс.Диск
                    temp_dict_upload = temp_dict.copy()
                    temp_dict_upload['url'] = size['url']
                    temp_dict_upload['user_id'] = user_id
                    json_data_upload_yadisc.append(temp_dict_upload)

                json.dump(json_data_file, f, ensure_ascii=False, indent=2)
        return json_data_upload_yadisc


class VkBackupPhotos:
    # Класс загружает фото из ВКонтакте на жесткий диск, а затем в Яндекс.Диск
    def __init__(self):
        self.token = input(f'\nВведите токен пользователя Яндекс.Диск:\n')

    def get_headers(self):
        # метод возвращает заголовки (headers) для http-запросов
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def _get_upload_link(self, disk_file_path):
        # метод получает ссылку для загрузки файла в Яндекс.Диск
        # disk_file_path - путь внутри Яндекс.Диска
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {'path': disk_file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def create_folder_yadisc(self):
        # метод создает папку в Яндекс.Диск
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        folder_name = 'New_photos'
        params = {'path': folder_name, 'overwrite': 'true'}
        response = requests.put(upload_url, headers=headers, params=params)
        response_info = requests.get(upload_url, headers=headers, params=params)
        message = f'Папка "{folder_name}" создана в Вашем Яндекс.Диске.\n'
        return print(message), response.json(), response_info.json()

    def upload(self, source_json):
        print(f'Найдено {len(source_json)} фотографий\n')

        # создаем папку VK_Photos в Яндекс.Диск
        self.create_folder_yadisc()

        count = 1
        try:
            for photo in source_json:
                # сохраняем фото на жесткий диск
                file_path = 'photos\\' + str(photo['filename'])
                with open(file_path, 'wb') as f:
                    f.write(requests.get(photo['url']).content)

                # путь к папке VK_Photos в Яндекс.Диск
                yadisc_file_path = 'New_photos/' + str(photo['filename'])

                # получаем ссылку для загрузки в Яндекс.Диск
                href = self._get_upload_link(disk_file_path=yadisc_file_path).get('href', '')

                # логирование процесса загрузки
                print(f'Загружено фотографий ... {count} из {len(source_json)}')

                # загружаем фото в Яндекс.Диск
                requests.put(href, data=open(file_path, 'rb'))
                count += 1
        except FileNotFoundError:
            message = f'\nВо время загрузки произошла ошибка! Не найден файл!'
        else:
            message = f'\nФотографии успешно загружены в Ваш Яндекс.Диск!'
        return print(message)


if __name__ == '__main__':
    vk_client = VkUser()
    uploader = VkBackupPhotos()
    uploader.upload(vk_client.get_photos())
