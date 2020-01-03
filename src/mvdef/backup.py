def backup(filepath, dry_run=False, suffix=".backup", hidden=True):
    """
    Given a filename, copy it to a backup before making changes and confirm success to
    allow an in place edit to proceed safely. If a file with the same name exists, add
    an incrementing integer. If dry_run is True, all the checks for the possibility of
    creating the backup will be run, but no files will be opened or touched. (To report
    on the funcdef/import statements to be moved without having to adhere to these
    requirements, don't call `mvdef.backup.backup` before calling `mvdef.ast_util.ast_parse`).
    """
    fd = filepath.parent
    assert fd.exists() and fd.is_dir(), f"Can't backup {filepath}: {fd} doesn't exist"
    hid_prefix = "." * int(hidden)  # Empty string if hidden is False
    if not filepath.exists():
        # This file is a dst to be created, make an empty backup (indicates no restore)
        assert not filepath.exists()
        empty_msg = f"# EMPTY BACKUP FOR {filepath.name} CREATED BY `mvdef⠶backup()`"
        b_file = fd / f"{hid_prefix}{filepath.name}.backup"
        # Do not tolerate even a single backup file for a file to be newly created
        assert not b_file.exists(), f"Backup {b_file} exists for non-existing file!"
        if not dry_run:
            with open(b_file, "w") as f:
                f.write(f"{empty_msg}\n")
        return True
    else:
        assert filepath.exists() and filepath.is_file() and filepath.suffix == ".py"
    bname = f"{hid_prefix}{filepath.name}{suffix}"
    if fd / bname in fd.iterdir():
        for i in range(0, 12):
            bname_i = fd / f"{bname}{i}"
            if bname_i not in fd.iterdir():
                break
            i += 1
            if i > 10:
                raise ValueError("There are over 10 backups, something's wrong")
        assert not (fd / bname_i).exists()
        # Use the filename {bname_i} for the backup
        bname = bname_i
    assert not (fd / bname).exists()
    if not dry_run:
        with open(filepath, "r") as o:
            original = o.read()
        with open(fd / bname, "w") as b:
            b.write(original)
    return True
