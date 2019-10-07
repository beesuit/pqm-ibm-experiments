# -----------------------------------------------------------------------------
# Distributed under the GNU General Public License.
#
# Contributors: Priscila
#               Rodrigo
#               Adenilton Silva adenilton.silva@ufrpe.br
# -----------------------------------------------------------------------------
# References:
#
# Trugenberger, Carlo A. "Probabilistic quantum memories." Physical Review
# Letters 87.6 (2001): 067901.
# -----------------------------------------------------------------------------
# File description:
#
# Probabilistic quantum memory implementation on qiskit
# -----------------------------------------------------------------------------


import qiskit
import sympy as sp

class PQM(object):

    """
    probabilistic quantum memory

    :param memory_size: number of qubits in memory quantum register
    :param c_size: Integer representing number of ancilla qubits
    :param cmap: Map from software to hardware
    :param circuit_name: Circuit name
    """

    def __init__(self, memory_size, c_size=1, cmap=None, circuit_name='pqm13'):
        self.memory_size = memory_size
        self.c_size = c_size
        self.cmap = cmap
        self.circuit_name = circuit_name
        
        self.pattern = [0 for x in range(memory_size)]
        self.m_input = None
        self.scale_parameter = 1
        
        mqr = qiskit.QuantumRegister(self.memory_size, 'memory')
        
        cqr = qiskit.QuantumRegister(self.c_size, 'ancilla')
        cr = qiskit.ClassicalRegister(self.c_size)
        qc = qiskit.QuantumCircuit(mqr, cqr, cr, name=circuit_name)
        
        self.circuit = qc
        self.mqr = mqr
        self.cqr = cqr
        self.cr = cr

    def set_memory(self, amplitudes):
        self.circuit.initialize(amplitudes, self.mqr)

    def store(self, pattern):
        # TODO implement storage algorithm arXiv:quant-ph/0012100
        if len(pattern) > self.memory_size:
            raise Exception
        
        self.pattern = pattern
        for i in pattern:
            if i == 1:
                self.circuit.x(self.mqr[i])
        
    def recover(self, m_input, scale_parameter = 1):
        """
        :param m_input:  input pattern
        :param scale_parameter:  Distance modifier
        :return: 0 with high probability if the Hamming distance
        between input and patterns is close to 0 (:param not equal to 1 changes this behaviour)
        """
        ms = self.memory_size
        n = ms
        
        self.m_input = m_input
        self.scale_parameter = scale_parameter
        
        #XORi_j, m_k
        for k in range(ms):
            if int(m_input[k]) == 1:
                self.circuit.x(self.mqr[k])
        
        for k in range(ms):
            self.circuit.u1(sp.pi/(2*n * scale_parameter), self.mqr[k])

        # initialize uaxiliary quantum bit |c>
        self.circuit.h(self.cqr[0])
        
        for k in range(ms):
            self.circuit.cu1(- sp.pi/(n * scale_parameter), self.cqr[0], self.mqr[k])
            
        #XORi_j, m_k
        for k in range(ms):
            if int(m_input[k]) == 1:
                self.circuit.x(self.mqr[k])
            
        self.circuit.h(self.cqr[0])
        
        self.circuit.barrier(self.mqr)
        
        self.circuit.measure(self.cqr[0], self.cr[0])