import argparse
import sys
from prettytable import PrettyTable

from ..core.usecases import AppLogic
from ..core.exceptions import *

from ..parser_service.config import DEFAULT_CONFIG
from ..parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from ..parser_service.storage import RatesStorage
from ..parser_service.updater import RatesUpdater
from ..core.utils import load_json


def main():
    """Главная функция."""
    app = AppLogic()

    parser = argparse.ArgumentParser(
        description="Торговля валютами - консольное приложение"
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # Регистрация
    reg = subparsers.add_parser('register', help='Создать аккаунт')
    reg.add_argument('--username', required=True)
    reg.add_argument('--password', required=True)

    # Вход
    login = subparsers.add_parser('login', help='Войти')
    login.add_argument('--username', required=True)
    login.add_argument('--password', required=True)

    # Выход
    subparsers.add_parser('logout', help='Выйти')

    # Портфель
    port = subparsers.add_parser('portfolio', help='Показать портфель')
    port.add_argument('--base', default='USD')

    show_port = subparsers.add_parser('show-portfolio', help='Показать портфель (алиас)')
    show_port.add_argument('--base', default='USD')

    # Купить
    buy = subparsers.add_parser('buy', help='Купить валюту')
    buy.add_argument('--currency', required=True)
    buy.add_argument('--amount', type=float, required=True)

    # Продать
    sell = subparsers.add_parser('sell', help='Продать валюту')
    sell.add_argument('--currency', required=True)
    sell.add_argument('--amount', type=float, required=True)

    # Курс
    rate = subparsers.add_parser('rate', help='Узнать курс')
    rate.add_argument('--from', dest='from_curr', required=True)
    rate.add_argument('--to', dest='to_curr', required=True)

    get_rate = subparsers.add_parser('get-rate', help='Узнать курс (алиас)')
    get_rate.add_argument('--from', dest='from_curr', required=True)
    get_rate.add_argument('--to', dest='to_curr', required=True)

    # Обновить курсы
    upd = subparsers.add_parser('update-rates', help='Обновить курсы валют')
    upd.add_argument('--source', choices=['coingecko', 'exchangerate'], required=False)

    # Показать курсы
    show_rates = subparsers.add_parser('show-rates', help='Показать курсы из кеша')
    show_rates.add_argument('--currency', required=False)

    # Добавить деньги 
    add = subparsers.add_parser('add-money', help='Добавить деньги (тест)')
    add.add_argument('--currency', default='USD')
    add.add_argument('--amount', type=float, required=True)

    subparsers.add_parser('whoami', help='Показать кто я')

    subparsers.add_parser('debug-session', help='Показать сессию (отладка)')

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    try:
        if args.command == 'register':
            user = app.register(args.username, args.password)
            print(f" Создан пользователь: {user.username} (ID: {user.user_id})")
            print("   Вы автоматически вошли в систему!")

        elif args.command == 'login':
            user = app.login(args.username, args.password)
            print(f" Вход выполнен: {user.username}")

        elif args.command == 'logout':
            app.logout()
            print(" Вы вышли")

        elif args.command in ('portfolio', 'show-portfolio'):
            data = app.show_my_portfolio(args.base)

            print(f"\n Портфель: {data['user']}")
            print("=" * 50)

            table = PrettyTable()
            table.field_names = ["Валюта", "Количество", f"В {args.base}"]

            for wallet in data['wallets']:
                table.add_row([
                    wallet['currency'],
                    f"{wallet['balance']:.4f}",
                    f"{wallet.get('value', 0):.2f}"
                ])

            print(table)
            print("=" * 50)
            print(f"Всего в {args.base}: {data['total']:.2f}")

        elif args.command == 'buy':
            result = app.buy(args.currency, args.amount)
            print(f"\n Куплено {result['amount']:.4f} {result['currency']}")
            print(f"   Стоимость: {result['cost']:.2f} USD")
            print(f"   Новый баланс: {result['new_balance']:.4f} {result['currency']}")
            print(f"   USD осталось: {result['usd_left']:.2f}")

        elif args.command == 'sell':
            result = app.sell(args.currency, args.amount)
            print(f"\n Продано {result['amount']:.4f} {result['currency']}")
            print(f"   Выручка: {result['revenue']:.2f} USD")
            print(f"   Новый баланс: {result['new_balance']:.4f} {result['currency']}")
            print(f"   USD теперь: {result['usd_now']:.2f}")

        elif args.command in ('rate', 'get-rate'):
            rate_val = app.get_rate(args.from_curr, args.to_curr)
            print(f"\n Курс: 1 {args.from_curr} = {rate_val:.6f} {args.to_curr}")
            if rate_val > 0:
                print(f"   Обратно: 1 {args.to_curr} = {1 / rate_val:.6f} {args.from_curr}")

        elif args.command == 'update-rates':
            cfg = DEFAULT_CONFIG
            clients = []

            if args.source in (None, 'coingecko'):
                clients.append(CoinGeckoClient(cfg))

            if args.source in (None, 'exchangerate'):
                clients.append(ExchangeRateApiClient(cfg))

            storage = RatesStorage(cfg.RATES_FILE_PATH, cfg.HISTORY_FILE_PATH)
            updater = RatesUpdater(clients, storage)

            updated = updater.run_update()
            print(f"\n Курсы обновлены: {len(updated)} пар")

        elif args.command == 'show-rates':
            data = load_json("data/rates.json")
            pairs = data.get("pairs", {})

            if not pairs:
                print(" Кеш курсов пуст. Выполните update-rates")
                return

            table = PrettyTable()
            table.field_names = ["Пара", "Курс", "Обновлено", "Источник"]

            for pair, info in pairs.items():
                if args.currency and not pair.startswith(args.currency.upper()):
                    continue
                table.add_row([
                    pair,
                    info.get("rate"),
                    info.get("updated_at"),
                    info.get("source"),
                ])

            print("\n💱 Курсы валют:")
            print(table)

        elif args.command == 'add-money':
            result = app.add_money(args.currency, args.amount)
            print(f"\n Добавлено {result['added']:.2f} {result['currency']}")
            print(f"   Было: {result['was']:.2f}, стало: {result['now']:.2f}")

        elif args.command == 'whoami':
            user = app.get_current_user()
            info = user.get_info()
            print(f"\n Вы: {info['name']} (ID: {info['id']})")
            print(f"   Зарегистрирован: {info['registered']}")

        elif args.command == 'debug-session':
            import os
            if os.path.exists("data/session.json"):
                with open("data/session.json", 'r') as f:
                    print(f.read())
            else:
                print("Файл сессии не найден")

        else:
            parser.print_help()

    except MyError as e:
        print(f"\n Ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n Неизвестная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
