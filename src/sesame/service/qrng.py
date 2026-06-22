from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class QRNG:
    def __init__(self):
        self.backend = AerSimulator()

    def get_qrng_sim_rand_bits(self, n):
        qc = QuantumCircuit(n, n)

        qc.h(range(n))

        qc.measure(range(n), range(n))

        result = self.backend.run(qc, shots=1).result()
        qrng_bits = next(iter(result.get_counts(qc).keys()))
        return qrng_bits
