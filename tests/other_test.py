from enum import Enum

from pytest import fixture, mark


class Int1(Enum):
    small = 0
    large = 100


class Int2(Enum):
    small = 2
    large = 200


@fixture(scope="function")
def numbers(request) -> tuple[int, int]:
    return Int1[request.param].value, Int2[request.param].value


@mark.parametrize("numbers,total", [("small", 2), ("large", 300)], indirect=["numbers"])
def test_other(numbers, total):
    "A fixture with an 'indirect' parameter, which passes along its name"
    first, second = numbers
    assert first + second == total
