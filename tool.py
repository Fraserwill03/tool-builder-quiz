import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import sys
import logging


# Set outgoing email address and password
EMAIL_USERNAME = "notificationtool12345@gmail.com"
EMAIL_PASSWORD = sys.argv[1]

# Set email count to 0
email_count = 0

# MISO API URL
URL = "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=gettotalload&returnType=json"


def get_load_data():
    """
    Get the total load data from MISO.
    Returns: total_load and time of the most recent timestamp   
    """
    # If there is an error, takes user input to try again or quit
    try:
        response = requests.get(URL)
    except requests.exceptions.RequestException as e:
        logging.error("ERROR connecting to MISO:")
        logging.error(e)
        while(True):
            try_again = input("Would you like to try again? [Y/N]: ")
            if try_again == "N" or try_again == "n":
                quit()
            elif try_again == "Y" or try_again == "y":
                try:
                    response = requests.get(URL)
                    break
                except requests.exceptions.RequestException as e:
                    logging.error("ERROR connecting to MISO:")
                    logging.error(e)
                    continue  
            else:
                logging.warning("Invalid input")
                continue

    # parse response data and return most recent load and time
    data = response.json()
    data  = data['LoadInfo']
    data = data['FiveMinTotalLoad']
    recent_data = data[len(data)-1]
    recent_data = recent_data['Load']
    recent_time = recent_data['Time']
    load = recent_data['Value']
    return recent_time, load


def send_email(email_address, recent_time, load):
    """
    Sends an email notification
    Params: 
        email_address: destination email address provided by user
        recent_time: the last timestamp in the data
        load: the load at the last timestamp
    """
    # set email message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = email_address
    msg['Subject'] = f'Load Notification for recent_time {recent_time}'
    body = f'The most recent load is {load} MW at time {recent_time} EST'
    msg.attach(MIMEText(body, 'plain'))

    # If there is an error, takes user input to try again or quit
    try:
        # connects to email server and sends email
        logging.debug("Connecting to stmp server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USERNAME, email_address, text)
        server.quit()
        global email_count
        email_count = email_count + 1
        logging.info(f"Email {email_count} sent successfully")
    except smtplib.SMTPException as e:
        logging.error("ERROR sending email:")
        logging.error(e)
        while(True):
            try_again = input("Would you like to try again? [Y/N]: ")
            if try_again == "N" or try_again == "n":
                quit()
            elif try_again == "Y" or try_again == "y":
                try:
                    logging.debug("Reattempting to connect to stmp server...")
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                    text = msg.as_string()
                    server.sendmail(EMAIL_USERNAME, email_address, text)
                    server.quit()
                    email_count = email_count + 1
                    logging.info(f"Email {email_count} sent successfully")
                    break
                except smtplib.SMTPException as e:
                    logging.error("ERROR sending email:")
                    logging.error(e)
                    continue
            else:
                logging.warning("Invalid input")
                continue


def main(email_address, log_level):
    """
    Main function.
    Param: 
        email_address: destination email address provided by user as command line argument
        log_level: log level provided by user as command line argument
    """
    if log_level == "1":
        logging.basicConfig(level=logging.ERROR)
    elif log_level == "2":
        logging.basicConfig(level=logging.INFO)
    elif log_level == "3":
        logging.basicConfig(level=logging.DEBUG)
    else: 
        logging.critical("Invalid log level")
        quit()
    
    logging.info("Starting program...")

    # get initial data
    logging.debug("Fetching initial data...")
    intial_time, initial_load = get_load_data()
    if initial_load == None or intial_time == None:
        logging.error("ERROR: No data found")
        quit()
    logging.debug("Initial data successfully fetched")

    #send initial email
    logging.debug("Sending initial email...")
    send_email(email_address, intial_time, initial_load)

    # find current minutes using time module
    logging.debug("Finding current time...")
    current_time = time.localtime()
    current_minute = current_time.tm_min
    current_seconds = current_time.tm_sec
    # wait until 10 seconds before the next 5 minute interval
    logging.info("Waiting for next change in data...")
    logging.debug("(Waiting " + str(5 - current_minute % 5) +
                   " minutes and " + str(60 - current_seconds) + " seconds)")
    wait_time = (5 - current_minute % 5) * 60 + (60 - current_seconds)
    time.sleep(wait_time - 10)

    # loop to check for new data every 10 seconds
    # if new data is found, send email notification, and wait 250 seconds
    logging.debug("Starting loop...")
    i = 0
    while(True):
        i += 1
        logging.debug("Looking for change in data\nIteration: " + str(i))
        logging.debug("Fetching data...")
        recent_time, recent_load = get_load_data()
        if recent_load == None or recent_time == None:
            logging.error("ERROR: No data found")
            quit()
        logging.debug("Data successfully fetched")
        if recent_time != intial_time:
            logging.debug("Change in data found")
            # only sends email if load has changed
            if recent_load != initial_load:               
                send_email(email_address, recent_time, recent_load)
            intial_time = recent_time
            initial_load = recent_load
            logging.info("Waiting for next change in data...")
            logging.debug("(Waiting 250 seconds)")
            time.sleep(250)
        else:
            logging.debug("No change in data found\nWaiting 10 seconds...")
            time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        logging.critical("Invalid number of arguments\n" + 
                        "Usage: python tool.py <tool_email_password> " + 
                        "<destination_email_address> <log_level>")
        quit()
    try:
        main(sys.argv[2], sys.argv[3])
    except KeyboardInterrupt:
        print("\nQuitting...")
        quit()