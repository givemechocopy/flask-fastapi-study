from flask import Flask, request, jsonify, make_response, render_template

app = Flask(__name__)


@app.route('/query')
def query_example():
    language = request.args.get('language')
    return f"Requested language: {language}"


@app.route('/json')
def json_example():
    return jsonify({"message": "Hello, World"})


@app.route('/direct')
def direct_response():
    headers = {'X-Example': 'DirectHeader'}
    return make_response("Direct Response", 200, headers)


@app.route('/custom')
def custom_response():
    response = make_response("Custom Response", 202)
    response.headers['X-Example'] = 'CustomHeader'
    return response


@app.route('/hello/<name>')
def hello_name(name):
    return render_template('hello.html', name=name)


@app.route('/fruits')
def show_fruits():
    fruits = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry']
    return render_template('fruits_list.html', fruits=fruits)


@app.route('/messages')
def show_messages():
    return render_template('messages.html')


@app.route('/about')
def about_page():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)