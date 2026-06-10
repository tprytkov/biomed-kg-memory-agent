from src.app.agent.memory_agent import BiomedicalKGMemoryAgent
from src.app.graph.factory import build_graph_store
from src.app.utils.config import get_settings


def main() -> None:
    settings = get_settings()
    store = build_graph_store(settings)
    agent = BiomedicalKGMemoryAgent(graph_store=store, settings=settings)
    result = agent.reset_and_seed()
    print(result.model_dump_json(indent=2))
    if hasattr(store, "close"):
        store.close()


if __name__ == "__main__":
    main()
