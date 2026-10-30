"""The public call shape (PRD B5.1): import model_interface as model; model.run(task, inputs,
output_schema). The function lives in model_interface.runner; there is no model_interface.run
module, so importing one fails loudly instead of returning the function by mistake."""

from __future__ import annotations

import importlib
import inspect
import types

import pytest

import model_interface
import model_interface as model
from model_interface import runner


def test_model_run_is_the_runner_function() -> None:
    assert model.run is runner.run
    assert inspect.isfunction(model.run)


def test_model_run_takes_task_inputs_output_schema_first() -> None:
    params = list(inspect.signature(model.run).parameters.values())
    assert [p.name for p in params[:3]] == ["task", "inputs", "output_schema"]
    assert all(p.kind is p.POSITIONAL_OR_KEYWORD for p in params[:3])
    assert all(p.kind is p.KEYWORD_ONLY for p in params[3:])


def test_from_import_gives_the_function() -> None:
    from model_interface import Result, run

    assert run is runner.run and Result is runner.Result


def test_runner_module_imports_as_a_module() -> None:
    assert isinstance(
        importlib.import_module("model_interface.runner"), types.ModuleType
    )


def test_there_is_no_model_interface_run_module() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("model_interface.run")


def test_every_exported_name_exists() -> None:
    for name in model_interface.__all__:
        assert hasattr(model_interface, name), name
