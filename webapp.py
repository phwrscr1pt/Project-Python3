import json
import os
import logging
from flask import Flask, render_template, request
from calcs import convert_request_to_expression

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

PATTERN_FILE = os.path.join(os.path.dirname(__file__), "pattern.json")


@app.route("/admin", methods=["GET", "POST"])
def admin_page():
    success_message = ""
    generated_expr = ""

    if request.method == "POST":
        pattern = request.form.get("pattern", "").strip()

        if pattern:
            generated_expr = convert_request_to_expression(pattern)

            pattern_data = {
                "name": pattern,
                "expression": generated_expr,
            }
            with open(PATTERN_FILE, "w", encoding="utf-8") as f:
                json.dump(pattern_data, f, indent=4)

            success_message = f"Pattern '{pattern}' saved successfully!"
            logging.info(f"Admin set bullet pattern: {pattern} -> {generated_expr}")

    return render_template(
        "admin.html",
        success_message=success_message,
        generated_expr=generated_expr,
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)
