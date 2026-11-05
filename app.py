
import streamlit as st
import json
import secrets
import hashlib
import hmac
import re
from pathlib import Path


# ==========================================
# BANK CLASS
# ==========================================

class Bank:

    database = Path(__file__).parent / "data.json"

    # --------------------------------------
    # Load existing data
    # --------------------------------------

    @classmethod
    def load_data(cls):

        if not cls.database.exists():
            return []

        try:
            with open(cls.database, "r") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Invalid database format")

            return data

        except (json.JSONDecodeError, ValueError) as err:
            st.error(f"Database error: {err}")
            return []

    # --------------------------------------
    # Save data
    # --------------------------------------

    @classmethod
    def update(cls, data):

        temp_file = cls.database.with_suffix(".tmp")

        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)

        temp_file.replace(cls.database)

    # --------------------------------------
    # Generate unique account number
    # --------------------------------------

    @staticmethod
    def account_generate(data):

        while True:

            account_number = "".join(
                secrets.choice("0123456789")
                for _ in range(10)
            )

            if not any(
                i["account_number"] == account_number
                for i in data
            ):
                return account_number

    # --------------------------------------
    # Secure PIN hashing
    # --------------------------------------

    @staticmethod
    def hash_pin(pin, salt=None):

        if salt is None:
            salt = secrets.token_hex(16)

        hashed_pin = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode(),
            bytes.fromhex(salt),
            200000
        ).hex()

        return salt, hashed_pin

    @staticmethod
    def verify_pin(pin, salt, stored_hash):

        _, entered_hash = Bank.hash_pin(pin, salt)

        return hmac.compare_digest(
            entered_hash,
            stored_hash
        )

    # --------------------------------------
    # Find account
    # --------------------------------------

    @staticmethod
    def find_account(data, account_number):

        for account in data:

            if account["account_number"] == account_number:
                return account

        return None

    # --------------------------------------
    # Create account
    # --------------------------------------

    @classmethod
    def create_account(cls, name, age, email, pin):

        data = cls.load_data()

        if not name.strip():
            return False, "Name cannot be empty."

        if age < 18:
            return False, "You must be at least 18 years old."

        if not re.fullmatch(r"\d{4}", pin):
            return False, "PIN must contain exactly 4 digits."

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return False, "Please enter a valid email address."

        salt, hashed_pin = cls.hash_pin(pin)

        account = {
            "name": name.strip(),
            "age": age,
            "email": email.strip(),
            "pin_salt": salt,
            "pin_hash": hashed_pin,
            "account_number": cls.account_generate(data),
            "balance": 0
        }

        data.append(account)
        cls.update(data)

        return True, account["account_number"]

    # --------------------------------------
    # Login / Authentication
    # --------------------------------------

    @classmethod
    def authenticate(cls, account_number, pin):

        data = cls.load_data()

        account = cls.find_account(data, account_number)

        if account is None:
            return False

        return cls.verify_pin(
            pin,
            account["pin_salt"],
            account["pin_hash"]
        )

    # --------------------------------------
    # Deposit money
    # --------------------------------------

    @classmethod
    def deposit(cls, account_number, amount):

        data = cls.load_data()

        account = cls.find_account(data, account_number)

        if account is None:
            return False, "Account not found."

        if amount <= 0:
            return False, "Amount must be greater than zero."

        if amount >= 10000:
            return False, "Maximum deposit per transaction is Rs. 9,999."

        account["balance"] += amount

        cls.update(data)

        return True, account["balance"]

    # --------------------------------------
    # Withdraw money
    # --------------------------------------

    @classmethod
    def withdraw(cls, account_number, amount):

        data = cls.load_data()

        account = cls.find_account(data, account_number)

        if account is None:
            return False, "Account not found."

        if amount <= 0:
            return False, "Amount must be greater than zero."

        if account["balance"] < amount:
            return False, "Insufficient balance."

        account["balance"] -= amount

        cls.update(data)

        return True, account["balance"]

    # --------------------------------------
    # Update account details
    # --------------------------------------

    @classmethod
    def update_account(cls, account_number, name, email, pin):

        data = cls.load_data()

        account = cls.find_account(data, account_number)

        if account is None:
            return False, "Account not found."

        if not name.strip():
            return False, "Name cannot be empty."

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return False, "Please enter a valid email."

        if pin and not re.fullmatch(r"\d{4}", pin):
            return False, "New PIN must contain exactly 4 digits."

        account["name"] = name.strip()
        account["email"] = email.strip()

        if pin:
            salt, hashed_pin = cls.hash_pin(pin)
            account["pin_salt"] = salt
            account["pin_hash"] = hashed_pin

        cls.update(data)

        return True, "Account details updated successfully."

    # --------------------------------------
    # Delete account
    # --------------------------------------

    @classmethod
    def delete_account(cls, account_number):

        data = cls.load_data()

        account = cls.find_account(data, account_number)

        if account is None:
            return False

        data.remove(account)

        cls.update(data)

        return True


# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================

st.set_page_config(
    page_title="Bank Management System",
    page_icon="🏦",
    layout="centered"
)

st.title("🏦 Bank Management System")

st.caption("Simple Banking Application using Python, OOP, JSON and Streamlit")

# Initialize session state

if "account_number" not in st.session_state:
    st.session_state.account_number = None


# ==========================================
# CREATE ACCOUNT
# ==========================================

if st.session_state.account_number is None:

    menu = st.sidebar.selectbox(
        "Select Option",
        ["Home", "Create Account", "Login"]
    )

    if menu == "Home":

        st.subheader("Welcome to Our Bank")

        st.write(
            "Create an account or log in to access "
            "your banking services."
        )

        st.info("Your account information is stored in data.json.")

    # --------------------------------------
    # Create Account Form
    # --------------------------------------

    elif menu == "Create Account":

        st.subheader("Create New Account")

        with st.form("create_form"):

            name = st.text_input("Full Name")

            age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                value=18
            )

            email = st.text_input("Email Address")

            pin = st.text_input(
                "Create 4-digit PIN",
                type="password",
                max_chars=4
            )

            submit = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if submit:

                success, result = Bank.create_account(
                    name, age, email, pin
                )

                if success:

                    st.success("Account created successfully!")

                    st.write("Your account number is:")

                    st.code(result)

                    st.warning(
                        "Save your account number. "
                        "You will need it to log in."
                    )

                else:
                    st.error(result)

    # --------------------------------------
    # Login Form
    # --------------------------------------

    elif menu == "Login":

        st.subheader("Customer Login")

        with st.form("login_form"):

            account_number = st.text_input(
                "Account Number"
            )

            pin = st.text_input(
                "PIN",
                type="password",
                max_chars=4
            )

            submit = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if submit:

                if Bank.authenticate(account_number, pin):

                    st.session_state.account_number = account_number

                    st.success("Login successful!")

                    st.rerun()

                else:
                    st.error("Invalid account number or PIN.")


# ==========================================
# CUSTOMER DASHBOARD
# ==========================================

else:

    account_number = st.session_state.account_number

    data = Bank.load_data()

    account = Bank.find_account(data, account_number)

    if account is None:

        st.session_state.account_number = None
        st.rerun()

    st.sidebar.success(f"Welcome, {account['name']}")

    st.sidebar.write(
        f"Account: {account_number}"
    )

    menu = st.sidebar.radio(
        "Banking Services",
        [
            "Dashboard",
            "Deposit",
            "Withdraw",
            "Account Details",
            "Update Account",
            "Delete Account"
        ]
    )

    if st.sidebar.button("Logout", use_container_width=True):

        st.session_state.account_number = None
        st.rerun()

    # --------------------------------------
    # Dashboard
    # --------------------------------------

    if menu == "Dashboard":

        st.subheader("Customer Dashboard")

        st.metric(
            "Available Balance",
            f"Rs. {account['balance']:,}"
        )

        st.write(f"**Name:** {account['name']}")
        st.write(f"**Account Number:** {account_number}")
        st.write(f"**Email:** {account['email']}")

    # --------------------------------------
    # Deposit
    # --------------------------------------

    elif menu == "Deposit":

        st.subheader("Deposit Money")

        with st.form("deposit_form"):

            amount = st.number_input(
                "Enter deposit amount (Rs.)",
                min_value=1,
                max_value=9999,
                value=100,
                step=1
            )

            submit = st.form_submit_button(
                "Deposit Money",
                use_container_width=True
            )

            if submit:

                success, result = Bank.deposit(
                    account_number, amount
                )

                if success:

                    st.success("Money deposited successfully!")

                    st.metric(
                        "New Balance",
                        f"Rs. {result:,}"
                    )

                else:
                    st.error(result)

    # --------------------------------------
    # Withdraw
    # --------------------------------------

    elif menu == "Withdraw":

        st.subheader("Withdraw Money")

        with st.form("withdraw_form"):

            amount = st.number_input(
                "Enter withdrawal amount (Rs.)",
                min_value=1,
                value=100,
                step=1
            )

            submit = st.form_submit_button(
                "Withdraw Money",
                use_container_width=True
            )

            if submit:

                success, result = Bank.withdraw(
                    account_number, amount
                )

                if success:

                    st.success("Withdrawal successful!")

                    st.metric(
                        "Remaining Balance",
                        f"Rs. {result:,}"
                    )

                else:
                    st.error(result)

    # --------------------------------------
    # Account Details
    # --------------------------------------

    elif menu == "Account Details":

        st.subheader("Your Account Details")

        st.write(f"**Name:** {account['name']}")
        st.write(f"**Age:** {account['age']}")
        st.write(f"**Email:** {account['email']}")
        st.write(f"**Account Number:** {account_number}")
        st.write(f"**Balance:** Rs. {account['balance']:,}")

        st.caption("Your PIN is not displayed for security.")

    # --------------------------------------
    # Update Account
    # --------------------------------------

    elif menu == "Update Account":

        st.subheader("Update Account Information")

        with st.form("update_form"):

            name = st.text_input(
                "New Name",
                value=account["name"]
            )

            email = st.text_input(
                "New Email",
                value=account["email"]
            )

            pin = st.text_input(
                "New PIN (leave blank to keep existing PIN)",
                type="password",
                max_chars=4
            )

            submit = st.form_submit_button(
                "Update Details",
                use_container_width=True
            )

            if submit:

                success, result = Bank.update_account(
                    account_number,
                    name,
                    email,
                    pin
                )

                if success:
                    st.success(result)
                    st.rerun()

                else:
                    st.error(result)

    # --------------------------------------
    # Delete Account
    # --------------------------------------

    elif menu == "Delete Account":

        st.subheader("Delete Your Account")

        st.warning(
            "Warning: Deleting your account will permanently "
            "remove your account information from this JSON database."
        )

        confirmation = st.checkbox(
            "I understand and want to delete my account."
        )

        if st.button(
            "Delete My Account",
            type="primary",
            disabled=not confirmation
        ):

            if Bank.delete_account(account_number):

                st.session_state.account_number = None

                st.success("Your account has been deleted.")

                st.rerun()

            else:
                st.error("Unable to delete account.")
