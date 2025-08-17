from app import db
from sqlalchemy import CheckConstraint

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    state = db.Column(db.String(25), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    sku = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    step = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(15), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('Pending', 'Processing', 'Shipped', 'Delivered')", name='valid_status'),
    )

class RMA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    reason = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        CheckConstraint("length(reason) > 3", name='valid_reason_length'),
    )
