from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import csv, io
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort
from flask_login import login_required, current_user
from .extensions import db
from .models import Lease, Payment
from .utils import generate_schedule

bp = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

def _d(v, name):
    try: return datetime.strptime(v, '%Y-%m-%d').date()
    except Exception: raise ValueError(f'Invalid date for {name}')

def _n(v, name, required=True):
    if (v is None or v=='') and not required: return None
    try: return Decimal(str(v))
    except (InvalidOperation, ValueError): raise ValueError(f'Invalid number for {name}')

@bp.app_template_filter('aud')
def aud(v):
    return '' if v is None else f"AUD${Decimal(v):,.2f}"

@bp.route('/health')
def health():
    return {'status':'ok'}

@bp.route('/')
@login_required
def index():
    lease = Lease.query.filter_by(user_id=current_user.id).order_by(Lease.id.desc()).first()
    if not lease:
        return render_template('index.html', lease=None, rows=[])
    rows = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.due_date.asc()).all()
    for r in rows: r.recalc_status()
    db.session.commit()
    total_due = sum((r.amount_due or Decimal('0')) for r in rows) if rows else Decimal('0')
    total_paid = sum((r.amount_paid or Decimal('0')) for r in rows if r.amount_paid is not None) if rows else Decimal('0')
    return render_template('index.html', lease=lease, rows=rows, total_due=total_due, total_paid=total_paid, balance=total_paid-total_due)

@bp.route('/lease', methods=['GET','POST'])
@login_required
def lease_page():
    lease = Lease.query.filter_by(user_id=current_user.id).order_by(Lease.id.desc()).first()
    if request.method == 'POST':
        try:
            data = dict(
                property_address=request.form.get('property_address','').strip(),
                landlord_name=request.form.get('landlord_name','').strip(),
                tenant_name=request.form.get('tenant_name','').strip(),
                start_date=_d(request.form.get('start_date',''),'start date'),
                end_date=_d(request.form.get('end_date',''),'end date'),
                rent_amount=_n(request.form.get('rent_amount',''),'rent amount'),
                frequency=request.form.get('frequency','').strip().lower(),
                bond_amount=_n(request.form.get('bond_amount',''),'bond amount', required=False),
                notes=request.form.get('notes','').strip() or None,
            )
            if data['end_date'] < data['start_date']:
                raise ValueError('End date must be on or after start date')
            if data['frequency'] not in {'weekly','fortnightly','monthly'}:
                raise ValueError('Frequency must be weekly, fortnightly or monthly')
            if lease:
                for k,v in data.items(): setattr(lease, k, v)
                flash('Lease updated','success')
            else:
                lease = Lease(user_id=current_user.id, **data)
                db.session.add(lease)
                flash('Lease created','success')
            db.session.commit()
            return redirect(url_for('main.lease_page'))
        except ValueError as e:
            flash(str(e),'danger')
    count = Payment.query.filter_by(lease_id=lease.id).count() if lease else 0
    return render_template('lease.html', lease=lease, count=count)

@bp.route('/schedule/generate', methods=['POST'])
@login_required
def generate():
    lease = Lease.query.filter_by(user_id=current_user.id).order_by(Lease.id.desc()).first()
    if not lease:
        flash('Create lease first','danger')
        return redirect(url_for('main.lease_page'))
    replace = request.form.get('replace_existing') == 'on'
    existing = Payment.query.filter_by(lease_id=lease.id).count()
    if existing and not replace:
        flash('Schedule exists. Tick replace to rebuild.','warning')
        return redirect(url_for('main.lease_page'))
    if replace:
        Payment.query.filter_by(lease_id=lease.id).delete()
    rows = generate_schedule(lease.start_date, lease.end_date, lease.frequency, lease.rent_amount)
    for r in rows:
        p = Payment(lease_id=lease.id, payment_method='bank transfer', **r)
        p.recalc_status()
        db.session.add(p)
    db.session.commit()
    flash(f'Generated {len(rows)} entries','success')
    return redirect(url_for('main.payments'))

@bp.route('/payments')
@login_required
def payments():
    lease = Lease.query.filter_by(user_id=current_user.id).order_by(Lease.id.desc()).first()
    if not lease:
        return redirect(url_for('main.lease_page'))
    status = request.args.get('status','all')
    q = Payment.query.filter_by(lease_id=lease.id)
    if status in {'due','paid','partial','overdue'}:
        q = q.filter_by(status=status)
    rows = q.order_by(Payment.due_date.asc()).all()
    changed=False
    for r in rows:
        prev=r.status
        r.recalc_status()
        changed |= (prev!=r.status)
    if changed: db.session.commit()
    running_due=Decimal('0'); running_paid=Decimal('0'); ledger=[]
    for r in rows:
        running_due += (r.amount_due or Decimal('0'))
        if r.amount_paid is not None: running_paid += r.amount_paid
        ledger.append((r, running_paid-running_due))
    return render_template('payments.html', lease=lease, ledger=ledger, status=status)

@bp.route('/payments/<int:pid>/record', methods=['GET','POST'])
@login_required
def record(pid):
    lease = Lease.query.filter_by(user_id=current_user.id).order_by(Lease.id.desc()).first()
    if not lease:
        abort(404)
    p = Payment.query.filter_by(id=pid, lease_id=lease.id).first_or_404()
    if request.method == 'POST':
        try:
            p.date_paid = _d(request.form.get('date_paid',''),'date paid')
            p.amount_paid = _n(request.form.get('amount_paid',''),'amount paid')
            p.payment_method = request.form.get('payment_method','bank transfer').strip() or 'bank transfer'
            p.bank_reference = request.form.get('bank_reference','').strip() or None
            p.transaction_id = request.form.get('transaction_id','').strip() or None
            p.notes = request.form.get('notes','').strip() or None
            p.recalc_status()
            db.session.commit()
            flash('Payment saved','success')
            return redirect(url_for('main.payments'))
        except ValueError as e:
            flash(str(e),'danger')
    return render_template('payment_form.html', payment=p)

@bp.route('/payments/<int:pid>/clear', methods=['POST'])
@login_required
def clear(pid):
    lease = Lease.query.filter_by(user_id=current_user.id).order_by(Lease.id.desc()).first()
    if not lease:
        abort(404)
    p = Payment.query.filter_by(id=pid, lease_id=lease.id).first_or_404()
    p.date_paid=None; p.amount_paid=None; p.bank_reference=None; p.transaction_id=None; p.notes=None; p.payment_method='bank transfer'
    p.recalc_status(); db.session.commit()
    flash('Payment cleared','success')
    return redirect(url_for('main.payments'))

@bp.route('/export/csv')
@login_required
def export_csv():
    lease = Lease.query.filter_by(user_id=current_user.id).order_by(Lease.id.desc()).first()
    if not lease:
        return redirect(url_for('main.lease_page'))
    rows = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.due_date.asc()).all()
    s = io.StringIO(); w = csv.writer(s)
    w.writerow(['Due Date','Period Start','Period End','Amount Due','Date Paid','Amount Paid','Payment Method','Bank Reference','Transaction ID','Status','Notes'])
    for p in rows:
        w.writerow([p.due_date,p.period_start,p.period_end,p.amount_due,p.date_paid,p.amount_paid,p.payment_method or '',p.bank_reference or '',p.transaction_id or '',p.status or '',p.notes or ''])
    return Response(s.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=rent_ledger_export.csv'})
