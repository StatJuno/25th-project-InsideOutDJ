import torch
import torch.nn as nn
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import kss
import ast

# KoBERTMultitaskModel 클래스 정의 (이전에 저장한 것과 동일하게 정의해야 함)
class KoBERTMultitaskModel(nn.Module):
    def __init__(self, n_classes, dropout_prob=0.3):
        super(KoBERTMultitaskModel, self).__init__()
        self.bert = BertModel.from_pretrained('monologg/kobert')
        self.drop = nn.Dropout(p=dropout_prob)
        self.out_valence = nn.Linear(self.bert.config.hidden_size, n_classes)
        self.out_arousal = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = self.drop(outputs.pooler_output)
        valence_output = self.out_valence(pooled_output)
        arousal_output = self.out_arousal(pooled_output)
        return valence_output, arousal_output

# KoBERT 모델 및 토크나이저 불러오기
model = torch.load('be/순서형회귀모델_v1.pth')
model = model.to('cuda' if torch.cuda.is_available() else 'cpu')
model.eval()
tokenizer = BertTokenizer.from_pretrained('monologg/kobert')

def split_sentences(paragraph):
    return kss.split_sentences(paragraph)

def predict_emotion(model, tokenizer, sentence, device='cuda' if torch.cuda.is_available() else 'cpu'):
    encoding = tokenizer.encode_plus(
        sentence,
        add_special_tokens=True,
        max_length=64,
        return_token_type_ids=False,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt',
    )

    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)

    with torch.no_grad():
        valence_output, arousal_output = model(input_ids, attention_mask)
        valence_prediction = torch.argmax(valence_output, dim=1).cpu().item()
        arousal_prediction = torch.argmax(arousal_output, dim=1).cpu().item()

    valence_prediction = {0: -1, 1: 0, 2: 1}[valence_prediction]
    arousal_prediction = {0: -1, 1: 0, 2: 1}[arousal_prediction]

    return (valence_prediction, arousal_prediction)

def calculate_paragraph_emotion(paragraph):
    sentences = split_sentences(paragraph)
    total_x, total_y = 0, 0

    print("Input Paragraph:")
    print(paragraph)
    print("\nAnalyzed Sentences and Their Emotions:")

    for sentence in sentences:
        emotion_vector = predict_emotion(model, tokenizer, sentence)
        total_x += emotion_vector[0]
        total_y += emotion_vector[1]

        # 각 문장의 감정 분석 결과 출력
        print(f"Sentence: {sentence}")
        print(f"Valence: {emotion_vector[0]}, Arousal: {emotion_vector[1]}\n")

    normalized_emotion = (total_x / len(sentences), total_y / len(sentences))
    normalized_emotion = (round(normalized_emotion[0], 2), round(normalized_emotion[1], 2))
    return normalized_emotion

def get_quadrant(x, y):
    if x >= 0 and y >= 0:
        return 1
    elif x < 0 and y > 0:
        return 2
    elif x < 0 and y <= 0:
        return 3
    else:
        return 4

def calculate_distance(x, y):
    return np.sqrt(x**2 + y**2)

# ~10% : 0.1858614651388976
# ~40% : 0.40769894062031914
# ~70% : 0.6352747241405549

def filter_by_intensity(df, distance):
    if distance <= 0.185:
        intensity_label = 'neutral'
    elif 0.185 < distance <= 0.4:
        intensity_label = 'low'
    elif 0.4 < distance <= 0.63:
        intensity_label = 'medium'
    else:
        intensity_label = 'high'

    # neutral의 경우 사분면과 상관없이 모든 neutral 노래를 반환
    if intensity_label == 'neutral':
        return df[df['intensity'] == intensity_label]
    else:
        return df[df['intensity'] == intensity_label]


def get_songs_by_emotion_and_intensity(df, normalized_emotion):
    distance = calculate_distance(*normalized_emotion)
    filtered_df = filter_by_intensity(df, distance)
    
    # neutral이 아닌 경우 감정 사분면으로 필터링
    if distance > 0.185:
        quadrant = get_quadrant(*normalized_emotion)
        filtered_df = filtered_df[filtered_df['emotion'] == quadrant]
    
    return filtered_df


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

# quadrant와 intensity에 따라 적절한 코멘트를 제공하는 함수
def get_comment_by_emotion_and_intensity(quadrant, intensity):
    comments = {
        "neutral": "평범한 하루를 보내셨군요.",
        (1, "high"): "많이 행복한 하루를 보내셨군요!",
        (1, "medium"): "행복한 기분이 느껴지네요.",
        (1, "low"): "조금 행복한 하루를 보내셨군요.",
        (2, "high"): "약간 복잡한 감정을 느끼고 계시군요.",
        (2, "medium"): "조금 혼란스러운 하루였을지도 몰라요.",
        (2, "low"): "살짝 우울한 기분을 느끼셨군요.",
        (3, "high"): "힘든 하루를 보내셨군요. 힘내세요!",
        (3, "medium"): "많이 지치고 힘든 하루였군요.",
        (3, "low"): "조금 힘든 하루였을 것 같아요.",
        (4, "high"): "기분이 많이 복잡하셨나 봐요.",
        (4, "medium"): "조금 복잡한 기분이 느껴지네요.",
        (4, "low"): "조금 혼란스러운 하루였을지도 몰라요.",
    }

    if intensity == 'neutral':
        return comments['neutral']
    else:
        return comments.get((quadrant, intensity), "기분이 복잡하셨던 것 같아요.")

def recommend_songs(paragraph, df_path='be/tracks_final.csv'):
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

    input_keywords = extract_keywords(paragraph, kw_model)
    input_embedding = embed_keywords(input_keywords, sbert_model)

    matching_songs['keyword_embedding'] = matching_songs['keyword_embedding'].apply(ast.literal_eval)
    matching_songs['similarity'] = matching_songs['keyword_embedding'].apply(lambda x: calculate_similarity(input_embedding, x))
    
    # 추천된 상위 5개의 노래를 추출
    top_5_songs = matching_songs.sort_values(by='similarity', ascending=False).head(5)
    top_5_songs_data = top_5_songs[['track_name', 'artist_name', 'uri']].to_dict(orient='records')
    
    # 감정 분석 결과와 추천된 노래 목록을 함께 반환
    quadrant = get_quadrant(float(normalized_emotion[0]), float(normalized_emotion[1]))
    distance = calculate_distance(float(normalized_emotion[0]), float(normalized_emotion[1]))
    intensity = filter_by_intensity(df, distance)['intensity'].iloc[0]

    comment = get_comment_by_emotion_and_intensity(quadrant, intensity)
    
    return {
        "emotion_analysis": emotion_analysis_result,
        #"comment": comment,
        "recommended_songs": top_5_songs_data
    }


# # 예시 문단 입력
# paragraph = """
# 오늘 날씨가 너무 좋네요. 기분이 좋지 않아요. 이 영화는 정말 재미있었어요.
# """

# # 노래 추천 실행
# recommendation_result = recommend_songs(paragraph)

# # 결과 출력
# print("Emotion Analysis Result:")
# print(recommendation_result["emotion_analysis"])

# print("\nComment:")
# print(recommendation_result["comment"])

# print("\nRecommended Songs:")
# for song in recommendation_result["recommended_songs"]:
#     print(f"Track: {song['track_name']}, Artist: {song['artist_name']}, URI: {song['uri']}")
