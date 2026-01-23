import sys

from src.common.request_client import request_client


def test_name():
    print(__name__)
    print(sys.path)
    assert 1==1
    assert 2==2

if __name__ == "__main__":
    print(__file__)