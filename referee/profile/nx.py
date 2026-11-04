"""``profile.nx``: an Nx project's ``lint`` and ``test`` targets as the direct commands their executors run, for
``profile.fit`` when the candidate's ``package.json`` has no such script.

Read from Nx 22.7.12's own code (``nx``, ``@nx/eslint`` and ``@nx/jest`` from the npm registry: target merging,
``resolveNxTokensInOptions``, ``interpolate``, the ``@nx/eslint:lint`` and ``@nx/jest:jest`` executors). The rules
below are the part of that code this module reproduces; anything else is refused with a reason, never guessed.

**The workspace and the target** (``target``): ``nx.json`` at the tree's root is a JSON object (else
``no_workspace``; the workspace root is the tree's root, a nested Nx workspace is not read); the candidate's nearest
lock (``derive.nearest_lock``) is the root's ``package-lock.json`` or ``npm-shrinkwrap.json``, where the commands'
``node_modules/.bin`` lies (``lock_not_at_workspace_root``); ``<path>/project.json`` is a JSON object whose
``targets`` holds the target name (``no_target``). The target's keys are within ``executor``, ``options``,
``inputs``, ``outputs``, ``cache`` and ``configurations`` (``target_key:<key>``: ``dependsOn`` runs other tasks
first, ``defaultConfiguration`` changes the options, a ``command`` is ``nx:run-commands``); its ``executor`` is the
one the name maps to, ``@nx/eslint:lint`` for ``lint`` and ``@nx/jest:jest`` for ``test`` (``executor:<value>``);
its ``options`` keys are within that executor's supported set (``option:<key>``). The ``targetDefaults`` entry Nx
merges in (``readTargetDefaultsForTarget``: the executor's key, else the target name, else the longest glob key
matching the name, ``fnmatch`` standing for ``minimatch``) has only ``inputs``, ``outputs`` and ``cache``
(``target_defaults_key:<key>``), which change caching, not what runs. Option strings are resolved as
``resolveNxTokensInOptions`` does: a leading ``{workspaceRoot}`` with its ``/`` dropped, any other
``{workspaceRoot}`` refused (``token:workspaceRoot``), every ``{projectRoot}`` the candidate's path, every
``{projectName}`` the ``name`` of ``project.json`` (``token:projectName`` when it has none).

**lint** (``@nx/eslint:lint``, options ``lintFilePatterns`` only): the patterns (default ``["{projectRoot}"]``)
pass through the executor's ``interpolate`` (``nx_interpolate``); the flat config is the first of
``FLAT_CONFIGS`` in the candidate's directory, then each directory above it to the root (``findFlatConfigFile``;
none: ``no_flat_config``, the eslintrc path is not read); the lock's ``node_modules/eslint`` has a ``version`` of
major 9 or more (``eslint_version``: the ESLint CLI reads ``--config`` as a flat config from 9 on). The command,
run from the workspace root as the executor ``chdir``s there::

    node_modules/.bin/eslint --config <flat config> --no-error-on-unmatched-pattern --format json <patterns...>

which is the executor's ``ESLint`` call (``overrideConfigFile``, ``errorOnUnmatchedPattern: false``,
``lintFiles(patterns)``, no fix and no cache) with the ``json`` formatter on stdout. A pattern starting with ``-``
is refused (``pattern_option``). The flat config file joins the recipe's inputs.

**test** (``@nx/jest:jest``, options ``jestConfig`` only, required: ``option_missing:jestConfig``): the command is::

    env TS_NODE_COMPILER_OPTIONS=<the executor's value> node_modules/.bin/jest --config <jestConfig>

the executor's ``runCLI`` with the one config (``NODE_ENV`` is ``test`` in both, the jest binary setting it when
unset). ``jestConfig`` starting with ``-`` is refused (``pattern_option``); it joins the inputs when it is a
relative path inside the tree.

Not reproduced (a run shows any difference): Nx's ``.env`` files loaded into a task's environment, inferred targets
of plugins (an explicit ``project.json`` target with another executor replaces them, ``isCompatibleTarget``), a
project declared only in ``package.json``'s ``nx`` field, ``nx:run-commands`` and other executors, the eslintrc
configuration, files a configuration imports (a root ``jest.preset.js``, a config's own imports), whether the
programs exist in the installed packages (``unit_verify.check_recipe`` judges the ``.bin`` paths against the lock).
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
from typing import Any

from profile import derive as D

FLAT_CONFIGS = ("eslint.config.cjs", "eslint.config.js", "eslint.config.mjs", "eslint.config.cts",
                "eslint.config.ts", "eslint.config.mts")
EXECUTORS = {"lint": "@nx/eslint:lint", "test": "@nx/jest:jest"}
OPTIONS = {"lint": ("lintFilePatterns",), "test": ("jestConfig",)}
TARGET_KEYS = ("executor", "options", "inputs", "outputs", "cache", "configurations")
DEFAULTS_KEYS = ("inputs", "outputs", "cache")
TS_NODE = json.dumps({"moduleResolution": "Node10", "module": "commonjs", "customConditions": None},
                     separators=(",", ":"))
REPLACEMENT = re.compile(r"{([\s\S]+?)}")


class NotComposed(Exception):
    """The target is outside the rules above; ``str(exc)`` is the reason."""


def resolve_tokens(value: str, root: str, name: Any) -> str:
    """Nx's ``resolveNxTokensInOptions`` on one string."""
    value = re.sub(r"^\{workspaceRoot\}/?", "", value, count=1)
    if "{workspaceRoot}" in value:
        raise NotComposed("token:workspaceRoot")
    value = value.replace("{projectRoot}", root)
    if "{projectName}" in value:
        if not isinstance(name, str) or not name:
            raise NotComposed("token:projectName")
        value = value.replace("{projectName}", name)
    return value


def _node_join(parts: list[str]) -> str:
    """Node's ``path.posix.join`` for relative parts: the non-empty parts joined and normalised, a trailing ``/``
    kept, ``.`` when nothing is left."""
    joined = "/".join(p for p in parts if p)
    if not joined:
        return "."
    norm = posixpath.normpath(joined)
    return norm + "/" if joined.endswith("/") and norm != "/" else norm


def nx_interpolate(template: str, root: str, name: Any) -> str:
    """The executor's ``interpolate`` with ``{workspaceRoot: '', projectRoot, projectName}``."""
    if template.startswith("/") or not REPLACEMENT.search(template):
        return template
    if template.find("{workspaceRoot}", 1) != -1:
        raise NotComposed("token:workspaceRoot")
    if root == "." and template.find("{projectRoot}", 1) != -1:
        raise NotComposed("token:projectRoot")
    data = {"workspaceRoot": "", "projectRoot": root, "projectName": name}

    def one(part: str) -> str:
        if root == ".":
            part = part.replace("{projectRoot}", "", 1)

        def sub(match: re.Match) -> str:
            value: Any = data
            for key in match.group(0)[1:-1].strip().split("."):
                if not isinstance(value, dict) or not value.get(key):
                    return match.group(0)
                value = value[key]
            return value if isinstance(value, str) else match.group(0)
        return REPLACEMENT.sub(sub, part)
    return _node_join([one(p) for p in template.split("/")]).replace("{workspaceRoot}/", "", 1)


def _target_defaults(nx: dict, name: str, executor: str) -> Any:
    defaults = nx.get("targetDefaults")
    if not isinstance(defaults, dict):
        return None
    if executor in defaults:
        return defaults[executor]
    if name in defaults:
        return defaults[name]
    globbed = [k for k in defaults if any(c in k for c in "*?[{") and fnmatch.fnmatchcase(name, k)]
    return defaults[max(globbed, key=len)] if globbed else None


def target(tree: str, path: str, name: str) -> tuple[dict, dict]:
    """``(project, options)`` of target ``name`` of candidate ``path``, token-resolved (module docstring)."""
    _, nx = D._json(tree, "nx.json")
    if not isinstance(nx, dict):
        raise NotComposed("no_workspace")
    lock = D.nearest_lock(tree, path)
    if lock not in ("package-lock.json", "npm-shrinkwrap.json"):
        raise NotComposed("lock_not_at_workspace_root")
    _, project = D._json(tree, "project.json" if path == "." else posixpath.join(path, "project.json"))
    targets = project.get("targets") if isinstance(project, dict) else None
    spec = targets.get(name) if isinstance(targets, dict) else None
    if not isinstance(spec, dict):
        raise NotComposed("no_target")
    for key in sorted(spec):
        if key not in TARGET_KEYS:
            raise NotComposed("target_key:" + key)
    if spec.get("executor") != EXECUTORS[name]:
        raise NotComposed("executor:%s" % spec.get("executor"))
    options = spec.get("options", {})
    if not isinstance(options, dict):
        raise NotComposed("option:options")
    for key in sorted(options):
        if key not in OPTIONS[name]:
            raise NotComposed("option:" + key)
    defaults = _target_defaults(nx, name, EXECUTORS[name])
    if defaults is not None:
        if not isinstance(defaults, dict):
            raise NotComposed("target_defaults_key:" + name)
        for key in sorted(defaults):
            if key not in DEFAULTS_KEYS:
                raise NotComposed("target_defaults_key:" + key)

    def resolved(value: Any) -> Any:
        if isinstance(value, str):
            return resolve_tokens(value, path, project.get("name"))
        if isinstance(value, list):
            return [resolved(v) for v in value]
        return value
    return project, {k: resolved(v) for k, v in options.items()}


def flat_config(tree: str, path: str) -> str | None:
    """``findFlatConfigFile`` from the candidate's directory up to the root: the tree path, or None."""
    directory = path
    while True:
        for file in FLAT_CONFIGS:
            rel = file if directory == "." else posixpath.join(directory, file)
            if os.path.exists(os.path.join(tree, rel)):
                return rel
        if directory == ".":
            return None
        directory = posixpath.dirname(directory) or "."


def _major(version: Any) -> int | None:
    match = re.match(r"(\d+)\.", version) if isinstance(version, str) else None
    return int(match.group(1)) if match else None


def lint(tree: str, path: str) -> tuple[list[str], list[str]]:
    """``(lint_cmd, extra inputs)`` of the ``lint`` target; ``NotComposed`` with the reason otherwise."""
    project, options = target(tree, path, "lint")
    patterns = options.get("lintFilePatterns", ["{projectRoot}"])
    if not isinstance(patterns, list) or not patterns or not all(isinstance(p, str) and p for p in patterns):
        raise NotComposed("option:lintFilePatterns")
    patterns = [nx_interpolate(p, path, project.get("name")) for p in patterns]
    if any(p.startswith("-") for p in patterns):
        raise NotComposed("pattern_option")
    config = flat_config(tree, path)
    if config is None:
        raise NotComposed("no_flat_config")
    _, parsed = D._json(tree, D.nearest_lock(tree, path))
    packages = parsed.get("packages") if isinstance(parsed, dict) else None
    eslint = packages.get("node_modules/eslint") if isinstance(packages, dict) else None
    major = _major(eslint.get("version")) if isinstance(eslint, dict) else None
    if major is None or major < 9:
        raise NotComposed("eslint_version")
    return (["node_modules/.bin/eslint", "--config", config, "--no-error-on-unmatched-pattern", "--format", "json"]
            + patterns, [config])


def test(tree: str, path: str) -> tuple[list[str], list[str]]:
    """``(test_cmd, extra inputs)`` of the ``test`` target; ``NotComposed`` with the reason otherwise."""
    _, options = target(tree, path, "test")
    config = options.get("jestConfig")
    if config is None:
        raise NotComposed("option_missing:jestConfig")
    if not isinstance(config, str) or not config:
        raise NotComposed("option:jestConfig")
    if config.startswith("-"):
        raise NotComposed("pattern_option")
    norm = D.norm_path(config)
    return (["env", "TS_NODE_COMPILER_OPTIONS=" + TS_NODE, "node_modules/.bin/jest", "--config", config],
            [norm] if norm else [])
