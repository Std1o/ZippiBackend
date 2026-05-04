from zippi import tables
from .database import (engine, Session)
from .tables import Base


def create_initial_data(session):
    """Создание начальных данных для каталога"""

    # Создаём категории
    categories = [
        tables.Category(name="Футболки", description="Мужские и женские футболки", sort_order=1),
        tables.Category(name="Джинсы", description="Джинсы разных моделей", sort_order=2),
        tables.Category(name="Куртки", description="Верхняя одежда", sort_order=3),
        tables.Category(name="Аксессуары", description="Ремни, сумки, головные уборы", sort_order=4),
    ]

    for category in categories:
        existing = session.query(tables.Category).filter_by(name=category.name).first()
        if not existing:
            session.add(category)

    session.commit()

    # Создаём товары
    products = [
        tables.Product(name="Футболка хлопок белая", description="Классическая белая футболка из 100% хлопка",
                       price=1500, old_price=2000, category_id=1, stock=50),
        tables.Product(name="Футболка с принтом", description="Футболка с современным принтом",
                       price=2000, old_price=2500, category_id=1, stock=30),
        tables.Product(name="Джинсы классические", description="Синие джинсы прямого кроя",
                       price=3500, old_price=4500, category_id=2, stock=25),
        tables.Product(name="Джинсы скинни", description="Узкие джинсы черного цвета",
                       price=4000, old_price=5000, category_id=2, stock=20),
        tables.Product(name="Куртка демисезонная", description="Легкая куртка для весны/осени",
                       price=8500, old_price=10000, category_id=3, stock=10),
        tables.Product(name="Пуховик", description="Теплый пуховик для зимы",
                       price=15000, old_price=18000, category_id=3, stock=5),
        tables.Product(name="Ремень кожаный", description="Натуральная кожа",
                       price=1200, old_price=1500, category_id=4, stock=100),
        tables.Product(name="Сумка шоппер", description="Вместительная сумка",
                       price=2500, old_price=3000, category_id=4, stock=40),
    ]

    for product in products:
        existing = session.query(tables.Product).filter_by(name=product.name).first()
        if not existing:
            session.add(product)

    session.commit()
    print("Начальные данные добавлены!")


def main():
    print("Создание таблиц базы данных...")
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы!")

    # Добавляем начальные данные
    session = Session()
    try:
        create_initial_data(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()