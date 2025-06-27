#import json
#import requests
#import time
#import pyotp
import os
#from urllib.parse import parse_qs, urlparse
#import sys
#from fyers_api import accessToken
from fyers_apiv3 import fyersModel
import webbrowser
from dotenv import load_dotenv

class fyerslogin_class:
    def auto_login(self):
        load_dotenv()    
        client_id = os.getenv("client_id")  # Replace with your client ID
        secret_key = os.getenv("secret_key")  # Replace with your secret key
        redirect_uri = os.getenv("redirect_uri")  # Replace with your redirect URI
        response_type = os.getenv("response_type") 
        grant_type = os.getenv("grant_type")

        FY_ID = os.getenv("FY_ID")
        APP_ID_TYPE = os.getenv("APP_ID_TYPE") # 2 IS WEB LOGIN
        TOTP_KEY = os.getenv("TOTP_KEY")
        PIN = os.getenv("PIN")
        #print(client_id, secret_key, redirect_uri, response_type, grant_type, FY_ID, APP_ID_TYPE, TOTP_KEY, PIN)

        session = fyersModel.SessionModel(
            client_id=client_id,
            secret_key=secret_key, 
            redirect_uri=redirect_uri, 
            response_type=response_type, 
            grant_type=grant_type
        )

        urlToActivate = session.generate_authcode()
        webbrowser.open(urlToActivate)
        auth_code = input("Enter the authorization code: ")
        session.set_token(auth_code)

        response_access = session.generate_token()
        access_token = response_access['access_token']

        # Initialize the FyersModel instance with your client_id, access_token, and enable async mode
        fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")

        # Make a request to get the user profile information
        response = fyers.get_profile()

        # Print the response received from the Fyers API
        print(response)

        return fyers