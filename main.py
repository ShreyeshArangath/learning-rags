import ollama 

DATASET_PATH = "cat-facts.txt"
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'

dataset = []
# Each element in the VECTOR_DB will be a tuple (chunk, embedding)
# The embedding is a list of floats, for example: [0.1, 0.04, -0.34, 0.21, ...]
VECTOR_DB = []

def read_dataset():
    with open(DATASET_PATH) as f: 
        dataset = f.readlines()
        print(f'Loaded {len(dataset)} entries from {DATASET_PATH}')
        return dataset

def add_chunk_to_db(chunk): 
    emebed_output = ollama.embed(model=EMBEDDING_MODEL, input=chunk)
    print(f'This is what the embed output looks like: {emebed_output}')
    embedding = emebed_output['embeddings'][0]
    VECTOR_DB.append((chunk, embedding))

def add_chunks(dataset): 
    for i, chunk in enumerate(dataset):
        add_chunk_to_db(chunk)
        print(f'Added chunk {i+1}/{len(dataset)} to the database')


def cosine_similarity(a, b): 
    dot_product = sum([x * y for x, y in zip(a, b)])
    magnitude_a = sum([x ** 2 for x in a]) ** 0.5
    magnitude_b = sum([x**2 for x in b ]) ** 0.5
    return dot_product / (magnitude_a * magnitude_b)


def retrieve(query, top_n = 3): 
    query_embedding = ollama.embed(model=EMBEDDING_MODEL, input=query)['embeddings'][0]
    # store the similarties for each chunk in a list of tuples (chunk, similarity)
    similarities = []
    for chunk, embedding in VECTOR_DB:
        similarity = cosine_similarity(query_embedding, embedding)
        print(f'Similarity: {similarity} for {query_embedding} and {embedding}')
        similarities.append((chunk, similarity))
    # sort by similarity in descending order, because higher similarity means more relevant chunks
    similarities.sort(key=lambda x:x[1], reverse=True)
    return similarities[:top_n]


def query():
    query = input('How can I help today? Ask me a question: ') 
    retrieved_knowledge = retrieve(query)
    print(f'Retrieved knowledge: {retrieved_knowledge}')
    for chunk, similarity in retrieved_knowledge:
        print(f'Chunk: {chunk} with similarity {similarity: .2f}')
    
    context = {'\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}
    instruction_prompt = f"""
    You are a helpful chatbot. Only answer the questions based on the given information. 
    Don't make up answers. If you don't know the answer, say "I don't know".
    {context}
    """
    return query, instruction_prompt

def prompt_llama(input_query, instruction_prompt): 
    stream = ollama.chat(model=LANGUAGE_MODEL,  
                messages=[
                {'role': 'system', 'content': instruction_prompt},
                {'role': 'user', 'content': input_query},
  ], 
   stream=True)
    # print the response from the chatbot in real-time
    print('Chatbot response:')
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)

if __name__ == "__main__":
    dataset = read_dataset()
    add_chunks(dataset)
    input_query, instruction_prompt = query()
    prompt_llama(input_query, instruction_prompt)
