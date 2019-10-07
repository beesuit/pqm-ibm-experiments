import numpy as np
import pqm
import util
import matplotlib.pyplot as plt
import quantum


def random_input(memory_size):
    random_input = np.random.randint(memory_size ** 2 / 4)
    pattern = np.binary_repr(random_input, memory_size)
    return pattern


def decimal_input(input_value, memory_size):
    pattern = np.binary_repr(input_value, memory_size)
    return pattern


def random_amplitude(memory_size, mu=0, sigma=1):
    amplitudes = sigma * np.random.randn(memory_size ** 2) + mu
    amplitudes = amplitudes / np.linalg.norm(amplitudes)
    return amplitudes


def qiskit_init(memory, patterns):
    amplitudes = np.zeros([memory.memory_size ** 2])
    for value in patterns:
        amplitudes[int(value, 2)] = 1
    amplitudes = amplitudes / np.linalg.norm(amplitudes)

    memory.circuit.initialize(amplitudes, memory.mqr)


def manual_init(memory, patterns):
    mem_size = memory.memory_size

    if len(patterns) == 1:
        for i in range(mem_size):
            if patterns[0][i] == str(1):
                memory.circuit.x(memory.mqr[i])

    elif len(patterns) == 2:
        for i in range(mem_size):
            if patterns[0][i] != patterns[1][i]:
                memory.circuit.h(memory.mqr[i])
            else:
                if patterns[0][i] == str(1):
                    memory.circuit.x(memory.mqr[i])


def set_memory(pattern, memory_size, c_size, input_pattern, mem_init, scale_parameter=1):
    memory = pqm.PQM(memory_size, c_size=c_size, circuit_name=str(pattern))

    mem_init(memory, pattern)

    memory.recover(input_pattern, scale_parameter=scale_parameter)

    return memory


def run_job(job_name, memories, backend, shots, initial_layout):
    print('RUN:', job_name)
    filename = job_name + '.p'

    try:
        result = util.load_result(filename)
    except Exception:
        circuits = [memory.circuit for memory in memories]
        result = util.execute(circuits, backend, shots=shots, max_credits=15, initial_layout=initial_layout)
        util.save_result(filename, result)

    job_result = util.check_result(result)

    return job_result


def run_experiment(exp_config, input_patterns, mem_patterns, c_size, num_shots, scale_parameter):
    backends = exp_config['backends']
    mem_init = exp_config['initialization_method']
    memory_layout = exp_config['initial_layout']
    memory_size = exp_config['memory_size']
    memory = mem_patterns[str(memory_size)]

    results = {}
    for backend in backends:
        results[backend] = {}
        if backend == quantum.__name__:
            for input_pattern in input_patterns:
                mock_results = []
                for v in memory.values():
                    q_result = quantum.memory_retrieval(input_pattern, v, c_size, scale_parameter)
                    mock_result = {'name': str(v), 'counts': {'0': q_result[0]*num_shots, '1': q_result[1]*num_shots}}
                    mock_results.append(mock_result)

                job_result = util._to_result(mock_results)

                results[backend][str(input_pattern)] = job_result

        else:
            for input_pattern in input_patterns:
                memories = []
                for v in memory.values():
                    mem = set_memory(v, memory_size, c_size, input_pattern, mem_init, scale_parameter=scale_parameter)
                    memories.append(mem)

                job_name = '{}_{}_{}_param{}{}'.format(backend, input_pattern, mem_init.__name__, str(scale_parameter),
                                                       ('_init_layout' if (memory_layout is not None) else ''))

                job_result = run_job(job_name, memories, backend, num_shots, initial_layout=memory_layout)
                results[backend][str(input_pattern)] = job_result

    return results


def plot_exp(name, exp_results, input_pattern, x_labels, orientation, max_shots):
    base_width = 0.3
    start_offset = -1
    offset = start_offset

    for backend in exp_results.keys():
        measure = '0'
        if backend == quantum.__name__:
            label = "Expected output probability"
        elif backend == 'ibmqx4':
            label = 'Tenerife backend'
            measure = '00000'
        elif backend == 'local_qasm_simulator':
            label = 'QISKit simulator'
        else:
            label = backend

        results = exp_results[backend]
        print('*******')
        print('Experiment:', name)
        print('Backend:', backend)

        counts = []
        for mem_pattern in results[input_pattern].get_names():
            print('-------')
            print('Input: {} | Memory: {}'.format(input_pattern, mem_pattern))
            data = results[input_pattern].get_data(mem_pattern)
            print(data)
            counts.append(data['counts'])

        position = base_width * offset
        util.bar_plot(counts, label, x_labels, measure, base_width, position, max_shots, orientation)
        offset += 1

    if orientation == 'H':
        plt.gca().invert_yaxis()

    plt.title('Input Pattern: {}'.format(input_pattern))
    plt.tight_layout()
    plt.legend()

    #add grid
    plt.grid()

    #save and close plot
    util.save_plot('{}_{}_{}.pdf'.format(name, input_pattern, orientation))
    plt.close(plt.gcf())


if __name__ == '__main__':
    backends = ['ibmqx4', 'local_qasm_simulator', 'quantum']

    experiments = {}
    experiments['mi_il_1q'] = {
        'backends': backends,
        'memory_size': 1,
        'initialization_method': manual_init,
        'initial_layout': {('memory', 0): ('q', 0), ('ancilla', 0): ('q', 2)}

    }

    experiments['mi_il_2q'] = {
        'backends': backends,
        'memory_size': 2,
        'initialization_method': manual_init,
        'initial_layout': {('memory', 0): ('q', 0), ('memory', 1): ('q', 1), ('ancilla', 0): ('q', 2)}

    }

    experiments['mi_il_3q'] = {
        'backends': backends,
        'memory_size': 3,
        'initialization_method': manual_init,
        'initial_layout': {('memory', 0): ('q', 0), ('memory', 1): ('q', 1), ('memory', 2): ('q', 4),
                           ('ancilla', 0): ('q', 2)}

    }

    experiments['mi_il_4q'] = {
        'backends': backends,
        'memory_size': 4,
        'initialization_method': manual_init,
        'initial_layout': {('memory', 0): ('q', 0), ('memory', 1): ('q', 1), ('memory', 2): ('q', 4),
                           ('memory', 3): ('q', 3), ('ancilla', 0): ('q', 2)}
    }

    classical_memories = {
        '1': {
            '0': ['0'],
            '1': ['1'],
            '2': ['0', '1']
        },

        '2': {
            '0': ['00'],
            '1': ['11'],
            '2': ['00', '01']
        },

        '3': {
            '0': ['000'],
            '1': ['000', '010'],
            '2': ['000', '100'],
            '3': ['000', '001'],
            '4': ['110', '111'],
            '5': ['111']
        },

        '4': {
            '0': ['0000'],
            '1': ['0000', '0100'],
            '2': ['1000'],
            '3': ['0100', '1100'],
            '4': ['1010'],
            '5': ['0110', '1110'],
            '6': ['1110'],
            '7': ['0111', '1111'],
            '8': ['1111']
        }

    }

    tex_labels = {
        '1': [r'$\left|{0}\right\rangle$', r'$\left|{1}\right\rangle$',
              r'$\frac{1}{\sqrt{2}}(\left|{0}\right\rangle + \left|{1}\right\rangle)$'],

        '2': [r'$\left|{00}\right\rangle$', r'$\left|{11}\right\rangle$', r'$\frac{1}{\sqrt{2}}(\left|{00}\right\rangle + \left|{01}\right\rangle)$'],

        '3': [r'$\left|{000}\right\rangle$', r'$\frac{1}{\sqrt{2}}(\left|{000}\right\rangle + \left|{010}\right\rangle)$', r'$\frac{1}{\sqrt{2}}(\left|{000}\right\rangle + \left|{100}\right\rangle)$',
              r'$\frac{1}{\sqrt{2}}(\left|{000}\right\rangle + \left|{001}\right\rangle)$', r'$\frac{1}{\sqrt{2}}(\left|{110}\right\rangle + \left|{111}\right\rangle)$', r'$\left|{111}\right\rangle$'],

        '4': [r'$\left|{0000}\right\rangle$', r'$\frac{1}{\sqrt{2}}(\left|{0000}\right\rangle + \left|{0100}\right\rangle)$', r'$\left|{1000}\right\rangle$',
              r'$\frac{1}{\sqrt{2}}(\left|{0100}\right\rangle + \left|{1100}\right\rangle)$', r'$\left|{1010}\right\rangle$', r'$\frac{1}{\sqrt{2}}(\left|{0110}\right\rangle + \left|{1110}\right\rangle)$',
              r'$\left|{1110}\right\rangle$', r'$\frac{1}{\sqrt{2}}(\left|{0111}\right\rangle + \left|{1111}\right\rangle)$', r'$\left|{1111}\right\rangle$']
    }

    #RUN EXPERIMENT

    scale_param = 1
    c_size = 1
    num_shots = 8192

    #Select experiment configuration
    exp_name = 'mi_il_1q'
    #exp_name = 'mi_il_2q'
    #exp_name = 'mi_il_3q'
    #exp_name = 'mi_il_4q'

    exp_config = experiments[exp_name]

    inputs = [0, 1]
    #inputs = [0, 1, 2, 3]
    #inputs = [0, 1, 2, 3, 4, 5, 6, 7]
    #inputs = [8, 9, 10, 11, 12, 13, 14, 15]
    #inputs = None

    if inputs is None:
        input_patterns = [decimal_input(i, exp_config['memory_size']) for i in range(2 ** exp_config['memory_size'])]
    else:
        input_patterns = [decimal_input(i, exp_config['memory_size']) for i in inputs]

    exp_results = run_experiment(exp_config, input_patterns, classical_memories, c_size, num_shots, scale_param)

    for input_p in input_patterns:
        plot_exp(exp_name, exp_results, input_p, tex_labels[str(exp_config['memory_size'])], 'H', num_shots)

    mean_error = util.MSE(exp_results, input_patterns)
    print('*******')
    print('MSE:', mean_error)
