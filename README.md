# Yatube
## Социальная сеть для публикации личных дневников
### Описание возможностей
Регистрация реализована с верификацией данных, сменой и восстановлением пароля через почту. На страницах используется пагинация и кэширование. Реализованы возможности добавлять изображение к своим постам, а также подписываться на других авторов и оставлять комментарии к постам. Написаны тесты, проверяющие работу сервиса.
### Технологии
Python 3.7,
Django 2.2.16
### Запуск проекта в dev-режиме
- Установите виртуальное окружение
```
python -m venv venv
```
- Активируйте виртуальное окружение
```
source venv/Scripts/activate
```
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
- В папке с файлом manage.py выполните миграции:
```
python manage.py migrate
```
- В папке с файлом manage.py выполните команду:
```
python manage.py runserver
```
- В своем враузере введите адрес:
```
http://127.0.0.1:8000/
```
### Автор
***VanZep***
