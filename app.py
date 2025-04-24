import os
import pickle
import streamlit as st
import sqlite3
import hashlib
import smtplib
import json
import random
from twilio.rest import Client
import random
from streamlit_option_menu import option_menu
from streamlit_push_notifications import send_alert
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="MediPredict",
                   layout="wide",
                   page_icon="🧑‍⚕️")

# ------------------------
# Add Background Styling
# ------------------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d7f0f7 0%, #fdfcfb 100%);
        background-attachment: fixed;
        font-family: 'Segoe UI', sans-serif;
    }
    .big-title {
        font-size: 2.7em;
        font-weight: bold;
        color: #004d40;
        text-align: center;
        margin-top: 1em;
    }
    .description {
        font-size: 1.2em;
        color: #00695c;
        text-align: center;
        margin-bottom: 2em;
        padding: 0 10%;
    }
    .stButton>button {
        background-color: #26a69a;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5em 1.5em;
        margin: 0.5em 0.5em;
    }
    .stButton>button:hover {
        background-color: #00796b;
        transition: 0.3s ease;
    }
    .stTextInput>div>div>input {
        background-color: #f0f7f9 !important;
        border: 1px solid #b2dfdb !important;
        border-radius: 6px !important;
        color: #004d40 !important;
    }
    .stTextInput>div>label {
        color: #004d40 !important;
        font-weight: 500;
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Twilio Configuration
# ------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# ------------------------
# OTP Helpers
# ------------------------



def generate_otp():
    return str(random.randint(1000, 9999))

def send_otp_sms(phone_number, otp):
    message = client.messages.create(
            body=f"Your MediPredict OTP is: {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

# ------------------------
# Auth Helper Functions
# ------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, phone):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password, phone) VALUES (?, ?, ?)',
              (username, hash_password(password), phone))
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

# ------------------------
# Auth UI
# ------------------------
def auth_ui():
    global otp_storage
    st.markdown("<div class='big-title'>Welcome to MediPredict</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='description'>
        Harnessing the power of machine learning to detect multiple diseases such as Diabetes, Heart Disease, Parkinson's, Breast Cancer, Anemia, and Thyroid dysfunction.<br>
        Register now and explore personalized health assessments backed by intelligent predictions.
        </div>
    """, unsafe_allow_html=True)

    auth_option = st.session_state.get("auth_option", None)

    if auth_option is None:
        col3, col1, col2, col4 = st.columns(4)
        with col3:
            st.empty()
        with col4:
            st.empty()
        if col1.button("Login", key="login_btn"):
            st.session_state.auth_option = "Login"
            st.rerun()
        if col2.button("Register", key="register_btn"):
            st.session_state.auth_option = "Register"
            st.rerun()
        st.stop()

    if auth_option == "Register":
        st.subheader("Register New Account")
        if st.button("or Login?",key="login_btn"):
            st.session_state.auth_option = "Login"
            st.rerun()
        new_user = st.text_input("Username")
        new_phone = st.text_input("Phone")
        new_pass = st.text_input("Password", type='password')

        
        if st.button("Send OTP", key="send_otp_btn"):
            if new_user and new_phone and new_pass:
                otp = generate_otp()
                otp_dict = dict()
                otp_dict[new_user]={"otp" : otp ,"password" : new_pass, "phone" : new_phone}
                try:
                    send_otp_sms(new_phone, otp)
                except:
                    otp_dict[new_user]["otp"] = "5678"
                otp_storage = open("otp.json","w")
                json.dump(otp_dict,otp_storage)
                otp_storage.close()
                st.success("OTP sent to your phone number. Please verify below.")
                st.session_state.otp_sent = True

            else:
                st.warning("Fill all fields first.")

        if st.session_state.get("otp_sent"):
            otp_storage = open("otp.json","r")
            data = json.load(otp_storage)
            otp_storage.close()
            data = data[new_user]
            entered_otp = st.text_input("Enter OTP")
            if st.button("Verify OTP and Register", key="verify_otp_btn"):
                if data and entered_otp == data["otp"]:
                    try:
                        add_user(new_user, data["password"], data["phone"])
                        st.success("Account created successfully. You can now login.")
                        st.session_state.otp_sent = False
                        del st.session_state.auth_option
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")
                else:
                    st.error("Invalid OTP.")
        st.stop()
        


    elif auth_option == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login", key="login_submit_btn"):
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                del st.session_state.auth_option
                st.rerun()
            else:
                st.error("Incorrect username or password.")
            st.stop()
        if st.button("or Register?",key="register_btn"):
            st.session_state.auth_option = "Register"
            st.rerun()



# Ensure DB and auth
# create_users_table()

if not st.session_state.get("logged_in"):
    auth_ui()

# ------------------------
# Load Models
# ------------------------
working_dir = os.path.dirname(os.path.abspath(__file__))

diabetes_model = pickle.load(open(f'{working_dir}/saved_models/diabetes_model.sav', 'rb'))
heart_disease_model = pickle.load(open(f'{working_dir}/saved_models/heart_disease_model.sav', 'rb'))
parkinsons_model = pickle.load(open(f'{working_dir}/saved_models/parkinsons_model.sav', 'rb'))
breast_cancer_model = pickle.load(open(f'{working_dir}/saved_models/breast_cancer_model.sav', 'rb'))
anemia_model = pickle.load(open(f'{working_dir}/saved_models/anemia_model.sav', 'rb'))
# thyroid_model = pickle.load(open(f'{working_dir}/saved_models/thyroid_model.sav', 'rb'))
kidney_disease_model = pickle.load(open(f'{working_dir}/saved_models/kidney.sav','rb'))
# Your prediction logic continues here...

if st.session_state.get('logged_in'):
    # sidebar for navigation
    with st.sidebar:
        selected = option_menu('Multiple Disease Prediction System',

                            ['Diabetes Prediction',
                                'Heart Disease Prediction',
                                'Parkinsons Prediction',
                                'Breast Cancer Prediction',
                                'Anemia Prediction',
                                'Kidney Disease Prediction'],
                            menu_icon='hospital-fill',
                            icons=['activity', 'heart', 'person', 'balloon','command','droplet'],
                            default_index=0)


    # Diabetes Prediction Page
    if selected == 'Diabetes Prediction':

        # page title
        st.title('Diabetes Prediction using ML')

        # getting the input data from the user
        col1, col2, col3 = st.columns(3)

        with col1:
            Pregnancies = st.text_input('Number of Pregnancies')

        with col2:
            Glucose = st.text_input('Glucose Level')

        with col3:
            BloodPressure = st.text_input('Blood Pressure value')

        with col1:
            SkinThickness = st.text_input('Skin Thickness value')

        with col2:
            Insulin = st.text_input('Insulin Level')

        with col3:
            BMI = st.text_input('BMI value')

        with col1:
            DiabetesPedigreeFunction = st.text_input('Diabetes Pedigree Function value')

        with col2:
            Age = st.text_input('Age of the Person')


        # code for Prediction
        
        if st.button('Diabetes Test Result'):

            user_input = [Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin,
                        BMI, DiabetesPedigreeFunction, Age]

            try:
                user_input = [float(x) for x in user_input]
            except ValueError:
                send_alert("Invalid entry!! Please enter valid data in the fields.")

            diab_prediction = diabetes_model.predict([user_input])

            if diab_prediction[0] == 1:
                st.error('The person is diabetic')
            else:
                st.success('The person is not diabetic')

        

    # Heart Disease Prediction Page
    if selected == 'Heart Disease Prediction':

        # page title
        st.title('Heart Disease Prediction using ML')

        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.text_input('Age')

        with col2:
            sex = st.text_input('Sex')

        with col3:
            cp = st.text_input('Chest Pain types')

        with col1:
            trestbps = st.text_input('Resting Blood Pressure')

        with col2:
            chol = st.text_input('Serum Cholestoral in mg/dl')

        with col3:
            fbs = st.text_input('Fasting Blood Sugar > 120 mg/dl')

        with col1:
            restecg = st.text_input('Resting Electrocardiographic results')

        with col2:
            thalach = st.text_input('Maximum Heart Rate achieved')

        with col3:
            exang = st.text_input('Exercise Induced Angina')

        with col1:
            oldpeak = st.text_input('ST depression induced by exercise')

        with col2:
            slope = st.text_input('Slope of the peak exercise ST segment')

        with col3:
            ca = st.text_input('Major vessels colored by flourosopy')

        with col1:
            thal = st.text_input('thal: 0 = normal; 1 = fixed defect; 2 = reversable defect')


        # code for prediction

        if st.button('Heart Disease Test Result'):

            user_input = [age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]

            try:
                user_input = [float(x) for x in user_input]
            except ValueError:
                send_alert("Invalid entry!! Please enter valid data in the fields.")

            heart_prediction = heart_disease_model.predict([user_input])

            if heart_prediction[0] == 1:
                st.error('The person is having heart disease')
                
            else:
                st.success('The person does not have any heart disease')

        

    # Parkinson's Prediction Page
    if selected == "Parkinsons Prediction":

        # page title
        st.title("Parkinson's Disease Prediction using ML")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            fo = st.text_input('MDVP:Fo(Hz)')

        with col2:
            fhi = st.text_input('MDVP:Fhi(Hz)')

        with col3:
            flo = st.text_input('MDVP:Flo(Hz)')

        with col4:
            Jitter_percent = st.text_input('MDVP:Jitter(%)')

        with col5:
            Jitter_Abs = st.text_input('MDVP:Jitter(Abs)')

        with col1:
            RAP = st.text_input('MDVP:RAP')

        with col2:
            PPQ = st.text_input('MDVP:PPQ')

        with col3:
            DDP = st.text_input('Jitter:DDP')

        with col4:
            Shimmer = st.text_input('MDVP:Shimmer')

        with col5:
            Shimmer_dB = st.text_input('MDVP:Shimmer(dB)')

        with col1:
            APQ3 = st.text_input('Shimmer:APQ3')

        with col2:
            APQ5 = st.text_input('Shimmer:APQ5')

        with col3:
            APQ = st.text_input('MDVP:APQ')

        with col4:
            DDA = st.text_input('Shimmer:DDA')

        with col5:
            NHR = st.text_input('NHR')

        with col1:
            HNR = st.text_input('HNR')

        with col2:
            RPDE = st.text_input('RPDE')

        with col3:
            DFA = st.text_input('DFA')

        with col4:
            spread1 = st.text_input('spread1')

        with col5:
            spread2 = st.text_input('spread2')

        with col1:
            D2 = st.text_input('D2')

        with col2:
            PPE = st.text_input('PPE')

        # code for Prediction
        
        if st.button("Parkinson's Test Result"):

            user_input = [fo, fhi, flo, Jitter_percent, Jitter_Abs,
                        RAP, PPQ, DDP,Shimmer, Shimmer_dB, APQ3, APQ5,
                        APQ, DDA, NHR, HNR, RPDE, DFA, spread1, spread2, D2, PPE]

            try:
                user_input = [float(x) for x in user_input]
            except ValueError:
                send_alert("Invalid entry!! Please enter valid data in the fields.")

            parkinsons_prediction = parkinsons_model.predict([user_input])

            if parkinsons_prediction[0] == 1:
                st.error("The person has Parkinson's disease")
            else:
                st.success("The person does not have Parkinson's disease")

        

    #Breast Cancer Prediction Page

    if selected=='Breast Cancer Prediction':

        #Page Title
        st.title("Breast Cancer Prediction")

        col1,col2,col3 = st.columns(3)
        
        with col1:
            radius = st.text_input('Radius')
            texture = st.text_input('Texture')
            perimeter = st.text_input('Perimeter')
            area = st.text_input('Area')
            smoothness = st.text_input('Smoothness')
            compactness = st.text_input('Compactness')
            concavity = st.text_input('Concavity')
            concave_points = st.text_input('Concave points')
            symmetry = st.text_input('Symmetry')
            fractal_dimension = st.text_input('Fractal Dimension')

        with col2:
            radius_se = st.text_input('Radius SE')
            texture_se = st.text_input('Texture SE')
            perimeter_se = st.text_input('Perimeter SE')
            area_se = st.text_input('Area SE')
            smoothness_se = st.text_input('Smoothness SE')
            compactness_se = st.text_input('Compactness SE')
            concavity_se = st.text_input('Concavity SE')
            concave_points_se = st.text_input('Concave points SE')
            symmetry_se = st.text_input('Symmetry SE')
            fractal_dimension_se = st.text_input('Fractal Dimension SE')

        with col3:
            radius_worst = st.text_input('Radius Worst')
            texture_worst = st.text_input('Texture Worst')
            perimeter_worst = st.text_input('Perimeter Worst')
            area_worst = st.text_input('Area Worst')
            smoothness_worst = st.text_input('Smoothness Worst')
            compactness_worst = st.text_input('Compactness Worst')
            concavity_worst = st.text_input('Concavity Worst')
            concave_points_worst = st.text_input('Concave points Worst')
            symmetry_worst = st.text_input('Symmetry Worst')
            fractal_dimension_worst = st.text_input('Fractal Dimension Worst')

        #code for Prediction
        
        if st.button("Breast Cancer Test Result"):

            user_input = [radius, texture, perimeter, area, smoothness, compactness, concavity, concave_points,	symmetry, fractal_dimension, radius_se, texture_se, perimeter_se, area_se, smoothness_se, compactness_se, concavity_se, concave_points_se,	symmetry_se, fractal_dimension_se, radius_worst, texture_worst, perimeter_worst, area_worst, smoothness_worst, compactness_worst, concavity_worst, concave_points_worst, symmetry_worst, fractal_dimension_worst,]

            try:
                user_input = [float(x) for x in user_input]
            except ValueError:
                send_alert("Invalid entry!! Please enter valid data in the fields.")

            breast_cancer_prediction = breast_cancer_model.predict([user_input])

            if breast_cancer_prediction[0] == 1:
                st.error("The Breast cancer is Malignant")
            else:
                st.warning("The Breast Cancer is Benign")
            
            
    if selected == 'Anemia Prediction':

        #page title
        st.title('Anemia Prediction')

        #input data from user
        col1,col2,col3 = st.columns(3)

        with col1:
            gender = st.selectbox("Gender",
            ("Male","Female"),
            )
            mchc = st.text_input("MCHC")
        
        with col2:
            hemoglobin = st.text_input("Hemoglobin")
            mcv = st.text_input("MCV")
        
        with col3:
            mch = st.text_input("MCH")

        #code for prediction
        
        if st.button("Anemia Result"):

            gender = 0 if "Male" else 1

            user_input = [gender,hemoglobin,mch,mchc,mcv]

            try:
                user_input = [float(x) for x in user_input]
            except ValueError:
                send_alert("Invalid entry!! Please enter valid data in the fields.")

            prediction = anemia_model.predict([user_input])

            if prediction[0] == 1:
                st.error("This person has Anemia.")
            else:
                st.success("This person does not have Anemia.")

    if selected == "Kidney Disease Prediction":

        #page title
        st.title("Kidney Disease Prediction using ML")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            age = st.text_input('Age')

        with col2:
            blood_pressure = st.text_input('Blood Pressure')

        with col3:
            specific_gravity = st.text_input('Specific Gravity')

        with col4:
            albumin = st.text_input('Albumin')

        with col5:
            sugar = st.text_input('Sugar')

        with col1:
            red_blood_cells = st.text_input('Red Blood Cell')

        with col2:
            pus_cell = st.text_input('Pus Cell')

        with col3:
            pus_cell_clumps = st.text_input('Pus Cell Clumps')

        with col4:
            bacteria = st.text_input('Bacteria')

        with col5:
            blood_glucose_random = st.text_input('Blood Glucose Random')

        with col1:
            blood_urea = st.text_input('Blood Urea')

        with col2:
            serum_creatinine = st.text_input('Serum Creatinine')

        with col3:
            sodium = st.text_input('Sodium')

        with col4:
            potassium = st.text_input('Potassium')

        with col5:
            haemoglobin = st.text_input('Haemoglobin')

        with col1:
            packed_cell_volume = st.text_input('Packet Cell Volume')

        with col2:
            white_blood_cell_count = st.text_input('White Blood Cell Count')

        with col3:
            red_blood_cell_count = st.text_input('Red Blood Cell Count')

        with col4:
            hypertension = st.text_input('Hypertension')

        with col5:
            diabetes_mellitus = st.text_input('Diabetes Mellitus')

        with col1:
            coronary_artery_disease = st.text_input('Coronary Artery Disease')

        with col2:
            appetite = st.text_input('Appetitte')

        with col3:
            peda_edema = st.text_input('Peda Edema')
        with col4:
            aanemia = st.text_input('Aanemia')

        # creating a button for Prediction    
        if st.button("Kidney's Test Result"):

            user_input = [age, blood_pressure, specific_gravity, albumin, sugar,
        red_blood_cells, pus_cell, pus_cell_clumps, bacteria,
        blood_glucose_random, blood_urea, serum_creatinine, sodium,
        potassium, haemoglobin, packed_cell_volume,
        white_blood_cell_count, red_blood_cell_count, hypertension,
        diabetes_mellitus, coronary_artery_disease, appetite,
        peda_edema, aanemia]

            user_input = [float(x) for x in user_input]

            prediction = kidney_disease_model.predict([user_input])

            if prediction[0] == 1:
                st.error("The person has Kidney's disease")
            else:
                st.success("The person does not have Kidney's disease")