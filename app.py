from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
import config

import json

app = Flask(__name__)
app.config.from_object(config)
mail = Mail(app)

app.secret_key = 'replace-this-with-a-secret-key'

DATA_FILE = 'data.json'

def get_available_eggs():
    with open(DATA_FILE) as f:
        data = json.load(f)
    return data.get('available_eggs', 0)

def update_available_eggs(new_count):
    with open(DATA_FILE, 'w') as f:
        json.dump({'available_eggs': new_count}, f)

@app.route('/')
def order_form():
    available_eggs = get_available_eggs()
    return render_template('order.html', available_eggs=available_eggs)

@app.route('/order', methods=['POST'])
def submit_order():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    quantity = int(request.form.get('quantity'))

    available_eggs = get_available_eggs()
    if quantity > available_eggs:
        flash(f'Not enough eggs available. Only {available_eggs} left.')
        return redirect(url_for('order_form'))

    update_available_eggs(available_eggs - quantity)

    # Email to admin
    admin_msg = Message(
        subject='New Egg Order',
        
        recipients=[app.config['ORDER_NOTIFICATION_EMAIL']],
        body=(
        f"New order from {name} ({email})\n"
        f"Phone: {phone}\n"
        f"Quantity: {quantity} eggs"
    ))
    mail.send(admin_msg)

    # Email to customer
    confirmation_msg = Message(
        subject='Your Egg Order Confirmation',
        recipients=[email],
        body=(
            f"Hello {name},\n\n"
            f"Phone: {phone}\n"
            f"Thank you for ordering {quantity} dozen egg(s).\n"
            "We'll be in touch shortly to arrange pickup or delivery.\n\n"
            "Best,\nThe Egg Team"
        )
    )
    mail.send(confirmation_msg)

    flash(f'Thank you, {name}! Your order for {quantity} dozen eggs has been placed.')
    return redirect(url_for('order_form'))

from flask import request

@app.route('/webhook/recurring', methods=['POST'])
def zapier_recurring_order():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    quantity = data.get('quantity', 12)

    # Send yourself a reminder email
    msg = Message(
        subject='Recurring Egg Order Reminder',
        recipients=[app.config['ORDER_NOTIFICATION_EMAIL']],
        body=f"Recurring order from {name} ({email})\nQuantity: {quantity} dozen eggs"
    )
    mail.send(msg)

    return {'status': 'received'}, 200   

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        try:
            new_quantity = int(request.form.get('new_quantity'))
            if new_quantity < 0:
                raise ValueError("Quantity cannot be negative")
            update_available_eggs(new_quantity)
            flash(f'Egg inventory updated to {new_quantity}.')
        except ValueError:
            flash('Invalid input. Please enter a non-negative number.')
        return redirect(url_for('admin'))

    available_eggs = get_available_eggs()
    return render_template('admin.html', available_eggs=available_eggs)


if __name__ == '__main__':
    app.run(debug=True)
