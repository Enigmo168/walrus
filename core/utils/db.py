import os
import sqlite3

from loguru import logger

from config import WAL_AMOUNT_FOR_STAKE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db = sqlite3.connect(os.path.join(BASE_DIR, 'data', 'walrus_db.db'))
c = db.cursor()


def add_users():
    users = get_users()
    with open(os.path.join(BASE_DIR, 'data', 'private_keys.txt')) as f:
        new_users = f.readlines()
    logger.info(f'Аккаунтов для добавления: "{len(new_users)}". Аккаунтов в БД: "{len(users)}". Добавление...')

    users_added = 0
    for new_user in new_users:
        if '::' in new_user:
            pk, proxy = new_user.strip().split('::')
        else:
            pk = new_user.strip()
            proxy = ''

        for user in users:
            if pk == user[1]:
                logger.error(f'"{new_user}" уже был записан в БД')
                break
        else:
            c.execute('INSERT INTO users (private_key, proxy) VALUES (?, ?)', (pk, proxy))
            db.commit()
            users_added += 1

    logger.info(f'Успешно добавил {users_added}/{len(new_users)} аккаунтов. Аккаунтов в БД: "{len(get_users())}"')


def update_users():
    with open(os.path.join(BASE_DIR, 'data', 'private_keys.txt')) as f:
        new_users_data = f.readlines()
    logger.info(f'Обновление прокси...')

    users_updated = 0
    if new_users_data:
        users_data = get_users()
        for new_user_data in new_users_data:
            if '::' in new_user_data:
                pk, proxy = new_user_data.strip().split('::')
            else:
                pk = new_user_data.strip()
                proxy = ''

            for user_data in users_data:
                if (pk == user_data[1]) and (proxy != user_data[2]):
                    c.execute('UPDATE users SET proxy = ? WHERE private_key = ?', (proxy, pk))
                    db.commit()
                    users_updated += 1
                    logger.success(f'{user_data[1]} изменил прокси c "{user_data[2]}" на "{proxy}"')
                    break

    logger.info(f'Успешно изменил "{users_updated}" прокси. Аккаунтов в БД: "{len(get_users())}"')


def delete_users():
    users = get_users()
    with open(os.path.join(BASE_DIR, 'data', 'delete.txt')) as f:
        del_users = f.readlines()
    logger.info(f'Аккаунтов для удаления: "{len(del_users)}". Аккаунтов в БД: "{len(users)}". Удаление...')

    users_deleted = 0
    for del_user in del_users:
        if '::' in del_user:
            pk, proxy = del_user.strip().split('::')
        else:
            pk = del_user.strip()
            proxy = ''

        for user in users:
            if pk == user[1]:
                c.execute('DELETE FROM users WHERE private_key = ?', (pk,))
                db.commit()
                users_deleted += 1
                logger.success(f'Удалил "{del_user}" из БД')
                break
        else:
            logger.error(f'"{del_user}" нет в БД для удаления')

    logger.info(f'Успешно удалил {users_deleted}/{len(del_users)} аккаунтов. Аккаунтов в БД: "{len(get_users())}"')


def get_users() -> list[tuple]:
    return c.execute('SELECT * FROM users').fetchall()


def get_pool_addresses() -> list[tuple]:
    return c.execute('SELECT * FROM pool_addresses').fetchall()


def update_stake(user_id: int, pool_address: str, amount):
    pool_address_id = c.execute('SELECT id FROM pool_addresses WHERE address = ?', (pool_address,)).fetchone()[0]
    stake = c.execute('SELECT * FROM stake WHERE user_id = ? AND pool_address_id = ? ORDER BY stake_amount ASC LIMIT 1', (user_id, pool_address_id)).fetchone()
    if stake is None:
        c.execute('INSERT INTO stake (user_id, pool_address_id, stake_amount) VALUES (?, ?, ?)', (user_id, pool_address_id, amount))
    else:
        c.execute('UPDATE stake SET stake_amount = stake_amount + 1 WHERE user_id = ? AND pool_address_id = ?', (user_id, pool_address_id))
    db.commit()


def update_mint(user_id: int):
    c.execute('UPDATE users SET mint = 1 WHERE id = ?', (user_id,))
    db.commit()

