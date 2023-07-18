import grpc
from typing import List
from engine.base_client.upload import BaseUploader
from engine.clients.vald.config import SERVICE_PORT
from vald.v1.agent.core import agent_pb2_grpc
from vald.v1.vald import insert_pb2_grpc
from vald.v1.payload import payload_pb2


class ValdUploader(BaseUploader):
    cfg: payload_pb2.Insert.Config = None
    stub: insert_pb2_grpc.InsertStub = None

    @classmethod
    def init_client(cls, host, distance, connection_params: dict, upload_params: dict):
        grpc_opts = map(lambda x: tuple(x), connection_params["grpc_opts"])
        cls.channel = grpc.insecure_channel(f"{host}:{SERVICE_PORT.node_port}", grpc_opts)
        cls.icfg = payload_pb2.Insert.Config(**upload_params["insert_config"])
        cls.acfg = payload_pb2.Control.CreateIndexRequest(
            **upload_params["index_config"]
        )

    @classmethod
    def upload_batch(
        cls, ids: List[int], vectors: List[list], metadata: List[dict | None]
    ):
        requests = [
            payload_pb2.Insert.Request(
                vector=payload_pb2.Object.Vector(id=str(i), vector=v), config=cls.icfg
            )
            for i, v in zip(ids, vectors)
        ]
        istub = insert_pb2_grpc.InsertStub(cls.channel)
        for _ in istub.StreamInsert(iter(requests)):
            pass

        astub = agent_pb2_grpc.AgentStub(cls.channel)
        astub.CreateIndex(cls.acfg)
