import json
import logging
from flask import Flask, render_template, request
from calcs import convert_request_to_expression

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

PATTERN_FILE = "pattern.json"


@app.route("/admin", methods=['GET', 'POST'])
def admin_page():
    result_text = ""
    expression = ""

    if request.method == 'POST':
        pattern_name = request.form.get('pattern_name', '').strip()

        if pattern_name:
            expression = convert_request_to_expression(pattern_name)

            pattern_data = {
                "expression": expression,
                "name": pattern_name
            }
            with open(PATTERN_FILE, 'w', encoding='utf-8') as f:
                json.dump(pattern_data, f, indent=4)

            result_text = f"Pattern '{pattern_name}' saved successfully!"
            logging.info(f"Admin set bullet pattern: {pattern_name} -> {expression}")

    return render_template('admin.html', result=result_text, expression=expression)


if __name__ == "__main__":
    app.run(debug=True)
