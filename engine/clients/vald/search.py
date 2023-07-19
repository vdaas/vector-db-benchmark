from typing import Dict, List, Tuple
import grpc
from engine.base_client.search import BaseSearcher
from vald.v1.vald import search_pb2_grpc
from vald.v1.payload import payload_pb2
from engine.clients.vald.config import SERVICE_PORT


class ValdSearcher(BaseSearcher):
    cfg: Dict = None
    stub: search_pb2_grpc.SearchStub = None

    @classmethod
    def init_client(
        cls, host: str, distance, connection_params: dict, search_params: dict
    ):
        grpc_opts = map(lambda x: tuple(x), connection_params["grpc_opts"])
        channel = grpc.insecure_channel(f"{host}:{SERVICE_PORT.node_port}", grpc_opts)
        cls.stub = search_pb2_grpc.SearchStub(channel)
        cls.cfg = payload_pb2.Search.Config(**search_params)

    @classmethod
    def search_one(
        cls, vector: List[float], meta_conditions, top: int | None
    ) -> List[Tuple[int, float]]:
        cfg = cls.cfg
        cfg.num = top
        res = cls.stub.Search(payload_pb2.Search.Request(vector=vector, config=cfg))
        return [(int(r.id), r.distance) for r in res.results]
