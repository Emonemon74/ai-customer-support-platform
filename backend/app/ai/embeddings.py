from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    _model = None

    @classmethod
    def load(cls):
        if cls._model is None:
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")

        return cls._model

    @classmethod
    def embed(cls, texts: list[str]) -> list[list[float]]:
        model = cls.load()

        return model.encode(
            texts,
            convert_to_numpy=True,
        ).tolist()


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    return EmbeddingModel.embed(texts)