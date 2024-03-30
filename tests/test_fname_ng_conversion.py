from util4tests import run_single_test

from syncfstriples.service import fname_to_ng, ng_to_fname


def test_fname_to_ng():
    # Test case 1: Valid filename
    fname = "example.txt"
    expected_ng = "urn:sync:example.txt"
    assert fname_to_ng(fname) == expected_ng

    # Test case 2: Filename with special characters
    fname = "file name with spaces.txt"
    expected_ng = "urn:sync:file%20name%20with%20spaces.txt"
    assert fname_to_ng(fname) == expected_ng

    # Test case 3: Empty filename
    fname = ""
    expected_ng = "urn:sync:"
    assert fname_to_ng(fname) == expected_ng

    # Add more test cases as needed


def test_ng_to_fname():
    # Test case 1: Valid named graph URN
    ng = "urn:sync:example.txt"
    expected_fname = "example.txt"
    assert ng_to_fname(ng) == expected_fname

    # Test case 2: Named graph URN with special characters
    ng = "urn:sync:file%20name%20with%20spaces.txt"
    expected_fname = "file name with spaces.txt"
    assert ng_to_fname(ng) == expected_fname

    # Add more test cases as needed


if __name__ == "__main__":
    run_single_test(__file__)