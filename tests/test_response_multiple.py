from ninja.errors import ConfigError
import pytest
from pydantic import ValidationError, BaseModel
from ninja import NinjaAPI
from client import NinjaClient
from typing import List, Union


api = NinjaAPI()


@api.get("/check_int", response={200: int})
def check_int(request):
    return 200, "1"


@api.get("/check_int2", response={200: int})
def check_int2(request):
    return 200, "str"


@api.get("/check_single_with_status", response=int)
def check_single_with_status(request):
    return 302, 1


@api.get("/check_response_schema", response={400: int})
def check_response_schema(request):
    return 200, 1


class User:
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password


class UserModel(BaseModel):
    id: int
    name: str
    # skipping password output to responses

    class Config:
        orm_mode = True


class ErrorModel(BaseModel):
    detail: str


@api.get("/check_model", response={200: UserModel, 202: UserModel})
def check_model(request):
    return 202, User(1, "John", "Password")


@api.get("/check_list_model", response={200: List[UserModel]})
def check_list_model(request):
    return 200, [User(1, "John", "Password")]


@api.get("/check_union", response={200: Union[int, UserModel], 400: ErrorModel})
def check_union(request, q: int):
    if q == 0:
        return 200, 1
    if q == 1:
        return 200, User(1, "John", "Password")
    if q == 2:
        return 400, {"detail": "error"}
    return "invalid"


client = NinjaClient(api)


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/check_int", 200, 1),
        ("/check_single_with_status", 302, 1),
        ("/check_model", 202, {"id": 1, "name": "John"}),  # the password is skipped
        (
            "/check_list_model",
            200,
            [{"id": 1, "name": "John"}],
        ),  # the password is skipped
        ("/check_union?q=0", 200, 1),
        ("/check_union?q=1", 200, {"id": 1, "name": "John"}),
        ("/check_union?q=2", 400, {"detail": "error"}),
    ],
)
def test_responses(path, expected_status, expected_response):
    response = client.get(path)
    assert response.status_code == expected_status, response.content
    assert response.json() == expected_response


def test_schema():
    checks = [
        ("/api/check_int", {200}),
        ("/api/check_int2", {200}),
        ("/api/check_single_with_status", {200}),
        ("/api/check_response_schema", {400}),
        ("/api/check_model", {200, 202}),
        ("/api/check_list_model", {200}),
        ("/api/check_union", {200, 400}),
    ]
    schema = api.get_openapi_schema()

    # checking codes
    for path, codes in checks:
        responses = schema["paths"][path]["get"]["responses"]
        responses_codes = set(responses.keys())
        assert codes == responses_codes, f"{codes} != {responses_codes}"

    # checking model
    check_model_responses = schema["paths"]["/api/check_model"]["get"]["responses"]

    assert check_model_responses == {
        200: {
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/UserModel"}
                }
            },
            "description": "OK",
        },
        202: {
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/UserModel"}
                }
            },
            "description": "OK",
        },
    }


def test_validates():
    with pytest.raises(ValidationError):
        client.get("/check_int2")

    with pytest.raises(ValidationError):
        client.get("/check_union?q=3")

    with pytest.raises(ConfigError):
        client.get("/check_response_schema")
