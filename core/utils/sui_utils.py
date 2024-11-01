from pysui import SuiConfig, AsyncClient
from pysui.sui.sui_types import SuiString
from pysui.sui.sui_txn.async_transaction import SuiTransactionAsync
from pysui.sui.sui_types.scalars import SuiTxBytes
from pysui.sui.sui_txresults.single_tx import SuiCoinObject


class SuiUtils:
    def __init__(self, rpc_url: str = "https://fullnode.testnet.sui.io:443", mnemonic: str = None, key: str = None):
        if mnemonic:
            self.mnemonic = mnemonic
            self.config = SuiConfig.user_config(
                rpc_url=rpc_url,
                prv_keys=[mnemonic]
            )
        elif key:
            self.mnemonic = ""
            self.key = key
            self.config = SuiConfig.user_config(
                rpc_url=rpc_url,
                prv_keys=[key]
            )
        else:
            self.config = SuiConfig.user_config(rpc_url=rpc_url)
            self.wallet, self.mnemonic = self.create_wallet()

        self.client = AsyncClient(self.config)

    def create_wallet(self):
        mnemonic, address = self.config.create_new_keypair_and_address()
        return address, mnemonic

    async def get_balance(self, coin_type: str | SuiString, fetch_all: bool = False):
        coins = (await self.client.get_coin(coin_type=coin_type, address=self.config.active_address, fetch_all=fetch_all)).result_data.to_dict()['data']
        total_balance = sum(int(coin['balance']) for coin in coins)
        return total_balance

    async def send_tx(self, tx: SuiTransactionAsync):
        tx_bytes = await tx.deferred_execution()
        sui_tx_bytes = SuiTxBytes(tx_bytes)
        sign_and_submit_res = await self.client.sign_and_submit(signer=self.config.active_address, tx_bytes=sui_tx_bytes)

        result_data = sign_and_submit_res.result_data
        status = True if result_data.effects.status.status == 'success' else False
        error_message = result_data.effects.status.error if not status else None
        return status, error_message

    async def send_tx_with_execute(self, tx: SuiTransactionAsync, gas_object: SuiCoinObject):
        execute_res = await tx.execute(
            gas_budget=gas_object.balance,
            use_gas_object=gas_object.object_id,
            run_verification=True
        )

        result_data = execute_res.result_data
        status = not execute_res.is_err() and result_data.effects.status.status == 'success'
        error_message = result_data.effects.status.error if not status else None
        return status, error_message

    async def get_sui_coin_objects(self, coin_type) -> list[SuiCoinObject]:
        coin_objects = await self.client.get_coin(
            coin_type=coin_type,
            address=self.config.active_address,
            fetch_all=True)

        coins = [x for x in coin_objects.result_data.data]
        return coins
