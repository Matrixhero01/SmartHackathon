# SmartHack backend module
from flask import Blueprint, request, jsonify
from backend.db import get_db_connection

problem_bp = Blueprint(
    "problems",
    __name__,
    url_prefix="/api/problems"
)


# =========================================================
# GET ALL PROBLEM STATEMENTS
# =========================================================

@problem_bp.route("/", methods=["GET"])
def get_problems():

    hackathon_id = request.args.get("hackathon_id")
    category = request.args.get("category")
    difficulty = request.args.get("difficulty")
    search = request.args.get("search")

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        query = """
            SELECT
                problem_id,
                hackathon_id,
                title,
                description,
                category,
                difficulty,
                max_teams,
                status,
                created_at
            FROM problem_statements
            WHERE 1=1
        """

        params = []

        if hackathon_id:
            query += " AND hackathon_id = %s"
            params.append(hackathon_id)

        if category:
            query += " AND category = %s"
            params.append(category)

        if difficulty:
            query += " AND difficulty = %s"
            params.append(difficulty)

        if search:
            query += """
                AND (
                    title LIKE %s
                    OR description LIKE %s
                    OR category LIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])

        query += " ORDER BY created_at DESC"

        cursor.execute(query, tuple(params))

        problems = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(problems),
            "problems": problems
        })

    finally:
        cursor.close()
        connection.close()


# =========================================================
# GET SINGLE PROBLEM
# =========================================================

@problem_bp.route("/<int:problem_id>", methods=["GET"])
def get_problem(problem_id):

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                p.problem_id,
                p.hackathon_id,
                h.name AS hackathon_name,
                p.title,
                p.description,
                p.category,
                p.difficulty,
                p.max_teams,
                p.status
            FROM problem_statements p
            JOIN hackathons h
                ON p.hackathon_id = h.hackathon_id
            WHERE p.problem_id = %s
            """,
            (problem_id,)
        )

        problem = cursor.fetchone()

        if not problem:
            return jsonify({
                "success": False,
                "message": "Problem statement not found"
            }), 404

        return jsonify({
            "success": True,
            "problem": problem
        })

    finally:
        cursor.close()
        connection.close()