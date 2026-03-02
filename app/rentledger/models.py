from datetime import date
from decimal import Decimal
from .extensions import db

class Lease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_address = db.Column(db.String(255), nullable=False)
    landlord_name = db.Column(db.String(120), nullable=False)
    tenant_name = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    rent_amount = db.Column(db.Numeric(10,2), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    bond_amount = db.Column(db.Numeric(10,2))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    payments = db.relationship('Payment', back_populates='lease', cascade='all, delete-orphan', order_by='Payment.due_date')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    amount_due = db.Column(db.Numeric(10,2), nullable=False)
    date_paid = db.Column(db.Date)
    amount_paid = db.Column(db.Numeric(10,2))
    payment_method = db.Column(db.String(50), default='bank transfer', nullable=False)
    bank_reference = db.Column(db.String(255))
    transaction_id = db.Column(db.String(255))
    status = db.Column(db.String(20), default='due', nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    lease = db.relationship('Lease', back_populates='payments')

    def recalc_status(self, today=None):
        today = today or date.today()
        paid = Decimal(str(self.amount_paid)) if self.amount_paid is not None else None
        due = Decimal(str(self.amount_due))
        if paid is None:
            self.status = 'overdue' if self.due_date < today else 'due'
        elif paid >= due:
            self.status = 'paid'
        elif paid > 0:
            self.status = 'partial'
        else:
            self.status = 'overdue' if self.due_date < today else 'due'
        return self.status
