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
Module containing Qiskit tools

"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator


def _unitary_from_qiskit(circuit: QuantumCircuit) -> np.ndarray:
    """Return the unitary of a Qiskit quantum circuit."""
    return Operator(circuit).data
