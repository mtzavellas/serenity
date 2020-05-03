from typing import List


class Portfolio:
    pass


class TradingAccount:
    def __init__(self, trading_account_id: int, trading_account_name: str, portfolio: Portfolio):
        self.trading_account_id = trading_account_id

        self.portfolio = portfolio

        self.trading_account_name = trading_account_name

    def get_trading_account_id(self) -> int:
        return self.trading_account_id

    def get_portfolio(self) -> Portfolio:
        return self.portfolio

    def get_trading_account_name(self) -> str:
        return self.trading_account_name


# noinspection PyRedeclaration
class Portfolio:
    def __init__(self, portfolio_id: int, portfolio_name: str):
        self.portfolio_id = portfolio_id
        self.portfolio_name = portfolio_name
        self.accounts = list()

    def get_portfolio_id(self):
        return self.portfolio_id

    def get_portfolio_name(self):
        return self.portfolio_name

    def get_accounts(self) -> List[TradingAccount]:
        return self.accounts

    def set_accounts(self, accounts: List[TradingAccount]):
        self.accounts = accounts
