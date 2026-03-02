from datetime import date, timedelta
import calendar

def add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def generate_schedule(start_date: date, end_date: date, frequency: str, amount):
    rows=[]
    current = start_date
    while current <= end_date:
        if frequency == 'weekly':
            next_start = current + timedelta(days=7)
        elif frequency == 'fortnightly':
            next_start = current + timedelta(days=14)
        elif frequency == 'monthly':
            next_start = add_months(current, 1)
        else:
            raise ValueError('Invalid frequency')
        rows.append({
            'due_date': current,
            'period_start': current,
            'period_end': min(next_start - timedelta(days=1), end_date),
            'amount_due': amount,
        })
        current = next_start
    return rows
