import grpc
import urllib
from typing import List
from engine.base_client.upload import BaseUploader
from vald.v1.agent.core import agent_pb2_grpc
from vald.v1.vald import insert_pb2_grpc
from vald.v1.payload import payload_pb2


class ValdUploader(BaseUploader):
    @classmethod
    def init_client(cls, host, distance, connection_params: dict, upload_params: dict):
        grpc_opts = map(lambda x: tuple(x), connection_params["grpc_opts"])
        cls.channel = grpc.insecure_channel(f"{host}:31081", grpc_opts)
        cls.icfg = payload_pb2.Insert.Config(**upload_params["insert_config"])
        cls.acfg = payload_pb2.Control.CreateIndexRequest(**upload_params["index_config"])

        while True:
            try:
                with urllib.request.urlopen(f"http://{host}:31001/readiness") as response:
                    if response.getcode() == 200:
                        break
            except (urllib.error.HTTPError, urllib.error.URLError):
                pass

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

    @classmethod
    def post_upload(cls, distance):
        astub = agent_pb2_grpc.AgentStub(cls.channel)
        astub.CreateIndex(cls.acfg)
        return {}

    @classmethod
    def delete_client(cls):
        if cls.channel != None:
            cls.channel.close()
            del cls.channel
