# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for calculating unitary of quantum circuit/program

"""
from typing import TYPE_CHECKING, Any, Callable, Optional

import numpy as np
from cirq.testing import assert_allclose_up_to_global_phase

from qbraid.exceptions import ProgramTypeError, QbraidError
from qbraid.interface.convert_to_contiguous import convert_to_contiguous

if TYPE_CHECKING:
    import qbraid


class UnitaryCalculationError(QbraidError):
    """Class for exceptions raised during unitary calculation"""


def to_unitary(program: "qbraid.QPROGRAM", ensure_contiguous: Optional[bool] = False) -> np.ndarray:
    """Calculates the unitary of any valid input quantum program.

    Args:
        program (:data:`~qbraid.QPROGRAM`): Any quantum program object supported by qBraid.
        ensure_contiguous: If True, calculates unitary using contiguous qubit indexing

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        UnitaryCalculationError: If the programs unitary could not be calculated.

    Returns:
        Matrix representation of the input quantum program.
    """
    to_unitary_function: Callable[[Any], np.ndarray]

    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    # pylint: disable=import-outside-toplevel

    if "qiskit" in package:
        from qbraid.interface.qbraid_qiskit.tools import _unitary_from_qiskit

        to_unitary_function = _unitary_from_qiskit
    elif "cirq" in package:
        from qbraid.interface.qbraid_cirq.tools import _unitary_from_cirq

        to_unitary_function = _unitary_from_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.tools import _unitary_from_braket

        to_unitary_function = _unitary_from_braket

    elif "pyquil" in package:
        from qbraid.interface.qbraid_pyquil.tools import _unitary_from_pyquil

        to_unitary_function = _unitary_from_pyquil

    else:
        raise ProgramTypeError(program)

    program_input = convert_to_contiguous(program) if ensure_contiguous else program

    try:
        unitary = to_unitary_function(program_input)
    except Exception as err:
        raise UnitaryCalculationError(
            "Unitary could not be calculated from given quantum program."
        ) from err

    return unitary


def circuits_allclose(
    circuit0: "qbraid.QPROGRAM",
    circuit1: "qbraid.QPROGRAM",
    index_contig: Optional[bool] = True,
    strict_gphase: Optional[bool] = False,
    **kwargs,
) -> bool:
    """Check if quantum program unitaries are equivalent.

    Args:
        circuit0 (:data:`~qbraid.QPROGRAM`): First quantum program to compare
        circuit1 (:data:`~qbraid.QPROGRAM`): Second quantum program to compare
        index_contig: If True, calculates circuit unitaries using contiguous qubit indexing.
        stric_gphase: If False, disregards global phase when verifying
            equivalance of the input circuit's unitaries.

    Returns:
        True if the input circuits pass unitary equality check

    """
    unitary0 = to_unitary(circuit0, ensure_contiguous=index_contig)
    unitary1 = to_unitary(circuit1, ensure_contiguous=index_contig)
    if strict_gphase:
        return np.allclose(unitary0, unitary1)
    try:
        atol = kwargs.pop("atol", None) or 1e-7
        assert_allclose_up_to_global_phase(unitary0, unitary1, atol=atol, **kwargs)
    except AssertionError:
        return False
    return True


def unitary_to_little_endian(matrix: np.ndarray) -> np.ndarray:
    """Converts unitary calculated using big-endian system to its
    equivalent form in a little-endian system.

    Args:
        matrix: big-endian unitary

    Raises:
        ValueError: If input matrix is not unitary

    Returns:
        little-endian unitary

    """
    rank = len(matrix)
    if not np.allclose(np.eye(rank), matrix.dot(matrix.T.conj())):
        raise ValueError("Input matrix must be unitary.")
    num_qubits = int(np.log2(rank))
    tensor_be = matrix.reshape([2] * 2 * num_qubits)
    indicies_in = list(reversed(range(num_qubits)))
    indicies_out = [i + num_qubits for i in indicies_in]
    tensor_le = np.einsum(tensor_be, indicies_in + indicies_out)
    return tensor_le.reshape([rank, rank])
