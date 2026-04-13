# Dummy app.py to trick Render.com
# Render's auto-detect defaults to running gunicorn app:app
# Since Streamlit was crashing the server in the old app.py, 
# this new file cleanly imports the lightweight mobile_server instead!

from mobile_server import app

if __name__ == "__main__":
    app.run()
