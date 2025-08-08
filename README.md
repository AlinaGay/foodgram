# Foodgram

**Foodgram** — платформа для публикации, поиска и хранения кулинарных рецептов. Пользователи могут добавлять свои блюда, собирать их в избранное, подписываться на любимых авторов и формировать список покупок по ингредиентам.

---

## Демо-версия

[https://foodgram-site.zapto.org](https://foodgram-site.zapto.org)

---

## Функционал

- **Регистрация и аутентификация** (djoser + authtoken)
- **CRUD для рецептов** — публикация, редактирование и удаление рецептов
- **Работа с ингредиентами и тегами** — фильтрация и поиск
- **Добавление рецептов в избранное**
- **Формирование и скачивание списка покупок** по ингредиентам
- **Подписки на других пользователей** и их рецепты
- **Загрузка/изменение аватара**
- **Фильтрация по тегам, авторам, избранному и корзине**
- **Пагинация для всех списков**

---

## Технологии

- Python 3.11+
- Django 5.1
- Django REST Framework
- Django Filters
- Djoser (аутентификация через токены)
- PostgreSQL/SQLite
- Docker, docker-compose
- drf-yasg (автогенерация документации API)

---

## Быстрый старт

### Клонирование репозитория

```bash
git clone https://github.com/yourusername/foodgram.git
cd foodgram
```


## Настройка окружения

### Через Docker Compose (рекомендуется)

1. Скопируйте файл переменных окружения .env (пример ниже)

2. Запустите проект:
```bash
docker compose up -d
```

3. Создайте миграции
```bash
docker compose exec backend python manage.py migrate
```

4. После запуска заполните ингредиенты:
```bash
docker compose exec backend python manage.py import_ingredients
```
5. Создайте суперюзера:
```bash
docker compose exec backend python manage.py createsuperuser
```
6. Добавьте тэги через админку (/admin), предварительно залогинившись в админке (введите данные суперюзера)

### Через Python (локально, без Docker)

1. Перейдите в папку проекта и создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```
2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Проведите миграции и соберите статику:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

4. Заполните ингредиенты:
```bash
python manage.py import_ingredients
```
5. Запустите сервер:
```bash
python manage.py runserver
```
6. Создайте суперюзера:
```bash
python manage.py createsuperuser
```
7. Добавьте тэги через админку (/admin), предварительно залогинившись в админке (введите данные суперюзера)

---

## Аутентификация

Используется djoser + authtoken (API-токены).
Авторизация по email и паролю, получение токена:

- POST /api/auth/token/login/ — получение токена (email, password)
- Токен добавляется в заголовок Authorization: Token <your_token>

---

## Контакты

Автор: [AlinaGay](https://github.com/AlinaGay)
