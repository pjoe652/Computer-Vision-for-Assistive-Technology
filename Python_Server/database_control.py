import sqlite3
import urllib
import json
import time
import hashlib
import traceback


""" databaseControl.py

    Part IV Computer Systems Engineering
    Author: Peter Joe (p.joe97@hotmail.com)

    This controls all interactions with the database, if a certain command is needed it
    is called here
"""

### db_initializer.js
def createTable():
    '''Creates a database if one doesn't exist'''
    conn = sqlite3.connect('activityDatabase.db')
    c = conn.cursor()

    # Log of all activities
    c.execute("""CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                pose TEXT,
                file TEXT,
                available INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")

    # Total user activity
    c.execute("""CREATE TABLE IF NOT EXISTS user_activity (
                username TEXT NOT NULL UNIQUE,
                standing INTEGER DEFAULT 0,
                sitting INTEGER DEFAULT 0,
                lying INTEGER DEFAULT 0,
                resting INTEGER DEFAULT 0,
                not_identified INTEGER DEFAULT 0
                )""")

    # User login details
    c.execute("""CREATE TABLE IF NOT EXISTS user_login (
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
                )""")

    # Populate login table
    username = "111"
    temp_pass = "222"
    password = hashlib.sha256(temp_pass.encode('utf-8')).hexdigest()
    c.execute("INSERT OR IGNORE INTO user_login (username, password) VALUES (?,?)", (username, password))

    # Populate user activity table
    c.execute("INSERT OR IGNORE INTO user_activity (username) VALUES (?)", (username,))
    
    conn.commit()
    conn.close()


def usernameValidation(username):
    '''Checks whether username exists in database'''
    conn = sqlite3.connect('activityDatabase.db')
    conn.text_factory = str
    c = conn.cursor()

    c.execute("SELECT username FROM user_login")
    usernames = [r[0] for r in c.fetchall()]
    if(username in usernames):
        return True
    else:
        return False

### logger.js
def handlePoseLog(username, pose):
    '''Checks whether the input pose from request is a valid pose, if so then increment pose value in database'''

    available_poses = ["standing", "sitting", "resting", "lying", "not_identified"]

    try:
        if(usernameValidation(username)):
            if(pose in available_poses):
                conn = sqlite3.connect('activityDatabase.db')
                c = conn.cursor()

                if(pose == "standing"):
                    c.execute("UPDATE user_activity SET standing = standing + 1 WHERE username = ?", (username,))
                elif(pose == "sitting"):
                    c.execute("UPDATE user_activity SET sitting = sitting + 1 WHERE username = ?", (username,))
                elif(pose == "resting"):
                    c.execute("UPDATE user_activity SET resting = resting + 1 WHERE username = ?", (username,))
                elif(pose == "lying"):
                    c.execute("UPDATE user_activity SET lying = lying + 1 WHERE username = ?", (username,))
                elif(pose == "not_identified"):
                    c.execute("UPDATE user_activity SET not_identified = not_identified + 1 WHERE username = ?", (username,))
                    
                c.execute("INSERT INTO activity_log (username, pose, available) VALUES (?, ?, ?)", (username, pose, 0))

                conn.commit()
                conn.close()
            else:
                print("Invalid pose")
                raise Exception("Invalid Pose")
        else:
            print("Invalid username")
            raise Exception("Invalid username")
    except Exception as e:
        print(e)
        traceback.print_exc()

### logger.js
def handlePoseLogFile(username, pose, file):
    '''Checks whether the input pose from request is a valid pose, if so then increment pose value and stores image in database'''

    available_poses = ["standing", "sitting", "resting", "lying", "not_identified"]

    try:
        if(usernameValidation(username)):
            if(pose in available_poses):
                conn = sqlite3.connect('activityDatabase.db')
                c = conn.cursor()

                if(pose == "standing"):
                    c.execute("UPDATE user_activity SET standing = standing + 1 WHERE username = ?", (username,))
                elif(pose == "sitting"):
                    c.execute("UPDATE user_activity SET sitting = sitting + 1 WHERE username = ?", (username,))
                elif(pose == "resting"):
                    c.execute("UPDATE user_activity SET resting = resting + 1 WHERE username = ?", (username,))
                elif(pose == "lying"):
                    c.execute("UPDATE user_activity SET lying = lying + 1 WHERE username = ?", (username,))
                elif(pose == "not_identified"):
                    c.execute("UPDATE user_activity SET not_identified = not_identified + 1 WHERE username = ?", (username,))
                    
                c.execute("INSERT INTO activity_log (username, pose, file, available) VALUES (?, ?, ?, ?)", (username, pose, file, 1))

                conn.commit()
                conn.close()
            else:
                print("Invalid pose")
                raise Exception("Invalid Pose")
        else:
            print("Invalid username")
            raise Exception("Invalid username")
    except Exception as e:
        print(e)
        traceback.print_exc()


def clearUserLog(username):
    '''Reset the number of poses detected to 0 for all poses'''
    if(usernameValidation(username)):
        conn = sqlite3.connect('activityDatabase.db')
        c = conn.cursor()
        c.execute("""UPDATE user_activity SET
                    standing = 0,
                    sitting = 0,
                    resting = 0,
                    lying = 0,
                    not_identified = 0
                    WHERE username = ?
                    """, (username,))
        conn.commit()
        conn.close()
    else:
        print("Invalid username")
        raise Exception("Invalid username")

### sender.js
def sendPose(username):
    '''Get number of poses detected from specific user'''
    if(usernameValidation(username)):
        conn = sqlite3.connect('activityDatabase.db')
        c = conn.cursor()
        c.execute("SELECT * FROM user_activity WHERE username = ?", (username,))
        user_activity = c.fetchone()
        conn.commit()
        conn.close()
        return user_activity
    else:
        print("Invalid username")
        raise Exception("Invalid username")


def sendRecords(username):
    '''Get specific record from database'''
    if(usernameValidation(username)):
        conn = sqlite3.connect('activityDatabase.db')
        c = conn.cursor()
        c.execute("SELECT id, username, pose, available, timestamp FROM activity_log WHERE username = ?", (username,))
        user_records = c.fetchall()
        conn.commit()
        conn.close()
        return user_records
    else:
        print("Invalid username")
        raise Exception("Invalid username")

def getImage(username, id):
    '''Get image from a specific instance'''
    if(usernameValidation(username)):
        conn = sqlite3.connect('activityDatabase.db')
        c = conn.cursor()
        c.execute("SELECT * FROM activity_log WHERE id = ?", (id,))
        image_data = c.fetchone()
        # print(image_data)
        # image_data = (*image_data[:3], image_data[3].decode('utf-8'), *image_data[4:])
        # print(image_data)
        conn.commit()
        conn.close()
        return image_data
    else:
        print("Invalid username")
        raise Exception("Invalid username")

### signin.js
def handleSignin(username, password):
    '''Checks whether the username and password are valid'''
    if(usernameValidation(username)):
        password = password.encode('utf-8')
        hashPass = hashlib.sha256(password).hexdigest()
        conn = sqlite3.connect('activityDatabase.db')
        c = conn.cursor()
        c.execute("SELECT * FROM user_login WHERE username = ?", (username,))
        user_details = c.fetchone()
        conn.commit()
        conn.close()
        if(hashPass == user_details[1]):
            return True
        else:
            return False
    else:
        print("Invalid username")
        raise Exception("Invalid username")
