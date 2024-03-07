from util4tests import run_single_test
from pyrdfstore.store import RDFStore
from rdflib import Graph
import pytest
import os


def test_fname_to_ng():
    from syncfstriples.service import fname_to_ng

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
    from syncfstriples.service import ng_to_fname

    # Test case 1: Valid named graph URN
    ng = "urn:sync:example.txt"
    expected_fname = "example.txt"
    assert ng_to_fname(ng) == expected_fname

    # Test case 2: Named graph URN with special characters
    ng = "urn:sync:file%20name%20with%20spaces.txt"
    expected_fname = "file name with spaces.txt"
    assert ng_to_fname(ng) == expected_fname

    # Add more test cases as needed


@pytest.mark.usefixtures("memorystore")
def test_get_fnames_in_store(memorystore):
    from syncfstriples.service import get_fnames_in_store

    # Test case 1: Empty store
    expected_result = []
    assert get_fnames_in_store(memorystore) == expected_result

    # Test case 2: Store with one named graph
    # add a graph to the memorystore
    to_add_file = os.path.join(os.path.dirname(__file__), "input", "63523.ttl")
    memorystore.insert(
        Graph().parse(to_add_file, format="turtle"), "urn:sync:63523.ttl"
    )

    assert get_fnames_in_store(memorystore) == ["63523.ttl"]

    # Add more test cases as needed


if __name__ == "__main__":
    run_single_test(__file__)
