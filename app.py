"""
Professional Streamlit Broadband Subscription Portal - Final Version
Complete with all features, CRUD operations, modern design, and enhanced UI

Designed by: G. Srinivasu & G. Viswesh
Designed for: DT Lab
"""

import streamlit as st
import sqlite3
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hashlib
import uuid
import plotly.express as px
import plotly.graph_objects as go
import random

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "broadband.db")
SALT = "broadband_demo_salt"
MOCK_DATA_CREATED = "mock_data_created"
DB_MIGRATED = "db_migrated_v5"

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

def get_conn():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def exec_query(query, params=(), fetch=False):
    """Execute query with error handling"""
    conn = None
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(query, params)
        if fetch:
            rows = c.fetchall()
            return rows
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return [] if fetch else False
    finally:
        if conn:
            conn.close()

def df_from_query(query, params=()):
    """Convert query results to DataFrame"""
    try:
        rows = exec_query(query, params, fetch=True)
        if not rows:
            return pd.DataFrame()
        cols = rows[0].keys()
        data = [tuple(r) for r in rows]
        return pd.DataFrame(data, columns=cols)
    except Exception as e:
        return pd.DataFrame()

def row_to_dict(row):
    """Convert row to dictionary"""
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}

def column_exists(table_name, column_name):
    """Check if column exists"""
    try:
        result = exec_query(f"PRAGMA table_info({table_name})", fetch=True)
        if result:
            columns = [row[1] for row in result]
            return column_name in columns
        return False
    except:
        return False

def add_column_if_not_exists(table_name, column_name, column_type, default_value=None):
    """Add column if not exists"""
    if not column_exists(table_name, column_name):
        try:
            default_clause = f" DEFAULT {default_value}" if default_value else ""
            exec_query(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}")
            return True
        except:
            return False
    return False

# ============================================================================
# DATABASE SCHEMA
# ============================================================================

def create_tables():
    """Create all database tables"""
    conn = get_conn()
    c = conn.cursor()
    
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            name TEXT,
            email TEXT,
            address TEXT,
            phone TEXT,
            city TEXT,
            state TEXT,
            is_autopay_enabled INTEGER DEFAULT 0,
            notification_preferences TEXT DEFAULT 'email,sms',
            referral_code TEXT UNIQUE,
            signup_date TEXT,
            last_login TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            speed_mbps INTEGER,
            upload_speed_mbps INTEGER,
            data_limit_gb REAL,
            price REAL,
            validity_days INTEGER,
            description TEXT,
            plan_type TEXT DEFAULT 'basic',
            is_unlimited INTEGER DEFAULT 0,
            features TEXT,
            created_date TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            auto_renew INTEGER DEFAULT 0,
            created_date TEXT,
            cancelled_date TEXT,
            cancellation_reason TEXT,
            renewal_count INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(plan_id) REFERENCES plans(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER,
            user_id INTEGER NOT NULL,
            amount REAL,
            payment_date TEXT,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'credit_card',
            bill_month INTEGER,
            bill_year INTEGER,
            late_fee REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            transaction_id TEXT,
            FOREIGN KEY(subscription_id) REFERENCES subscriptions(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT,
            data_used_gb REAL,
            peak_hour_usage REAL,
            off_peak_usage REAL,
            upload_usage REAL,
            average_speed REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT,
            description TEXT,
            category TEXT,
            status TEXT DEFAULT 'open',
            priority TEXT,
            created_date TEXT,
            resolved_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS wifi_credentials (
            user_id INTEGER PRIMARY KEY,
            wifi_username TEXT DEFAULT 'MyWiFi',
            wifi_password TEXT DEFAULT 'password123',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_user_id INTEGER NOT NULL,
            referred_email TEXT,
            status TEXT DEFAULT 'pending',
            reward_amount REAL DEFAULT 100,
            created_date TEXT,
            FOREIGN KEY(referrer_user_id) REFERENCES users(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS speed_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            download_speed REAL,
            upload_speed REAL,
            ping REAL,
            test_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS meta (
            k TEXT PRIMARY KEY,
            v TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER,
            title TEXT,
            message TEXT,
            notification_type TEXT DEFAULT 'general',
            is_read INTEGER DEFAULT 0,
            created_date TEXT,
            target_type TEXT DEFAULT 'specific',
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(recipient_id) REFERENCES users(id)
        )''')
        
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def migrate_database():
    """Migrate database schema"""
    try:
        if meta_get(DB_MIGRATED) == '1':
            return True
        
        add_column_if_not_exists('users', 'city', 'TEXT')
        add_column_if_not_exists('users', 'state', 'TEXT')
        add_column_if_not_exists('users', 'signup_date', 'TEXT')
        add_column_if_not_exists('users', 'last_login', 'TEXT')
        add_column_if_not_exists('users', 'notification_preferences', 'TEXT')
        add_column_if_not_exists('users', 'referral_code', 'TEXT')
        
        add_column_if_not_exists('plans', 'plan_type', 'TEXT')
        add_column_if_not_exists('plans', 'is_unlimited', 'INTEGER', '0')
        add_column_if_not_exists('plans', 'created_date', 'TEXT')
        add_column_if_not_exists('plans', 'features', 'TEXT')
        add_column_if_not_exists('plans', 'upload_speed_mbps', 'INTEGER')
        
        add_column_if_not_exists('subscriptions', 'created_date', 'TEXT')
        add_column_if_not_exists('subscriptions', 'cancelled_date', 'TEXT')
        add_column_if_not_exists('subscriptions', 'cancellation_reason', 'TEXT')
        add_column_if_not_exists('subscriptions', 'renewal_count', 'INTEGER', '0')
        
        add_column_if_not_exists('payments', 'payment_method', 'TEXT')
        add_column_if_not_exists('payments', 'late_fee', 'REAL', '0')
        add_column_if_not_exists('payments', 'discount', 'REAL', '0')
        add_column_if_not_exists('payments', 'tax_amount', 'REAL', '0')
        add_column_if_not_exists('payments', 'transaction_id', 'TEXT')
        
        add_column_if_not_exists('usage', 'peak_hour_usage', 'REAL')
        add_column_if_not_exists('usage', 'off_peak_usage', 'REAL')
        add_column_if_not_exists('usage', 'upload_usage', 'REAL')
        add_column_if_not_exists('usage', 'average_speed', 'REAL')
        
        ensure_default_admin()
        meta_set(DB_MIGRATED, '1')
        return True
    except:
        return False

def meta_get(k):
    """Get metadata value"""
    try:
        r = exec_query("SELECT v FROM meta WHERE k = ?", (k,), fetch=True)
        return r[0][0] if r else None
    except:
        return None

def meta_set(k, v):
    """Set metadata value"""
    try:
        exec_query("INSERT OR REPLACE INTO meta (k, v) VALUES (?, ?)", (k, v))
    except:
        pass

# ============================================================================
# AUTHENTICATION & PASSWORD
# ============================================================================

def hash_password(password):
    """Hash password with salt"""
    salt = SALT + uuid.uuid4().hex
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"

def verify_password(password, stored):
    """Verify password"""
    try:
        salt, h = stored.split('$')
        calc = hashlib.sha256((salt + password).encode()).hexdigest()
        return calc == h
    except:
        return False

def ensure_default_admin():
    """Ensure admin user exists"""
    try:
        r = exec_query("SELECT * FROM users WHERE username = ? AND role = ?", ("admin", "admin"), fetch=True)
        if not r:
            pw = hash_password("admin123")
            signup_date = (datetime.utcnow() - timedelta(days=365)).isoformat()
            referral_code = f"ADMIN{uuid.uuid4().hex[:6].upper()}"
            exec_query(
                "INSERT INTO users (username, password_hash, role, name, email, signup_date, city, state, referral_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("admin", pw, "admin", "Administrator", "admin@broadband.com", signup_date, "Mumbai", "Maharashtra", referral_code)
            )
        
        # Create default plans if they don't exist
        create_default_plans()
    except:
        pass

def create_default_plans():
    """Create default broadband plans"""
    try:
        existing = exec_query("SELECT COUNT(*) FROM plans", fetch=True)
        if existing and existing[0][0] > 0:
            return
        
        plans = [
            # Daily Plans - 28 Days
            ("Smart 1GB Daily", 50, 10, 28, 28*1, 299, "1GB per day, perfect for basic browsing and social media", "basic", "Unlimited calls, Free router, 24x7 support", 0),
            ("Super 1.5GB Daily", 100, 20, 28, 28*1.5, 399, "1.5GB per day, ideal for streaming and video calls", "standard", "Unlimited calls, Free router, 24x7 support, OTT benefits", 0),
            ("Premium 2GB Daily", 150, 30, 28, 28*2, 499, "2GB per day, great for HD streaming and gaming", "premium", "Unlimited calls, Free router, 24x7 support, OTT apps, Priority support", 0),
            ("Ultimate 3GB Daily", 200, 40, 28, 28*3, 699, "3GB per day, unlimited entertainment for families", "elite", "Unlimited calls, Free router, 24x7 support, Premium OTT, Priority support, No FUP", 0),
            
            # Daily Plans - 30 Days
            ("Smart Plus 1GB", 50, 10, 30, 30*1, 319, "1GB per day for 30 days, extended validity", "basic", "Unlimited calls, Free router, 24x7 support", 0),
            ("Super Plus 1.5GB", 100, 20, 30, 30*1.5, 429, "1.5GB per day for 30 days with more benefits", "standard", "Unlimited calls, Free router, 24x7 support, OTT benefits", 0),
            ("Premium Plus 2GB", 150, 30, 30, 30*2, 539, "2GB per day for 30 days, best for streaming", "premium", "Unlimited calls, Free router, 24x7 support, OTT apps, Priority support", 0),
            ("Ultimate Plus 3GB", 200, 40, 30, 30*3, 749, "3GB per day for 30 days, ultimate package", "elite", "Unlimited calls, Free router, 24x7 support, Premium OTT, Priority support, No FUP", 0),
            
            # Monthly Data Plans
            ("Monthly 75GB", 100, 20, 30, 75, 499, "75GB monthly data, flexible usage", "standard", "High-speed internet, Free router, Email support", 0),
            ("Monthly 100GB", 150, 30, 30, 100, 649, "100GB monthly data with faster speeds", "premium", "High-speed internet, Free router, Priority support, OTT apps", 0),
            ("Monthly 150GB", 200, 40, 30, 150, 849, "150GB monthly data for heavy users", "premium", "Ultra-fast speeds, Free router, Priority support, Premium OTT", 0),
            ("Monthly Unlimited", 300, 50, 30, 999999, 999, "Truly unlimited data with no FUP", "elite", "Ultra-fast speeds, Free router, 24x7 Priority support, All OTT apps", 1),
            
            # Half-Yearly Plans
            ("Half-Year 1GB Daily", 100, 20, 180, 180*1, 1699, "1GB per day for 6 months, great savings", "standard", "Unlimited calls, Free router, 24x7 support, OTT benefits, 6-month validity", 0),
            ("Half-Year 2GB Daily", 150, 30, 180, 180*2, 2799, "2GB per day for 6 months, maximum value", "premium", "Unlimited calls, Free router, Priority support, Premium OTT, 6-month validity", 0),
            ("Half-Year 500GB", 200, 40, 180, 500, 2499, "500GB for 6 months, flexible monthly usage", "premium", "High-speed internet, Free router, Priority support, OTT apps", 0),
            
            # Yearly Plans
            ("Annual 1GB Daily", 100, 20, 365, 365*1, 3299, "1GB per day for full year, best value", "premium", "Unlimited calls, Free router, 24x7 support, All OTT apps, 1-year validity", 0),
            ("Annual 2GB Daily", 150, 30, 365, 365*2, 4999, "2GB per day for full year, premium choice", "elite", "Unlimited calls, Free router, Priority support, Premium OTT, 1-year validity, No FUP", 0),
            ("Annual 1000GB", 200, 40, 365, 1000, 4499, "1TB data for full year, ultimate flexibility", "elite", "Ultra-fast speeds, Free router, 24x7 Priority support, All OTT apps", 0),
            ("Annual Unlimited", 300, 50, 365, 999999, 9999, "Truly unlimited for full year, no limits", "elite", "Blazing fast speeds, Free router, Dedicated support, All Premium OTT apps", 1),
        ]
        
        for plan in plans:
            name, speed, upload, validity, data, price, desc, ptype, features, unlimited = plan
            exec_query("""
                INSERT INTO plans (name, speed_mbps, upload_speed_mbps, validity_days, 
                                 data_limit_gb, price, description, plan_type, features, 
                                 is_unlimited, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, speed, upload, validity, data, price, desc, ptype, features, 
                  unlimited, datetime.utcnow().isoformat()))
    except:
        pass

# ============================================================================
# USER MANAGEMENT - CRUD OPERATIONS
# ============================================================================

def create_user(username, password, name, email, role='user', city='', state='', phone=''):
    """Create new user"""
    try:
        existing = exec_query("SELECT id FROM users WHERE username = ?", (username,), fetch=True)
        if existing:
            return False, "Username already exists"
        
        pw_hash = hash_password(password)
        signup_date = datetime.utcnow().isoformat()
        referral_code = f"REF{uuid.uuid4().hex[:8].upper()}"
        
        result = exec_query("""
            INSERT INTO users (username, password_hash, role, name, email, city, state, 
                             phone, signup_date, referral_code, is_autopay_enabled, 
                             notification_preferences)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, pw_hash, role, name, email, city, state, phone, signup_date, 
              referral_code, 0, 'email,sms'))
        
        return result, "User created successfully" if result else "Failed to create user"
    except Exception as e:
        return False, str(e)

def signin(username, password):
    """Sign in user"""
    try:
        r = exec_query("SELECT * FROM users WHERE username = ?", (username,), fetch=True)
        if r:
            row = r[0]
            if verify_password(password, row[2]):
                exec_query("UPDATE users SET last_login = ? WHERE id = ?", (datetime.utcnow().isoformat(), row[0]))
                return True, row_to_dict(row)
        return False, "Invalid credentials"
    except Exception as e:
        return False, str(e)

def get_user_by_id(uid):
    """Get user by ID"""
    try:
        r = exec_query("SELECT * FROM users WHERE id = ?", (uid,), fetch=True)
        return row_to_dict(r[0]) if r else None
    except:
        return None

def read_all_users(role_filter=None, search_term=''):
    """Read all users with filtering"""
    try:
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        
        if role_filter and role_filter != "All":
            query += " AND role = ?"
            params.append(role_filter)
        
        if search_term:
            query += " AND (username LIKE ? OR email LIKE ? OR name LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY id DESC"
        
        rows = exec_query(query, tuple(params), fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

def update_user(user_id, **kwargs):
    """Update user"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        allowed_fields = ['username', 'name', 'email', 'address', 'phone', 'city', 'state', 
                         'is_autopay_enabled', 'notification_preferences']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        
        if not updates:
            return False, "No fields to update"
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        
        result = exec_query(f"UPDATE users SET {set_clause} WHERE id = ?", tuple(values))
        return result, "User updated successfully" if result else "Failed to update user"
    except Exception as e:
        return False, str(e)

def delete_user(user_id):
    """Delete user (soft delete)"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        active_subs = exec_query(
            "SELECT COUNT(*) FROM subscriptions WHERE user_id = ? AND status = 'active'",
            (user_id,), fetch=True
        )
        
        if active_subs and active_subs[0][0] > 0:
            return False, "Cannot delete user with active subscriptions"
        
        result = exec_query("UPDATE users SET role = 'archived' WHERE id = ?", (user_id,))
        return result, "User deleted successfully" if result else "Failed to delete user"
    except Exception as e:
        return False, str(e)

def change_password(user_id, new_password):
    """Change user password"""
    try:
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters"
        
        pw_hash = hash_password(new_password)
        result = exec_query("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user_id))
        return result, "Password changed successfully" if result else "Failed to change password"
    except Exception as e:
        return False, str(e)

# ============================================================================
# PLAN MANAGEMENT - CRUD OPERATIONS
# ============================================================================

def create_plan(name, speed_mbps, data_limit_gb, price, validity_days, description, 
                plan_type='basic', is_unlimited=False, features='', upload_speed_mbps=10):
    """Create new plan"""
    try:
        if not name or price < 0:
            return False, "Invalid plan details"
        
        created_date = datetime.utcnow().isoformat()
        
        result = exec_query("""
            INSERT INTO plans (name, speed_mbps, upload_speed_mbps, data_limit_gb, price, 
                             validity_days, description, plan_type, is_unlimited, 
                             features, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, speed_mbps, upload_speed_mbps, data_limit_gb, price, validity_days, 
              description, plan_type, 1 if is_unlimited else 0, features, created_date))
        
        return result, "Plan created successfully" if result else "Failed to create plan"
    except Exception as e:
        return False, str(e)

def get_plan(plan_id):
    """Get plan by ID"""
    try:
        r = exec_query("SELECT * FROM plans WHERE id = ?", (plan_id,), fetch=True)
        return row_to_dict(r[0]) if r else None
    except:
        return None

def get_all_plans():
    """Get all plans"""
    try:
        rows = exec_query("SELECT * FROM plans WHERE name NOT LIKE '[ARCHIVED]%' ORDER BY price ASC", fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

def read_all_plans(plan_type_filter=None, price_min=None, price_max=None):
    """Read all plans with filtering"""
    try:
        query = "SELECT * FROM plans WHERE name NOT LIKE '[ARCHIVED]%'"
        params = []
        
        if plan_type_filter and plan_type_filter != "All":
            query += " AND plan_type = ?"
            params.append(plan_type_filter)
        
        if price_min is not None:
            query += " AND price >= ?"
            params.append(price_min)
        
        if price_max is not None:
            query += " AND price <= ?"
            params.append(price_max)
        
        query += " ORDER BY price ASC"
        
        rows = exec_query(query, tuple(params), fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

def update_plan(plan_id, **kwargs):
    """Update plan"""
    try:
        plan = get_plan(plan_id)
        if not plan:
            return False, "Plan not found"
        
        allowed_fields = ['name', 'speed_mbps', 'upload_speed_mbps', 'data_limit_gb', 
                         'price', 'validity_days', 'description', 'plan_type', 
                         'is_unlimited', 'features']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        
        if not updates:
            return False, "No fields to update"
        
        if 'is_unlimited' in updates:
            updates['is_unlimited'] = 1 if updates['is_unlimited'] else 0
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [plan_id]
        
        result = exec_query(f"UPDATE plans SET {set_clause} WHERE id = ?", tuple(values))
        return result, "Plan updated successfully" if result else "Failed to update plan"
    except Exception as e:
        return False, str(e)

def delete_plan(plan_id):
    """Delete plan (soft delete)"""
    try:
        plan = get_plan(plan_id)
        if not plan:
            return False, "Plan not found"
        
        active_subs = exec_query(
            "SELECT COUNT(*) FROM subscriptions WHERE plan_id = ? AND status = 'active'",
            (plan_id,), fetch=True
        )
        
        if active_subs and active_subs[0][0] > 0:
            return False, "Cannot delete plan with active subscriptions"
        
        result = exec_query("UPDATE plans SET name = ? WHERE id = ?", 
                           (f"[ARCHIVED] {plan['name']}", plan_id))
        return result, "Plan deleted successfully" if result else "Failed to delete plan"
    except Exception as e:
        return False, str(e)

def get_plan_stats(plan_id):
    """Get plan statistics"""
    try:
        plan = get_plan(plan_id)
        if not plan:
            return None
        
        active_count = exec_query(
            "SELECT COUNT(*) FROM subscriptions WHERE plan_id = ? AND status = 'active'",
            (plan_id,), fetch=True
        )
        
        revenue = exec_query(
            """SELECT COALESCE(SUM(py.amount), 0) FROM payments py 
               JOIN subscriptions s ON py.subscription_id = s.id 
               WHERE s.plan_id = ? AND py.status = 'paid'""",
            (plan_id,), fetch=True
        )
        
        return {
            'plan': plan,
            'active_subscriptions': active_count[0][0] if active_count else 0,
            'total_revenue': revenue[0][0] if revenue else 0
        }
    except:
        return None

# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

def get_user_active_subscription(user_id):
    """Get user's active subscription"""
    try:
        r = exec_query("""
            SELECT s.*, p.name, p.data_limit_gb, p.price, p.speed_mbps, 
                   p.validity_days, p.description, p.features, p.upload_speed_mbps, 
                   p.plan_type, p.is_unlimited
            FROM subscriptions s 
            JOIN plans p ON s.plan_id = p.id 
            WHERE s.user_id = ? AND s.status = 'active' 
            ORDER BY s.start_date DESC LIMIT 1
        """, (user_id,), fetch=True)
        return row_to_dict(r[0]) if r else None
    except:
        return None

def subscribe_to_plan(user_id, plan_id, auto_renew=1):
    """Subscribe user to plan"""
    try:
        plan = get_plan(plan_id)
        if not plan:
            return False, "Plan not found"
        
        exec_query("UPDATE subscriptions SET status = 'cancelled' WHERE user_id = ? AND status = 'active'", (user_id,))
        
        today = datetime.utcnow().date()
        end = today + timedelta(days=plan['validity_days'])
        
        result = exec_query("""
            INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status, 
                                      auto_renew, created_date, renewal_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, plan_id, today.isoformat(), end.isoformat(), 'active', auto_renew, 
              datetime.utcnow().isoformat(), 0))
        
        return result, "Subscribed successfully" if result else "Failed to subscribe"
    except Exception as e:
        return False, str(e)

def calculate_upgrade_price(current_sub, new_plan):
    """Calculate price for plan upgrade/downgrade"""
    try:
        if not current_sub:
            return new_plan['price'], "New subscription"
        
        # Calculate remaining days
        today = datetime.utcnow().date()
        end_date = datetime.fromisoformat(current_sub['end_date']).date()
        remaining_days = (end_date - today).days
        
        if remaining_days <= 0:
            return new_plan['price'], "Current plan expired, full price"
        
        # Calculate prorated amounts
        current_plan_price = current_sub['price']
        current_plan_validity = current_sub['validity_days']
        
        # Price per day for current and new plan
        current_per_day = current_plan_price / current_plan_validity
        new_per_day = new_plan['price'] / new_plan['validity_days']
        
        # Remaining value of current plan
        remaining_value = current_per_day * remaining_days
        
        # Cost for remaining days on new plan
        new_plan_cost = new_per_day * remaining_days
        
        # Net amount to pay
        amount_to_pay = new_plan_cost - remaining_value
        
        if amount_to_pay > 0:
            return round(amount_to_pay, 2), f"Upgrade for {remaining_days} days"
        else:
            return 0, f"Downgrade - ₹{abs(round(amount_to_pay, 2))} credit (refund not applicable)"
    except Exception as e:
        return new_plan['price'], "Error calculating - using full price"

def upgrade_plan(user_id, new_plan_id):
    """Upgrade or downgrade user plan"""
    try:
        current_sub = get_user_active_subscription(user_id)
        new_plan = get_plan(new_plan_id)
        
        if not new_plan:
            return False, "Plan not found"
        
        amount, description = calculate_upgrade_price(current_sub, new_plan)
        
        # Cancel current subscription
        if current_sub:
            exec_query("UPDATE subscriptions SET status = 'cancelled', cancelled_date = ? WHERE id = ?", 
                      (datetime.utcnow().isoformat(), current_sub['id']))
        
        # Create new subscription starting from today
        today = datetime.utcnow().date()
        
        if current_sub and (datetime.fromisoformat(current_sub['end_date']).date() - today).days > 0:
            # Use remaining days for upgrade/downgrade
            remaining_days = (datetime.fromisoformat(current_sub['end_date']).date() - today).days
            end = today + timedelta(days=remaining_days)
        else:
            # New plan with full validity
            end = today + timedelta(days=new_plan['validity_days'])
        
        result = exec_query("""
            INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status, 
                                      auto_renew, created_date, renewal_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, new_plan_id, today.isoformat(), end.isoformat(), 'active', 1, 
              datetime.utcnow().isoformat(), 0))
        
        if result:
            return True, f"{description} - Amount: ₹{amount}"
        else:
            return False, "Failed to upgrade plan"
    except Exception as e:
        return False, str(e)

# ============================================================================
# SUPPORT TICKETS
# ============================================================================

def submit_ticket(user_id, subject, description, category, priority):
    """Submit support ticket"""
    try:
        result = exec_query("""
            INSERT INTO support_tickets (user_id, subject, description, category, status, priority, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, subject, description, category, 'open', priority, datetime.utcnow().isoformat()))
        return result, "Ticket submitted successfully" if result else "Failed to submit ticket"
    except Exception as e:
        return False, str(e)

def get_user_tickets(user_id):
    """Get user's support tickets"""
    try:
        rows = exec_query("""
            SELECT * FROM support_tickets WHERE user_id = ? ORDER BY created_date DESC
        """, (user_id,), fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

def get_all_tickets():
    """Get all support tickets"""
    try:
        rows = exec_query("""
            SELECT t.*, u.username, u.email FROM support_tickets t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.created_date DESC
        """, fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

def update_ticket_status(ticket_id, new_status):
    """Update ticket status"""
    try:
        resolved_date = datetime.utcnow().isoformat() if new_status == 'resolved' else None
        result = exec_query("""
            UPDATE support_tickets SET status = ?, resolved_date = ? WHERE id = ?
        """, (new_status, resolved_date, ticket_id))
        return result, "Ticket updated successfully" if result else "Failed to update ticket"
    except Exception as e:
        return False, str(e)

# ============================================================================
# REFERRAL PROGRAM
# ============================================================================

def create_referral(referrer_user_id, referred_email):
    """Create referral"""
    try:
        result = exec_query("""
            INSERT INTO referrals (referrer_user_id, referred_email, status, reward_amount, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (referrer_user_id, referred_email, 'pending', 100.0, datetime.utcnow().isoformat()))
        return result, "Referral created successfully" if result else "Failed to create referral"
    except Exception as e:
        return False, str(e)

def get_user_referrals(user_id):
    """Get user referrals"""
    try:
        rows = exec_query("""
            SELECT * FROM referrals WHERE referrer_user_id = ? ORDER BY created_date DESC
        """, (user_id,), fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

# ============================================================================
# SPEED TESTS
# ============================================================================

def run_speed_test(user_id):
    """Run speed test simulation"""
    try:
        subscription = get_user_active_subscription(user_id)
        if not subscription:
            return False, None
        
        plan_speed = subscription['speed_mbps']
        download_speed = plan_speed * random.uniform(0.85, 0.98)
        upload_speed = download_speed * random.uniform(0.15, 0.25)
        ping = random.uniform(5, 30)
        
        exec_query("""
            INSERT INTO speed_tests (user_id, download_speed, upload_speed, ping, test_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, download_speed, upload_speed, ping, datetime.utcnow().isoformat()))
        
        return True, {
            'download_speed': round(download_speed, 2),
            'upload_speed': round(upload_speed, 2),
            'ping': round(ping, 2)
        }
    except:
        return False, None

def get_recent_speed_tests(user_id, limit=10):
    """Get recent speed tests"""
    try:
        rows = exec_query("""
            SELECT * FROM speed_tests WHERE user_id = ? ORDER BY test_date DESC LIMIT ?
        """, (user_id, limit), fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

def send_notification(sender_id, title, message, notification_type='general', 
                     recipient_ids=None, target_type='specific'):
    """Send notification to users"""
    try:
        sent_count = 0
        if target_type == 'all':
            users = read_all_users(role_filter='user')
            for user in users:
                result = exec_query("""
                    INSERT INTO notifications (sender_id, recipient_id, title, message, 
                                              notification_type, created_date, target_type, is_read)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (sender_id, user['id'], title, message, notification_type, 
                      datetime.utcnow().isoformat(), 'all', 0))
                if result:
                    sent_count += 1
        else:
            if recipient_ids:
                for recipient_id in recipient_ids:
                    result = exec_query("""
                        INSERT INTO notifications (sender_id, recipient_id, title, message, 
                                                  notification_type, created_date, target_type, is_read)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sender_id, recipient_id, title, message, notification_type, 
                          datetime.utcnow().isoformat(), 'specific', 0))
                    if result:
                        sent_count += 1
        
        return True, f"Notification sent successfully to {sent_count} users"
    except Exception as e:
        return False, str(e)

def get_user_notifications(user_id, unread_only=False):
    """Get notifications for user"""
    try:
        query = "SELECT * FROM notifications WHERE recipient_id = ?"
        params = [user_id]
        
        if unread_only:
            query += " AND is_read = 0"
        
        query += " ORDER BY created_date DESC"
        
        rows = exec_query(query, tuple(params), fetch=True)
        return [row_to_dict(r) for r in rows] if rows else []
    except:
        return []

def mark_notification_as_read(notification_id):
    """Mark notification as read"""
    try:
        result = exec_query("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        return result
    except:
        return False

def get_unread_count(user_id):
    """Get unread notification count"""
    try:
        result = exec_query("SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND is_read = 0", 
                           (user_id,), fetch=True)
        return result[0][0] if result else 0
    except:
        return 0

# ============================================================================
# DATA EXPORT
# ============================================================================

def export_users():
    """Export all users to CSV"""
    try:
        df = df_from_query("SELECT id, username, name, email, city, state, signup_date FROM users WHERE role != 'archived'")
        if df.empty:
            return None, "No users to export"
        return df.to_csv(index=False), "Export successful"
    except:
        return None, "Export failed"

def export_plans():
    """Export all plans to CSV"""
    try:
        df = df_from_query("SELECT * FROM plans WHERE name NOT LIKE '[ARCHIVED]%'")
        if df.empty:
            return None, "No plans to export"
        return df.to_csv(index=False), "Export successful"
    except:
        return None, "Export failed"

# ============================================================================
# STYLING
# ============================================================================

def load_css():
    """Load CSS styling with modern design"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif;
        color: #1a202c;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.8rem;
        border-radius: 16px;
        color: white;
        margin: 0.8rem 0;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.4);
    }
    
    .plan-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border: 2px solid #e5e7eb;
        border-radius: 16px;
        padding: 2rem;
        margin: 1.2rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .plan-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
        border-color: #667eea;
    }
    
    .plan-card.recommended {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 2px solid #10b981;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.2);
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-active {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    .status-inactive {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }
    
    .status-cancelled {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
    
    .status-pending {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
    }
    
    .alert-box {
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .alert-success {
        background: linear-gradient(135deg, #f0fdf4 0%, #dbeafe 100%);
        border-left-color: #10b981;
        color: #065f46;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
        border-left-color: #f59e0b;
        color: #92400e;
    }
    
    .alert-danger {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-left-color: #ef4444;
        color: #7f1d1d;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-left-color: #3b82f6;
        color: #0c2d6b;
    }
    
    .stButton > button {
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 0.8rem 1.5rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    .feature-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .feature-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_header():
    """Render attractive header"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3.5rem; margin-bottom: 0.5rem;'>📡 Comrades Telecom Services</h1>
        <p style='font-size: 1.2rem; color: #666; margin-top: 0;'>Lightning-Fast Internet at Your Fingertips</p>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, emoji=""):
    """Render metric card with emoji"""
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 1.1rem; opacity: 0.9; margin-bottom: 0.5rem;">{emoji} {label}</div>
        <div style="font-size: 2.5rem; font-weight: 800;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_plan_card(plan, is_current=False, is_recommended=False, current_user_id=None):
    """Render attractive plan card"""
    card_class = "plan-card"
    if is_recommended:
        card_class += " recommended"
    
    emoji_map = {
        'basic': '🌟',
        'standard': '⭐',
        'premium': '💎',
        'elite': '👑'
    }
    
    emoji = emoji_map.get(plan.get('plan_type', 'basic'), '📦')
    
    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"### {emoji} {plan.get('name', 'Plan')}")
        if is_current:
            st.markdown('<span class="status-badge status-active">✓ Current Plan</span>', unsafe_allow_html=True)
        if is_recommended:
            st.markdown('<span class="status-badge status-pending">⭐ Recommended</span>', unsafe_allow_html=True)
    
    with col2:
        if not is_current and current_user_id:
            if st.button(f"Subscribe 🚀", key=f"sub_{plan.get('id', 0)}", use_container_width=True):
                success, msg = subscribe_to_plan(current_user_id, plan['id'])
                if success:
                    st.success("✅ Subscribed successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚀 Speed", f"{plan.get('speed_mbps', 0)} Mbps")
    with col2:
        st.metric("💾 Data", f"{plan.get('data_limit_gb', 0)} GB")
    with col3:
        st.metric("💵 Price", f"₹{plan.get('price', 0)}")
    with col4:
        st.metric("📅 Validity", f"{plan.get('validity_days', 0)} days")
    
    st.write(f"**Description:** {plan.get('description', 'N/A')}")
    if plan.get('features'):
        st.write(f"**Features:** {plan['features']}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# USER DASHBOARD
# ============================================================================

def user_dashboard(user):
    """Render user dashboard"""
    render_header()
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 16px; margin-bottom: 2rem;'>
        <h2>👋 Welcome, {user.get('name', 'User')}!</h2>
        <p style='margin: 0; opacity: 0.9;'>Email: {user.get('email', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'user_section' not in st.session_state:
        st.session_state.user_section = 'current_plan'
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    sections = [
        (col1, 'current_plan', '📶 Plan'),
        (col2, 'speed_test', '🚀 Speed'),
        (col3, 'all_plans', '📋 Plans'),
        (col4, 'referral', '🎁 Refer'),
        (col5, 'history', '📜 History'),
        (col6, 'profile', '👤 Profile'),
        (col7, 'support', '🎫 Support'),
    ]
    
    for col, section, label in sections:
        with col:
            btn_type = "primary" if st.session_state.user_section == section else "secondary"
            if st.button(label, use_container_width=True, type=btn_type):
                st.session_state.user_section = section
    
    # Notifications button
    unread_count = get_unread_count(user['id'])
    if st.button(f"📬 Notifications ({unread_count})" if unread_count > 0 else "📬 Notifications", 
                 type="primary" if st.session_state.user_section == 'notifications' else "secondary"):
        st.session_state.user_section = 'notifications'
    
    st.markdown("---")
    
    current_sub = get_user_active_subscription(user['id'])
    
    if st.session_state.user_section == 'current_plan':
        st.markdown("## 📶 Current Plan")
        if current_sub:
            render_plan_card(current_sub, is_current=True)
        else:
            st.markdown("""
            <div class="alert-box alert-info">
                <h3>🔔 No Active Plan</h3>
                <p>Choose a plan below to get started with blazing-fast internet!</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### ⭐ Available Plans")
        all_plans = get_all_plans()[:5]
        for plan in all_plans:
            render_plan_card(plan, current_user_id=user['id'])
    
    elif st.session_state.user_section == 'speed_test':
        st.markdown("## 🚀 Speed Test")
        if current_sub:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("▶️ Run Speed Test", use_container_width=True):
                    with st.spinner("Running test... ⏳"):
                        import time
                        time.sleep(2)
                        success, result = run_speed_test(user['id'])
                        if success:
                            st.balloons()
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                        color: white; padding: 2rem; border-radius: 16px; text-align: center;'>
                                <h2>⬇️ {result['download_speed']} Mbps</h2>
                                <p>Download Speed</p>
                                <h3 style='margin-top: 1rem;'>⬆️ {result['upload_speed']} Mbps</h3>
                                <p>Upload Speed</p>
                                <h3 style='margin-top: 1rem;'>📡 {result['ping']} ms</h3>
                                <p>Ping</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("❌ Speed test failed")
            
            with col2:
                if st.button("📊 View History", use_container_width=True):
                    st.session_state.show_speed_history = not st.session_state.get('show_speed_history', False)
            
            if st.session_state.get('show_speed_history'):
                tests = get_recent_speed_tests(user['id'], 5)
                if tests:
                    df = pd.DataFrame(tests)
                    st.dataframe(df, use_container_width=True)
        else:
            st.markdown("""
            <div class="alert-box alert-warning">
                <h3>⚠️ Subscribe First</h3>
                <p>You need an active subscription to run speed tests.</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif st.session_state.user_section == 'all_plans':
        st.markdown("## 📋 All Available Plans")
        
        col1, col2 = st.columns(2)
        with col1:
            plan_type = st.selectbox("🎯 Filter by Type", ["All", "basic", "standard", "premium", "elite"])
        with col2:
            max_price = st.number_input("💰 Max Price", value=5000)
        
        plans = read_all_plans(
            plan_type_filter=plan_type if plan_type != "All" else None,
            price_max=max_price
        )
        
        for plan in plans:
            render_plan_card(plan, current_user_id=user['id'])
    
    elif st.session_state.user_section == 'referral':
        st.markdown("## 🎁 Referral Program")
        
        st.markdown("""
        <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white; padding: 2rem; border-radius: 16px; margin-bottom: 2rem;'>
            <h3 style='color: white; margin-top: 0;'>💰 Earn ₹100 for Every Referral!</h3>
            <p style='color: white; opacity: 0.9; margin-bottom: 0;'>
                Share your referral code and earn rewards when your friends subscribe
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔑 Your Referral Code")
            referral_code = user.get('referral_code', 'N/A')
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <h2 style='color: white; margin: 0; font-family: monospace;'>{referral_code}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 📊 Referral Statistics")
            referrals = get_user_referrals(user['id'])
            total_referrals = len(referrals)
            successful = len([r for r in referrals if r['status'] == 'completed'])
            pending = len([r for r in referrals if r['status'] == 'pending'])
            total_earned = sum([r['reward_amount'] for r in referrals if r['status'] == 'completed'])
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("👥 Total Referrals", total_referrals)
                st.metric("✅ Successful", successful)
            with col_b:
                st.metric("⏳ Pending", pending)
                st.metric("💰 Earned", f"₹{total_earned}")
        
        with col2:
            st.markdown("### ✉️ Send Invitation")
            with st.form("referral_form"):
                friend_email = st.text_input("📧 Friend's Email", placeholder="friend@example.com")
                friend_name = st.text_input("👤 Friend's Name (Optional)", placeholder="Optional")
                
                col_submit, col_clear = st.columns(2)
                with col_submit:
                    submit_referral = st.form_submit_button("📤 Send Invitation", use_container_width=True)
                with col_clear:
                    clear_form = st.form_submit_button("🔄 Clear", use_container_width=True)
                
                if submit_referral:
                    if friend_email:
                        existing = exec_query(
                            "SELECT id FROM referrals WHERE referrer_user_id = ? AND referred_email = ?",
                            (user['id'], friend_email), fetch=True
                        )
                        
                        if existing:
                            st.warning("⚠️ You've already referred this email")
                        else:
                            success, msg = create_referral(user['id'], friend_email)
                            if success:
                                st.success(f"✅ Invitation sent to {friend_email}!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    else:
                        st.error("❌ Please enter an email address")
            
            st.markdown("### 📋 How It Works")
            st.markdown("""
            1. 🔗 Share your referral code with friends
            2. 👥 They sign up using your code
            3. 💳 They subscribe to any plan
            4. 💰 You earn ₹100 reward instantly!
            """)
        
        if referrals:
            st.markdown("---")
            st.markdown("### 📜 Your Referral History")
            
            for referral in referrals:
                status_colors = {
                    'pending': '#f59e0b',
                    'completed': '#10b981',
                    'expired': '#ef4444'
                }
                status_icons = {
                    'pending': '⏳',
                    'completed': '✅',
                    'expired': '❌'
                }
                
                color = status_colors.get(referral['status'], '#6b7280')
                icon = status_icons.get(referral['status'], '📧')
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
                            border-left: 4px solid {color};
                            padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <strong>{icon} {referral['referred_email']}</strong>
                            <p style='margin: 0.25rem 0 0 0; color: #666; font-size: 0.9rem;'>
                                Created: {referral['created_date'][:10]}
                            </p>
                        </div>
                        <div style='text-align: right;'>
                            <span style='background: {color}; color: white; padding: 0.3rem 0.8rem;
                                        border-radius: 20px; font-size: 0.85rem; font-weight: 600;'>
                                {referral['status'].upper()}
                            </span>
                            <p style='margin: 0.25rem 0 0 0; font-weight: 600; color: {color};'>
                                ₹{referral['reward_amount']}
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-box alert-info">
                <p>📭 No referrals yet. Start inviting friends to earn rewards!</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif st.session_state.user_section == 'history':
        st.markdown("## 📜 Subscription History")
        
        subs_df = df_from_query("""
            SELECT s.start_date, s.end_date, s.status, p.name, p.price
            FROM subscriptions s 
            JOIN plans p ON s.plan_id = p.id 
            WHERE s.user_id = ? 
            ORDER BY s.start_date DESC
        """, (user['id'],))
        
        if not subs_df.empty:
            st.dataframe(subs_df, use_container_width=True)
        else:
            st.markdown("""
            <div class="alert-box alert-info">
                <p>📭 No subscription history yet</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif st.session_state.user_section == 'profile':
        st.markdown("## 👤 Profile Settings")
        
        tab1, tab2, tab3 = st.tabs(["📝 Edit Profile", "🔒 Change Password", "📶 Manage Plan"])
        
        with tab1:
            with st.form("profile_form"):
                name = st.text_input("👤 Name", value=user.get('name', ''))
                email = st.text_input("📧 Email", value=user.get('email', ''))
                phone = st.text_input("📱 Phone", value=user.get('phone', ''))
                city = st.text_input("🏙️ City", value=user.get('city', ''))
                
                if st.form_submit_button("💾 Save Profile"):
                    success, msg = update_user(user['id'], name=name, email=email, phone=phone, city=city)
                    if success:
                        st.success(f"✅ {msg}")
                        st.session_state.user = get_user_by_id(user['id'])
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        
        with tab2:
            with st.form("password_form"):
                new_password = st.text_input("🔑 New Password", type="password")
                confirm_password = st.text_input("🔑 Confirm New Password", type="password")
                
                if st.form_submit_button("🔐 Change Password"):
                    if not all([new_password, confirm_password]):
                        st.error("❌ Please fill all fields")
                    elif new_password != confirm_password:
                        st.error("❌ New passwords don't match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        success, msg = change_password(user['id'], new_password)
                        if success:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")
        
        with tab3:
            st.markdown("### 📶 Current Plan & Upgrade/Downgrade")
            
            current_sub = get_user_active_subscription(user['id'])
            
            if current_sub:
                # Show current plan details
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;'>
                    <h3 style='color: white; margin-top: 0;'>✅ Active Plan: {current_sub['name']}</h3>
                    <p style='margin: 0;'><strong>Speed:</strong> {current_sub['speed_mbps']} Mbps</p>
                    <p style='margin: 0;'><strong>Data:</strong> {current_sub['data_limit_gb']} GB</p>
                    <p style='margin: 0;'><strong>Price:</strong> ₹{current_sub['price']}</p>
                    <p style='margin: 0;'><strong>Valid Until:</strong> {current_sub['end_date']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Calculate remaining days
                today = datetime.utcnow().date()
                end_date = datetime.fromisoformat(current_sub['end_date']).date()
                remaining_days = (end_date - today).days
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📅 Days Remaining", remaining_days)
                with col2:
                    st.metric("💰 Current Price", f"₹{current_sub['price']}")
                
                st.markdown("---")
                st.markdown("### 🔄 Change Your Plan")
                
                # Plan selection
                all_plans = get_all_plans()
                
                # Filter out current plan
                available_plans = [p for p in all_plans if p['id'] != current_sub['plan_id']]
                
                if available_plans:
                    # Group plans by type
                    plan_types = {}
                    for plan in available_plans:
                        ptype = plan.get('plan_type', 'basic')
                        if ptype not in plan_types:
                            plan_types[ptype] = []
                        plan_types[ptype].append(plan)
                    
                    # Filter options
                    col1, col2 = st.columns(2)
                    with col1:
                        filter_type = st.selectbox("Filter by Type", ["All", "basic", "standard", "premium", "elite"])
                    with col2:
                        filter_validity = st.selectbox("Filter by Validity", ["All", "28 days", "30 days", "180 days", "365 days"])
                    
                    # Apply filters
                    filtered_plans = available_plans
                    if filter_type != "All":
                        filtered_plans = [p for p in filtered_plans if p.get('plan_type') == filter_type]
                    if filter_validity != "All":
                        validity_map = {"28 days": 28, "30 days": 30, "180 days": 180, "365 days": 365}
                        filtered_plans = [p for p in filtered_plans if p['validity_days'] == validity_map[filter_validity]]
                    
                    if filtered_plans:
                        selected_plan_id = st.selectbox(
                            "Select New Plan",
                            options=[p['id'] for p in filtered_plans],
                            format_func=lambda x: next((f"{p['name']} - ₹{p['price']} - {p['validity_days']} days" 
                                                       for p in filtered_plans if p['id'] == x), "")
                        )
                        
                        selected_plan = next((p for p in filtered_plans if p['id'] == selected_plan_id), None)
                        
                        if selected_plan:
                            # Show selected plan details
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;'>
                                <h4 style='color: white; margin-top: 0;'>📋 Selected Plan: {selected_plan['name']}</h4>
                                <p style='margin: 0;'><strong>Speed:</strong> {selected_plan['speed_mbps']} Mbps</p>
                                <p style='margin: 0;'><strong>Data:</strong> {selected_plan['data_limit_gb']} GB</p>
                                <p style='margin: 0;'><strong>Validity:</strong> {selected_plan['validity_days']} days</p>
                                <p style='margin: 0;'><strong>Features:</strong> {selected_plan.get('features', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Calculate upgrade cost
                            amount, description = calculate_upgrade_price(current_sub, selected_plan)
                            
                            st.markdown(f"""
                            <div class="alert-box alert-info">
                                <h4>💰 Pricing Details</h4>
                                <p><strong>New Plan Price:</strong> ₹{selected_plan['price']}</p>
                                <p><strong>Your Remaining Days:</strong> {remaining_days} days</p>
                                <p><strong>Calculation:</strong> {description}</p>
                                <h3 style='color: #667eea;'>Amount to Pay: ₹{amount}</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Confirm Change", use_container_width=True, type="primary"):
                                    success, msg = upgrade_plan(user['id'], selected_plan_id)
                                    if success:
                                        st.success(f"✅ Plan changed successfully! {msg}")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {msg}")
                            with col2:
                                st.info("ℹ️ Your current plan will be cancelled and new plan will be activated immediately")
                    else:
                        st.info("ℹ️ No plans available with selected filters")
                else:
                    st.info("ℹ️ No other plans available")
            else:
                st.markdown("""
                <div class="alert-box alert-warning">
                    <h3>⚠️ No Active Plan</h3>
                    <p>You don't have an active subscription. Please subscribe to a plan first.</p>
                </div>
                """, unsafe_allow_html=True)
    
    elif st.session_state.user_section == 'support':
        st.markdown("## 🎫 Support Tickets")
        
        with st.form("ticket_form"):
            subject = st.text_input("📝 Subject")
            category = st.selectbox("📂 Category", ['billing', 'technical', 'service', 'other'])
            priority = st.selectbox("⚡ Priority", ['low', 'medium', 'high'])
            description = st.text_area("📄 Description", height=150)
            
            if st.form_submit_button("📤 Submit Ticket"):
                if subject and description:
                    success, msg = submit_ticket(st.session_state.user['id'], subject, description, category, priority)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.error("❌ Please fill all fields")
        
        tickets = get_user_tickets(st.session_state.user['id'])
        if tickets:
            st.markdown("### Your Tickets")
            for ticket in tickets:
                status_icon = {'open': '🟡', 'in_progress': '🔵', 'resolved': '🟢', 'closed': '⚫'}.get(ticket['status'], '⚪')
                with st.expander(f"{status_icon} #{ticket['id']} - {ticket['subject']}"):
                    st.write(f"**Category:** {ticket['category']}")
                    st.write(f"**Priority:** {ticket['priority']}")
                    st.write(f"**Status:** {ticket['status']}")
                    st.write(f"**Description:** {ticket['description']}")
    
    elif st.session_state.user_section == 'notifications':
        st.markdown("## 📬 Your Notifications")
        
        notifications = get_user_notifications(st.session_state.user['id'])
        if notifications:
            unread = [n for n in notifications if not n['is_read']]
            read = [n for n in notifications if n['is_read']]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🆕 Unread", len(unread))
            with col2:
                st.metric("✅ Read", len(read))
            
            st.markdown("---")
            
            for notif in notifications:
                icon_map = {'general': '📢', 'alert': '🚨', 'maintenance': '🔧', 
                           'promotion': '🎯', 'urgent': '⛔'}
                icon = icon_map.get(notif['notification_type'], '📢')
                read_status = "✓" if notif['is_read'] else "🆕"
                
                with st.expander(f"{read_status} {icon} {notif['title']}"):
                    st.write(f"**From:** Admin")
                    st.write(f"**Type:** {notif['notification_type']}")
                    st.write(f"**Date:** {notif['created_date']}")
                    st.write(f"**Message:**\n{notif['message']}")
                    
                    if not notif['is_read']:
                        if st.button(f"✓ Mark as Read", key=f"notif_{notif['id']}"):
                            mark_notification_as_read(notif['id'])
                            st.rerun()
        else:
            st.markdown("""
            <div class="alert-box alert-info">
                <p>📭 No notifications yet</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Show section content based on user_section value
        pass
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem; margin-top: 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px; color: white;'>
        <p style='margin: 0; font-size: 1rem;'>💻 Designed by <strong>G. Srinivasu & G. Viswesh</strong></p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;'>🔬 Designed for DT Lab</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

def admin_dashboard(user):
    """Render admin dashboard"""
    render_header()
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 16px; margin-bottom: 2rem;'>
        <h2>⚙️ Admin Dashboard</h2>
        <p style='margin: 0; opacity: 0.9;'>Admin: {user.get('name', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'admin_section' not in st.session_state:
        st.session_state.admin_section = 'overview'
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    sections = [
        (col1, 'overview', '📊 Overview'),
        (col2, 'users', '👥 Users'),
        (col3, 'plans', '📋 Plans'),
        (col4, 'tickets', '🎫 Tickets'),
        (col5, 'notifications', '📢 Notify'),
    ]
    
    for col, section, label in sections:
        with col:
            btn_type = "primary" if st.session_state.admin_section == section else "secondary"
            if st.button(label, use_container_width=True, type=btn_type):
                st.session_state.admin_section = section
    
    st.markdown("---")
    
    if st.session_state.admin_section == 'overview':
        st.markdown("## 📊 Dashboard Overview")
        
        users_count = len(read_all_users(role_filter='user'))
        all_users_count = len(read_all_users())
        plans_count = len(get_all_plans())
        active_subs = exec_query("SELECT COUNT(*) FROM subscriptions WHERE status='active'", fetch=True)
        active_count = active_subs[0][0] if active_subs else 0
        revenue_result = exec_query('SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status="paid"', fetch=True)
        revenue = revenue_result[0][0] if revenue_result else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Regular Users", users_count, "👥")
        with col2:
            render_metric_card("Total Plans", plans_count, "📋")
        with col3:
            render_metric_card("Active Subs", active_count, "✅")
        with col4:
            render_metric_card("Revenue", f"₹{revenue:,.0f}", "💰")
    
    elif st.session_state.admin_section == 'notifications':
        admin_notifications(user)
    
    elif st.session_state.admin_section == 'users':
        st.markdown("## 👥 User Management")
        
        tab1, tab2, tab3, tab4 = st.tabs(["👁️ View Users", "➕ Create User", "🔍 User Details", "🔒 Reset Password"])
        
        with tab1:
            role_filter = st.selectbox("Filter by Role", ["All", "user", "admin"], key="user_role_filter")
            users = read_all_users(role_filter=role_filter if role_filter != "All" else None)
            
            if users:
                display_df = pd.DataFrame(users)
                if 'password_hash' in display_df.columns:
                    display_df = display_df.drop('password_hash', axis=1)
                
                st.dataframe(display_df, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Export Users"):
                        csv, msg = export_users()
                        if csv:
                            st.download_button("📥 Download CSV", csv, "users.csv", "text/csv")
                        else:
                            st.error(f"❌ {msg}")
                
                with col2:
                    st.metric("Total Users", len(users))
        
        with tab2:
            with st.form("create_user_form"):
                st.markdown("### Create New User")
                
                col1, col2 = st.columns(2)
                with col1:
                    username = st.text_input("👤 Username")
                    password = st.text_input("🔒 Password", type="password")
                    name = st.text_input("📝 Name")
                    email = st.text_input("📧 Email")
                
                with col2:
                    phone = st.text_input("📱 Phone")
                    city = st.text_input("🏙️ City")
                    state = st.text_input("🗺️ State")
                    role = st.selectbox("👔 Role", ["user", "admin"], help="Select 'admin' to create another administrator")
                
                st.markdown("---")
                
                col_create, col_info = st.columns([1, 2])
                with col_create:
                    submit_create = st.form_submit_button("✅ Create User", use_container_width=True)
                with col_info:
                    if role == "admin":
                        st.info("ℹ️ Creating an admin user will grant full system access")
                
                if submit_create:
                    if username and password and name and email:
                        success, msg = create_user(username, password, name, email, role=role, 
                                                  city=city, state=state, phone=phone)
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("❌ Please fill required fields (username, password, name, email)")
        
        with tab3:
            st.markdown("### 🔍 View User Details")
            search_term = st.text_input("🔍 Search by username, email, or name")
            
            if search_term:
                users = read_all_users(search_term=search_term)
                if users:
                    user_options = {f"{u['username']} ({u['email']})": u['id'] for u in users}
                    selected_user_key = st.selectbox("Select User", list(user_options.keys()))
                    
                    if selected_user_key:
                        selected_user_id = user_options[selected_user_key]
                        user_data = get_user_by_id(selected_user_id)
                        
                        if user_data:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 📋 User Information")
                                st.write(f"**ID:** {user_data['id']}")
                                st.write(f"**Username:** {user_data['username']}")
                                st.write(f"**Name:** {user_data.get('name', 'N/A')}")
                                st.write(f"**Email:** {user_data.get('email', 'N/A')}")
                                st.write(f"**Phone:** {user_data.get('phone', 'N/A')}")
                                st.write(f"**Role:** {user_data['role']}")
                            
                            with col2:
                                st.markdown("#### 📍 Location & Status")
                                st.write(f"**City:** {user_data.get('city', 'N/A')}")
                                st.write(f"**State:** {user_data.get('state', 'N/A')}")
                                st.write(f"**Signup Date:** {user_data.get('signup_date', 'N/A')[:10] if user_data.get('signup_date') else 'N/A'}")
                                st.write(f"**Last Login:** {user_data.get('last_login', 'N/A')[:10] if user_data.get('last_login') else 'Never'}")
                                st.write(f"**Referral Code:** {user_data.get('referral_code', 'N/A')}")
                            
                            st.markdown("---")
                            st.markdown("#### 🔐 Password Hash")
                            st.code(user_data['password_hash'], language=None)
                            
                            st.markdown("---")
                            st.markdown("#### 📊 User Activity")
                            
                            active_sub = get_user_active_subscription(user_data['id'])
                            if active_sub:
                                st.success(f"✅ Active Plan: {active_sub['name']}")
                            else:
                                st.info("ℹ️ No active subscription")
                            
                            referrals = get_user_referrals(user_data['id'])
                            st.write(f"**Referrals Made:** {len(referrals)}")
                            
                            tickets = get_user_tickets(user_data['id'])
                            st.write(f"**Support Tickets:** {len(tickets)}")
                            
                            st.markdown("---")
                            
                            with st.form("admin_update_user_form"):
                                st.markdown("#### ✏️ Update User Information")
                                new_name = st.text_input("📝 Name", value=user_data.get('name', ''))
                                new_email = st.text_input("📧 Email", value=user_data.get('email', ''))
                                new_phone = st.text_input("📱 Phone", value=user_data.get('phone', ''))
                                new_city = st.text_input("🏙️ City", value=user_data.get('city', ''))
                                new_state = st.text_input("🗺️ State", value=user_data.get('state', ''))
                                
                                if st.form_submit_button("✅ Update User", use_container_width=True):
                                    success, msg = update_user(selected_user_id, name=new_name, 
                                                              email=new_email, phone=new_phone,
                                                              city=new_city, state=new_state)
                                    if success:
                                        st.success(f"✅ {msg}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {msg}")
                else:
                    st.warning("⚠️ No users found matching your search")
        
        with tab4:
            st.markdown("### 🔒 Reset User Password")
            st.markdown("""
            <div class="alert-box alert-warning">
                <strong>⚠️ Warning:</strong> This will reset the user's password. 
                Make sure to inform the user of their new password.
            </div>
            """, unsafe_allow_html=True)
            
            users = read_all_users()
            if users:
                user_options = {f"{u['id']} - {u['username']} ({u['email']})": u['id'] for u in users}
                selected_user_key = st.selectbox("Select User to Reset Password", list(user_options.keys()))
                
                if selected_user_key:
                    selected_user_id = user_options[selected_user_key]
                    user_info = get_user_by_id(selected_user_id)
                    
                    if user_info:
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;'>
                            <h4 style='color: white; margin-top: 0;'>Selected User:</h4>
                            <p style='margin: 0;'><strong>Username:</strong> {user_info['username']}</p>
                            <p style='margin: 0;'><strong>Email:</strong> {user_info.get('email', 'N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.form("reset_password_form"):
                            new_password = st.text_input("🔑 New Password", type="password", 
                                                        placeholder="Enter new password (min 6 characters)")
                            confirm_new_password = st.text_input("🔑 Confirm New Password", type="password",
                                                                placeholder="Confirm new password")
                            
                            admin_confirm = st.checkbox("⚠️ I confirm that I want to reset this user's password")
                            
                            if st.form_submit_button("🔐 Reset Password", use_container_width=True):
                                if not admin_confirm:
                                    st.error("❌ Please confirm that you want to reset the password")
                                elif not new_password or not confirm_new_password:
                                    st.error("❌ Please fill both password fields")
                                elif new_password != confirm_new_password:
                                    st.error("❌ Passwords don't match")
                                elif len(new_password) < 6:
                                    st.error("❌ Password must be at least 6 characters")
                                else:
                                    success, msg = change_password(selected_user_id, new_password)
                                    if success:
                                        st.success(f"✅ {msg}")
                                        st.balloons()
                                        st.markdown(f"""
                                        <div class="alert-box alert-success">
                                            <h4>✅ Password Reset Successful!</h4>
                                            <p><strong>Username:</strong> {user_info['username']}</p>
                                            <p><strong>New Password:</strong> <code>{new_password}</code></p>
                                            <p>⚠️ Please inform the user of their new password securely.</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.error(f"❌ {msg}")
    
    elif st.session_state.admin_section == 'plans':
        st.markdown("## 📋 Plan Management")
        
        tab1, tab2, tab3 = st.tabs(["👁️ View Plans", "➕ Create Plan", "✏️ Edit Plan"])
        
        with tab1:
            plans = get_all_plans()
            if plans:
                st.dataframe(pd.DataFrame(plans), use_container_width=True)
                
                if st.button("📥 Export Plans"):
                    csv, msg = export_plans()
                    if csv:
                        st.download_button("📥 Download CSV", csv, "plans.csv", "text/csv")
                    else:
                        st.error(f"❌ {msg}")
        
        with tab2:
            with st.form("create_plan_form"):
                name = st.text_input("📝 Plan Name")
                speed = st.number_input("🚀 Speed (Mbps)", min_value=1, value=50)
                upload = st.number_input("⬆️ Upload Speed (Mbps)", min_value=1, value=10)
                data = st.number_input("💾 Data Limit (GB)", min_value=0.0, value=100.0)
                price = st.number_input("💰 Price (₹)", min_value=0.0, value=500.0)
                validity = st.number_input("📅 Validity (Days)", min_value=1, value=30)
                plan_type = st.selectbox("🎯 Plan Type", ["basic", "standard", "premium", "elite"])
                description = st.text_area("📝 Description")
                features = st.text_input("✨ Features (comma-separated)")
                
                if st.form_submit_button("✅ Create Plan"):
                    if name and description:
                        success, msg = create_plan(name, speed, data, price, validity, description, 
                                                  plan_type=plan_type, features=features, upload_speed_mbps=upload)
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("❌ Please fill required fields")
        
        with tab3:
            plan_id = st.number_input("📋 Plan ID to Edit", min_value=1)
            if st.button("Load Plan"):
                plan = get_plan(plan_id)
                if plan:
                    with st.form("update_plan_form"):
                        new_name = st.text_input("📝 Name", value=plan.get('name', ''))
                        new_speed = st.number_input("🚀 Speed (Mbps)", value=plan.get('speed_mbps', 50))
                        new_price = st.number_input("💰 Price (₹)", value=plan.get('price', 500.0))
                        new_description = st.text_area("📝 Description", value=plan.get('description', ''))
                        
                        if st.form_submit_button("✅ Update Plan"):
                            success, msg = update_plan(plan_id, name=new_name, speed_mbps=new_speed, 
                                                      price=new_price, description=new_description)
                            if success:
                                st.success(f"✅ {msg}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                else:
                    st.error("❌ Plan not found")
    
    elif st.session_state.admin_section == 'tickets':
        st.markdown("## 🎫 Support Tickets")
        
        tickets = get_all_tickets()
        if tickets:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total", len(tickets))
            with col2:
                st.metric("🟡 Open", len([t for t in tickets if t['status'] == 'open']))
            with col3:
                st.metric("🟢 Resolved", len([t for t in tickets if t['status'] == 'resolved']))
            with col4:
                st.metric("🔴 Priority", len([t for t in tickets if t['priority'] == 'high']))
            
            st.dataframe(pd.DataFrame(tickets), use_container_width=True)
            
            ticket_id = st.number_input("🎫 Ticket ID", min_value=1)
            new_status = st.selectbox("📊 New Status", ['open', 'in_progress', 'resolved', 'closed'])
            
            if st.button("✅ Update Ticket"):
                success, msg = update_ticket_status(ticket_id, new_status)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
        else:
            st.markdown("""
            <div class="alert-box alert-info">
                <p>📭 No support tickets</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem; margin-top: 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px; color: white;'>
        <p style='margin: 0; font-size: 1rem;'>💻 Designed by <strong>G. Srinivasu & G. Viswesh</strong></p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;'>🔬 Designed for DT Lab</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ADMIN NOTIFICATIONS SECTION
# ============================================================================

def admin_notifications(user):
    """Render admin notifications management"""
    st.markdown("## 📢 Send Notifications")
    
    if 'notifications_section' not in st.session_state:
        st.session_state.notifications_section = 'send'
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Send Notification", use_container_width=True,
                    type="primary" if st.session_state.notifications_section == 'send' else "secondary"):
            st.session_state.notifications_section = 'send'
    with col2:
        if st.button("📬 View Sent", use_container_width=True,
                    type="primary" if st.session_state.notifications_section == 'view' else "secondary"):
            st.session_state.notifications_section = 'view'
    
    st.markdown("---")
    
    if st.session_state.notifications_section == 'send':
        st.markdown("### 📤 Send New Notification")
        
        with st.form("send_notification_form"):
            title = st.text_input("📝 Notification Title", placeholder="e.g., Maintenance Update")
            message = st.text_area("💬 Message", placeholder="Write your notification message", height=150)
            notification_type = st.selectbox("🏷️ Type", ['general', 'alert', 'maintenance', 'promotion', 'urgent'])
            
            target_option = st.radio("👥 Send To", ["All Users", "Selected Users"])
            
            selected_user_ids = []
            if target_option == "Selected Users":
                users = read_all_users(role_filter='user')
                if users:
                    user_options = {f"{u['username']} - {u['email']} (ID: {u['id']})": u['id'] for u in users}
                    selected_keys = st.multiselect("Choose Users", list(user_options.keys()), key="user_select")
                    selected_user_ids = [user_options[k] for k in selected_keys]
                else:
                    st.warning("⚠️ No users available")
            
            col_submit, col_preview = st.columns(2)
            with col_submit:
                submit_btn = st.form_submit_button("✅ Send Notification", use_container_width=True)
            with col_preview:
                preview_btn = st.form_submit_button("👁️ Preview", use_container_width=True)
            
            if preview_btn and title and message:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;'>
                    <h4 style='color: white; margin-top: 0;'>📧 {title}</h4>
                    <p style='color: white; opacity: 0.9;'>{message}</p>
                    <p style='color: white; opacity: 0.7; font-size: 0.85rem; margin: 0;'>
                        Type: {notification_type} | Target: {target_option}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            if submit_btn:
                if not title or not message:
                    st.error("❌ Please fill all fields")
                else:
                    if target_option == "All Users":
                        success, msg = send_notification(user['id'], title, message, notification_type, 
                                                        target_type='all')
                    else:
                        if selected_user_ids:
                            success, msg = send_notification(user['id'], title, message, notification_type,
                                                           recipient_ids=selected_user_ids, target_type='specific')
                        else:
                            success = False
                            msg = "Please select at least one user"
                    
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        
                        if target_option == "All Users":
                            user_count = len(read_all_users(role_filter='user'))
                            st.info(f"📧 Notification sent to {user_count} users")
                        else:
                            st.info(f"📧 Notification sent to {len(selected_user_ids)} users")
                    else:
                        st.error(f"❌ {msg}")
    
    elif st.session_state.notifications_section == 'view':
        st.markdown("### 📬 Sent Notifications")
        
        all_notifications = exec_query("""
            SELECT n.*, COUNT(DISTINCT n.recipient_id) as recipient_count
            FROM notifications n
            WHERE n.sender_id = ?
            GROUP BY n.id
            ORDER BY n.created_date DESC
        """, (user['id'],), fetch=True)
        
        if all_notifications:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📧 Total Sent", len(all_notifications))
            with col2:
                total_recipients = sum([row[9] for row in all_notifications])
                st.metric("👥 Total Recipients", total_recipients)
            with col3:
                recent = len([n for n in all_notifications if 
                             (datetime.utcnow() - datetime.fromisoformat(n[7])).days < 7])
                st.metric("🆕 Last 7 Days", recent)
            
            st.markdown("---")
            
            for notif_row in all_notifications:
                notif_dict = row_to_dict(notif_row)
                icon_map = {'general': '📢', 'alert': '🚨', 'maintenance': '🔧', 
                           'promotion': '🎯', 'urgent': '⛔'}
                icon = icon_map.get(notif_dict['notification_type'], '📢')
                
                created_date = notif_dict['created_date'][:19] if notif_dict['created_date'] else 'Unknown'
                
                with st.expander(f"{icon} {notif_dict['title']} - {created_date}"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**Recipients:** {notif_dict.get('recipient_count', 0)} users")
                    with col2:
                        st.write(f"**Type:** {notif_dict['notification_type']}")
                    with col3:
                        st.write(f"**Target:** {notif_dict['target_type']}")
                    with col4:
                        read_count = exec_query(
                            "SELECT COUNT(*) FROM notifications WHERE id = ? AND is_read = 1",
                            (notif_dict['id'],), fetch=True
                        )
                        read = read_count[0][0] if read_count else 0
                        st.write(f"**Read:** {read}/{notif_dict.get('recipient_count', 0)}")
                    
                    st.markdown("**Message:**")
                    st.markdown(f"""
                    <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px;
                                border-left: 4px solid #667eea;'>
                        {notif_dict['message']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-box alert-info">
                <p>📭 No notifications sent yet</p>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# AUTHENTICATION PAGE
# ============================================================================

def auth_page():
    """Render login/signup page"""
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'signin'
    
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 4rem; margin-bottom: 0.5rem;'>📡</h1>
        <h1 style='font-size: 3.5rem; margin-bottom: 0.5rem; 
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;'>
            Comrades Telecom Services
        </h1>
        <p style='font-size: 1.3rem; color: #666; margin-top: 0; font-weight: 500;'>
            🚀 Lightning-Fast Internet at Your Fingertips
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Top navigation buttons - centered
    col_spacer1, col1, col2, col_spacer2 = st.columns([2, 1, 1, 2])
    with col1:
        if st.button("🔐 SIGN IN", use_container_width=True, 
                    type="primary" if st.session_state.auth_mode == 'signin' else "secondary"):
            st.session_state.auth_mode = 'signin'
    with col2:
        if st.button("📝 SIGN UP", use_container_width=True,
                    type="primary" if st.session_state.auth_mode == 'signup' else "secondary"):
            st.session_state.auth_mode = 'signup'
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f8f9ff 0%, #e8ecff 100%);
                border-radius: 20px; padding: 2rem; margin: 2rem 0;
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);'>
        <h2 style='text-align: center; margin-bottom: 1.5rem; color: #667eea;'>✨ Why Choose Us?</h2>
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem;'>
            <div class='feature-box' style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;'>
                <div class='feature-icon'>🚀</div>
                <h3 style='color: white;'>Ultra Fast</h3>
                <p style='color: white; opacity: 0.9;'>Up to 1000 Mbps</p>
            </div>
            <div class='feature-box' style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white;'>
                <div class='feature-icon'>💰</div>
                <h3 style='color: white;'>Best Prices</h3>
                <p style='color: white; opacity: 0.9;'>Starting ₹299</p>
            </div>
            <div class='feature-box' style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white;'>
                <div class='feature-icon'>⏰</div>
                <h3 style='color: white;'>24/7 Support</h3>
                <p style='color: white; opacity: 0.9;'>Always Ready</p>
            </div>
            <div class='feature-box' style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white;'>
                <div class='feature-icon'>🎁</div>
                <h3 style='color: white;'>Referrals</h3>
                <p style='color: white; opacity: 0.9;'>Earn ₹100</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.auth_mode == 'signin':
            st.markdown("""
            <div style='background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
                        border-radius: 20px; padding: 2.5rem; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
                <h2 style='text-align: center; margin-bottom: 1.5rem;'>🔐 Sign In to Your Account</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("signin_form", clear_on_submit=False):
                username = st.text_input("👤 Username", placeholder="Enter your username", key="signin_username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password", key="signin_password")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    signin_btn = st.form_submit_button("🔓 Sign In", use_container_width=True)
                with col_btn2:
                    if st.form_submit_button("📝 Create Account Instead", use_container_width=True):
                        st.session_state.auth_mode = 'signup'
                        st.rerun()
                
                if signin_btn:
                    if username and password:
                        success, result = signin(username, password)
                        if success:
                            st.session_state.user = result
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
                    else:
                        st.error("❌ Please fill all fields")
        
        else:  # signup mode
            st.markdown("""
            <div style='background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
                        border-radius: 20px; padding: 2.5rem; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
                <h2 style='text-align: center; margin-bottom: 1.5rem;'>📝 Create Your Account</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("signup_form", clear_on_submit=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    username = st.text_input("👤 Username", placeholder="Choose a unique username", key="signup_username")
                    password = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters", key="signup_password")
                    name = st.text_input("👤 Full Name", placeholder="Your full name", key="signup_name")
                
                with col_b:
                    confirm_pass = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm password", key="signup_confirm")
                    email = st.text_input("📧 Email", placeholder="your@email.com", key="signup_email")
                    city = st.text_input("🏙️ City", value="Mumbai", key="signup_city")
                
                referral_code_input = st.text_input("🎁 Referral Code (Optional)", placeholder="Enter referral code if you have one", key="signup_referral")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    signup_btn = st.form_submit_button("🎉 Create Account", use_container_width=True)
                with col_btn2:
                    if st.form_submit_button("🔐 Already have account?", use_container_width=True):
                        st.session_state.auth_mode = 'signin'
                        st.rerun()
                
                if signup_btn:
                    if not all([username, password, name, email]):
                        st.error("❌ Please fill all required fields")
                    elif password != confirm_pass:
                        st.error("❌ Passwords don't match")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        success, msg = create_user(username, password, name, email, city=city)
                        if success:
                            st.success("✅ Account created successfully!")
                            # Auto login
                            success, result = signin(username, password)
                            if success:
                                st.session_state.user = result
                                st.balloons()
                                st.rerun()
                        else:
                            st.error(f"❌ {msg}")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; margin-top: 4rem; padding: 2rem; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px; color: white;'>
        <p style='margin: 0; font-size: 1rem;'>💻 Designed by <strong>G. Srinivasu & G. Viswesh</strong></p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;'>🔬 Designed for DT Lab</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application"""
    st.set_page_config(
        page_title="Comrades Telecom Services",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    load_css()
    create_tables()
    migrate_database()
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if st.session_state.user:
        # Top navigation bar
        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
        
        with col1:
            st.markdown(f"**Logged in as:** {st.session_state.user['username']} ({st.session_state.user['role']})")
        
        with col2:
            unread_count = get_unread_count(st.session_state.user['id'])
            if unread_count > 0:
                st.markdown(f"**📬 {unread_count}** new notifications")
        
        with col4:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.user_section = None
                st.session_state.admin_section = None
                st.rerun()
        
        if st.session_state.user['role'] == 'admin':
            admin_dashboard(st.session_state.user)
        else:
            user_dashboard(st.session_state.user)
    else:
        auth_page()

if __name__ == "__main__":
    main()

""" Viswesh
DT LAB"""
