import os
from flask import Flask
from flask_cors import CORS
from routes.browser import browser_bp

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(browser_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)