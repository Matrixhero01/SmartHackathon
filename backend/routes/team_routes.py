# SmartHack backend module

from flask import Blueprint, request, jsonify
from backend.db import get_db_connection


team_bp = Blueprint(
    "teams",
    __name__,
    url_prefix="/api/teams"
)


# =========================================================
# CREATE TEAM
# =========================================================

@team_bp.route("/", methods=["POST"])
def create_team():

    data = request.get_json() or {}

    hackathon_id = data.get("hackathon_id")
    team_name = data.get("team_name")
    team_code = data.get("team_code")
    team_leader_id = data.get("team_leader_id")

    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if not all([
        hackathon_id,
        team_name,
        team_code,
        team_leader_id
    ]):

        return jsonify({
            "success": False,
            "message": "All team details are required"
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
        # Check hackathon
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                hackathon_id,
                name
            FROM hackathons
            WHERE hackathon_id = %s
            """,
            (hackathon_id,)
        )

        hackathon = cursor.fetchone()


        if not hackathon:

            return jsonify({
                "success": False,
                "message": "Hackathon not found"
            }), 404


        # -------------------------------------------------
        # Check user
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                email
            FROM users
            WHERE user_id = %s
            """,
            (team_leader_id,)
        )

        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "message": "Team leader does not exist"
            }), 404


        # -------------------------------------------------
        # Check duplicate team code
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT team_id
            FROM teams
            WHERE team_code = %s
            """,
            (team_code,)
        )

        existing_code = cursor.fetchone()


        if existing_code:

            return jsonify({
                "success": False,
                "message": "Team code already exists"
            }), 409


        # -------------------------------------------------
        # Check duplicate team name
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT team_id
            FROM teams
            WHERE hackathon_id = %s
            AND team_name = %s
            """,
            (
                hackathon_id,
                team_name
            )
        )

        existing_name = cursor.fetchone()


        if existing_name:

            return jsonify({
                "success": False,
                "message": "A team with this name already exists"
            }), 409


        # -------------------------------------------------
        # Check whether leader is already in a team
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                tm.team_id,
                t.team_name
            FROM team_members tm
            JOIN teams t
                ON tm.team_id = t.team_id
            WHERE tm.user_id = %s
            AND t.hackathon_id = %s
            """,
            (
                team_leader_id,
                hackathon_id
            )
        )

        existing_membership = cursor.fetchone()


        if existing_membership:

            return jsonify({
                "success": False,
                "message":
                    "User is already a member of a team "
                    "in this hackathon"
            }), 409


        # -------------------------------------------------
        # Create team
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO teams
            (
                hackathon_id,
                team_name,
                team_code,
                team_leader_id
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                hackathon_id,
                team_name,
                team_code,
                team_leader_id
            )
        )


        team_id = cursor.lastrowid


        # -------------------------------------------------
        # Add leader to team_members
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO team_members
            (
                team_id,
                user_id,
                member_role
            )
            VALUES
            (
                %s,
                %s,
                'LEADER'
            )
            """,
            (
                team_id,
                team_leader_id
            )
        )


        connection.commit()


        return jsonify({

            "success": True,

            "message":
                "Team created successfully",

            "team": {
                "team_id": team_id,
                "team_name": team_name,
                "team_code": team_code,
                "hackathon_id": hackathon_id,
                "team_leader_id": team_leader_id
            }

        }), 201


    except Exception as error:

        connection.rollback()

        return jsonify({

            "success": False,

            "message":
                "Failed to create team",

            "error":
                str(error)

        }), 500


    finally:

        cursor.close()
        connection.close()



# =========================================================
# GET ALL TEAMS
# =========================================================

@team_bp.route("/", methods=["GET"])
def get_teams():

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
                t.team_id,
                t.team_name,
                t.team_code,
                t.hackathon_id,
                t.team_leader_id,
                h.name AS hackathon_name,
                u.full_name AS team_leader,
                t.created_at,

                (
                    SELECT COUNT(*)
                    FROM team_members tm
                    WHERE tm.team_id = t.team_id
                ) AS member_count

            FROM teams t

            JOIN hackathons h
                ON t.hackathon_id = h.hackathon_id

            JOIN users u
                ON t.team_leader_id = u.user_id

            WHERE 1 = 1
        """

        params = []


        if hackathon_id:

            query += """
                AND t.hackathon_id = %s
            """

            params.append(
                hackathon_id
            )


        query += """
            ORDER BY t.created_at DESC
        """


        cursor.execute(
            query,
            tuple(params)
        )


        teams = cursor.fetchall()


        return jsonify({

            "success": True,

            "count": len(teams),

            "teams": teams

        })


    finally:

        cursor.close()
        connection.close()



# =========================================================
# GET SINGLE TEAM
# =========================================================

@team_bp.route("/<int:team_id>", methods=["GET"])
def get_team(team_id):

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
                t.team_id,
                t.team_name,
                t.team_code,
                t.hackathon_id,
                h.name AS hackathon_name,
                t.team_leader_id,
                u.full_name AS team_leader,
                t.created_at

            FROM teams t

            JOIN hackathons h
                ON t.hackathon_id =
                   h.hackathon_id

            JOIN users u
                ON t.team_leader_id =
                   u.user_id

            WHERE t.team_id = %s
            """,
            (team_id,)
        )


        team = cursor.fetchone()


        if not team:

            return jsonify({
                "success": False,
                "message": "Team not found"
            }), 404


        return jsonify({

            "success": True,

            "team": team

        })


    finally:

        cursor.close()
        connection.close()



# =========================================================
# GET TEAM MEMBERS
# =========================================================

@team_bp.route(
    "/<int:team_id>/members",
    methods=["GET"]
)
def get_team_members(team_id):

    connection = get_db_connection()


    if not connection:

        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500


    cursor = connection.cursor(dictionary=True)


    try:

        # -------------------------------------------------
        # Check team
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT team_id
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
        # Members
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                tm.team_member_id,
                tm.team_id,

                u.user_id,
                u.full_name,
                u.email,
                u.phone,

                tm.member_role,
                tm.joined_at

            FROM team_members tm

            JOIN users u
                ON tm.user_id = u.user_id

            WHERE tm.team_id = %s

            ORDER BY
                CASE
                    WHEN tm.member_role = 'LEADER'
                    THEN 1
                    ELSE 2
                END,
                tm.joined_at
            """,
            (team_id,)
        )


        members = cursor.fetchall()


        return jsonify({

            "success": True,

            "team_id": team_id,

            "count": len(members),

            "members": members

        })


    finally:

        cursor.close()
        connection.close()



# =========================================================
# JOIN TEAM USING TEAM ID
# =========================================================

@team_bp.route(
    "/<int:team_id>/join",
    methods=["POST"]
)
def join_team(team_id):

    data = request.get_json() or {}

    user_id = data.get("user_id")


    if not user_id:

        return jsonify({
            "success": False,
            "message": "user_id is required"
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
        # Check team
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                team_id,
                hackathon_id
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
        # Check user
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        # -------------------------------------------------
        # Check existing membership
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT team_member_id
            FROM team_members
            WHERE team_id = %s
            AND user_id = %s
            """,
            (
                team_id,
                user_id
            )
        )

        existing = cursor.fetchone()


        if existing:

            return jsonify({
                "success": False,
                "message":
                    "User is already a team member"
            }), 409


        # -------------------------------------------------
        # Check whether user is already in another team
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                tm.team_id,
                t.team_name
            FROM team_members tm

            JOIN teams t
                ON tm.team_id = t.team_id

            WHERE tm.user_id = %s
            AND t.hackathon_id = %s
            """,
            (
                user_id,
                team["hackathon_id"]
            )
        )

        another_team = cursor.fetchone()


        if another_team:

            return jsonify({

                "success": False,

                "message":
                    "User is already in another "
                    "team for this hackathon"

            }), 409


        # -------------------------------------------------
        # Add member
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO team_members
            (
                team_id,
                user_id,
                member_role
            )
            VALUES
            (
                %s,
                %s,
                'MEMBER'
            )
            """,
            (
                team_id,
                user_id
            )
        )


        connection.commit()


        return jsonify({

            "success": True,

            "message":
                "Joined team successfully",

            "team_id":
                team_id,

            "user_id":
                user_id

        }), 201


    except Exception as error:

        connection.rollback()

        return jsonify({

            "success": False,

            "message":
                "Failed to join team",

            "error":
                str(error)

        }), 500


    finally:

        cursor.close()
        connection.close()



# =========================================================
# JOIN TEAM USING TEAM CODE
# =========================================================

@team_bp.route(
    "/join-by-code",
    methods=["POST"]
)
def join_team_by_code():

    data = request.get_json() or {}

    team_code = data.get("team_code")
    user_id = data.get("user_id")


    if not team_code or not user_id:

        return jsonify({

            "success": False,

            "message":
                "team_code and user_id are required"

        }), 400


    connection = get_db_connection()


    if not connection:

        return jsonify({

            "success": False,

            "message":
                "Database connection failed"

        }), 500


    cursor = connection.cursor(dictionary=True)


    try:

        # -------------------------------------------------
        # Find team
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                team_id,
                team_name,
                team_code,
                hackathon_id
            FROM teams
            WHERE team_code = %s
            """,
            (team_code,)
        )


        team = cursor.fetchone()


        if not team:

            return jsonify({

                "success": False,

                "message":
                    "Invalid team code"

            }), 404


        # -------------------------------------------------
        # Check user
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                user_id,
                full_name
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )


        user = cursor.fetchone()


        if not user:

            return jsonify({

                "success": False,

                "message":
                    "User not found"

            }), 404


        # -------------------------------------------------
        # Already member?
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT team_member_id
            FROM team_members
            WHERE team_id = %s
            AND user_id = %s
            """,
            (
                team["team_id"],
                user_id
            )
        )


        existing = cursor.fetchone()


        if existing:

            return jsonify({

                "success": False,

                "message":
                    "You are already a member of this team"

            }), 409


        # -------------------------------------------------
        # Another team?
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                tm.team_id,
                t.team_name
            FROM team_members tm

            JOIN teams t
                ON tm.team_id = t.team_id

            WHERE tm.user_id = %s
            AND t.hackathon_id = %s
            """,
            (
                user_id,
                team["hackathon_id"]
            )
        )


        another_team = cursor.fetchone()

        if another_team:

            return jsonify({

                "success": False,

                "message":
                    "You are already in team '"
                    + another_team["team_name"]
                    + "' for this hackathon"

            }), 409


        # -------------------------------------------------
        # Add member
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO team_members
            (
                team_id,
                user_id,
                member_role
            )
            VALUES
            (
                %s,
                %s,
                'MEMBER'
            )
            """,
            (
                team["team_id"],
                user_id
            )
        )


        connection.commit()


        return jsonify({

            "success": True,

            "message":
                "Joined team successfully",

            "team": team

        }), 201


    except Exception as error:

        connection.rollback()

        return jsonify({

            "success": False,

            "message":
                "Failed to join team",

            "error":
                str(error)

        }), 500


    finally:

        cursor.close()
        connection.close()