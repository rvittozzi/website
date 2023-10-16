from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=True)  # Add 'name' field


# Create Registration and Login Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=120)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    name = StringField('Name', validators=[DataRequired()])
    full_address = StringField('Full Address', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Create a Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)  # new field


# Initialize shopping cart
cart = {}


# Routes for Registration and Login
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data, password=hashed_password, name=form.name.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Store user's ID in the session
            session['user_name'] = user.name  # Store user's name in the session
            flash('You have been logged in!', 'success')
            return redirect(url_for('index'))  # Redirects to the 'index' route after successful login
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    return render_template('login.html', form=form)  # Renders the separate login page


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/')
def index():
    products = {product.name: product.price for product in Product.query.all()}
    registration_form = RegistrationForm()
    return render_template("index.html", products=products, form=registration_form, cart=cart)


@app.route('/product/<string:product_name>')
def product_page(product_name):
    product = Product.query.filter_by(name=product_name).first_or_404()
    return render_template('product_page.html', product=product)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item = request.form.get('item')
    quantity = int(request.form.get('quantity'))
    if item in cart:
        cart[item] += quantity
    else:
        cart[item] = quantity
    return redirect(url_for('index'))


@app.route('/cart')
def show_cart():
    products = {product.name: product.price for product in Product.query.all()}
    total = 0
    for item, quantity in cart.items():
        total += products[item] * quantity
    return render_template("cart.html", cart=cart, products=products, total=total)


def add_initial_products():
    initial_products = [
        {'name': 'Butterfly Wind-charm', 'price': 50, 'image_filename': 'butterfly.png'},
        {'name': 'Hanging Basket', 'price': 30, 'image_filename': 'hanging_basket.png'},
        {'name': 'Fish Carving', 'price': 40},
        {'name': 'Tree Carving', 'price': 70},
        {'name': 'Custom Carving', 'price': 100},
    ]

    for product in initial_products:
        db_product = Product.query.filter_by(name=product['name']).first()
        if db_product is None:
            new_product = Product(name=product['name'], price=product['price'],
                                  image_filename=product.get('image_filename', None))
            db.session.add(new_product)
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the tables
        add_initial_products()  # This will populate the Product table
    app.run(debug=True)
