from flask import Flask, render_template, request, redirect, url_for, session
import re
import shortuuid
import time

# This makes PyMySQL pretend be MySQLdb
import pymysql
pymysql.install_as_MySQLdb()

# Now these allow PyMySQL to function like MySQL
import MySQLdb
import MySQLdb.cursors

time.sleep(15)  # give MySQL time to start which windows systems need sometimes to sync with MySQL

app = Flask(__name__)
app.secret_key = '51420' #Encrypts the session providing security making the login process security even functional.

# Sets up the connecetion to the database in MySQL for use
def get_db():
    return MySQLdb.connect(
        host="db",
        user="user",
        passwd="pass",
        db="urlshortener",
        cursorclass=MySQLdb.cursors.DictCursor
    )


# First thing hit when entering the local service.
@app.route('/')
def home():
    if 'loggedin' in session: # Will reroute to main page if already logged into session.
        return redirect(url_for('listing'))
    return redirect(url_for('login')) # If not logged in, reroutes to login page.

# allows access to the main page
@app.route('/login', methods=['GET', 'POST']) 
def login():
    msg = ''
    if request.method == 'POST': # When the login button is pressed this will activate
        username = request.form.get('username', '') # Grabs the inputed username
        password = request.form.get('password', '') # Grabs the inputed password

        if not username or not password: # If either fields are empty, will not accept command and alert to unfilled fields
            msg = 'Please fill in both fields!'
        else:
            conn = get_db() # Establishes the connection to the database
            cursor = conn.cursor() # Sets up the cursor used to grab data from the database
            cursor.execute("SELECT UserID, username FROM users WHERE username = %s AND password = %s", (username, password)) # Looks for account in database
            account = cursor.fetchone() # Stores account information temporarily
            conn.close() # Disconnects from the database

            if account: # If it returns a valid account will fill out session data with the relavent account data.
                session['loggedin'] = True 
                session['UserID'] = account['UserID'] 
                session['username'] = account['username'] 
                return redirect(url_for('listing'))
            else: # If there the data doesn't match up, rejects attempt.
                msg = 'Wrong username or password! (case-sensitive)'

    return render_template('login.html', msg=msg) # Reloads the page if it makes it this far and returns whatever failure to login occured.

# This is a short redirect for when logging out which resets the session data an redirects back to login for a clean slate
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# This is the page used create new user data for the database
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST': # Grabs the inputed username and password when register button clicked sending post method
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        conn = get_db() #connects to database
        cursor = conn.cursor() # sets up cursor for database viewing
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,)) # Looks for existing ccount
        account = cursor.fetchone() # temporarily stores information
        if account:
            msg = 'Account already exists!' # I account exists, reject and notify
        elif not re.match(r'[A-Za-z0-9]', username):
            msg = 'Username must contain only letters and numbers!' # if usesrname does not conform to specified rules then reject and notify
        elif not username or not password:
            msg = 'Please fill out the form!' # If a field is left empty, reject and notify
        else:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password)) # Successful registration will store account info
            conn.commit() # Saves the new insert to the database to the "hard copy"
            msg = 'You have successfully registered!' # Notify success
        cursor.close() # End cursor connection
        conn.close() # End database connection
    return render_template('register.html', msg=msg) # Reloads the page showing whatever error or success message reached it.

# Main page of the website displaying the table and shorten URL usage
@app.route('/listing', methods=['GET', 'POST']) 
def listing():
    if 'loggedin' not in session: # Double checks whether you are logged in
        return redirect(url_for('login'))
    msg = '' #lays ground work variables for later use
    urls = []
    if request.method == 'POST': # This grabs the original URL when the shorten button is pressed
        original_url = request.form.get('original_url', '')
        if not original_url: #checks whether field is empty and then rejects and notifies if it is otherwise continues
            msg = 'Please provide a URL!'
        else:
            conn = get_db() # Establishes the connection to the database
            cursor = conn.cursor() # Establishes the cursor used to navigate the database
            short_url = shortuuid.ShortUUID().random(length=7) # This applies the shortened URL code shortening the URL
            cursor.execute('INSERT INTO urls (short_url, original_url, UserID) VALUES (%s, %s, %s)', (short_url, original_url, session['UserID'])) # This stores the shortened url and the original url in the datbase along with the user id currently being used in the session
            conn.commit() # saves these changes to the "hard drive"
            conn.close() # Ends connection
            cursor.close() # Ends cursor connection
            msg = 'URL shortened successfully!'
            return redirect(url_for('listing')) # Reloads min page to show updated information and notify success
    conn = get_db() #Establishes the connection
    cursor = conn.cursor() # Establishes the cursor to interact with the database
    cursor.execute('SELECT original_url, short_url FROM urls WHERE UserID = %s', (session['UserID'],)) #Loads the data for all urls attatched to the user id
    urls = cursor.fetchall() # stores it temporarily
    conn.close() # Ends database connection
    cursor.close() # Ends cursor connection
    return render_template('listing.html', username=session['username'], urls=urls, msg=msg, ) # Loads the page with all relevant information

# This handles redirects from the page to the original urls
@app.route('/<short_url>') # This looks for whatever the shortenedd url is  
def redirect_url(short_url):
        conn = get_db() # Establishes connection
        cursor = conn.cursor() #Establishes curor connection
        cursor.execute('SELECT original_url FROM urls WHERE short_url = %s', (short_url,)) # Look for the original url
        result = cursor.fetchone() # Temporarily stores it
        cursor.close() # Ends cursor connection
        conn.close() # Ends connection to database
        if result:
            url = result['original_url'] if isinstance(result, dict) else result[0] # sets up the redirect for the original url making sure it is in the proper format
            return redirect(url, code=302) # finally, redirects the user giving the correct 302 HTTP code

        return '<h1>404 - URL not found</h1>', 404 # If there is a url failure somewhere, it will return this error


#----------------------------------------------------IMPORTANT CITATION SECTION------------------------------------------
''' I am using this as a way to Cite every source I used to gather the knowledge from to code in html and utilize it.

Used the AI response from typing into google "how to get information from html form using python" in order to learn how to
do stuff

Used the templates and this website to learn how to utilize the html code: https://code.visualstudio.com/docs/languages/html

Learned how to get information from MySQL by using the AI responses from google typing "How to get information from a MySQL 
database using python"

I used AI to help with coding problems early on when I had no clue what I was doing but then used it for problems I had no 
clue how to solve which then turned out to be mainly software issues

I used AI a lot to help set up the docker system to work with windows as it was causing multiple issues and required specific 
system requirements to get working

The use of AI for docker set up is because of the use of docker-compose which was suggested to use because of the MySQL usage 
but also helped in making the image not require constant resets whenever the code changed (which it did a lot)

'''
#------------------------------------------------------------------------------------------------------------------------------


'''
Easy launch of application

    If this ile is being executed, __name__ will be equal to __main__ and the code below it will run.

    More info can be found here: https://medium.com/@mycodingmantras/what-does-if-name-main-mean-in-python-fa6b0460a62d
    Scripts vs modules
'''
if __name__ == "__main__":
    app.run(debug=True)