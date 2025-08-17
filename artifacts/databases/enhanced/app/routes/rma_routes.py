from flask import Blueprint, request, render_template, redirect, url_for
from app.models import db
from sqlalchemy import text

rma_bp = Blueprint('rma', __name__)

@rma_bp.route('/submit', methods=['GET', 'POST'])
def submit_rma():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        reason = request.form.get('reason')
        if order_id and reason:
            db.session.execute(
                text("CALL InsertRMA(:order_id, :reason)"),
                {"order_id": order_id, "reason": reason}
            )
            db.session.commit()
            return redirect(url_for('main.home'))
    return render_template("submit_rma.html")
