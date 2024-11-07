import asyncio
from random import randint, sample, shuffle

import inquirer
from loguru import logger
from tabulate import tabulate

from core.walrus import Walrus, convert_balance
from core.utils.db import add_users, update_users, delete_users, get_users, get_pool_addresses, update_stake, update_mint
from config import DELAY, MAX_VALIDATORS, MAX_CONCURRENT_TASKS, RANGE_OF_ACCOUNTS


async def random_sleep(user_id, address):
    seconds = randint(DELAY[0], DELAY[1])
    logger.success(f'{user_id} | {address} | Спит {seconds} секунд перед следующей задачей')
    await asyncio.sleep(seconds)


async def user_tasks(user_data):
    user_id = user_data[0]
    private_key = user_data[1]
    proxy = user_data[2]
    mint = user_data[3]
    galxe = user_data[4]

    logger.info(f'{user_id} | Начал работу')

    try:
        walrus = Walrus(private_key, proxy)
        address = walrus.sui_utils.config.active_address

        get_test_sui_res, sui_balance = await walrus.get_test_sui()
        if get_test_sui_res:
            logger.success(f'{user_id} | {address} | Получил тестовый SUI токен из крана. Баланс test SUI = {convert_balance(sui_balance)}')
        else:
            logger.error(f'{user_id} | {address} | Не удалось получить тестовый SUI токен из крана. Баланс test SUI = {convert_balance(sui_balance)}')

        if await walrus.connect_stake_walrus_site():
            logger.success(f'{user_id} | {address} | Подключился к Stake')
        else:
            logger.error(f'{user_id} | {address} | Не удалось подключиться к Stake')
            return

        await random_sleep(user_id, address)

        if sui_balance > 1_100_000_000:
            result_exchange, err_msg, wal_balance = await walrus.call_exchange_all_for_wal()
            if result_exchange:
                logger.success(f'{user_id} | {address} | Обменял тестовый SUI токен на WAL. Баланс WAL = {convert_balance(wal_balance)}')
            else:
                logger.error(f'{user_id} | {address} | Не удалось обменять тестовый SUI токен на WAL. Баланс WAL = {convert_balance(wal_balance)}. Ошибка: {err_msg}')
        else:
            logger.error(f'{user_id} | {address} | Минимальный баланс для обмена на WAL должен быть больше 1.1 SUI. Баланс test SUI = {convert_balance(sui_balance)}')

        await random_sleep(user_id, address)

        pool_addresses = get_pool_addresses()
        random_pools = sample(pool_addresses, min(MAX_VALIDATORS, len(pool_addresses)))
        for pool_address in random_pools:
            result_stake, err_msg, wal_balance = await walrus.call_stake_with_pool(pool_address[1])
            if result_stake:
                logger.success(f'{user_id} | {address} | Застейкал WAL в {pool_address[1]}. Баланс WAL = {convert_balance(wal_balance)}')
                update_stake(user_id, pool_address[1])
                await random_sleep(user_id, address)
            else:
                logger.error(f'{user_id} | {address} | Не удалось застейкать WAL в {pool_address[1]}. Баланс WAL = {convert_balance(wal_balance)}. Ошибка: {err_msg}')
                break

        if await walrus.connect_flatland_walrus_site():
            logger.success(f'{user_id} | {address} | Подключился к Flatland')
        else:
            logger.error(f'{user_id} | {address} | Не удалось подключиться к Flatland')
            return

        await random_sleep(user_id, address)

        if not mint:
            result_mint, err_msg = await walrus.call_mint_function()
            if result_mint:
                logger.success(f'{user_id} | {address} | Cминтил NFT')
                update_mint(user_id)
            else:
                logger.error(f'{user_id} | {address} | Не удалось cминтить NFT. Ошибка: {err_msg}')
        else:
            logger.info(f'{user_id} | {address} | Mint NFT уже был сделан')

        await walrus.logout()

        logger.info(f'{user_id} | {address} | Закончил работу')

    except Exception as e:
        logger.error(f'{user_id} | Неожиданная ошибка: {e}')


async def main():
    choices = [
        'Выполнение задач',
        'Мои аккаунты',
        'Добавить аккаунты в БД',
        'Обновить прокси в БД',
        'Удалить аккаунты из БД',
        'Выход'
    ]

    questions = [
        inquirer.List(
            'action',
            message="Выберите действие:",
            choices=choices,
        ),
    ]
    action = inquirer.prompt(questions)['action']

    match action:
        case 'Выполнение задач':
            users = get_users()

            user_from = RANGE_OF_ACCOUNTS[0]
            user_to = len(users)

            if len(RANGE_OF_ACCOUNTS) == 2:
                user_to = RANGE_OF_ACCOUNTS[1]

            logger.info(f'Аккаунтов в БД: "{len(users)}". Диапазон аккаунтов: "{user_from}-{user_to}". Выполнение...')

            users = users[user_from - 1:user_to]
            shuffle(users)

            semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

            async def limited_task(user_data):
                async with semaphore:
                    await user_tasks(user_data)

            try:
                tasks = [limited_task(user_data) for user_data in users]
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f'Завершено с ошибкой: {e}')

            logger.info(f'Выполнил все доступные задачи')

        case 'Мои аккаунты':
            users = get_users()
            headers = ["id", "Private Key", "Proxy", "Mint NFT", "Galxe Tasks"]
            print(tabulate(users, headers=headers, tablefmt="fancy_grid"))

        case 'Добавить аккаунты в БД':
            add_users()

        case 'Обновить прокси в БД':
            update_users()

        case 'Удалить аккаунты из БД':
            delete_users()

        case 'Выход':
            exit()


if __name__ == "__main__":
    asyncio.run(main())
