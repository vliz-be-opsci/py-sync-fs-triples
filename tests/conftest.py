import pytest
import os
from pyrdfstore.store import RDFStore
from pyrdfstore import create_rdf_store
from rdflib import Graph


@pytest.fixture
def memorystore():
    return create_rdf_store()


# Other fixtures and tests here
