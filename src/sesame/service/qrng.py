from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def get_qrng_sim_value():
    qc = QuantumCircuit(128, 128)

    qc.h(range(128))

    qc.measure(range(128), range(128))

    result = AerSimulator().run(qc, shots=1).result()
    qrng_value = next(iter(result.get_counts(qc).keys()))

    hex_string = hex(int(qrng_value, 2))[2:].zfill(32)
    return hex_string
