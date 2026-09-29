from flask import Blueprint, request, jsonify
from backend.db import get_db_connection


project_bp = Blueprint(
    "projects",
    __name__,
    url_prefix="/api/projects"
)


# =========================================================
# CREATE PROJECT
# POST /api/projects/
# =========================================================
@project_bp.route("/", methods=["POST"])
def create_project():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    team_id = data.get("team_id")
    problem_id = data.get("problem_id")
    project_name = data.get("project_name")
    project_description = data.get("project_description")
    technology_stack = data.get("technology_stack")
    github_url = data.get("github_url")
    demo_url = data.get("demo_url")

    # Required fields
    if not team_id or not problem_id or not project_name:
        return jsonify({
            "success": False,
            "message": "team_id, problem_id and project_name are required"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # Check whether team exists
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT team_id, hackathon_id
            FROM teams
            WHERE team_id = %s
            """,
            (team_id,)
        )

        team = cursor.fetchone()

        if not team:
            return jsonify({
                "success": False,
                "message": "Team not found"
            }), 404

        # -------------------------------------------------
        # Check whether problem exists
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT problem_id, hackathon_id, status
            FROM problem_statements
            WHERE problem_id = %s
            """,
            (problem_id,)
        )

        problem = cursor.fetchone()

        if not problem:
            return jsonify({
                "success": False,
                "message": "Problem statement not found"
            }), 404

        # -------------------------------------------------
        # Check problem status
        # -------------------------------------------------
        if problem["status"] != "OPEN":
            return jsonify({
                "success": False,
                "message": "Problem statement is closed"
            }), 400

        # -------------------------------------------------
        # Make sure team and problem belong to same hackathon
        # -------------------------------------------------
        if team["hackathon_id"] != problem["hackathon_id"]:
            return jsonify({
                "success": False,
                "message": "Team and problem statement belong to different hackathons"
            }), 400

        # -------------------------------------------------
        # Check whether team already has a project
        # -------------------------------------------------
        cursor.execute(
            """
            SELECT project_id
            FROM projects
            WHERE team_id = %s
            """,
            (team_id,)
        )

        existing_project = cursor.fetchone()

        if existing_project:
            return jsonify({
                "success": False,
                "message": "Team already has a project"
            }), 409

        # -------------------------------------------------
        # Insert project
        # -------------------------------------------------
        cursor.execute(
            """
            INSERT INTO projects
            (
                team_id,
                problem_id,
                project_name,
                project_description,
                technology_stack,
                github_url,
                demo_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                team_id,
                problem_id,
                project_name,
                project_description,
                technology_stack,
                github_url,
                demo_url
            )
        )

        project_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Project created successfully",
            "project_id": project_id
        }), 201

    except Exception as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET ALL PROJECTS
# GET /api/projects/
# =========================================================
@project_bp.route("/", methods=["GET"])
def get_projects():

    hackathon_id = request.args.get("hackathon_id")

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
                p.project_id,
                p.project_name,
                p.project_description,
                p.technology_stack,
                p.github_url,
                p.demo_url,
                p.status,
                p.created_at,

                t.team_id,
                t.team_name,

                ps.problem_id,
                ps.title AS problem_title,

                h.hackathon_id,
                h.name AS hackathon_name

            FROM projects p

            JOIN teams t
                ON p.team_id = t.team_id

            JOIN problem_statements ps
                ON p.problem_id = ps.problem_id

            JOIN hackathons h
                ON t.hackathon_id = h.hackathon_id
        """

        params = []

        if hackathon_id:

            query += """
                WHERE h.hackathon_id = %s
            """

            params.append(hackathon_id)

        query += """
            ORDER BY p.created_at DESC
        """

        cursor.execute(query, tuple(params))

        projects = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(projects),
            "projects": projects
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET SINGLE PROJECT
# GET /api/projects/<project_id>
# =========================================================
@project_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id):

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
                p.project_id,
                p.project_name,
                p.project_description,
                p.technology_stack,
                p.github_url,
                p.demo_url,
                p.status,
                p.created_at,

                t.team_id,
                t.team_name,

                ps.problem_id,
                ps.title AS problem_title,

                h.hackathon_id,
                h.name AS hackathon_name

            FROM projects p

            JOIN teams t
                ON p.team_id = t.team_id

            JOIN problem_statements ps
                ON p.problem_id = ps.problem_id

            JOIN hackathons h
                ON t.hackathon_id = h.hackathon_id

            WHERE p.project_id = %s
            """,
            (project_id,)
        )

        project = cursor.fetchone()

        if not project:

            return jsonify({
                "success": False,
                "message": "Project not found"
            }), 404

        return jsonify({
            "success": True,
            "project": project
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =========================================================
# UPDATE PROJECT
# PUT /api/projects/<project_id>
# =========================================================
@project_bp.route("/<int:project_id>", methods=["PUT"])
def update_project(project_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        # Check project
        cursor.execute(
            """
            SELECT project_id
            FROM projects
            WHERE project_id = %s
            """,
            (project_id,)
        )

        project = cursor.fetchone()

        if not project:
            return jsonify({
                "success": False,
                "message": "Project not found"
            }), 404

        # Get values
        project_name = data.get("project_name")
        project_description = data.get("project_description")
        technology_stack = data.get("technology_stack")
        github_url = data.get("github_url")
        demo_url = data.get("demo_url")
        status = data.get("status")

        # Update only supplied values
        cursor.execute(
            """
            UPDATE projects
            SET
                project_name = COALESCE(%s, project_name),
                project_description = COALESCE(%s, project_description),
                technology_stack = COALESCE(%s, technology_stack),
                github_url = COALESCE(%s, github_url),
                demo_url = COALESCE(%s, demo_url),
                status = COALESCE(%s, status)
            WHERE project_id = %s
            """,
            (
                project_name,
                project_description,
                technology_stack,
                github_url,
                demo_url,
                status,
                project_id
            )
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Project updated successfully"
        })

    except Exception as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =========================================================
# DELETE PROJECT
# DELETE /api/projects/<project_id>
# =========================================================
@project_bp.route("/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):

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
            SELECT project_id
            FROM projects
            WHERE project_id = %s
            """,
            (project_id,)
        )

        project = cursor.fetchone()

        if not project:

            return jsonify({
                "success": False,
                "message": "Project not found"
            }), 404

        cursor.execute(
            """
            DELETE FROM projects
            WHERE project_id = %s
            """,
            (project_id,)
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Project deleted successfully"
        })

    except Exception as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()