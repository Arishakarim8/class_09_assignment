import sqlite3
import streamlit as st
import json
import os
from PIL import Image
from oop_project2 import is_premium_user, record_transaction
from footer import footer
TRANSACTION_FEE_RATE = 0.01  # 1%

def main(username):
    """Main function that takes username as parameter"""
    DATA_FILE = f"accounts_{username}.json"  # Separate file for each user

    class BalanceException(Exception):
        pass

    # Load account data from JSON
    def load_accounts():
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {}

    # Save account data to JSON
    def save_accounts(accounts):
        with open(DATA_FILE, "w") as f:
            json.dump(accounts, f, indent=4)

    # Bank Account Base Class
    class BankAccount:
        def __init__(self, name, balance=0):
            self.name = name
            self.balance = balance

        def get_balance(self):
            return self.balance

        def deposit(self, amount):
            self.balance += amount
            record_transaction(self.name, f"deposit to {self.name}", amount)
            return self.get_balance()
            

        def viable_transaction(self, amount):
            if self.balance >= amount:
                return
            raise BalanceException(f"Not enough funds in '{self.name}'. Balance: ${self.balance:.2f}")

        def withdraw(self, amount):
            try:
                self.viable_transaction(amount)
                self.balance -= amount
                record_transaction(self.name, f"Withdraw from {self.name}", amount)
                return self.get_balance()
            except BalanceException as error:
                raise BalanceException(f"Withdrawal interrupted: {error}")

        def transfer(self, amount, other):
            try:
                fee = amount * TRANSACTION_FEE_RATE if not is_premium_user(self.name) else 0
                self.viable_transaction(amount)
                self.withdraw(amount)
                other.deposit(amount)
                record_transaction(self.name, 
                         f"Transfer to {other.name}", 
                         amount, 
                         fee)
            except BalanceException as error:
                raise BalanceException(f"Transfer interrupted: {error}")

    class InterestRewardAcct(BankAccount):
        def deposit(self, amount):
            interest_rate = 1.10 if is_premium_user(self.name) else 1.05
            self.balance = self.balance + (amount * interest_rate)
            record_transaction(self.name, "deposit", amount)
            return self.get_balance()

    class SavingsAcct(InterestRewardAcct):
        def __init__(self, name, balance=0):
            super().__init__(name, balance)
            self.fee = 5

        def withdraw(self, amount):
            try:
                total_amount = amount + self.fee
                if not is_premium_user(self.name):
                        total_amount += amount * TRANSACTION_FEE_RATE  # Additional fee for non-premium
            
                self.viable_transaction(total_amount)
                self.balance = self.balance - total_amount
                record_transaction(self.name, "withdraw", amount, total_amount-amount)
                return self.get_balance()
            except BalanceException as error:
                raise BalanceException(f"\n Withdraw interrupted: {error}")

    # Streamlit Interface
    st.title(f"🏦 NeoBank - Welcome {username}")
    
    accounts = load_accounts()
    account_names = list(accounts.keys())

    # Account creation
    st.subheader("➕ Open Account")
    new_name = st.text_input("Account Name")
    new_type = st.selectbox("Account Type", ["BankAccount", "InterestRewardAcct", "SavingsAcct"])
    new_balance = st.number_input("Initial Balance", min_value=0.0, step=10.0)

    if st.button("Create Account"):
        if new_name in accounts:
            st.error("Account with this name already exists.")
        else:
            accounts[new_name] = {"balance": new_balance, "type": new_type}
            save_accounts(accounts)
            st.success(f"{new_type} '{new_name}' created with balance ${new_balance:.2f}")
            st.rerun()

    def apply_premium_benefits(username, account_type, balance):
        if is_premium_user(username):
            if account_type == "SavingsAcct":
                return balance * 1.10  # 10% higher interest for premium
        return balance
    
    st.subheader("⚙️ Manage Accounts")
    selected = st.selectbox("Select Your Account", account_names)

    acc = None

    if selected:
        acc_data = accounts[selected]
        if acc_data["type"] == "BankAccount":
            acc = BankAccount(selected, acc_data["balance"])
        elif acc_data["type"] == "InterestRewardAcct":
            acc = InterestRewardAcct(selected, acc_data["balance"])
        else:
            acc = SavingsAcct(selected, acc_data["balance"])

    if acc:
        st.write(f"### Current Balance: ${acc.get_balance():.2f}")

        current_balance = acc.get_balance()
        if is_premium_user(username) and isinstance(acc, SavingsAcct):
            st.metric("Balance with Premium Bonus", f"${current_balance * 1.10:.2f}", delta="10% premium bonus")
        else:
            st.metric("Available Balance", f"${current_balance:.2f}")

        if st.button("View Transaction History"):
            try:
                conn = sqlite3.connect('bank.db')
                c = conn.cursor()
        
                # First show debug info
                c.execute("SELECT COUNT(*) FROM transactions WHERE username=?", (username,))
                count = c.fetchone()[0]
                st.write(f"Found {count} transactions for user: {username}")
        
        # Get transactions
                c.execute("""
                    SELECT type, amount, fee, timestamp 
                    FROM transactions 
                    WHERE username = ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                """, (username,))
        
                transactions = c.fetchall()
        
                if transactions:
                    st.write("### Transaction History")
                    for t in transactions:
                        cols = st.columns([3, 2, 1])
                        with cols[0]:
                            st.write(f"**{t[0]}**")
                        with cols[1]:
                            st.write(f"${t[1]:.2f}")
                        with cols[2]:
                            st.caption(t[3].split('T')[0])  # Just show date
                
                        if t[2] > 0:
                            st.write(f"Fee: ${t[2]:.2f}")
                        st.divider()
                else:
                        st.info("No transactions found. Make a transaction to see history here.")
            
            except Exception as e:
                st.error(f"Error loading transactions: {e}")
            finally:
                conn.close()
    else:
        st.warning("Please select an account to manage")

    # Rest of your account management code...
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Available Balance", f"${acc.get_balance():.2f}")
        with col2:
            if is_premium_user(username):
                st.metric("Account Status", "Premium", delta="No fees")
            else:
                st.metric("Account Status", "Basic", delta="Upgrade to save on fees")


    action = st.selectbox("Action", ["Deposit", "Withdraw", "Transfer"])
    amount = st.number_input("Amount", min_value=0.0, step=10.0, key="amount")

    if action == "Deposit" and st.button("Deposit"):
        acc.deposit(amount)
        accounts[selected]["balance"] = acc.get_balance()
        save_accounts(accounts)
        st.success(f"Deposited ${amount:.2f}")

    elif action == "Withdraw" and st.button("Withdraw"):
        try:
            acc.withdraw(amount)
            accounts[selected]["balance"] = acc.get_balance()
            save_accounts(accounts)
            st.success(f"Withdrew ${amount:.2f}")
        except BalanceException as e:
            st.error(str(e))

    elif action == "Transfer":
        receiver = st.selectbox("Transfer To", [x for x in account_names if x != selected])
        if st.button("Transfer"):
            try:
                receiver_data = accounts[receiver]
                if receiver_data["type"] == "BankAccount":
                    receiver_acc = BankAccount(receiver, receiver_data["balance"])
                elif receiver_data["type"] == "InterestRewardAcct":
                    receiver_acc = InterestRewardAcct(receiver, receiver_data["balance"])
                else:
                    receiver_acc = SavingsAcct(receiver, receiver_data["balance"])

                acc.transfer(amount, receiver_acc)

                accounts[selected]["balance"] = acc.get_balance()
                accounts[receiver]["balance"] = receiver_acc.get_balance()
                save_accounts(accounts)
                st.success(f"Transferred ${amount:.2f} to {receiver}")
            except BalanceException as e:
                st.error(str(e))

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()


footer()