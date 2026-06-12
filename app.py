import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    url = request.form.get('url_input') if request.method == 'POST' else None
    return render_template('index.html', url=url)

if __name__ == '__main__':
    # Grab the port from Render's environment, default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    # 0.0.0.0 allows external connections
    app.run(host='0.0.0.0', port=port)
