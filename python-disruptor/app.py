#! /bin/env python3
"""pyhton-disruptor deletes or restores kubernetes pod disruption budgets"""
import os
import yaml
from kubernetes import client, config

STATE_CONFIG_NAME = os.getenv('STATE_CM_NAME', "dis-disruptor-state")
STATE_CONFIG_NAMESPACE = os.getenv('STATE_CM_NAMESPACE', "kube-system")

def read_config(config_path):
    """reading the config file yaml from disk returning a dict"""
    # TODO: handle error
    file_handle = open(config_path)
    cfg = yaml.load(file_handle, Loader=yaml.FullLoader)
    file_handle.close()
    # TODO: input validation 
    return cfg

def create_pdb(pdb_namespace, pdb):
    """creaing the pod disruption budget in the specified namespace"""
    poly_client = client.PolicyV1beta1Api()
    # TODO: handle complete selector object  
    selector = client.models.v1_label_selector.V1LabelSelector(
        match_labels=pdb['spec']['selector']['match_labels'])
    # TODO: handle complete spec object
    spec = client.models.v1beta1_pod_disruption_budget_spec.V1beta1PodDisruptionBudgetSpec(
        selector=selector,
        min_available=pdb['spec']['min_available'])
    # TODO: maybe use real metadata object instead of trusting dict serialisation
    body = client.models.v1beta1_pod_disruption_budget.V1beta1PodDisruptionBudget(
        spec=spec,
        metadata=pdb['metadata'])
    # TODO: handle failing api request
    api_response = poly_client.create_namespaced_pod_disruption_budget(
        pdb_namespace, body)
    print(api_response)

def create_all_pdbs(pdbs):
    """iterates over all provided pdb dicts and creates each of them"""
    for pdb in pdbs:
        namespace = pdb['metadata']['namespace']
        create_pdb(namespace, pdb)

def get_pdbs(label_selector):
    """get_pdb returns all pod disruptino budgets from all namespaces"""
    print('geeting pdbs with labesl', label_selector)
    poly_client = client.PolicyV1beta1Api()
    pdbs = []
    # TODO: handle failing api request
    raw_pdbs = poly_client.list_pod_disruption_budget_for_all_namespaces(
        label_selector=label_selector)
    for pdb in raw_pdbs.items:
        pdbs.append(pdb.to_dict())
    return pdbs

def delete_pdb(pdb_name, pdb_namespace):
    """deleting the specified pod disruption budget"""
    poly_client = client.PolicyV1beta1Api()
    # TODO: handle failing api request
    api_response = poly_client.delete_namespaced_pod_disruption_budget(
        pdb_name, pdb_namespace)
    print(api_response)

def delete_all_pdbs(pdbs):
    """deleting all given pdbs """
    for pdb in pdbs:
        name = pdb['metadata']['name']
        namespace = pdb['metadata']['namespace']
        delete_pdb(name, namespace)

def trim_null_values(my_dict):
    """returnes a new dict with all values stripped that are none"""
    return {key:val for key, val in my_dict.items() if val is not None}

def pdbs_to_state(pdbs):
    """turns a pdb dict list into a dict that can be passed as state"""
    state = {}
    for pdb in pdbs:
        state[pdb['metadata']['name']] = yaml.dump(pdb)
    return state

def state_to_pdbs(state):
    """returns list of pdb dicts from the given state dict"""
    pdbs = []
    for name, pdb in state.data.items():
        pdbs.append(yaml.load(pdb, Loader=yaml.FullLoader))
    return pdbs

def read_state(name, namespace):
    """reading the state from the config map"""
    default_client = client.CoreV1Api()
    # TODO: handle failing api request
    api_response = default_client.read_namespaced_config_map(name, namespace)
    return api_response

def write_state(state_name, state_namespace, state):
    """writing state as data into the state config map"""
    default_client = client.CoreV1Api()
    metadata = client.V1ObjectMeta(
        name=state_name,
        namespace=state_namespace)
    body = client.V1ConfigMap(
        api_version='v1',
        data=state,
        kind='ConfigMap',
        metadata=metadata)
    # TODO: handle failing api request
    api_response = default_client.replace_namespaced_config_map(
        state_name, state_namespace, body)
    print(api_response)

def label_dict_to_string(s_dict):
    """converts a config dict to selector string to be pased to an api request"""
    return ', '.join("{!s}={!s}".format(key, val) for (key, val) in s_dict.items())

def disruption(state_name, state_namespace, label_selector):
    """save all discovered pdbs and then delete them"""
    pdbs = get_pdbs(label_selector)
    state = pdbs_to_state(pdbs)
    write_state(state_name, state_namespace, state)
    delete_all_pdbs(pdbs)

def reconstruction(state_name, state_namespace):
    """reconstructs all pod disruption budgets from the state config map"""
    state = read_state(state_name, state_namespace)
    pdbs = state_to_pdbs(state)
    create_all_pdbs(pdbs)


config.load_incluster_config()
CFG = read_config('/config.yaml')
print(CFG)
if CFG['mode'] == 'disruption':
    disruption(
        STATE_CONFIG_NAME,
        STATE_CONFIG_NAMESPACE,
        label_dict_to_string(CFG['labelSelector']))
else:
    reconstruction(STATE_CONFIG_NAME, STATE_CONFIG_NAMESPACE)
