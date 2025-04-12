from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app, db
from app.models import Product, Sale, SaleItem, Category, User
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar
from functools import wraps

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            if remember:
                # Session will last for 30 days
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            
            next_page = request.args.get('next')
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    # Pass the current datetime to the template
    return render_template('login.html', now=datetime.now())

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

# Protect routes with login_required
@app.route('/')
@login_required
def index():
    # Get basic statistics
    total_products = Product.query.count()
    total_categories = Category.query.count()
    
    # Sales statistics
    total_sales = Sale.query.count()
    total_revenue = db.session.query(func.sum(Sale.total)).scalar() or 0
    
    # Get today's sales
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_sales = Sale.query.filter(Sale.date.between(today_start, today_end)).count()
    today_revenue = db.session.query(func.sum(Sale.total)).filter(
        Sale.date.between(today_start, today_end)
    ).scalar() or 0
    
    # Get this month's sales
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    month_start = datetime.combine(first_day, datetime.min.time())
    month_end = datetime.combine(last_day, datetime.max.time())
    month_sales = Sale.query.filter(Sale.date.between(month_start, month_end)).count()
    month_revenue = db.session.query(func.sum(Sale.total)).filter(
        Sale.date.between(month_start, month_end)
    ).scalar() or 0
    
    # Get low stock products
    low_stock_products = Product.query.filter(Product.stock <= 5).count()
    
    # Top selling products
    top_products = db.session.query(
        Product.name, func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()
    
    stats = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_sales': total_sales,
        'total_revenue': round(total_revenue, 3),
        'today_sales': today_sales,
        'today_revenue': round(today_revenue, 3),
        'month_sales': month_sales,
        'month_revenue': round(month_revenue, 3),
        'low_stock_products': low_stock_products,
        'top_products': top_products
    }
    
    return render_template('index.html', stats=stats)

@app.route('/products')
@login_required
def products():
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('products.html', products=products, categories=categories)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        category_id = request.form['category_id'] or None
        
        product = Product(code=code, name=name, description=description, price=price, stock=stock, category_id=category_id)
        db.session.add(product)
        db.session.commit()
        
        flash('تم إضافة المنتج بنجاح!', 'success')
        return redirect(url_for('products'))
    
    categories = Category.query.all()
    return render_template('add_product.html', categories=categories)

@app.route('/pos')
def pos():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('pos.html', products=products, categories=categories)

@app.route('/sales', methods=['GET'])
def sales():
    # Get filter parameter
    filter_type = request.args.get('filter', 'all')
    
    # Define date ranges based on filter
    today = datetime.now().date()
    
    if filter_type == 'today':
        # Today's sales
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        sales = Sale.query.filter(Sale.date.between(start_date, end_date)).order_by(Sale.date.desc()).all()
    
    elif filter_type == 'week':
        # This week's sales (starting from Monday)
        start_of_week = today - timedelta(days=today.weekday())
        start_date = datetime.combine(start_of_week, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        sales = Sale.query.filter(Sale.date.between(start_date, end_date)).order_by(Sale.date.desc()).all()
    
    elif filter_type == 'month':
        # This month's sales
        start_of_month = today.replace(day=1)
        start_date = datetime.combine(start_of_month, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        sales = Sale.query.filter(Sale.date.between(start_date, end_date)).order_by(Sale.date.desc()).all()
    
    else:
        # All sales
        sales = Sale.query.order_by(Sale.date.desc()).all()
    
    # Calculate statistics based on filtered sales
    total_sales = len(sales)
    total_revenue = sum(sale.total for sale in sales) if sales else 0
    
    # Average sale value
    avg_sale = total_revenue / total_sales if total_sales > 0 else 0
    
    # Total items sold and unique products for filtered sales
    sale_ids = [sale.id for sale in sales]
    
    if sale_ids:
        total_items_query = db.session.query(func.sum(SaleItem.quantity)).filter(
            SaleItem.sale_id.in_(sale_ids)
        ).scalar()
        
        unique_products_query = db.session.query(func.count(func.distinct(SaleItem.product_id))).filter(
            SaleItem.sale_id.in_(sale_ids)
        ).scalar()
    else:
        total_items_query = 0
        unique_products_query = 0
    
    total_items_sold = total_items_query or 0
    unique_products = unique_products_query or 0
    
    # Last sale information
    last_sale = sales[0] if sales else None
    last_sale_time = last_sale.date.strftime('%Y-%m-%d %H:%M') if last_sale else "لا يوجد"
    last_sale_amount = last_sale.total if last_sale else 0
    
    return render_template('sales.html', 
                          sales=sales,
                          total_sales=total_sales,
                          total_revenue=total_revenue,
                          avg_sale=avg_sale,
                          total_items_sold=total_items_sold,
                          unique_products=unique_products,
                          last_sale_time=last_sale_time,
                          last_sale_amount=last_sale_amount)

@app.route('/sales/add', methods=['POST'])
def add_sale():
    data = request.json
    
    # Create new sale with rounded total (3 decimal places)
    sale = Sale(total=round(data['total'], 3))
    db.session.add(sale)
    db.session.flush()
    
    # Add sale items
    for item in data['items']:
        product = Product.query.get(item['product_id'])
        if product:
            sale_item = SaleItem(
                quantity=item['quantity'],
                price=round(item['price'], 3),  # Round price to 3 decimal places
                product_id=item['product_id'],
                sale_id=sale.id
            )
            db.session.add(sale_item)
            
            # Update stock
            product.stock -= item['quantity']
    
    db.session.commit()
    return jsonify({'success': True, 'sale_id': sale.id})

@app.route('/sales/<int:sale_id>')
def sale_details(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sale_details.html', sale=sale)


@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        
        db.session.commit()
        
        flash('تم تحديث المنتج بنجاح!', 'success')
        return redirect(url_for('products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    product = Product.query.get_or_404(product_id)
    
    # Check if product is used in any sales
    if SaleItem.query.filter_by(product_id=product_id).first():
        flash('لا يمكن حذف هذا المنتج لأنه مستخدم في عمليات بيع سابقة!', 'danger')
        return redirect(url_for('products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash('تم حذف المنتج بنجاح!', 'success')
    return redirect(url_for('products'))


@app.route('/categories')
@login_required
def categories():
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    name = request.form['name']
    description = request.form['description']
    
    # Check if category with this name already exists
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        flash('هذا التصنيف موجود بالفعل!', 'danger')
        return redirect(url_for('categories'))
    
    category = Category(name=name, description=description)
    
    try:
        db.session.add(category)
        db.session.commit()
        flash('تم إضافة التصنيف بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء إضافة التصنيف!', 'danger')
    
    return redirect(url_for('categories'))

@app.route('/categories/edit/<int:category_id>', methods=['POST'])
@login_required
def edit_category(category_id):
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    category = Category.query.get_or_404(category_id)
    
    category.name = request.form['name']
    category.description = request.form['description']
    
    db.session.commit()
    
    flash('تم تحديث التصنيف بنجاح!', 'success')
    return redirect(url_for('categories'))

@app.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    # Check if user has admin permissions
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    category = Category.query.get_or_404(category_id)
    
    # Check if category is used in any products
    if Product.query.filter_by(category_id=category_id).first():
        flash('لا يمكن حذف هذا التصنيف لأنه مستخدم في منتجات!', 'danger')
        return redirect(url_for('categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('تم حذف التصنيف بنجاح!', 'success')
    return redirect(url_for('categories'))


# إضافة طرق إدارة المستخدمين
@app.route('/users')
@login_required
def users():
    # التحقق من صلاحيات المستخدم
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    # التحقق من صلاحيات المستخدم
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'is_admin' in request.form
        
        # التحقق من عدم وجود مستخدم بنفس اسم المستخدم
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return render_template('add_user.html')
            
        # التحقق من عدم وجود مستخدم بنفس البريد الإلكتروني
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني موجود بالفعل', 'danger')
            return render_template('add_user.html')
            
        # إنشاء مستخدم جديد
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('تم إضافة المستخدم بنجاح', 'success')
        return redirect(url_for('users'))
        
    return render_template('add_user.html')

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # التحقق من صلاحيات المستخدم
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(user_id)
    
    # لا يمكن تعديل المستخدم الحالي
    if user.id == session.get('user_id'):
        flash('لا يمكنك تعديل حسابك الحالي من هنا', 'warning')
        return redirect(url_for('users'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        is_admin = 'is_admin' in request.form
        new_password = request.form['password']
        
        # التحقق من عدم وجود مستخدم آخر بنفس اسم المستخدم
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return render_template('edit_user.html', user=user)
            
        # التحقق من عدم وجود مستخدم آخر بنفس البريد الإلكتروني
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            flash('البريد الإلكتروني موجود بالفعل', 'danger')
            return render_template('edit_user.html', user=user)
            
        # تحديث بيانات المستخدم
        user.username = username
        user.email = email
        user.is_admin = is_admin
        
        # تحديث كلمة المرور إذا تم إدخالها
        if new_password:
            user.set_password(new_password)
            
        db.session.commit()
        
        flash('تم تحديث بيانات المستخدم بنجاح', 'success')
        return redirect(url_for('users'))
        
    return render_template('edit_user.html', user=user)

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # التحقق من صلاحيات المستخدم
    if not session.get('is_admin'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(user_id)
    
    # لا يمكن حذف المستخدم الحالي
    if user.id == session.get('user_id'):
        flash('لا يمكنك حذف حسابك الحالي', 'danger')
        return redirect(url_for('users'))
        
    # التحقق من وجود مستخدم آخر بصلاحيات المدير
    admin_count = User.query.filter_by(is_admin=True).count()
    if admin_count <= 1 and user.is_admin:
        flash('لا يمكن حذف المستخدم لأنه المدير الوحيد في النظام', 'danger')
        return redirect(url_for('users'))
        
    db.session.delete(user)
    db.session.commit()
    
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('users'))