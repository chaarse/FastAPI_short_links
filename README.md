# API-сервис сокращения ссылок
Сервис позволяет пользователям сокращать длинные ссылки, получать их аналитику и управлять ими. Пользователь вводит длинный URL, сервис генерирует для него короткую ссылку, которую можно использовать для быстрого доступа.

Swagger UI: https://fastapi-short-links.onrender.com/docs 


## Описание API
Изменение и удаление ссылки доступно только зарегистрированным пользователям, *GET / POST* - всем.  
Все параметры запросов передаются через удобные формы, чтобы пользователь не вставлял значения в JSON.


### Базовые возможности без регистрации
#### 1. Создание короткой ссылки `POST /links/shorten` 
**Параметры запроса**:  
* *original_url* - оригинальный URL
* *custom_alias* (optional) - уникальный alias, для создания кастомных ссылок
* *expires_at* (optional) - указание времени жизни ссылки в формате даты с точностью до минуты (2025-03-22T13:56:19.685Z)

**Ответ**:
```json
{
    "id": 1,
    "original_url": "http://wiki.cs.hse.ru/%D0%BC%D0%B0%D1%82%D0%B5%D0%BC%D0%B0%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9_%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7_1_2024/25_(%D0%BF%D0%B8%D0%BB%D0%BE%D1%82%D0%BD%D1%8B%D0%B9_%D0%BF%D0%BE%D1%82%D0%BE%D0%BA)",
    "short_code": "math_fcs",
    "created_at": "2025-03-22T14:08:07.703389",
    "expires_at": "2025-04-20T07:26:00.991000Z",
    "user_id": null,
    "click_count": 0,
    "short_url": "http://127.0.0.1:8000/links/math_fcs"
}
```
---


#### 2. Перенапрвление на оригинальный URL `GET /links/{short_code}`
**Параметры запроса**:  
* *short_code* - alias ссылки

**Ответ**:

![изображение](https://github.com/user-attachments/assets/231259ae-f39f-4d61-ac91-701824949c1a)
---


#### 3. Статистика по ссылке `GET /links/{short_code}/stats`  
Получаем оригинальный URL, дату создания, количество переходов, дату окончания действия ссылки.  
**Параметры запроса**:  
* *short_code* - alias ссылки

**Ответ**:
```json
{
    "original_url": "http://wiki.cs.hse.ru/%D0%BC%D0%B0%D1%82%D0%B5%D0%BC%D0%B0%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9_%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7_1_2024/25_(%D0%BF%D0%B8%D0%BB%D0%BE%D1%82%D0%BD%D1%8B%D0%B9_%D0%BF%D0%BE%D1%82%D0%BE%D0%BA)",
    "created_at": "2025-03-22T14:08:07.703389",
    "click_count": 3,
    "last_used_at": "2025-03-22T14:08:07.703389"
}
```
---


#### 4. Поиск ссылки по оригинальному URL `GET /links/search?original_url={url}`
**Параметры запроса**:
* *original_url* - оригинальный URL

**Ответ**:
```json
{
    "id": 1,
    "original_url": "http://wiki.cs.hse.ru/%D0%BC%D0%B0%D1%82%D0%B5%D0%BC%D0%B0%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9_%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7_1_2024/25_(%D0%BF%D0%B8%D0%BB%D0%BE%D1%82%D0%BD%D1%8B%D0%B9_%D0%BF%D0%BE%D1%82%D0%BE%D0%BA)",
    "short_code": "math_fcs",
    "created_at": "2025-03-22T14:08:07.703389",
    "expires_at": "2025-04-20T07:26:00.991000",
    "user_id": null,
    "click_count": 3,
    "short_url": "http://127.0.0.1:8000/links/math_fcs"
}
```
---


### Дополнительные возможности для авторизированных пользователей
#### Регистрация пользователя `POST /auth/register`
**Параметры запроса**:
* *username* - логин
* *password* - пароль

**Ответ**:
```json
{
    "id": 1,
    "username": "user123"
}
```
---


#### Авторизация пользователя `POST /auth/token`
**Параметры запроса**:
* *username* - логин
* *password* - пароль

**Ответ**:
```json
{
    "access_token": "e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446",
    "token_type": "bearer"
}
```
---


#### 5. Обновление URL `PUT /links/{short_code}`  
**Параметры запроса**:
* *short_code* - alias ссылки
* *new_url* - новый URL, к которому привязываем раннее созданный alias

**Ответ**:
```json
{
    "id": 1,
    "original_url": "http://wiki.cs.hse.ru/%D0%BB%D0%B8%D0%BD%D0%B5%D0%B9%D0%BD%D0%B0%D1%8F_%D0%B0%D0%BB%D0%B3%D0%B5%D0%B1%D1%80%D0%B0_%D0%B8_%D0%B3%D0%B5%D0%BE%D0%BC%D0%B5%D1%82%D1%80%D0%B8%D1%8F_%D0%BD%D0%B0_%D0%BF%D0%BC%D0%B8_2024/2025_(%D0%BE%D1%81%D0%BD%D0%BE%D0%B2%D0%BD%D0%BE%D0%B9_%D0%BF%D0%BE%D1%82%D0%BE%D0%BA)",
    "short_code": "math_fcs",
    "created_at": "2025-03-22T14:08:07.703389",
    "expires_at": "2025-04-20T07:26:00.991000",
    "user_id": 1,
    "click_count": 3,
    "short_url": "http://127.0.0.1:8000/links/math_fcs"
}
```
---


#### 6. Удаляение связи `DELETE /links/{short_code}`  
**Параметры запроса**:
* *short_code* - alias ссылки

**Ответ**:  
```json
{
    "ok": true
}
```
---


## Описание базы данных
База данных использует SQLite и создана с помощью SQLAlchemy. Она состоит из двух таблиц: `users` и `links`.

### Таблица `users`
|Поле|Тип данных|Описание|
|-------------------|-------------------|-------------------|
|`id`|`INTEGER`|Уникальный идентификатор пользователя (первичный ключ)|
|`username`|`VARCHAR`|Уникальное имя пользователя|
|`password_hash`|`VARCHAR`|Хэш пароля пользователя|



### Таблица `links`
|Поле|Тип данных|Описание|
|-------------------|-------------------|-------------------|
|`id`|`INTEGER`|Уникальный идентификатор ссылки (первичный ключ)|
|`original_url`|`VARCHAR`|Оригинальный URL, который был сокращен|
|`short_code`|`VARCHAR`|Уникальный короткий код для сокращенной ссылки|
|`created_at`|`DATETIME`|Дата и время создания ссылки|
|`expires_at`|`DATETIME`|Дата и время истечения срока действия ссылки (по умолчанию — 30 дней с момента создания)|
|`user_id`|`INTEGER`|Идентификатор пользователя, создавшего ссылку (может быть NULL, если ссылка создана анонимно)|
|`click_count`|`INTEGER`|Количество переходов по ссылке (по умолчанию — 0)|
|`last_used_at`|`DATETIME`|Дата и время последнего использования ссылки|


## Инструкцию по запуску
#### Создание репозитория
```
git init
git remote add origin git@github.com:<никнейм>/<названиеРепозитория>.git
.... add gitignore
git add .
git commit -m "..."
git branch -M main
git push -u origin main
```


#### Подготовка сервера
git
```
sudo apt-get update
sudo apt-get install git
```
[docker](https://docs.docker.com/engine/install/ubuntu/)
```
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```


#### Запуск приложения
Перейдите в корневую директорию вашего проекта (где находится Dockerfile). Соберите Docker-образ:
```
docker build . --tag fastapi_app
```
Запустите контейнер:
```
docker run -p 80:80 fastapi_app
```
`-p 80:80` — связывает порт 80 на вашем компьютере с портом 80 внутри контейнера.


#### Деплой на Render.com
[Документация](https://render.com/docs)
