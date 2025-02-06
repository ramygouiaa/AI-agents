# Looking to send emails in production? Check out our Email API/SMTP product!
import smtplib

sender = "from@example.com"
receiver = "ramigouia1990@gmail..com>"

message = f"""\
Subject: Hi Mailtrapclear
To: {receiver}
From: {sender}

This is a test e-mail message."""

with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
    server.starttls()
    server.login("54d59ff1e5dbc3", "d7d0c5ce9428c1")
    server.sendmail(sender, receiver, message)