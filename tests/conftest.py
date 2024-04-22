import os
import shutil
from pathlib import Path
from typing import Callable, Iterable, Optional
from uuid import uuid4

import pytest
from pyrdfstore.store import (
    GraphNameMapper,
    MemoryRDFStore,
    RDFStore,
    URIRDFStore,
)
from rdflib import BNode, Graph, URIRef
from util4tests import enable_test_logging, log

TEST_FOLDER = Path(__file__).parent
TEST_INPUT_FOLDER = TEST_FOLDER / "input"
TEST_SYNC_FOLDER = TEST_FOLDER / "__sync__"


enable_test_logging()  # note that this includes loading .env into os.getenv


@pytest.fixture()
def base() -> str:
    return f"urn:test-sync:{uuid4()}:"


@pytest.fixture()
def nmapper(base: str) -> GraphNameMapper:
    return GraphNameMapper(base=base)


@pytest.fixture(scope="session")
def _mem_store_build():
    def fn(*, cleaner: Callable = None, mapper: GraphNameMapper = None):
        return MemoryRDFStore(cleaner=cleaner, mapper=mapper)

    fn.store_type = MemoryRDFStore
    fn.store_info = ()
    return fn


@pytest.fixture(scope="session")
def _uri_store_build():
    read_uri: str = os.getenv("TEST_SPARQL_READ_URI", None)
    write_uri: str = os.getenv("TEST_SPARQL_WRITE_URI", read_uri)
    if read_uri is None or write_uri is None:
        return None
    # else

    def fn(*, cleaner: Callable = None, mapper: GraphNameMapper = None):
        return URIRDFStore(read_uri, write_uri, cleaner=cleaner, mapper=mapper)

    fn.store_type = URIRDFStore
    fn.store_info = tuple(read_uri, write_uri)
    return fn


@pytest.fixture(scope="session")
def store_builds(_mem_store_build, _uri_store_build):
    return tuple(
        storeinfo
        for storeinfo in (_mem_store_build, _uri_store_build)
        if storeinfo is not None
    )


@pytest.fixture(scope="session")
def rdf_stores(store_builds):
    return (storebuild() for storebuild in store_builds)


@pytest.fixture()
def _mem_rdf_store(_mem_store_build, nmapper: GraphNameMapper) -> RDFStore:
    """in memory store
    uses simple dict of Graph
    """
    log.debug("creating in memory rdf store")
    return _mem_store_build(mapper=nmapper)


@pytest.fixture()
def _uri_rdf_store(_uri_store_build, nmapper: GraphNameMapper) -> RDFStore:
    """proxy to available graphdb store
    But only if environment variables are set and service is available
    else None (which will result in trimming it from rdf_stores fixture)
    """
    if _uri_store_build is None:
        return None
    # else
    return _uri_store_build(mapper=nmapper)


def make_sample_graph(
    items: Iterable,
    base: Optional[str] = "https://example.org/",
    bnode_subjects: Optional[bool] = False,
) -> Graph:
    """makes a small graph for testing purposes
    the graph is build up of triples that follow the pattern {base}{part}-{item}
    where:
     - base is optionally provided as argument
     - item is iterated from the required items argument
     - part is built in iterated over ("subject", "predicate", "object")

    :param items: list of 'items' to be inserted in the uri
    :type items: Iterable, note that all members will simply be str()-ified into the uri building
    :param base: (optional) baseuri to apply into the pattern
    :type base: str
    :param bnode_subjects: indicating that the subject
    :type bnode_subjects: bool
    :return: the graph
    :rtype
    """

    def replace_with_bnode(part):
        return bool(bnode_subjects and part == "subject")

    g = Graph()
    for item in items:
        triple = tuple(
            (
                URIRef(f"{base}{part}-{item}")
                if not replace_with_bnode(part)
                else BNode()
            )
            for part in ["subject", "predicate", "object"]
        )
        g.add(triple)
    return g


@pytest.fixture(scope="function")  # a fresh folder per store for each test
def syncfolders(store_builds) -> Iterable[Path]:
    mainpath = TEST_SYNC_FOLDER
    syncpathperstore = list()
    for n, store_build in enumerate(store_builds):
        rdf_store_type: str = store_build.store_type.__name__
        syncpathname: str = f"sync-{n+1:02d}-{rdf_store_type}"
        syncpath: Path = mainpath / syncpathname
        shutil.rmtree(str(syncpath), ignore_errors=True)  # force remove it
        syncpath.mkdir(parents=True, exist_ok=True)  # create it afresh
        syncpathperstore.append(syncpath)
    return syncpathperstore
