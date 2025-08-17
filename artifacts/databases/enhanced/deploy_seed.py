import pandas as pd
from app import create_app, db
from app.models import Customer, Order, RMA

app = create_app()

def load_data():
    with app.app_context():
        db.create_all()  # Ensure tables exist

        # Load and insert customers
        customers = pd.read_csv("data/customers.csv")
        for _, row in customers.iterrows():
            customer = Customer(
                id=row['id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                state=row['state']
            )
            db.session.add(customer)

        # Load and insert orders
        orders = pd.read_csv("data/orders.csv")
        for _, row in orders.iterrows():
            order = Order(
                id=row['id'],
                customer_id=row['customer_id'],
                sku=row['sku'],
                description=row['description'],
                step=row['step'],
                status=row['status']
            )
            db.session.add(order)

        # Load and insert RMAs
        rmas = pd.read_csv("data/rma.csv")
        for _, row in rmas.iterrows():
            rma = RMA(
                id=row['id'],
                order_id=row['order_id'],
                reason=row['reason']
            )
            db.session.add(rma)

        db.session.commit()
        print("Data seeded successfully.")

if __name__ == "__main__":
    load_data()