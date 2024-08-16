import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import kss
import ast

# 모델 로드 및 초기화
tokenizer = BertTokenizer.from_pretrained('monologg/kobert')
model = BertForSequenceClassification.from_pretrained('monologg/kobert', num_labels=5)
loaded_data = torch.load('./kobert_emotion_model.pth', map_location=torch.device('cpu'))
model.load_state_dict(loaded_data, strict=False)

device = torch.device('cpu')
model.to(device)
model.eval()

label_to_emotion_vector = {
    0: (1, 1),
    1: (1, -1),
    2: (-1, -1),
    3: (-1, 1),
    4: (0, 0)
}

def split_sentences(paragraph):
    return kss.split_sentences(paragraph)

def predict_emotion(model, tokenizer, sentence):
    inputs = tokenizer.encode_plus(
        sentence,
        add_special_tokens=True,
        max_length=64,
        return_token_type_ids=False,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt',
    )
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    predicted_class = torch.argmax(logits, dim=1).cpu().numpy()[0]
    emotion_vector = label_to_emotion_vector[predicted_class]

    return emotion_vector

def calculate_paragraph_emotion(paragraph):
    sentences = split_sentences(paragraph)
    total_x, total_y = 0, 0

    for sentence in sentences:
        emotion_vector = predict_emotion(model, tokenizer, sentence)
        total_x += emotion_vector[0]
        total_y += emotion_vector[1]

    normalized_emotion = (total_x / len(sentences), total_y / len(sentences))
    return normalized_emotion

def get_quadrant(x, y):
    if x >= 0 and y >= 0:
        return 1
    elif x < 0 and y >= 0:
        return 2
    elif x <= 0 and y < 0:
        return 3
    else:
        return 4

def calculate_distance(x, y):
    return np.sqrt(x**2 + y**2)

def filter_by_intensity(df, distance):
    if distance <= 0.1:
        intensity_label = 'neutral'
    elif 0.1 < distance <= 0.4:
        intensity_label = 'low'
    elif 0.4 < distance <= 0.7:
        intensity_label = 'medium'
    else:
        intensity_label = 'high'

    return df[df['intensity'] == intensity_label]

def get_songs_by_emotion_and_intensity(df, normalized_emotion):
    quadrant = get_quadrant(*normalized_emotion)
    filtered_df = df[df['emotion'] == quadrant]
    distance = calculate_distance(*normalized_emotion)
    final_songs = filter_by_intensity(filtered_df, distance)
    return final_songs

def extract_keywords(text, kw_model):
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)
    return [kw[0] for kw in keywords]

def embed_keywords(keywords, sbert_model):
    embeddings = sbert_model.encode(keywords)
    return embeddings

def calculate_similarity(input_embedding, song_embedding):
    # 입력 임베딩을 평균으로 줄여서 차원을 맞춤
    input_embedding = np.mean(np.array(input_embedding), axis=0).reshape(1, -1)
    song_embedding = np.array(song_embedding).reshape(1, -1)

    # 차원이 다르면 예외를 발생시키지 않고 맞추기 위해 필요한 처리를 적용
    if input_embedding.shape[1] != song_embedding.shape[1]:
        min_dim = min(input_embedding.shape[1], song_embedding.shape[1])
        input_embedding = input_embedding[:, :min_dim]
        song_embedding = song_embedding[:, :min_dim]

    return cosine_similarity(input_embedding, song_embedding)[0][0]
def recommend_songs(paragraph, df_path='./tracks_final.csv'):
    # 감정 분석을 수행하고, 그 결과를 반환할 데이터에 포함시킴
    normalized_emotion = calculate_paragraph_emotion(paragraph)
    
    # 감정 분석 결과를 사전 형태로 준비
    emotion_analysis_result = {
        "normalized_emotion": {
            "x": normalized_emotion[0],
            "y": normalized_emotion[1]
        }
    }
    
    # 추천된 노래 목록을 계산
    df = pd.read_csv(df_path)
    matching_songs = get_songs_by_emotion_and_intensity(df, normalized_emotion)
    
    # 키워드 임베딩 및 유사도 계산
    kw_model = KeyBERT()
    sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    input_keywords = kw_model.extract_keywords(paragraph, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)
    input_embedding = sbert_model.encode([kw[0] for kw in input_keywords])

    matching_songs['keyword_embedding'] = matching_songs['keyword_embedding'].apply(ast.literal_eval)
    matching_songs['similarity'] = matching_songs['keyword_embedding'].apply(lambda x: calculate_similarity(input_embedding, x))
    
    # 추천된 상위 5개의 노래를 추출
    top_5_songs = matching_songs.sort_values(by='similarity', ascending=False).head(5)
    top_5_songs_data = top_5_songs[['track_name', 'artist_name', 'uri']].to_dict(orient='records')
    
    # 감정 분석 결과와 추천된 노래 목록을 함께 반환
    return {
        "emotion_analysis": emotion_analysis_result,
        "recommended_songs": top_5_songs_data
    }
# def recommend_songs(paragraph, df_path='./tracks_final.csv'):
#     normalized_emotion = calculate_paragraph_emotion(paragraph)
#     df = pd.read_csv(df_path)
#     matching_songs = get_songs_by_emotion_and_intensity(df, normalized_emotion)

#     kw_model = KeyBERT()
#     sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

#     input_keywords = extract_keywords(paragraph, kw_model)
#     input_embedding = embed_keywords(input_keywords, sbert_model)

#     matching_songs['keyword_embedding'] = matching_songs['keyword_embedding'].apply(ast.literal_eval)
#     matching_songs['similarity'] = matching_songs['keyword_embedding'].apply(lambda x: calculate_similarity(input_embedding, x))

#     top_5_songs = matching_songs.sort_values(by='similarity', ascending=False).head(5)
#     return top_5_songs[['track_name', 'artist_name', 'uri']].to_dict(orient='records')