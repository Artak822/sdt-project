from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Customer, Product, Order, OrderItem


def place_order(session: Session, customer_id: int, items: list[dict]) -> Order:
    """
    Сценарий 1: Размещение заказа.

    items — список словарей вида:
        {"product_id": int, "quantity": int, "price": Decimal}

    Транзакция:
    1. INSERT в Orders (TotalAmount = 0 временно)
    2. INSERT позиций в OrderItems с Quantity и Subtotal
    3. UPDATE TotalAmount = сумма всех Subtotal
    При любой ошибке — ROLLBACK, заказ не создаётся.
    """
    try:
        order = Order(
            customer_id=customer_id,
            order_date=datetime.utcnow(),
            total_amount=Decimal("0"),
        )
        session.add(order)
        session.flush()  # получаем order.id до COMMIT

        for item in items:
            subtotal = Decimal(str(item["price"])) * item["quantity"]
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                subtotal=subtotal,
            )
            session.add(order_item)

        session.flush()  # записываем OrderItems, чтобы можно было читать order.items
        order.total_amount = sum(i.subtotal for i in order.items)
        session.commit()
    except Exception:
        session.rollback()
        raise

    return order


def update_customer_email(session: Session, customer_id: int, new_email: str) -> Customer:
    """
    Сценарий 2: Атомарное обновление email клиента.

    Транзакция:
    1. SELECT клиента по ID
    2. UPDATE Email
    При любой ошибке — ROLLBACK, email остаётся прежним.
    """
    try:
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise ValueError(f"Клиент с ID={customer_id} не найден")
        customer.email = new_email
        session.commit()
    except Exception:
        session.rollback()
        raise

    return customer


def add_product(session: Session, product_name: str, price: Decimal) -> Product:
    """
    Сценарий 3: Атомарное добавление нового продукта.

    Транзакция:
    1. INSERT в Products
    При любой ошибке — ROLLBACK, БД остаётся в консистентном состоянии.
    """
    try:
        product = Product(product_name=product_name, price=Decimal(str(price)))
        session.add(product)
        session.flush()
        session.commit()
    except Exception:
        session.rollback()
        raise

    return product
