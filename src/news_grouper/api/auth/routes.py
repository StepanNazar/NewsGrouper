from apiflask import APIBlueprint, abort
from flask import Response, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from news_grouper.api import db
from news_grouper.api.auth.models import User
from news_grouper.api.auth.schemas import (
    AccessTokenSchema,
    LoginSchema,
    RegisterSchema,
    WhoAmISchema,
)

auth = APIBlueprint("auth", __name__, url_prefix="/api", tag="Auth")


def generate_jwt_tokens(user: User) -> Response:
    refresh_token = create_refresh_token(identity=str(user.id))
    access_token = create_access_token(identity=str(user.id))
    response = jsonify({"access_token": access_token})
    set_refresh_cookies(response, refresh_token)
    return response


@auth.post("/register")
@auth.input(RegisterSchema)
@auth.output(AccessTokenSchema, status_code=201)
@auth.doc(
    responses={
        400: "Invalid email or password",
        409: "Email already used",
        201: "User registered",
    },
)
def register(json_data):
    """Register a new user. Set refresh token cookie."""
    try:
        current_user = User.find_by_email(json_data["email"])
        if current_user:
            abort(409, message="Email already used")
        new_user = User(**json_data)
    except ValueError as e:
        abort(400, message=str(e))
    db.session.add(new_user)
    db.session.commit()

    response = generate_jwt_tokens(new_user)
    response.status_code = 201
    return response


@auth.post("/login")
@auth.input(LoginSchema)
@auth.output(AccessTokenSchema)
@auth.doc(
    responses={401: "Invalid email or password", 200: "User logged in"},
)
def login(json_data):
    """Login user. Set refresh token cookie."""
    db_user = User.find_by_email(json_data["email"])
    if db_user and db_user.check_password(json_data["password"]):
        return generate_jwt_tokens(db_user)
    abort(401, message="Invalid username or password")


@auth.post("/refresh")
@jwt_required(refresh=True)
@auth.output(AccessTokenSchema)
@auth.doc(
    security=["jwt_refresh_token", "csrf_refresh_token"],
    responses={200: "Access token refreshed"},
)
def refresh():
    """Refresh access token"""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token})


@auth.post("/logout")
@jwt_required()
@auth.doc(security=["jwt_access_token"])
def logout():
    """Log out from the current device. Unset refresh token cookie."""
    response = jsonify({"message": "Logged out"})
    unset_jwt_cookies(response)
    return response


@auth.get("/whoami")
@jwt_required()
@auth.output(WhoAmISchema)
@auth.doc(security=["jwt_access_token"])
def me():
    """Get current user information."""
    user_id = get_jwt_identity()
    db_user = db.session.get(User, int(user_id))
    if not db_user:
        abort(404, message="User not found")
    return db_user
