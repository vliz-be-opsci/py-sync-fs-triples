from datetime import datetime, UTC_tz
from logging import getLogger
from pathlib import Path
from urllib.parse import quote, unquote

from pyrdfstore import create_rdf_store
from pyrdfstore.store import RDFStore
from rdflib import Graph

log = getLogger(__name__)

SUFFIX_TO_FORMAT = {
    ".ttl": "turtle",
    ".turtle": "turtle",
    ".jsonld": "json-ld",
    ".json-ld": "json-ld",
    ".json": "json-ld",
}
SUPPORTED_RDF_DUMP_SUFFIXES = [sfx for sfx in SUFFIX_TO_FORMAT]
URN_BASE = "urn:sync"  # TODO consider os.getenv mechanism (or other) to configure this in certain context


def fname_to_ng(fname: str) -> str:
    """converts local filename to a named_graph
    :param fname: local file-name
    :type fname: str
    :returns: urn representing the filename to be used as named-graph
    :retype: str
    """
    return f"{URN_BASE}:{quote(fname)}"


# todo make roundtrip tests for ng_to_fname and fname_to_ng
def ng_to_fname(ng: str) -> str:
    """converts named_graph urn back into local filename
    :param fname: local file-name
    :type fname: str
    :returns: urn representing the filename to be used as named-graph
    :retype: str
    """
    assert ng.startswith(
        URN_BASE
    ), f"Unknown {ng=}. It should start with {URN_BASE=}"
    return unquote(ng[len(URN_BASE) + 1 :])


def get_fnames_in_store(store: RDFStore):
    return [
        ng_to_fname(ng) for ng in store.named_graphs if ng.startswith(URN_BASE)
    ]  # filter and convert the named_graphs to file_names we handle


def get_lastmod_by_fname(from_path: Path):
    return {
        str(p): datetime.fromtimestamp(p.stat().st_mtime, UTC_tz)
        for p in from_path.glob("**/*")
        if p.is_file() and p.suffix in SUPPORTED_RDF_DUMP_SUFFIXES
    }


def format_from_filepath(fpath: Path):
    suffix = fpath.suffix.lower()
    return SUFFIX_TO_FORMAT.get(suffix, None)


def load_graph_fpath(fpath: Path, format: str = None):
    format = format or format_from_filepath(fpath)
    graph: Graph = Graph().parse(location=str(fpath), format=format)
    return graph


def load_graph_fname(fname: str, format: str = None):
    return load_graph_fpath(Path(fname), format)


def sync_removal(store: RDFStore, fname: str) -> None:
    ng = fname_to_ng(fname)
    store.drop_graph(ng)
    store.forget_graph(ng)


def sync_addition(store: RDFStore, fname: str) -> None:
    ng = fname_to_ng(fname)
    g = load_graph_fname(fname)
    store.insert(g, ng)


def sync_update(store: RDFStore, fname: str) -> None:
    ng = fname_to_ng(fname)
    store.drop_graph(ng)
    g = load_graph_fname(fname)
    store.insert(g, ng)


def perform_sync(from_path: Path, to_store: RDFStore):
    """synchronizes found rdf-dump files in the from_path to the RDFStore specified

    :param from_path: folder path to sync from
    :type from_path: Path
    :param to_store: rdf store target for the sync operation
    :type to_store: RDFStore
    """
    known_fnames_in_store = get_fnames_in_store(to_store)
    current_lastmod_by_fname = get_lastmod_by_fname(from_path)
    log.info(f"current_lastmod_by_fname: {current_lastmod_by_fname}")
    for fname in known_fnames_in_store:
        if fname not in current_lastmod_by_fname:
            log.info(f"old file {fname} no longer exists")
            sync_removal(to_store, fname)
    for fname, lastmod in current_lastmod_by_fname.items():
        if fname not in known_fnames_in_store:
            log.info(f"new file {fname} with lastmod {lastmod}")
            sync_addition(to_store, fname)
        elif lastmod > to_store.lastmod_ts(fname_to_ng(fname)):
            sync_update(to_store, fname)


class SyncFsTriples:
    """Process-wrapper-pattern for easy inclusion in other contexts."""

    def __init__(
        self, fpath: str, read_uri: str = None, write_uri: str = None
    ):
        """Creates the process-wrapper instance

        :param fpath: path to te folder to check for nested rdf dump files to be synced up.
        :type fpath: str
        :param read_uri: uri to the triple-store to sync to (defaults to None - leading to using an in-MemoryStore)
        :type read_uri: str
        :param write_uri: uri for write operations to the triple store (defaults to None - leading to a store that can only be read from)
        :type write_uri: str
        """
        self.source_path: Path = Path(fpath)
        assert (
            self.source_path.exists()
        ), f"cannot sync a source-path { fpath } that does not exist."
        assert (
            self.source_path.is_dir()
        ), f"source-path { fpath } should be a folder."
        self.rdfstore: RDFStore = create_rdf_store(read_uri, write_uri)

    def process(self) -> None:
        """executes the SyncFs command"""
        perform_sync(from_path=self.source_path, to_store=self.rdfstore)
