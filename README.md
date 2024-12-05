# Автоматизация Walrus
___
Версия Python 3.11

### 🤔 Что делает софт?
1. Берет тестовые токены из крана.
2. Обменивает тестовые SUI на WAL.
3. Рандомно стейкает WAL.
4. Минтит NFT.

### ⚙️ Настройка перед запуском:
+ Заполняете файл `data/private_keys.txt` вашими приватниками (каждый с новой строки) через `::` можете указать прокси в формате `login:password@ip:port`
+ Можете изменить данные в config.py:
    - `DELAY` - Диапазон рандомной задержки между задачами
    - `WAL_AMOUNT_FOR_STAKE` - Диапазон рандомного кол-ва WAL токенов для стейкинга каждому валидатору (минимум 1)
    - `MAX_VALIDATORS` - Количество валидаторов для стейкинга одного аккаунта за один запуск софта (максимум 25)
    - `MAX_CONCURRENT_TASKS` - Одновременно выполняемых аккаунтов
    - `RANGE_OF_ACCOUNTS` - Диапазон аккаунтов для выполнения задач
    - `CHANCE_FOR_MINT` - Шанс в процентах для минта nft на Flatland (от 0 до 100)
+ Устанавливаете нужные библиотеки: 
```
pip install -r requirements.txt
```

### 🚀 Запуск:
```
python main.py
```

📚Взаимодействие с базой данных (БД):
После запуска у вас появится выбор действия (выберите стрелочками на клавиатуре):
1. Выполнение задач
2. Мои аккаунты
3. Добавить аккаунты в БД
4. Обновить прокси в БД 
5. Удалить аккаунты из БД 
6. Выход 

Пояснение:
1. Выполняет все вышеописанные задачи.
2. Выведет некоторую информацию об аккаунтах из БД.
3. Добавляет аккаунты в БД из файла `data/private_keys.txt`, если в БД уже есть запись о таком приватном ключе, то он его не добавит.
4. Если вы измените или добавите прокси к приватному ключу в `data/private_keys.txt`, то он измениться в БД.
5. Для удаления аккаунтов из БД нужно заполнить `data/delete.txt` приватниками или приваник::прокси (без разницы).
6. Завершает выполнение программы.

Больше крипто тем и софтов в Телеграм: [enigmo](https://t.me/enigmo_crypto)