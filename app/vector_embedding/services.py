from app.doc_processing.services import DocProcessing

doc_processing = DocProcessing()

class VectorEmbeddings:
    def generate_embedding(self, file_path: str):
        vectors = []
        for chunks in doc_processing.load_and_split(file_path):
            for i, chunk in enumerate(chunks):
                vector = doc_processing.encode(chunk)
                vectors.append(vector)
        return vectors


test = VectorEmbeddings()
file = test.generate_embedding("document/documents.pdf")
print(file)  # giờ sẽ in ra list các vector