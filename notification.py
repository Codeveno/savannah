import smtplib
from email.message import EmailMessage

# Email configuration
# just for this, 
EMAIL_FROM = "tracksavannah@proton.me"
EMAIL_PASSWORD = "12345678"  
EMAIL_TO = "hayenaandgeckos@gmail.com"
SMTP_SERVER = "smtp.protonmail.com"
SMTP_PORT = 465

def alert(object, latitude, longitude):
    """Send email alert instead of SMS"""
    try:
        # Create email message
        msg = EmailMessage()
        msg.set_content(f"{object} Detected!\nAt location {latitude}, {longitude}")
        msg['Subject'] = f"ALERT: {object} Detected"
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO

        # Send email
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Alert sent via email!")
    except Exception as e:
        print(f"Failed to send email alert: {e}")

def sendAlert(result_list):
    alert_classes = ['Person', 'Vehicle', 'Fire']  

    # Initialize variables to store the last seen locations for each class
    last_seen_locations = {class_name: None for class_name in alert_classes}

    # Iterate through the frames and detections
    for frame in result_list:
        frame_number = frame['frame_number']
        detections = frame['detections']
        
        for detection in detections:
            class_name = detection['class_name']
            latitude = detection['latitude']
            longitude = detection['longitude']
            
            # Check if the class is in the alert_classes
            if class_name in alert_classes:
                # Update the last seen location for the class
                last_seen_locations[class_name] = (latitude, longitude)

    # Check if any alert was triggered for each class
    for class_name, location in last_seen_locations.items():
        if location:
            latitude, longitude = location
            alert(class_name, latitude, longitude)