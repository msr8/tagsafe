from app import create_app

app = create_app()

if __name__ == '__main__':
    # Print all the available routes
    print(app.url_map)

    app.run()



'''
Special thanks to https://kelvinmwinuka.com/structuring-large-applications-in-flask-using-blueprints

The env file should be like:
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

About the google login:

1) Go to https://console.developers.google.com
2) Create a new project (somewhere top left)
3) Go to "APIs & Services" > "OAuth consent screen"
4) If not in the "Overview" section, go to it and click on "GET STARTED" and fill in the required fields
5) Go to the "Data Access" section, click on "ADD OR REMOVE SCOPES" and add the "email" and "profile" scopes
6) Now that the consent screen is set up, go to "Credentials" and click on "Create credentials" > "OAuth client ID" (Note: sometimes an error may occur at this step that our consent screen is not setup, so just wait a bit and reload the page). Also alternatively you can go to the "Clients" section and click on "Create Client"
7) In "Application type", select "Web application" and fill in the required fields. In the "Authorized redirect URIs" section, add the redirect URIs "http://localhost:5000/login/google/authorized" and "http://127.0.0.1:5000/login/google/authorized"
8) Click on "Create" and you will get your client ID and client secret, note that in the .env file
'''