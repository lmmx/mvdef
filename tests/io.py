from pathlib import Path

__all__ = ["write_files"]


def write_files(names, contents, path, len_check=True) -> list[Path]:
    files = [path / name for name in names]
    for file, content in zip(files, contents):
        file.write_text(content)
        assert file.read_text() == content
    files_in_dir = list(path.iterdir())
    if len_check:
        assert len(files_in_dir) == len(files)
    return files
