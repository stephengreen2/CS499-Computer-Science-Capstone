from flask import Blueprint, render_template
from app.models import db
from sqlalchemy import text

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template("dashboard.html")

@main_bp.route('/report')
def report():
    results = db.session.execute(text("CALL GetReturnRateBySKU()")).fetchall()
    return render_template("report.html", results=results)
