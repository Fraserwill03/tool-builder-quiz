import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import sys


# Set outgoing email address and password
EMAIL_USERNAME = "toolbuilder123487152@outlook.com"
EMAIL_PASSWORD = sys.argv[1]

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
        print("ERROR retrieving data from MISO:")
        print(e)
        while(True):
            try_again = input("Would you like to try again? [Y/N]: ")
            if try_again == "N" or try_again == "n":
                quit()
            elif try_again == "Y" or try_again == "y":
                try:
                    response = requests.get(URL)
                    break
                except requests.exceptions.RequestException as e:
                    print("ERROR connecting to MISO:")
                    print(e)
                    continue  
            else:
                print("Invalid input")
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
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USERNAME, email_address, text)
        server.quit()
    except smtplib.SMTPException as e:
        print("ERROR sending email:")
        print(e)
        while(True):
            try_again = input("Would you like to try again? [Y/N]: ")
            if try_again == "N" or try_again == "n":
                quit()
            elif try_again == "Y" or try_again == "y":
                try:
                    server = smtplib.SMTP('smtp.office365.com', 587)
                    server.starttls()
                    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                    text = msg.as_string()
                    server.sendmail(EMAIL_USERNAME, email_address, text)
                    server.quit()
                    break
                except smtplib.SMTPException as e:
                    print("ERROR sending email:")
                    print(e)
                    continue
            else:
                print("Invalid input")
                continue


def main(email_address):
    """
    Main function.
    Param: 
        email_address: destination email address provided by user as command line argument
    """
    # get initial data
    intial_time, initial_load = get_load_data()

    #send initial email
    send_email(email_address, intial_time, initial_load)

    # find current minutes using time module
    current_time = time.localtime()
    current_minute = current_time.tm_min
    current_seconds = current_time.tm_sec
    # wait until 10 seconds before the next 5 minute interval
    wait_time = (5 - current_minute % 5) * 60 + (60 - current_seconds)
    time.sleep(wait_time - 10)

    # loop to check for new data every 10 seconds
    # if new data is found, send email notification, and wait 250 seconds
    while(True):
        recent_time, recent_load = get_load_data()
        if recent_time != intial_time:
            # only sends email if load has changed
            if recent_load != initial_load:               
                send_email(email_address, recent_time, recent_load)
            intial_time = recent_time
            initial_load = recent_load
            time.sleep(250)
        else:
            time.sleep(10)


if __name__ == "__main__":
    try:
        main(sys.argv[2])
    except KeyboardInterrupt:
        print("\nQuitting...")
        quit()