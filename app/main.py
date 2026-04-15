from decimal import Decimal
from app.database import engine, SessionLocal
from app.models import Base, Customer, Product
from app.transactions import place_order, update_customer_email, add_product


def seed(session):
    if session.query(Customer).count() == 0:
        customer = Customer(first_name="Иван", last_name="Иванов", email="ivan@example.com")
        session.add(customer)

    if session.query(Product).count() == 0:
        session.add(Product(product_name="Телефон", price=Decimal("1500.00")))
        session.add(Product(product_name="Наушники", price=Decimal("1000.00")))

    session.commit()


def main():
    Base.metadata.create_all(engine)
    print("Таблицы созданы.\n")

    with SessionLocal() as session:
        seed(session)

        customer = session.query(Customer).first()
        products = session.query(Product).all()

        items = [
            {"product_id": products[0].id, "quantity": 1, "price": products[0].price},
            {"product_id": products[1].id, "quantity": 1, "price": products[1].price},
        ]
        order = place_order(session, customer_id=customer.id, items=items)
        print(f"[Сценарий 1] Заказ #{order.id} создан.")
        print(f"             CustomerID={order.customer_id}, TotalAmount={order.total_amount}\n")

        old_email = customer.email
        updated = update_customer_email(session, customer_id=customer.id, new_email="new@example.com")
        print(f"[Сценарий 2] Email клиента #{updated.id} обновлён.")
        print(f"             {old_email!r} → {updated.email!r}\n")

        new_product = add_product(session, product_name="Ноутбук", price=Decimal("50000.00"))
        print(f"[Сценарий 3] Продукт добавлен.")
        print(f"             ProductID={new_product.id}, Name={new_product.product_name!r}, Price={new_product.price}\n")


if __name__ == "__main__":
    main()
