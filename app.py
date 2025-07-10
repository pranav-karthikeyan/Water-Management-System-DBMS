from flask import Flask
from routes import bp  # Import the Blueprint from routes.py

# Create the app instance
app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Register the blueprint
app.register_blueprint(bp, url_prefix='/')

if __name__ == "__main__":
    app.run(debug=True)
    print(app.url_map)  # To see the route mappings
