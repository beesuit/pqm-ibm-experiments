import qiskit
import Qconfig
from IBMQuantumExperience import IBMQuantumExperience
import matplotlib.pyplot as plt
import pickle
from qiskit._result import Result
import numpy as np
import os

EXPS_FOLDER = 'exps/'
PLOTS_FOLDER = 'plots/'


def execute(circuits, backend, shots, max_credits=15, initial_layout=None):
    try:
        backend_instance = qiskit.get_backend(backend)
    except Exception:
        try:
            print('Qconfig loaded from %s.' % Qconfig.__file__)
            qiskit.register(Qconfig.APItoken, Qconfig.config['url'])
            backend_instance = qiskit.get_backend(backend)
        except ConnectionError as e:
            raise e
    
    job = qiskit.execute(circuits, backend=backend_instance, shots=shots, max_credits=max_credits, initial_layout=initial_layout)

    if not backend_instance.configuration['local']:
        print('Submitting job to {} backend...'.format(backend))
        print(job.status)
        print('Waiting for job_id...')
        job.id
        print(job.status)
        result = job.result(timeout=0)

    else:
        print('Initializing job on {}...'.format(backend))
        print(job.status)
        result = job.result()

    return result


def save_plot(filename):
    filename = PLOTS_FOLDER + filename
    os.makedirs(os.path.dirname(PLOTS_FOLDER), exist_ok=True)
    plt.savefig(filename, format='pdf', dpi=1000)


def save_result(filename, result):
    filename = EXPS_FOLDER + filename
    os.makedirs(os.path.dirname(EXPS_FOLDER), exist_ok=True)
    with open(filename, 'wb') as file:
        pickle.dump(result, file)


def load_result(filename):
    filename = EXPS_FOLDER + filename
    try:
        with open(filename, 'rb') as file:
            return pickle.load(file)
    except Exception as e:
        raise e


def check_result(result):
    result_status = result.get_status()

    if result_status != 'COMPLETED':
        job_id = result._result['id']

        return fetch_result(job_id)

    print(result_status)
    return result


def fetch_result(job_id):
    api = IBMQuantumExperience(Qconfig.APItoken, Qconfig.config, verify=True)
    user = _get_user(api)
    print('Requesting job {} result as user: {}'.format(job_id, user))

    job_result = api.get_job(job_id)
    job_status = job_result['status']
    print('Job {} is {}'.format(job_id, job_status))
    #print(job_result)

    job_result_list = []
    for circuit_result in job_result['qasms']:
        this_result = {'data': circuit_result.get('data'),
                       'name': circuit_result['name'],
                       'compiled_circuit_qasm': circuit_result['qasm'],
                       'status': circuit_result['status']}

        if 'metadata' in circuit_result:
            this_result['metadata'] = circuit_result['metadata']
        job_result_list.append(this_result)

    job_result = {'id': job_result['id'],
                  'status': job_result['status'],
                  'used_credits': job_result['usedCredits'],
                  'result': job_result_list,
                  'backend_name': job_result['backend']}

    return Result(job_result)


def bar_plot(counts, label, x_labels, measure, width, position, max_shots=None, orientation='H'):
    plt.style.use('tableau-colorblind10')
    xlabel = 'Memory pattern'
    ylabel = r'Probability of $\left|{c}\right\rangle = \left|{0}\right\rangle$'
    x = np.arange(len(counts))
    if max_shots is not None:
        counts_0 = [c.get(measure, 0) / max_shots for c in counts]
    else:
        counts_0 = [c.get(measure, 0) for c in counts]

    #print('counts0', counts_0)

    if orientation == 'H':
        y = x
        x = counts_0
        plt.barh(y + position, x, width, label=label)
        plt.xlabel(ylabel)
        plt.ylabel(xlabel)
        plt.yticks(y, x_labels, fontsize=12)
        plt.xlim(xmax=1)
    else:
        y = counts_0
        plt.bar(x + position, y, width=width, label=label)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(x, x_labels, fontsize=12)


def MSE(exp_results, input_patterns):
    mem_patterns = exp_results['ibmqx4'][input_patterns[0]].get_names()

    result = {}
    for mem_pattern in mem_patterns:
        error_sum_per_mem_pattern = 0
        for input_pattern in input_patterns:
            observed = exp_results['quantum'][input_pattern].get_data(mem_pattern)['counts']['0'] / 8192
            estimated = exp_results['ibmqx4'][input_pattern].get_data(mem_pattern)['counts']['00000']/8192

            error = (observed - estimated) ** 2

            error_sum_per_mem_pattern += error

        mean_error = error_sum_per_mem_pattern/len(input_patterns)
        result[mem_pattern] = mean_error
        #print('Pattern: {} | MSE: {}'.format(mem_pattern, error_sum_per_mem_pattern/len(input_patterns)))

    return result


def _get_user(api):
    user_id = api.req.credential.get_user_id()
    user_data_url = '/users/' + user_id
    return api.req.get(user_data_url)['username']


def _to_result(quantum_result):
    job_result_list = []

    for circuit_result in quantum_result:
        this_result = {'data': {'counts': circuit_result.get('counts')},
                       'name': circuit_result['name'],
                       'compiled_circuit_qasm': None,
                       'status': 'COMPLETED'}

        job_result_list.append(this_result)

    job_result = {'id': None,
                  'status': 'COMPLETED',
                  'used_credits': None,
                  'result': job_result_list,
                  'backend_name': 'quantum'}

    return Result(job_result)
