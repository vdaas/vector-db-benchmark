import kubernetes as k8s
import time
import yaml
from benchmark.dataset import Dataset
from engine.base_client.configure import BaseConfigurator
from engine.base_client.distances import Distance
from engine.clients.vald.config import (
    POD_DISRUPTION_BUDGET,
    CONFIG_MAP,
    SERVICE,
    STATEFUL_SET,
    PRIORITY_CLASS,
)


def _delete(f1, f2, resource, namespace="default"):
    res = f1(namespace, field_selector=f"metadata.name={resource.metadata.name}")
    if len(res.items) > 0:
        f2(resource.metadata.name, namespace)


class ValdConfigurator(BaseConfigurator):
    DISTANCE_MAPPING = {
        Distance.L2: "L2",
        Distance.DOT: "COS",
        Distance.COSINE: "COS",
    }

    def __init__(self, host, collection_params: dict, connection_params: dict):
        super().__init__(host, collection_params, connection_params)

        k8s.config.load_kube_config(connection_params["kubeconfig"])

    def clean(self):
        api_client = k8s.client.ApiClient()
        policy_api = k8s.client.PolicyV1Api(api_client)
        _delete(
            policy_api.list_namespaced_pod_disruption_budget,
            policy_api.delete_namespaced_pod_disruption_budget,
            POD_DISRUPTION_BUDGET,
        )
        core_api = k8s.client.CoreV1Api(api_client)
        _delete(
            core_api.list_namespaced_config_map,
            core_api.delete_namespaced_config_map,
            CONFIG_MAP,
        )
        _delete(
            core_api.list_namespaced_service,
            core_api.delete_namespaced_service,
            SERVICE,
        )
        apps_api = k8s.client.AppsV1Api(api_client)
        _delete(
            apps_api.list_namespaced_stateful_set,
            apps_api.delete_namespaced_stateful_set,
            STATEFUL_SET,
        )
        scheduling_api = k8s.client.SchedulingV1Api(api_client)
        res = scheduling_api.list_priority_class(
            field_selector=f"metadata.name={PRIORITY_CLASS.metadata.name}"
        )
        if len(res.items) > 0:
            scheduling_api.delete_priority_class(PRIORITY_CLASS.metadata.name)
        
        time.sleep(10) # TODO: using watch

    def recreate(self, dataset: Dataset, collection_params):
        api_client = k8s.client.ApiClient()
        configmap = CONFIG_MAP
        with open(collection_params["base_config"]) as f:
            cfg = yaml.safe_load(f)
            configmap.data = {
                "config.yaml": yaml.safe_dump(
                    {
                        **cfg,
                        **collection_params["ngt_config"],
                        **{
                            "dimension": dataset.config.vector_size,
                            "distance_type": self.DISTANCE_MAPPING[
                                dataset.config.distance
                            ],
                        },
                    }
                )
            }

        policy_api = k8s.client.PolicyV1Api(api_client)
        policy_api.create_namespaced_pod_disruption_budget(
            "default", POD_DISRUPTION_BUDGET
        )
        core_api = k8s.client.CoreV1Api(api_client)
        core_api.create_namespaced_config_map("default", configmap)
        core_api.create_namespaced_service("default", SERVICE)
        apps_api = k8s.client.AppsV1Api(api_client)
        apps_api.create_namespaced_stateful_set("default", STATEFUL_SET)
        scheduling_api = k8s.client.SchedulingV1Api(api_client)
        scheduling_api.create_priority_class(PRIORITY_CLASS)

        time.sleep(30) # TODO: using watch
