import datetime
import kubernetes as k8s
import yaml
from benchmark.dataset import Dataset
from engine.base_client.configure import BaseConfigurator
from engine.base_client.distances import Distance


class ValdConfigurator(BaseConfigurator):
    DISTANCE_MAPPING = {
        Distance.L2: "L2",
        Distance.DOT: "COS",
        Distance.COSINE: "COS",
    }

    def __init__(self, host, collection_params: dict, connection_params: dict):
        super().__init__(host, collection_params, connection_params)

        k8s.config.load_kube_config(connection_params["kubeconfig"])
        with open(collection_params["base_config"]) as f:
            self.base_config = yaml.safe_load(f)

    def clean(self):
        pass

    def recreate(self, dataset: Dataset, collection_params):
        api_client = k8s.client.ApiClient()

        ngt_config = collection_params["ngt_config"] | {
            "dimension": dataset.config.vector_size,
            "distance_type": self.DISTANCE_MAPPING[dataset.config.distance]
        }
        core_api = k8s.client.CoreV1Api(api_client)
        core_api.patch_namespaced_config_map("vald-agent-ngt-config", "default", body={"data":{"config.yaml":yaml.safe_dump(self.base_config|{'ngt': ngt_config})}})

        apps_api = k8s.client.AppsV1Api(api_client)
        apps_api.patch_namespaced_stateful_set("vald-agent-ngt", "default", body={"spec":{"template":{"metadata":{"annotations":{"reloaded-at":datetime.datetime.now().isoformat()}}}}})

        w = k8s.watch.Watch()
        for event in w.stream(apps_api.list_namespaced_stateful_set, namespace='default', label_selector='app=vald-agent-ngt', timeout_seconds=30):
            if event['object'].status.available_replicas is not None and event['object'].status.available_replicas != 0:
                w.stop()
