from flask import Flask, request, make_response
from datetime import datetime, timedelta
import mysql.connector
import logging
import os
import socket

log_dir = '/app/logs'

container_name = os.environ['HOSTNAME']

logging.basicConfig(filename=f'{log_dir}/{container_name}.log',
                    level=logging.DEBUG)

app = Flask(__name__)

DATABASE_CONFIG = {
    'host': "db",
    'user': "root",
    'password': "password",
    'database': "access_log"
}
counter = 0
# connecting to db
db = mysql.connector.connect(**DATABASE_CONFIG)

if db.is_connected():
    logging.info("DB connection is successful.")

access_log_schema = ('CREATE TABLE IF NOT EXISTS access_log ('
                     'id INT AUTO_INCREMENT PRIMARY KEY,'
                     'date_time DATETIME NOT NULL,'
                     'client_ip VARCHAR(15) NOT NULL,'
                     'server_ip VARCHAR(15) NOT NULL'
                     ')')

global_count_schema = ('CREATE TABLE IF NOT EXISTS global_count ('
                       'id INT AUTO_INCREMENT PRIMARY KEY,'
                       'count INT NOT NULL'
                       ')')
cursor = db.cursor()
cursor.execute(access_log_schema)
cursor.execute(global_count_schema)

@app.route("/")
def home():
    global counter
    cursor.execute('SELECT count FROM global_count WHERE id = %s', (1,))
    result = cursor.fetchone()
    if result is not None:
        counter = int(str(result[0])) + 1
        cursor.execute("UPDATE global_count SET count = %s WHERE id = %s", (counter,1,))
    else:
        cursor.execute("INSERT INTO global_count (count) VALUES (%s)", (counter,))

    # Get the client's IP address
    client_ip = request.remote_addr

    # Get the server's internal IP address
    server_ip = socket.gethostbyname(socket.gethostname())

    # Record the access log in the database
    date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = (date_time, client_ip, server_ip)
    cursor.execute(
        'INSERT INTO access_log (date_time, client_ip, server_ip) VALUES (%s, %s, %s)',
        log_entry)
    db.commit()

    # Create a response with the server's internal IP address
    response = make_response(server_ip)

    # Set a cookie with the server's internal IP address for 5 minutes
    expires = datetime.now() + timedelta(minutes=5)
    response.set_cookie('server_ip', server_ip, expires=expires)
    logging.debug(
        f' ---- VALUES: logged: {str(date_time)}, client_ip:{client_ip}, internal_ip: {server_ip} count:{counter} HAS BEEN INSERTED '
    )
    return response


@app.route('/showcount')
def show_count():
    cursor.execute("SELECT count FROM global_count WHERE id = %s", (1,))
    result = cursor.fetchone()
    if result:
        logging.info(f'count: {result[0]}')
        return f'The count is: {result[0]}'
    return f'count for this server: {counter}'


if __name__ == "__main__":
    app.run("0.0.0.0", 5000, True)