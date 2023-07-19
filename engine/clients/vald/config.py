from kubernetes import client


def _metadata(name="vald-agent-ngt"):
    return client.V1ObjectMeta(
        name=name,
        labels={
            "app": "vald-agent-ngt",
            "app.kubernetes.io/name": "vald",
            "helm.sh/chart": "vald-v1.7.6",
            "app.kubernetes.io/managed-by": "Helm",
            "app.kubernetes.io/instance": "vald",
            "app.kubernetes.io/version": "v1.7.6",
            "app.kubernetes.io/component": "agent",
        },
    )


_label_selector = client.V1LabelSelector(match_labels={"app": "vald-agent-ngt"})

POD_DISRUPTION_BUDGET = client.V1PodDisruptionBudget(
    api_version="policy/v1",
    metadata=_metadata(),
    spec=client.V1PodDisruptionBudgetSpec(max_unavailable=1, selector=_label_selector),
)

CONFIG_MAP = client.V1ConfigMap(
    api_version="v1",
    metadata=_metadata(name="vald-agent-ngt-config"),
    data={"config.yaml": ""},
)

SERVICE_PORT = client.V1ServicePort(
    name="grpc", port=8081, target_port='grpc', protocol="TCP", node_port=31081
)

READINESS_PORT = client.V1ServicePort(
    name="readiness", port=3001, target_port='readiness', protocol="TCP", node_port=31001
)

SERVICE = client.V1Service(
    api_version="v1",
    metadata=_metadata(),
    spec=client.V1ServiceSpec(
        ports=[SERVICE_PORT, READINESS_PORT],
        selector={
            "app.kubernetes.io/name": "vald",
            "app.kubernetes.io/component": "agent",
        },
        type="NodePort",
        cluster_ip=None,
    ),
)

STATEFUL_SET = client.V1StatefulSet(
    api_version="apps/v1",
    metadata=_metadata(),
    spec=client.V1StatefulSetSpec(
        service_name="vald-agent-ngt",
        pod_management_policy="Parallel",
        replicas=1,
        revision_history_limit=2,
        selector=_label_selector,
        update_strategy=client.V1StatefulSetUpdateStrategy(
            type="RollingUpdate", rolling_update={"partition": 0}
        ),
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                creation_timestamp=None,
                labels={
                    "app": "vald-agent-ngt",
                    "app.kubernetes.io/name": "vald",
                    "app.kubernetes.io/instance": "vald",
                    "app.kubernetes.io/component": "agent",
                },
            ),
            spec=client.V1PodSpec(
                affinity=client.V1Affinity(
                    node_affinity=client.V1NodeAffinity(
                        preferred_during_scheduling_ignored_during_execution=[]
                    ),
                    pod_affinity=client.V1PodAffinity(
                        preferred_during_scheduling_ignored_during_execution=[],
                        required_during_scheduling_ignored_during_execution=[],
                    ),
                    pod_anti_affinity=client.V1PodAntiAffinity(
                        preferred_during_scheduling_ignored_during_execution=[
                            client.V1WeightedPodAffinityTerm(
                                pod_affinity_term=client.V1PodAffinityTerm(
                                    label_selector=client.V1LabelSelector(
                                        match_expressions=[
                                            client.V1LabelSelectorRequirement(
                                                key="app",
                                                operator="In",
                                                values=["vald-agent-ngt"],
                                            )
                                        ]
                                    ),
                                    topology_key="kubernetes.io/hostname",
                                ),
                                weight=100,
                            )
                        ],
                        required_during_scheduling_ignored_during_execution=[],
                    ),
                ),
                containers=[
                    client.V1Container(
                        name="vald-agent-ngt",
                        image="vdaas/vald-agent-ngt:v1.7.6",
                        image_pull_policy="Always",
                        liveness_probe=client.V1Probe(
                            failure_threshold=2,
                            http_get=client.V1HTTPGetAction(
                                path="/liveness", port="liveness", scheme="HTTP"
                            ),
                            initial_delay_seconds=5,
                            period_seconds=3,
                            success_threshold=1,
                            timeout_seconds=2,
                        ),
                        readiness_probe=client.V1Probe(
                            failure_threshold=2,
                            http_get=client.V1HTTPGetAction(
                                path="/readiness", port="readiness", scheme="HTTP"
                            ),
                            initial_delay_seconds=10,
                            period_seconds=3,
                            success_threshold=1,
                            timeout_seconds=2,
                        ),
                        startup_probe=client.V1Probe(
                            http_get=client.V1HTTPGetAction(
                                path="/liveness", port="liveness", scheme="HTTP"
                            ),
                            initial_delay_seconds=5,
                            timeout_seconds=2,
                            success_threshold=1,
                            failure_threshold=200,
                            period_seconds=5,
                        ),
                        ports=[
                            client.V1ContainerPort(
                                name="liveness",
                                protocol="TCP",
                                container_port=3000,
                            ),
                            client.V1ContainerPort(
                                name="readiness",
                                protocol="TCP",
                                container_port=3001,
                            ),
                            client.V1ContainerPort(
                                name="grpc",
                                protocol="TCP",
                                container_port=8081,
                            ),
                        ],
                        resources=client.V1ResourceRequirements(
                            requests={"cpu": "100m", "memory": "100Mi"}
                        ),
                        termination_message_path="/dev/termination-log",
                        termination_message_policy="File",
                        security_context=client.V1SecurityContext(
                            allow_privilege_escalation=False,
                            capabilities=client.V1Capabilities(drop=["ALL"]),
                            privileged=False,
                            read_only_root_filesystem=False,
                            run_as_group=65532,
                            run_as_non_root=True,
                            run_as_user=65532,
                        ),
                        env=[
                            client.V1EnvVar(
                                name="MY_NODE_NAME",
                                value_from=client.V1EnvVarSource(
                                    field_ref=client.V1ObjectFieldSelector(
                                        field_path="spec.nodeName"
                                    )
                                ),
                            ),
                            client.V1EnvVar(
                                name="MY_POD_NAME",
                                value_from=client.V1EnvVarSource(
                                    field_ref=client.V1ObjectFieldSelector(
                                        field_path="metadata.name"
                                    )
                                ),
                            ),
                            client.V1EnvVar(
                                name="MY_POD_NAMESPACE",
                                value_from=client.V1EnvVarSource(
                                    field_ref=client.V1ObjectFieldSelector(
                                        field_path="metadata.namespace"
                                    )
                                ),
                            ),
                        ],
                        volume_mounts=[
                            client.V1VolumeMount(
                                name="vald-agent-ngt-config", mount_path="/etc/server"
                            )
                        ],
                    )
                ],
                dns_policy="ClusterFirst",
                restart_policy="Always",
                scheduler_name="default-scheduler",
                security_context=client.V1PodSecurityContext(
                    fs_group=65532,
                    fs_group_change_policy="OnRootMismatch",
                    run_as_group=65532,
                    run_as_non_root=True,
                    run_as_user=65532,
                ),
                termination_grace_period_seconds=120,
                volumes=[
                    client.V1Volume(
                        name="vald-agent-ngt-config",
                        config_map=client.V1ConfigMapVolumeSource(
                            default_mode=420, name="vald-agent-ngt-config"
                        ),
                    )
                ],
                priority_class_name="default-vald-agent-ngt-priority",
            ),
        ),
    ),
)

PRIORITY_CLASS = client.V1PriorityClass(
    api_version="scheduling.k8s.io/v1",
    metadata=_metadata(name="default-vald-agent-ngt-priority"),
    value=int(1e9),
    preemption_policy="Never",
    global_default=False,
    description="A priority class for Vald agent.",
)
