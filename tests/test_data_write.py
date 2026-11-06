"""Tests for ClawData.data_write value formatting (clawpack/clawutil#176)"""

import io
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from clawpack.clawutil.data import ClawData


def _write(value):
    data = ClawData()
    data._out_file = io.StringIO()
    data.data_write("x", value=value)
    line = data._out_file.getvalue()
    assert line.count("\n") == 1, f"value spans lines: {line!r}"
    return line.split("=:")[0].strip()


@pytest.mark.parametrize("value", [
    [1, 2, 3],
    [0.1, 1e-20, -2.5],
    (1.0, 2),
    ["a.txt", "b.txt"],
    [True, False],
    [],
])
def test_python_lists_unchanged(value):
    # Byte-identical to the previous str(value)[1:-1].replace(',', '') so
    # existing .data files can still be diffed against new ones
    assert _write(value) == str(value)[1:-1].replace(',', '').strip()


def test_array_full_precision():
    x = np.array([0.123456789012345, 1.0 / 3.0, 1e-300, 6.02214076e23])
    np.testing.assert_array_equal(
        np.array(_write(x).split(), dtype=float), x)


def test_float32_array_shortest():
    assert _write(np.array([0.1, 2.5], dtype=np.float32)) == "0.1 2.5"


@pytest.mark.parametrize("n", [30, 2000])
def test_long_array_not_wrapped_or_elided(n):
    x = np.arange(n, dtype=float)
    s = _write(x)
    assert "..." not in s
    np.testing.assert_array_equal(np.array(s.split(), dtype=float), x)


def test_list_of_numpy_scalars():
    assert _write(list(np.array([1, 2, 3]))) == "1 2 3"
    assert _write(list(np.array([0.1, 0.2]))) == "0.1 0.2"


def test_list_of_paths():
    assert _write([Path("a.txt"), Path("dir/b.txt")]) == "'a.txt' 'dir/b.txt'"


def test_scalars():
    assert _write(True) == "T"
    assert _write(Path("a.txt")) == "'a.txt'"
    assert _write(np.float64(0.1)) == "0.1"
    assert _write(np.array(0.1)) == "0.1"


@pytest.mark.parametrize("value", [np.ones((2, 2)), [[1, 2], [3, 4]]])
def test_multidimensional_rejected(value):
    with pytest.raises(ValueError, match="only 1-D"):
        _write(value)


def test_dataframe():
    pd = pytest.importorskip("pandas")
    assert _write(pd.DataFrame({"a": [1.5, 2.5]})) == "1.5 2.5"
    with pytest.raises(ValueError, match="only 1-D"):
        _write(pd.DataFrame({"a": [1, 2], "b": [3, 4]}))


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="needs gfortran")
def test_fortran_list_read_round_trip(tmp_path):
    """What Fortran reads back is bit-identical to what was written."""
    x = np.array([0.123456789012345, 1.0 / 3.0, 1e-300, -6.02214076e23,
                  np.pi, 0.1])
    data = ClawData()
    with open(tmp_path / "x.data", "w") as data._out_file:
        data.data_write("x", value=x)

    (tmp_path / "read.f90").write_text(f"""
program read_values
    implicit none
    real(kind=8) :: x({len(x)})
    open(7, file='x.data')
    read(7, *) x
    write(*, '(es26.17e3)') x
end program
""")
    subprocess.run(["gfortran", "read.f90", "-o", "read_values"],
                   cwd=tmp_path, check=True)
    out = subprocess.run(["./read_values"], cwd=tmp_path, check=True,
                         capture_output=True, text=True).stdout
    np.testing.assert_array_equal(np.array(out.split(), dtype=float), x)
