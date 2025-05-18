import streamlit as st
import sqlite3
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont  # Fixed import
import datetime
from streamlit.components.v1 import html

# Add these constants after imports
PREMIUM_COST = 5.0  # $5/month
# TRANSACTION_FEE_RATE = 0.01  # 1%
PARTNER_OFFERS = {
    "XYZ Restaurant": "10% cashback",
    "ABC Cinema": "1 free ticket per month",
    "QuickDelivery": "Free delivery on first order"
}

# Database setup
def init_db():
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, 
                  password TEXT,
                  full_name TEXT,
                  email TEXT)''')
    
    # Create accounts table
    c.execute('''CREATE TABLE IF NOT EXISTS accounts
                 (account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  account_type TEXT,
                  balance REAL DEFAULT 0.0,
                  FOREIGN KEY(username) REFERENCES users(username))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS premium_members
                 (username TEXT PRIMARY KEY,
                  since_date TEXT,
                  expiry_date TEXT,
                  FOREIGN KEY(username) REFERENCES users(username))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  type TEXT,
                  amount REAL,
                  fee REAL,
                  timestamp TEXT,
                  FOREIGN KEY(username) REFERENCES users(username))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS partner_usage
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  partner_name TEXT,
                  used INTEGER DEFAULT 0,
                  FOREIGN KEY(username) REFERENCES users(username))''')

    
    conn.commit()
    conn.close()

init_db()
def is_premium_user(username):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT * FROM premium_members WHERE username=? AND expiry_date > ?", 
             (username, datetime.datetime.now().isoformat()))
    result = c.fetchone()
    conn.close()
    return result is not None

def upgrade_to_premium(username):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    today = datetime.datetime.now()
    expiry = today + datetime.timedelta(days=30)  # 1 month
    
    try:
        c.execute("INSERT INTO premium_members VALUES (?, ?, ?)",
                 (username, today.isoformat(), expiry.isoformat()))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# def record_transaction(username, trans_type, amount, fee=0.0):
#     conn = sqlite3.connect('bank.db')
#     c = conn.cursor()
#     c.execute("INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?, ?)",
#              (username, trans_type, amount, fee, datetime.datetime.now().isoformat()))
#     conn.commit()
#     conn.close()
def record_transaction(username, trans_type, amount, fee=0.0):
    try:
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        c.execute("""
            INSERT INTO transactions 
            (username, type, amount, fee, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """, (username, trans_type, amount, fee, timestamp))
        conn.commit()
    except Exception as e:
        st.error(f"Failed to record transaction: {e}")
    finally:
        conn.close()

def show_ads():
    """Simulated ad display"""
    html("""
    <div style="border:1px solid #ccc; padding:10px; margin:10px 0; border-radius:5px;">
        <p style="color:gray; font-size:small;">Advertisement</p>
        <p>Special offer: Get 20% off on XYZ Services!</p>
    </div>
    """)

# Modify the run_bank_account function
def run_bank_account(username):
    """Function to run the banking system after login"""
    from Bank_account import main as bank_main
    
    # Premium account upsell
    if is_premium_user(username):
        conn = sqlite3.connect('bank.db')
        c = conn.cursor()
        c.execute("SELECT expiry_date FROM premium_members WHERE username=?", (username,))
        expiry = datetime.datetime.fromisoformat(c.fetchone()[0])
        conn.close()
    
    days_left = (expiry - datetime.datetime.now()).days
    if days_left <= 7:
        st.sidebar.warning(f"Premium expires in {days_left} days")
    if not is_premium_user(username):
        st.sidebar.subheader("Go Premium!")
        st.sidebar.write(f"Upgrade for ${PREMIUM_COST}/month and get:")
        st.sidebar.write("- No transaction fees")
        st.sidebar.write("- Higher interest rates")
        st.sidebar.write("- Exclusive partner offers")
        
        if st.sidebar.button("Upgrade Now"):
            if upgrade_to_premium(username):
                st.sidebar.success("Premium membership activated!")
            else:
                st.sidebar.error("Upgrade failed. Please try again.")
    
    # Partner offers section
    st.sidebar.subheader("Partner Offers")
    for partner, offer in PARTNER_OFFERS.items():
        with st.sidebar.expander(f"{partner}: {offer}"):
            st.write(f"Show this offer at {partner} to get {offer}")
            if st.button(f"Use {partner} Offer"):
                st.success(f"Offer activated! Visit {partner} to claim your {offer}")
    
    # Show ads for non-premium users
    if not is_premium_user(username):
        show_ads()
    
    # Run main banking interface
    bank_main(username)

# Modify the create_account function in Bank_account.py to include premium benefits
# Add this to your Bank_account.py:
def apply_premium_benefits(username, account_type, balance):
    if is_premium_user(username):
        if account_type == "SavingsAcct":
            return balance * 1.10  # 10% higher interest for premium
    return balance


# Logo and styling
def load_logo():
    try:
        # Try to open existing logo
        return Image.open("NBank.png")
    except FileNotFoundError:
        # Create a simple logo if file doesn't exist
        img = Image.new('RGB', (200, 100), color=(42, 92, 170))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        d.text((10,10), "ProfitPeak", fill=(255,215,0), font=font)
        img.save("NBank.png")
        return img

        
def add_funds(username, amount):
    """Add funds to user's primary account"""
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    try:
        # Get user's first account
        c.execute("SELECT account_id FROM accounts WHERE username=? LIMIT 1", (username,))
        account_id = c.fetchone()[0]
        
        # Update balance
        c.execute("UPDATE accounts SET balance = balance + ? WHERE account_id=?", 
                 (amount, account_id))
        
        # Record transaction
        record_transaction(username, "deposit", amount)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding funds: {e}")
        return False
    finally:
        conn.close()

def simulate_payment(username, amount):
    """Simulate payment processing"""
    if st.button(f"Add ${amount} via Paypal/Stripe"):
        if add_funds(username, amount):
            st.success(f"${amount} added successfully! (Simulated)")
            st.rerun()
        else:
            st.error("Failed to add funds")


# Authentication functions
def create_user(username, password, full_name, email):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                 (username, hashed_pwd, full_name, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
             (username, hashed_pwd))
    result = c.fetchone()
    conn.close()
    return result is not None

def run_bank_account(username):
    """Function to run the banking system after login"""
    from Bank_account import main as bank_main

    st.sidebar.subheader("Add Funds")
    amount = st.sidebar.selectbox("Amount", [10, 20, 50, 100, 200, 500], key="funds_amount")
    simulate_payment(username, amount)

    if is_premium_user(username):
        st.sidebar.success("⭐ Premium Member")
    else:
        st.sidebar.warning("Basic Member")
    # Premium account upsell

    # In the account management section
    # if is_premium_user(username):
    #     expiry_date = # get from database
    #     days_left = (expiry_date - datetime.datetime.now()).days
    #     st.sidebar.success(f"Premium Member ({days_left} days remaining)")
    #     st.sidebar.write("✨ Premium Benefits:")
    #     st.sidebar.write("- No transaction fees")
    #     st.sidebar.write("- Higher interest rates")
    # else:
    #     st.sidebar.warning("Basic Member")


    if not is_premium_user(username):
        st.sidebar.subheader("Go Premium!")
        st.sidebar.write(f"Upgrade for ${PREMIUM_COST}/month and get:")
        st.sidebar.write("- No transaction fees")
        st.sidebar.write("- Higher interest rates")
        st.sidebar.write("- Exclusive partner offers")
        
        if st.sidebar.button("Upgrade Now"):
            if upgrade_to_premium(username):
                st.sidebar.success("Premium membership activated!")
            else:
                st.sidebar.error("Upgrade failed. Please try again.")
        # Partner offers section
    st.sidebar.subheader("Partner Offers")
    for partner, offer in PARTNER_OFFERS.items():
        with st.sidebar.expander(f"{partner}: {offer}"):
            st.write(f"Show this offer at {partner} to get {offer}")
            if st.button(f"Use {partner} Offer"):
                st.success(f"Offer activated! Visit {partner} to claim your {offer}")
    
    # Show ads for non-premium users
    if not is_premium_user(username):
        show_ads()
    
    
    bank_main(username)  # Pass the username to Bank_account.py

# Main app
def main():
    st.set_page_config(
        page_title="ProfitPeak Bank",
        page_icon="🏦",
        layout="centered"
    )
    
    logo = load_logo()
    st.image(logo, width=200)
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Landing Page (if not logged in)
    if not st.session_state.logged_in:
        st.title("Welcome to NeoBank!")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("Login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if verify_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            with st.form("Sign Up"):
                st.subheader("Create New Account")
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                
                if st.form_submit_button("Sign Up"):
                    if new_password != confirm_password:
                        st.error("Passwords don't match!")
                    elif create_user(new_username, new_password, full_name, email):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")
    
    # After login - run the banking system
    else:
        run_bank_account(st.session_state.username)

if __name__ == "__main__":
    main()