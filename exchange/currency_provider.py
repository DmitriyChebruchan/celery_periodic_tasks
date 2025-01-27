import dataclasses
from abc import ABC, abstractmethod

import requests


@dataclasses.dataclass
class SellBuy:
    sell: float
    buy: float


class RateNotFound(Exception):
    pass


class ProviderBase(ABC):
    name = None

    def __init__(self, currency_from: str, currency_to: str):
        self.currency_from = currency_from
        self.currency_to = currency_to

    @abstractmethod
    def get_rate(self) -> SellBuy:
        pass


class MonoProvider(ProviderBase):
    name = "monobank"

    iso_from_country_code = {
        "UAH": 980,
        "USD": 840,
        "EUR": 978,
    }

    def get_rate(self) -> SellBuy:
        url = "https://api.monobank.ua/bank/currency"
        response = requests.get(url)
        response.raise_for_status()

        currency_from_code = self.iso_from_country_code[self.currency_from]
        currency_to_code = self.iso_from_country_code[self.currency_to]

        for currency in response.json():
            if (
                currency["currencyCodeA"] == currency_from_code
                and currency["currencyCodeB"] == currency_to_code
            ):
                value = SellBuy(
                    sell=float(currency["rateSell"]), buy=float(currency["rateBuy"])
                )
                return value
        raise RateNotFound(
            f"Cannot find rate from {self.currency_from} to {self.currency_to} in provider {self.name}"
        )


class PrivatbankProvider(ProviderBase):
    name = "privatbank"

    def get_rate(self) -> SellBuy:
        url = "https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5"
        response = requests.get(url)
        response.raise_for_status()
        for currency in response.json():
            if (
                currency["ccy"] == self.currency_from
                and currency["base_ccy"] == self.currency_to
            ):
                value = SellBuy(
                    buy=float(currency["buy"]), sell=float(currency["sale"])
                )
                return value
        raise RateNotFound(
            f"Cannot find rate from {self.currency_from} to {self.currency_to} in provider {self.name}"
        )


class NationalBankProvider(ProviderBase):
    name = "NationalBank"

    def get_rate(self) -> SellBuy:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        response = requests.get(url)
        response.raise_for_status()
        for currency in response.json():
            if currency["cc"] == self.currency_from:
                value = SellBuy(
                    # There is no sell parameter in the json file, so I make it by default larger by 0.5
                    buy=float(currency["rate"]),
                    sell=float(currency["rate"] + 0.5),
                )
                return value
        raise RateNotFound(
            f"Cannot find rate from {self.currency_from} to {self.currency_to} in provider {self.name}"
        )


class VKurseProvider(ProviderBase):
    name = "VKurse"
    country_code = {"USD": "Dollar", "EUR": "Euro"}

    def get_rate(self) -> SellBuy:
        url = "https://vkurse.dp.ua/course.json"
        response = requests.get(url)
        response.raise_for_status()

        currency_from_code = self.country_code[self.currency_from]
        currency_data = response.json().get(currency_from_code)

        if currency_data:
            value = SellBuy(
                sell=float(currency_data['sale']), buy=float(currency_data['buy'])
            )
            return value

        raise RateNotFound(
            f"Cannot find rate from {self.currency_from} to {self.currency_to} in provider {self.name}"
        )


PROVIDERS = [MonoProvider, PrivatbankProvider, NationalBankProvider, VKurseProvider]
