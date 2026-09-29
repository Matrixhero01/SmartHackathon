from flask import Flask, render_template
from backend.routes.auth_routes import auth_bp
from backend.routes.team_routes import team_bp
from backend.routes.problem_routes import problem_bp
from backend.routes.project_routes import project_bp

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

# Register routes
app.register_blueprint(auth_bp)
app.register_blueprint(team_bp)
app.register_blueprint(problem_bp)
app.register_blueprint(project_bp)


@app.route("/")
def home():

    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/problems")
def problems_page():
    return render_template("problems.html")

@app.route("/problems/<int:problem_id>")
def problem_details_page(problem_id):
    return render_template(
        "problem_details.html",
        problem_id=problem_id
    )

@app.route("/team")
def team_page():
    return render_template("participant/team.html")

@app.route("/test-db")
def test_db():

    from backend.db import get_db_connection

    connection = get_db_connection()

    if connection:

        connection.close()

        return {
            "status": "success",
            "message": "MySQL database connected successfully!"
        }

    return {
        "status": "error",
        "message": "Database connection failed!"
    }, 500


if __name__ == "__main__":
    app.run(debug=True)