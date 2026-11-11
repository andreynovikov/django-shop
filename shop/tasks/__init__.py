"""
Celery tasks of the shop, in bundles:

- user_interaction: what customers get, SMS and mail about their accounts, orders, baskets and expiring bonuses
- admin: notices to the shop's staff
- workflow: what keeps orders, products and baskets going, and the storefronts' caches up to date with them
- stocks: stock and prices from 1C, through Yandex Disk
- integrations: exchange with other outside systems: bonuses from 1C, the Central Bank, ModulKassa, Yandex Metrika

Each task is named shop.tasks.<function>, as it was when they all were in shop/tasks.py: Celery finds a task by its
name, which beat schedules in the database, stored results and tasks waiting in the broker keep.
"""
from . import admin, integrations, stocks, user_interaction, workflow  # noqa: F401 (registers the tasks)
