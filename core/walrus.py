import asyncio
import aiohttp

from pysui.sui.sui_txn.async_transaction import SuiTransactionAsync
from pysui.sui.sui_types import ObjectID, SuiString, SuiAddress
from pysui.sui.sui_types.bcs import Argument
from fake_useragent import UserAgent
from loguru import logger

from core.utils.sui_utils import SuiUtils
from config import WAL_AMOUNT_FOR_STAKE


class Walrus:
    def __init__(self, key: str, proxy: str):
        self.sui_utils = SuiUtils(key=key)
        self.proxy = f"http://{proxy}" if proxy is not None else None

        self.session = aiohttp.ClientSession(
            # headers=headers,
            trust_env=True
        )

    async def get_test_sui(self):
        url = "https://faucet.testnet.sui.io/v1/gas"

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://faucet.blockbolt.io',
            'priority': 'u=1, i',
            'referer': 'https://faucet.blockbolt.io/',
            # 'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            # 'sec-ch-ua-mobile': '?0',
            # 'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': UserAgent(os='windows').random,
        }

        json_data = {
            'FixedAmountRequest': {
                'recipient': str(self.sui_utils.config.active_address),
            },
        }

        code_202 = False
        code_429 = False
        while not code_429:
            response = await self.session.post(url=url, json=json_data, headers=headers, proxy=self.proxy)
            if response.status == 202:
                code_202 = True
            elif response.status == 429:
                code_429 = True

        await asyncio.sleep(10)
        sui_balance = await self.sui_utils.get_balance(coin_type='0x2::sui::SUI')
        return (True, sui_balance) if code_202 and code_429 else (False, sui_balance)
        # return True if (await response.json()).get('error') == 'null' else False

    # WALRUS - https://stake.walrus.site/
    async def connect_stake_walrus_site(self):
        try:
            url = "https://fullnode.testnet.sui.io/"

            headers = {
                # 'Client-Sdk-Version': '1.9.0',
                # 'sec-ch-ua-platform': '"Windows"',
                'Referer': 'https://stake.walrus.site/',
                # 'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                # 'sec-ch-ua-mobile': '?0',
                # 'Client-Target-Api-Version': '1.34.0',
                'User-Agent': UserAgent(os='windows').random,
                'Content-Type': 'application/json',
                'Client-Sdk-Type': 'typescript',
            }

            json_data = {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'suix_getBalance',
                'params': [
                    str(self.sui_utils.config.active_address),
                    '0x2::sui::SUI',
                ],
            }

            response = await self.session.post(url=url, json=json_data, headers=headers, proxy=self.proxy)
            return True if response.status == 200 else False
            # return (await response.json()).get('result').get('totalBalance')

        except Exception as e:
            logger.error(f'Error: {e}')

    async def call_exchange_all_for_wal(self):
        try:
            all_coins = await self.sui_utils.get_sui_coin_objects(coin_type='0x2::sui::SUI')

            if len(all_coins) >= 3:
                tx_merge = SuiTransactionAsync(client=self.sui_utils.client)
                gas_coin_object = all_coins[0]
                merge_to_coin = all_coins[1]
                merge_from_coins = all_coins[2:]

                await tx_merge.merge_coins(merge_to=merge_to_coin, merge_from=merge_from_coins)
                status, err_msg = await self.sui_utils.send_tx_with_execute(tx_merge, gas_coin_object)

            tx = SuiTransactionAsync(client=self.sui_utils.client)

            all_coins = await self.sui_utils.get_sui_coin_objects(coin_type='0x2::sui::SUI')
            amount = int(int(all_coins[0].balance) - (int(all_coins[0].balance) * 0.05))
            await tx.split_coin(coin=Argument('GasCoin'), amounts=[amount])

            move_call_result = await tx.move_call(
                target=SuiString("0x9f992cc2430a1f442ca7a5ca7638169f5d5c00e0ebc3977a65e9ac6e497fe5ef::wal_exchange::exchange_all_for_wal"),
                arguments=[
                    ObjectID("0x0e60a946a527902c90bbc71240435728cd6dc26b9e8debc69f09b71671c3029b"),
                    Argument("NestedResult", (0, 0))
                ],
            )

            await tx.transfer_objects(
                transfers=[move_call_result],
                recipient=self.sui_utils.config.active_address
            )

            # all_coins = await self.sui_utils.get_sui_coin_objects(coin_type='0x2::sui::SUI')
            status, err_msg = await self.sui_utils.send_tx(tx)

            await asyncio.sleep(5)
            wal_balance = await self.sui_utils.get_balance(coin_type='0x9f992cc2430a1f442ca7a5ca7638169f5d5c00e0ebc3977a65e9ac6e497fe5ef::wal::WAL')
            return status, err_msg, wal_balance

        except Exception as e:
            logger.error(f'Error: {e}')

    async def call_stake_with_pool(self, pool_address: str):
        try:
            amount = int(f'{str(WAL_AMOUNT_FOR_STAKE)}_000_000_000')

            tx = SuiTransactionAsync(client=self.sui_utils.client)

            coin_type_balance = (await self.sui_utils.client.get_coin(
                coin_type="0x9f992cc2430a1f442ca7a5ca7638169f5d5c00e0ebc3977a65e9ac6e497fe5ef::wal::WAL",
                address=self.sui_utils.config.active_address
            ))
            try:
                sui_object_id = coin_type_balance.result_data.to_dict()['data'][0]['coinObjectId']
            except IndexError:
                return False, 'Недостаточный баланс WAL', 0

            await tx.split_coin(
                coin=ObjectID(sui_object_id),
                amounts=[amount]
            )

            move_call_result = await tx.move_call(
                target=SuiString("0x9f992cc2430a1f442ca7a5ca7638169f5d5c00e0ebc3977a65e9ac6e497fe5ef::staking::stake_with_pool"),
                arguments=[
                    ObjectID("0x37c0e4d7b36a2f64d51bba262a1791f844cfd88f31379f1b7c04244061d43914"),
                    Argument("NestedResult", (0, 0)),
                    SuiAddress(pool_address)
                ],
            )

            await tx.transfer_objects(
                transfers=[move_call_result],
                recipient=self.sui_utils.config.active_address
            )

            status, err_msg = await self.sui_utils.send_tx(tx)
            await asyncio.sleep(5)
            wal_balance = await self.sui_utils.get_balance(coin_type='0x9f992cc2430a1f442ca7a5ca7638169f5d5c00e0ebc3977a65e9ac6e497fe5ef::wal::WAL')
            return status, err_msg, wal_balance

        except Exception as e:
            logger.error(f'Error: {e}')

    async def connect_flatland_walrus_site(self):
        url = "https://fullnode.testnet.sui.io/"

        headers = {
            # 'Client-Sdk-Version': '0.54.1',
            # 'sec-ch-ua-platform': '"Windows"',
            'Referer': 'https://flatland.walrus.site/',
            # 'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            # 'sec-ch-ua-mobile': '?0',
            # 'Client-Target-Api-Version': '1.25.0',
            'User-Agent': UserAgent(os='windows').random,
            'Content-Type': 'application/json',
            'Client-Sdk-Type': 'typescript',
        }

        json_data = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'suix_resolveNameServiceNames',
            'params': [
                str(self.sui_utils.config.active_address),
                None,
                1,
            ],
        }

        response = await self.session.post(url=url, json=json_data, headers=headers, proxy=self.proxy)
        return True if response.status == 200 else False

    async def call_mint_function(self):
        try:
            tx = SuiTransactionAsync(client=self.sui_utils.client)

            await tx.move_call(
                target=SuiString("0x4cb65566af16acb9ae48c437e99653e77c06c1b712329486987223ca99f44575::flatland::mint"),
                arguments=[
                    ObjectID("0x0000000000000000000000000000000000000000000000000000000000000008")
                ]
            )

            status, err_msg = await self.sui_utils.send_tx(tx)
            return status, err_msg

        except Exception as e:
            logger.error(f'Error: {e}')

    async def blob_upload(self):
        try:
            # url = 'https://publish.walrus.site/'
            pass
        except Exception as e:
            logger.error(f'Error: {e}')

    async def logout(self):
        await self.session.close()


def convert_balance(token_amount: int):
    if str(token_amount)[:-9]:
        return f'{str(token_amount)[:-9]},{str(token_amount)[-9:-7]}'
    else:
        return f'0,{str(token_amount)[-9:-7]}'
