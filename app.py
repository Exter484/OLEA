from datetime import datetime, date as date_obj, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Thailand Timezone Helper
THAILAND_TZ = timezone(timedelta(hours=7))

def get_thailand_now():
    return datetime.now(THAILAND_TZ)

def get_thailand_today():
    return datetime.now(THAILAND_TZ).date()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here' # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    duration = db.Column(db.Integer, default=1) # Duration in hours
    end_time = db.Column(db.String(10)) # Calculated end time
    guests = db.Column(db.Integer, nullable=False)
    table_number = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_thailand_now)

    def __init__(self, name, email, phone, date, time, guests, table_number, duration=1, message=None):
        self.name = name
        self.email = email
        self.phone = phone
        self.date = date
        self.time = time
        self.duration = int(duration)
        self.guests = guests
        self.table_number = table_number
        self.message = message
        
        # Calculate end_time
        try:
            start_dt = datetime.strptime(time, '%H:%M')
            from datetime import timedelta
            end_dt = start_dt + timedelta(hours=self.duration)
            self.end_time = end_dt.strftime('%H:%M')
        except:
            self.end_time = time # Fallback

    def __repr__(self):
        return f'<Reservation {self.name} - {self.phone} - {self.date} {self.time} - Table {self.table_number}>'

# Create the database and tables
with app.app_context():
    # db.drop_all() # Uncomment this if you need to reset the schema completely
    db.create_all()

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/check_availability')
def check_availability():
    date = request.args.get('date')
    time = request.args.get('time')
    duration = request.args.get('duration', 1)
    
    if not date or not time:
        return {"error": "Missing date or time"}, 400
        
    try:
        duration = int(duration)
        start_dt = datetime.strptime(time, '%H:%M')
        from datetime import timedelta
        end_dt = start_dt + timedelta(hours=duration)
        new_start = start_dt.strftime('%H:%M')
        new_end = end_dt.strftime('%H:%M')
    except:
        return {"error": "Invalid time or duration"}, 400

    # Find all reservations for that date
    reservations = Reservation.query.filter_by(date=date).all()
    booked_list = []
    
    for res in reservations:
        # Overlap check: (start1 < end2) AND (end1 > start2)
        if (new_start < res.end_time) and (new_end > res.time):
            if res.table_number not in booked_list:
                booked_list.append(res.table_number)
    
    return {"booked_tables": booked_list}

@app.route('/admin/reserve', methods=['POST'])
@login_required
def admin_reserve():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        date = request.form.get('date')
        time = request.form.get('time')
        duration = request.form.get('duration', 1)
        guests = request.form.get('guests')
        table_number = request.form.get('table_number')
        
        # Admin overlap check
        duration = int(duration)
        start_dt = datetime.strptime(time, '%H:%M')
        from datetime import timedelta
        end_dt = start_dt + timedelta(hours=duration)
        new_start = start_dt.strftime('%H:%M')
        new_end = end_dt.strftime('%H:%M')

        # Check for overlaps
        reservations = Reservation.query.filter_by(date=date, table_number=table_number).all()
        overlap = False
        for res in reservations:
            if (new_start < res.end_time) and (new_end > res.time):
                overlap = True
                break
        
        if overlap:
            flash(f'คำเตือน: {table_number} มีการจองที่ทับซ้อนในช่วงเวลานี้ แต่ระบบแอดมินยังบันทึกให้ครับ', 'warning')

        new_reservation = Reservation(
            name=name,
            email=email or "Admin Booking",
            phone=phone,
            date=date,
            time=time,
            duration=duration,
            guests=guests,
            table_number=table_number
        )
        db.session.add(new_reservation)
        db.session.commit()
        flash('บันทึกการจองโดยแอดมินเรียบร้อยแล้ว!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/cancel/<int:reservation_id>', methods=['POST'])
@login_required
def admin_cancel(reservation_id):
    try:
        print(f"\n[DEBUG] Cancellation request for ID: {reservation_id}")
        reservation = Reservation.query.get(reservation_id)
        if reservation:
            name = reservation.name
            print(f"[DEBUG] Found reservation for {name}. Deleting...")
            db.session.delete(reservation)
            db.session.commit()
            print(f"[DEBUG] Successfully deleted ID {reservation_id}")
            flash(f'ยกเลิกรายการจองของ {name} เรียบร้อยแล้ว', 'success')
        else:
            print(f"[DEBUG] Reservation ID {reservation_id} NOT FOUND in database.")
            flash(f'ไม่พบรายการจองรหัส {reservation_id}', 'error')
    except Exception as e:
        db.session.rollback()
        print(f"[DEBUG] EXCEPTION during cancellation: {str(e)}")
        flash(f'เกิดข้อผิดพลาดในการยกเลิก: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/reserve', methods=['POST'])
def reserve():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        date = request.form.get('date')
        time = request.form.get('time')
        duration = request.form.get('duration', 1)
        guests = request.form.get('guests')
        table_number = request.form.get('table_number')
        message = request.form.get('message')

        # Overlap validation
        duration = int(duration)
        start_dt = datetime.strptime(time, '%H:%M')
        from datetime import timedelta
        end_dt = start_dt + timedelta(hours=duration)
        new_start = start_dt.strftime('%H:%M')
        new_end = end_dt.strftime('%H:%M')

        reservations = Reservation.query.filter_by(date=date, table_number=table_number).all()
        for res in reservations:
            if (new_start < res.end_time) and (new_end > res.time):
                flash(f'ขออภัยครับ {table_number} ถูกจองแล้วในช่วงเวลานี้ กรุณาเลือกโต๊ะอื่นหรือเวลาอื่นนะครับ', 'error')
                return redirect(url_for('index', _anchor='reservations'))

        new_reservation = Reservation(
            name=name,
            email=email,
            phone=phone,
            date=date,
            time=time,
            duration=duration,
            guests=guests,
            table_number=table_number,
            message=message
        )

        db.session.add(new_reservation)
        db.session.commit()
        
        flash('ขอบคุณครับ! เราได้รับการจองของคุณเรียบร้อยแล้ว แล้วเจอกันนะครับ', 'success')
        return redirect(url_for('index', _anchor='reservations'))
    
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return redirect(url_for('index', _anchor='reservations'))

@app.route('/admin')
@login_required
def admin():
    selected_date = request.args.get('date', get_thailand_today().strftime('%Y-%m-%d'))
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    
    # Organize data for the schedule grid
    tables = ["Table 1", "Table 2", "Table 3", "Table 4", "Table 5", "Table 6", "Table 7", "Table 8", "Meeting Room"]
    times = ["17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]
    
    # Grid structure: { table: { time: is_booked } }
    schedule = {table: {time: False for time in times} for table in tables}
    
    # Fill grid with actual reservations for the selected date
    day_reservations = Reservation.query.filter_by(date=selected_date).all()
    for res in day_reservations:
        if res.table_number in schedule:
            for slot_time in times:
                # Check if this specific slot time falls within the reservation range
                if res.time <= slot_time < res.end_time:
                    schedule[res.table_number][slot_time] = True
            
    return render_template('admin.html', 
                         reservations=reservations, 
                         schedule=schedule, 
                         tables=tables, 
                         times=times,
                         selected_date=selected_date)

if __name__ == '__main__':
    app.run(debug=True)
