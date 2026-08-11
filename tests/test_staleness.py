from __future__ import annotations

from tracelib.graph import build_graph
from tracelib.sidecar import load_workspace, parse_sidecar
from tracelib.staleness import apply_status, detect


def graph_for(fixtures_root, name):
    root = fixtures_root / name
    return build_graph(load_workspace(root)), root


def test_clean_fixture_has_no_staleness(fixtures_root):
    graph, _ = graph_for(fixtures_root, "clean")
    assert detect(graph) == []


def test_hash_mismatch_marks_direct_consumer_stale(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    entries = detect(graph)
    direct = [e for e in entries if e.subject == "SCR-004"]
    assert direct
    assert direct[0].changed_upstream == ["FR-012"]
    assert direct[0].signoff_voided is True


def test_staleness_cascades_transitively(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    subjects = {e.subject for e in detect(graph)}
    assert "ARC-002" in subjects


def test_cascaded_entry_records_transitive_reason(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    arc = next(e for e in detect(graph) if e.subject == "ARC-002")
    assert arc.reason == "transitive"


def test_signoff_not_voided_when_absent(fixtures_root):
    graph, _ = graph_for(fixtures_root, "stale-hash")
    arc = next(e for e in detect(graph) if e.subject == "ARC-002")
    assert arc.signoff_voided is False


def test_detect_is_read_only(fixtures_root):
    root = fixtures_root / "stale-hash"
    before = (root / "03-design" / "mockups" / "SCR-004.md").read_text(
        encoding="utf-8"
    )
    graph, _ = graph_for(fixtures_root, "stale-hash")
    detect(graph)
    after = (root / "03-design" / "mockups" / "SCR-004.md").read_text(
        encoding="utf-8"
    )
    assert before == after


def test_yaml_parses_padded_hash_as_string_when_quoted():
    # Characterization test documenting why source_hash values must be
    # quoted: an unquoted `000000` is parsed by YAML as an octal int (0),
    # silently losing its padding, whereas a quoted '000000' round-trips
    # as the string "000000". This is why schema.py's source_hash
    # validation (see tests/test_schema.py) requires quoted hex strings.
    import yaml

    assert yaml.safe_load("h: '000000'")["h"] == "000000"


def test_stale_entry_carries_current_hash(fixtures_root):
    from tracelib.hashing import normative_hash

    graph, _ = graph_for(fixtures_root, "stale-hash")
    entries = detect(graph)
    direct = next(e for e in entries if e.subject == "SCR-004")
    assert direct.current_hashes["FR-012"] == normative_hash(graph.nodes["FR-012"])


def test_apply_status_writes_stale_and_strips_signoff(tmp_path, fixtures_root):
    import shutil

    root = tmp_path / "ws"
    shutil.copytree(fixtures_root / "stale-hash", root)
    graph = build_graph(load_workspace(root))

    written = apply_status(detect(graph), graph)

    screen = parse_sidecar(root / "03-design" / "mockups" / "SCR-004.md")
    assert screen.frontmatter["status"] == "stale"
    assert "signoff" not in screen.frontmatter
    assert any(p.name == "SCR-004.md" for p in written)


def test_apply_status_never_rewrites_a_journey_file(tmp_path, fixtures_root):
    # Journey steps are SYNTHESIZED nodes: graph._synthesize_journey_steps
    # gives each one the owning journey's path and an empty body. A stale
    # step must therefore never be written back, or apply_status overwrites
    # the journey's own file with the step's frontmatter and destroys the
    # journey's persona, steps, title and prose beyond recovery.
    import shutil

    root = tmp_path / "ws"
    shutil.copytree(fixtures_root / "stale-hash", root)

    sources = sorted(
        p for p in root.rglob("*.md") if "traceability" not in p.parts
    )
    before = {p: parse_sidecar(p).id for p in sources}

    graph = build_graph(load_workspace(root))
    written = apply_status(detect(graph), graph)

    after = {p: parse_sidecar(p).id for p in sources}
    assert after == before, "apply_status rewrote a file with another node's identity"

    journey = parse_sidecar(root / "03-design" / "journeys" / "J-01.md")
    assert journey.frontmatter["type"] == "journey"
    assert journey.frontmatter["persona"] == "P-02"
    assert journey.frontmatter["steps"]

    # Return value must name only files actually written.
    assert all(p in before for p in written)
    assert not any(p.name == "J-01.md" for p in written)
