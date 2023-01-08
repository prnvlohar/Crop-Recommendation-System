from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import requests, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report
from sklearn import model_selection
from sklearn import metrics
from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
import pickle
import smtplib
import ssl



PATH = 'Crops2.csv'
df = pd.read_csv(PATH)

features = df[['temperature', 'humidity','irrigation','soiltype','Season']]
target = df['label']
labels = df['label']

# Initializing empty lists to append all model's name and corresponding name
acc = []
model = []

# Splitting into train and test data

Xtrain, Xtest, Ytrain, Ytest = train_test_split(features,target,test_size = 0.2,random_state =2)

NaiveBayes = GaussianNB()

NaiveBayes.fit(Xtrain,Ytrain)

predicted_values = NaiveBayes.predict(Xtest)
x = metrics.accuracy_score(Ytest, predicted_values)
acc.append(x)
model.append('Naive Bayes')

score = model_selection.cross_val_score(NaiveBayes,features,target,cv=5)


# Dump the trained Naive Bayes classifier with Pickle
NB_pkl_filename = 'NBClassifier.pkl'
# Open the file to save as pkl file
NB_Model_pkl = open(NB_pkl_filename, 'wb')
pickle.dump(NaiveBayes, NB_Model_pkl)
# Close the pickle instances
NB_Model_pkl.close()

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Pranav@19'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

def weather(CITY):
   BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
   API_KEY = "b827020b9c9e2f693070bf1183e771d3"
   # upadting the URL
   URL = BASE_URL + "q=" + CITY + "&appid=" + API_KEY + '&units={Metric}'
   # HTTP request
   response = requests.get(URL)
   # checking the status code of the request
   if response.status_code == 200:
      # getting data in the json format
      data = response.json()
      # getting the main dict block
      main = data['main']
      # getting temperature
      temperature = main['temp']
      temp=temperature-273.15
      # getting the humidity
      humi= main['humidity']
      a=[]
      a.append(temp)
      a.append(humi)
      return a
   

def soiltypecon(str1):
   if str1=='black soil':
      return 6
   elif str1=='alluvial soil':
      return 1   
   elif str1=='clay soil':
      return 2  
   elif str1=='loamy soil':
      return 3 
   elif str1=='sandy soil':
      return 4  
   elif str1=='red sandy soil':
      return 5
   else:
      return 'invalid soil type'                  

def irrigationcon(str1):
   if str1=='sprinkler':
      return 1
   elif str1=='drip':
      return 2   
   elif str1=='flood':
      return 3
   else:
      return 'invalid irrigation type'

def seasoncon(str1):
    if str1=='rabi':
        return 1
    elif str1=='kharif':
        return 2
    elif str1=='whole year':
        return 3    
    elif str1=='zaid':
        return 4


# http://localhost:5000/pythonlogin/ - the following will be our login page, which will use both GET and POST requests
@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    
        # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg=msg)    
# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))
# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile/<name>')
def success(name):
    if name=='pigeonpeas':
        o='<a href="https://www.apnikheti.com/en/pn/agriculture/crops/pulses/pigeon-pea-tur">pigeonpeas<a>'
        return o
    else:
        return name

@app.route('/pythonlogin/profile',methods=['GET','POST'])
def profile():
    # Check if user is loggedin
    
    if request.method == 'POST':
        st = soiltypecon(request.form['soiltype'])
        it= irrigationcon(request.form['irrigation'])
        ct= weather(request.form['city'])
        seas=seasoncon(request.form['season'])
        if ct!=None:
            err1='suggested crop is'
            temp=ct[0]
            humi=ct[1]
            data = np.array([[temp,humi,it,st,seas]])
            data1=np.array(data,dtype=float)
            prediction = NaiveBayes.predict(data1)
            for i in prediction:
                k=i
            return render_template('profile.html',msg1="suggested crop is "+k) 
        else:
            err1='invalid city'
            return render_template('profile.html',err=err1)    
           
    return render_template('profile.html')
@app.route('/pythonlogin/contact',methods=['GET','POST'])
def contact():
    if request.method=='POST':
        nm=request.form['fname']
        sn=request.form['surname']
        em=request.form['email']
        ph=request.form['phone']
        mg=request.form['comment']
        p="hello my name is "+nm+" "+sn+" and my email and phone no. is "+em+", "+ph+" and my message to you is"+"{mg}"
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("prnvlohar@gmail.com", "qzobplbtuzlvidln")
        emailid = "prnalohar@gmail.com"
        s.sendmail('&&&&&&&&&&&',emailid,p)
        o="email sent successfully"
        return render_template('contact.html',msg2=o)
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
