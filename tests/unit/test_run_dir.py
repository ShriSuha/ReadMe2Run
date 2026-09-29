from readme2run.workspace.run_dir import cleanup, create_run


def test_create_run_builds_the_tree_and_cleanup_removes_it(tmp_path) -> None:
    """One run gets repo/, logs/, and events.jsonl. Cleanup deletes that folder."""
    run = create_run("https://github.com/org/repo", runs_root=tmp_path)

    assert run.path.parent == tmp_path
    assert run.path.name.endswith("-repo")
    assert run.repo.is_dir()
    assert run.logs.is_dir()
    assert run.events_path.name == "events.jsonl"
    run.events_path.write_text("one line\n")
    assert run.events_path.read_text() == "one line\n"

    cleanup(run)

    assert not run.path.exists()
