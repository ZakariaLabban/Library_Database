## 433proj
# How to run the streamlit code:
 1. First of all you need to change these variables at the start of the code according to each one's pgadmin:
DB_HOST = "127.0.0.1"
DB_PORT = "5432"
DB_NAME = "test"
DB_USER = "postgres"
DB_PASSWORD = "xxxxx"
ENCRYPTION_KEY = "s3cUr3!kEy#2023@P0stgreSQL^"

 2. Save the python file as 'app.py' in the desired directory (i.e. Desktop) and also save the 'logo.jpg' in the same directory of the 'app.py'.
open command prompt and enter these:
a. cd Desktop
b. streamlit run app.py
