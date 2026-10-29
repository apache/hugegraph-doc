#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

"""Keep Hugo diagnostics blocking except for the pinned LibSass deprecation."""

from __future__ import annotations

import re
import subprocess
import sys


LIBSASS_DEPRECATION = (
    "deprecated: css.Sass: libsass was deprecated in Hugo v0.153.0 and will be "
    "removed in a future release. Use dartsass instead. "
    "See https://gohugo.io/functions/css/sass/#dart-sass"
)
ANSI_SGR = re.compile(r"\x1b\[[0-9;]*m")
WARNING = re.compile(r"^WARN\s+(.*)$")


def is_unexpected_warning(line: str) -> bool:
    """Allow only the exact known warning, ignoring terminal color codes."""
    record = ANSI_SGR.sub("", line).rstrip("\r\n")
    match = WARNING.fullmatch(record)
    return match is not None and match.group(1) != LIBSASS_DEPRECATION


def run_hugo(command, *, cwd=None, env=None) -> None:
    """Stream complete Hugo output and reject other warnings after it exits."""
    warnings = 0
    with subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ) as process:
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            warnings += is_unexpected_warning(line)
        returncode = process.wait()

    # A Hugo failure takes precedence over the additional warning gate.
    if returncode:
        raise subprocess.CalledProcessError(returncode, command)
    if warnings:
        print(
            f"Hugo build rejected: {warnings} unexpected warning(s); "
            "only the exact LibSass deprecation is allowed.",
            file=sys.stderr,
        )
        raise subprocess.CalledProcessError(1, command)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: hugo_build.py HUGO [arguments...]")
    try:
        run_hugo(sys.argv[1:])
    except subprocess.CalledProcessError as error:
        status = error.returncode
        raise SystemExit(status if status > 0 else 128 - status) from None


if __name__ == "__main__":
    main()
