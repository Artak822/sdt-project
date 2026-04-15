from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column("CustomerID", Integer, primary_key=True, autoincrement=True)
    first_name = Column("FirstName", String(100), nullable=False)
    last_name = Column("LastName", String(100), nullable=False)
    email = Column("Email", String(255), nullable=False, unique=True)

    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column("ProductID", Integer, primary_key=True, autoincrement=True)
    product_name = Column("ProductName", String(255), nullable=False)
    price = Column("Price", Numeric(10, 2), nullable=False)

    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column("OrderID", Integer, primary_key=True, autoincrement=True)
    customer_id = Column("CustomerID", Integer, ForeignKey("customers.CustomerID"), nullable=False)
    order_date = Column("OrderDate", DateTime, nullable=False, default=datetime.utcnow)
    total_amount = Column("TotalAmount", Numeric(10, 2), nullable=False, default=0)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column("OrderItemID", Integer, primary_key=True, autoincrement=True)
    order_id = Column("OrderID", Integer, ForeignKey("orders.OrderID"), nullable=False)
    product_id = Column("ProductID", Integer, ForeignKey("products.ProductID"), nullable=False)
    quantity = Column("Quantity", Integer, nullable=False)
    subtotal = Column("Subtotal", Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
