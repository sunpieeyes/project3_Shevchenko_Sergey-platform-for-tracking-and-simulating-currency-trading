"""
CLI interface for ValutaTrade Hub.
Поддерживает команды: register, login, logout, show-portfolio, buy, sell, get-rate, update-rates
"""

import argparse
from prettytable import PrettyTable

from valutatrade_hub.core import usecases
from valutatrade_hub.core.exceptions import (
    AuthenticationError,
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
    UserExistsError,
)


def _print_portfolio(res: dict):
    if not res or not res.get("wallets"):
        print("Пустой портфель")
        return
    print(f"Портфель пользователя '{res['user']}' (база: {res['base']}):")
    t = PrettyTable()
    t.field_names = ["Currency", "Balance", f"Value ({res['base']})"]
    for cur, info in res["wallets"].items():
        bal = info.get("balance", 0.0)
        val = info.get("value_in_base", 0.0)
        t.add_row([cur, f"{bal}", f"{val:.8f}"])
    print(t)
    print("-" * 40)
    print(f"ИТОГО: {res['total']} {res['base']}")
    if res.get("rates_last_refresh"):
        print(f"Курсы обновлены: {res['rates_last_refresh']}")


def cli_entrypoint(argv=None):
    parser = argparse.ArgumentParser(prog="valutatrade", description="ValutaTrade Hub CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_register = sub.add_parser("register")
    p_register.add_argument("--username", required=True)
    p_register.add_argument("--password", required=True)

    p_login = sub.add_parser("login")
    p_login.add_argument("--username", required=True)
    p_login.add_argument("--password", required=True)

    p_logout = sub.add_parser("logout")

    p_show = sub.add_parser("show-portfolio")
    p_show.add_argument("--base", required=False, default="USD")

    p_buy = sub.add_parser("buy")
    p_buy.add_argument("--currency", required=True)
    p_buy.add_argument("--amount", required=True, type=float)

    p_sell = sub.add_parser("sell")
    p_sell.add_argument("--currency", required=True)
    p_sell.add_argument("--amount", required=True, type=float)

    p_rate = sub.add_parser("get-rate")
    p_rate.add_argument("--from", dest="from_currency", required=True)
    p_rate.add_argument("--to", dest="to_currency", required=True)

    # -------------------------------
    # NEW COMMAND: update-rates
    # -------------------------------
    p_update = sub.add_parser("update-rates")

    args = parser.parse_args(argv)

    try:
        if args.command == "register":
            res = usecases.register(args.username, args.password)
            print(f"Пользователь '{res['username']}' зарегистрирован (id={res['user_id']}). Войдите: login --username {res['username']} --password <password>")

        elif args.command == "login":
            res = usecases.login(args.username, args.password)
            print(f"Вы вошли как '{res['username']}'")

        elif args.command == "logout":
            usecases.logout()
            print("Вы вышли из сессии")

        elif args.command == "show-portfolio":
            res = usecases.show_portfolio(base=args.base)
            _print_portfolio(res)

        elif args.command == "buy":
            res = usecases.buy(args.currency, args.amount)
            if res.get("estimated_cost_usd") is not None:
                print(f"Покупка выполнена: {res['amount']:.8f} {res['currency']} (оценочная стоимость: {res['estimated_cost_usd']:.2f} USD)")
            else:
                print(f"Покупка выполнена: {res['amount']:.8f} {res['currency']} (курс недоступен)")

        elif args.command == "sell":
            res = usecases.sell(args.currency, args.amount)
            if res.get("estimated_revenue_usd") is not None:
                print(f"Продажа выполнена: {res['amount']:.8f} {res['currency']} (оценочная выручка: {res['estimated_revenue_usd']:.2f} USD)")
            else:
                print(f"Продажа выполнена: {res['amount']:.8f} {res['currency']} (курс недоступен)")

        elif args.command == "get-rate":
            res = usecases.get_rate(args.from_currency, args.to_currency)
            print(f"Курс {res['from']}→{res['to']}: {res['rate']:.8f} (обновлено: {res['rates_last_refresh']})")

        elif args.command == "update-rates":
            from valutatrade_hub.services.rates_updater import update_rates
            update_rates()
            print("Курсы успешно обновлены.")

    except UserExistsError as e:
        print("Ошибка:", e)
    except AuthenticationError as e:
        print("Ошибка авторизации:", e)
    except InsufficientFundsError as e:
        print("Ошибка:", e)
    except CurrencyNotFoundError as e:
        print("Ошибка: ", e)
        print("Подсказка: используйте supported currencies list (например, USD, EUR, BTC, ETH)")
    except ApiRequestError as e:
        print("Ошибка получения курсов:", e)
    except ValueError as e:
        print("Ошибка валидации:", e)
    except Exception as e:
        print("Unexpected error:", e)
