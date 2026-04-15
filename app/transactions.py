from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Customer, Product, Order, OrderItem


def place_order(session: Session, customer_id: int, items: list[dict]) -> Order:
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
    try:
        product = Product(product_name=product_name, price=Decimal(str(price)))
        session.add(product)
        session.flush()
        session.commit()
    except Exception:
        session.rollback()
        raise

    return product
