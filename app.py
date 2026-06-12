from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Get the URL if the form was submitted, otherwise it's None
    url = request.form.get('url_input') if request.method == 'POST' else None
    return render_template('index.html', url=url)

if __name__ == '__main__':
    app.run(debug=True)
