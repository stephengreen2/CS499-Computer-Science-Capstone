# Quantigration RMA Flask App

This is a Flask-based web application for managing Return Merchandise Authorizations (RMAs) as part of the Quantigration RMA system. It includes schema definitions, stored procedures, analytics, and seeded test data for evaluating and processing product returns.

## 🚀 Features

- Submit RMAs tied to existing orders
- Use stored procedures to encapsulate logic in the database
- Generate return rate reports grouped by SKU
- Seed customers, orders, and RMAs from CSV files
- Deploy-ready schema and setup script
- Modular Flask project structure

## 🗂️ Project Structure

```
rma_app/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── routes/
│   │   ├── main_routes.py
│   │   └── rma_routes.py
│   ├── templates/
│   └── static/
├── sql/
│   ├── setup_database.sql
│   └── rma_stored_procedures.sql
├── data/
│   ├── customers.csv
│   ├── orders.csv
│   └── rma.csv
├── deploy_setup.py
├── deploy_seed.py
└── requirements.txt
```

## ⚙️ Setup Instructions

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   Create a `.env` file with:

   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=yourpassword
   DB_NAME=rma_db
   ```

3. **Run database setup**
   ```bash
   python deploy_setup.py
   ```

4. **Run the Flask app**
   ```bash
   flask run
   ```

## 📈 Stored Procedures Used

- `InsertRMA(order_id, reason)`
- `GetReturnRateBySKU()`
- `GetRMAByCustomerState()`
- `GetCustomerRMAs(customer_id)`

## ✅ Requirements

- Python 3.10+
- MySQL (or compatible RDBMS with stored procedure support)
- Flask
- SQLAlchemy
- Pandas
- dotenv

---

© 2025 Quantigration — Built for CS 499 Capstone
