import streamlit as st
import sqlite3
import hashlib

# --- Helper Functions ---
def create_users_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username=?', (username,))
    data = c.fetchone()
    conn.close()
    if data and data[0] == hash_password(password):
        return True
    return False

# --- Main App ---
create_users_table()

menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

if menu == "Register":
    st.title("Register")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    if st.button("Create Account"):
        try:
            add_user(new_user, new_password)
            st.success("Account created successfully! You can now login.")
        except sqlite3.IntegrityError:
            st.error("Username already exists!")

elif menu == "Login":
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if verify_user(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success(f"Welcome, {username}!")
            st.write("You can now access your protected content.")
        else:
            st.error("Incorrect username or password.")

# --- Protected Content ---
if st.session_state.get('logged_in'):
    st.subheader("Protected Area")
    st.write(f"Hello, {st.session_state['username']}! You're logged in.")
    if st.button("Logout"):
        st.session_state.clear()
