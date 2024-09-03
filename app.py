from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from  models import Customer, StoreManager, Category, Product, db, CartItem
from sqlalchemy import or_
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_bcrypt import Bcrypt
from datetime import datetime
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(current_dir, "grocery_store.sqlite3")
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'customer_login'
@login_manager.user_loader
def load_customer(customer_id):
    return Customer.query.get(int(customer_id))
bcrypt = Bcrypt(app)
@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)
@app.route('/',methods=['GET', 'POST'])
# Customer Login
def customer_login():
    categories = Category.query.all()
    products = Product.query.all()
    if request.method == 'GET':
     return render_template('customer_login.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        customer = Customer.query.filter_by(username=username).first()
        if customer and bcrypt.check_password_hash(customer.password, password):
            login_user(customer)
            flash('You are logged in as a customer.', 'success')
            return render_template('home.html', categories=categories, products=products, username=username)
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template("error.html", error='Invalid username or password')

@app.route('/customer/signup', methods=['GET', 'POST'])
def customer_signup():
    categories = Category.query.all()
    products = Product.query.all()
    if request.method == 'GET':
        return render_template('customer_signup.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('customer_signup'))
        # Check if username or email already exists
        existing_user = Customer.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('customer_signup'))
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # Create a new customer
        new_customer = Customer(username=username, password=hashed_password)
        db.session.add(new_customer)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('customer_login'))
    return render_template('home.html', categories=categories, products=products)

@app.route('/customer/logout')
def customer_logout():
    logout_user()
    return redirect(url_for('customer_login'))

@app.route('/add_to_cart/<int:product_id>/<username>', methods=['POST'])
def add_to_cart(product_id,username):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    u=Customer.query.filter_by(username=username).first()
    if quantity <= 0:
        flash('Quantity must be greater than zero.', 'danger')
    elif quantity > product.quantity:
        flash('Not enough quantity available.', 'danger')
    else:
        # Check if the product is already in the cart
        cart_item = CartItem.query.filter_by(customer_id=u.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(customer_id=u.id, product_id=product.id, quantity=quantity)
            db.session.add(cart_item)
        # Update the product quantity
        product.quantity -= quantity
        # Make sure the product quantity doesn't go negative
        if product.quantity < 0:
            product.quantity = 0
        db.session.commit()
        flash('Product added to cart.', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    # Fetch the cart items for the current customer from the database
    customer = current_user
    cart_items = customer.cart_items
    total_amount = 0
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        total_amount += product.rate_per_unit * cart_item.quantity
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    # Your logic to remove the product from the cart
    # ...
    flash('Product removed from cart.', 'success')
    return redirect(url_for('cart'))
@app.route('/checkout', methods=['POST'])
def checkout():
    categories = Category.query.all()
    products = Product.query.all()
    # Fetch the cart items for the current customer from the database
    customer = current_user
    cart_items = customer.cart_items
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return render_template('cart.html')
    # Placeholder: You can implement the payment and order processing logic here
    # Clear the cart items after successful checkout
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    flash('Order placed successfully. Thank you for shopping!', 'success')
    # Redirect back to the cart page (you can customize this redirection)
    return render_template('home.html', categories=categories, products=products)

# Store Manager Login
@app.route('/store_manager/login', methods=['GET', 'POST'])
def store_manager_login():
    if request.method == 'GET':
        return render_template('store_manager_login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        store_manager = StoreManager.query.filter_by(username=username).first()
        if store_manager and bcrypt.check_password_hash(store_manager.password, password):
            login_user(store_manager)
            print('You are logged in as a store manager.', 'success')
            return render_template('store_manager_dashboard.html')
        else:
            flash('Login unsuccessful. Please check your credentials.', 'danger')
    return render_template('store_manager_dashboard.html')

@app.route('/store_manager/signup', methods=['GET', 'POST'])
def store_manager_signup():
    if request.method == 'GET':
        return render_template('store_manager_signup.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('store_manager_signup'))
        # Check if username or email already exists
        existing_user = StoreManager.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('store_manager_signup'))
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # Create a new customer
        new_customer = StoreManager(username=username, password=hashed_password)
        db.session.add(new_customer)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('store_manager_login'))
    return render_template('store_manager_dashboard.html')

@app.route('/store_manager/logout')
def store_manager_logout():
    logout_user()
    return redirect(url_for('store_manager_login'))

@app.route('/store_manager/dashboard')
def store_manager_dashboard():
    store_manager_id = session.get('store_manager_id')
    if store_manager_id:
        store_manager = StoreManager.query.get(store_manager_id)
        return render_template('store_manager_dashboard.html', store_manager=store_manager)
    else:
        flash('You need to log in as a store manager to access this page.', 'warning')
        return redirect(url_for('store_manager_login'))

# Category List (for both customers and store managers)
@app.route('/categories')
def category_list():
    # Placeholder to fetch and display the list of categories
    categories = Category.query.all()
    return render_template('category_list.html', categories=categories)

# Add New Category (accessible only to store managers)
@app.route('/addcategory', methods=['GET', 'POST'])
def add_category():
        if request.method == 'GET':
            print("entered get")
            return render_template('addcategory.html')
   # if current_user.is_store_manager:
        if request.method == 'POST':
            name = request.form['name']
            # Placeholder: Add the new category to the database
            new_category = Category(name=name)
            db.session.add(new_category)
            db.session.commit()
            flash('New category added successfully.', 'success')
            return redirect(url_for('store_manager_dashboard'))
        
@app.route('/editcategory/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'GET':
        return render_template('editcategory.html', category=category)
    if request.method == 'POST':
        new_name = request.form['name']
    # Placeholder: Update the category in the database
        category.name = new_name
        db.session.commit()
        flash('Category updated successfully.', 'success')
        return redirect(url_for('store_manager_dashboard'))

@app.route('/addproduct', methods=['GET', 'POST'])
def add_product():
    # Fetch the list of categories from the database to display in the form
    categories = Category.query.all()
    if request.method == 'GET':
        return render_template('addproduct.html', categories=categories)
    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category']
        manufacture_date_str = request.form['manufacture_date']
        manufacture_date = datetime.strptime(manufacture_date_str, '%Y-%m-%d')
        rate_per_unit = request.form['rate_per_unit']
        quantity = request.form['quantity']
        # Placeholder: Add the new product to the database
        new_product = Product(
            name=name,
            manufacture_date=manufacture_date,
            rate_per_unit=rate_per_unit,
            quantity=quantity,
            category_id=category_id
            )
        db.session.add(new_product)
        db.session.commit()
        flash('New product added successfully.', 'success')
        return redirect(url_for('store_manager_dashboard'))

@app.route('/editproduct/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    if request.method == 'GET':
        return render_template('editproduct.html', product=product, categories=categories)
    if request.method == 'POST':
        new_name = request.form['name']
        new_category_id = request.form['category']
        manufacture_date_str = request.form['manufacture_date']
        manufacture_date = datetime.strptime(manufacture_date_str, '%Y-%m-%d')
        rate_per_unit = request.form['rate_per_unit']
        quantity = request.form['quantity']
        # Update the product attributes
        product.name = new_name
        product.category_id = new_category_id
        product.manufacture_date = manufacture_date
        product.rate_per_unit = rate_per_unit
        product.quantity = quantity
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('store_manager_dashboard'))

@app.route('/products')
def product_list():
    # Fetch the list of products from the database
    products = Product.query.all()
    return render_template('product_list.html', products=products)

def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)