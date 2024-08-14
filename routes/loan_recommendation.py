from flask import Blueprint, jsonify, request
from elasticsearch import Elasticsearch
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config import Config

# Blueprint 생성
loan_recommendation_bp = Blueprint('loan_recommendation', __name__)

# Elasticsearch 클라이언트 설정
es = Elasticsearch(Config.ELASTICSEARCH_URL)

# 대출 상품 추천 함수
def get_similar_loans(product_id, num_recommendations=5):
    # Elasticsearch에서 데이터 조회
    query = {
        "query": {
            "match_all": {}
        },
        "size": 1000  # 필요한 만큼 데이터를 가져옵니다.
    }
    result = es.search(index="jeonse_loan", body=query)

    # 결과를 DataFrame으로 변환
    hits = result['hits']['hits']
    data = pd.DataFrame([hit['_source'] for hit in hits])

    # 데이터 전처리
    if data.empty:
        return []  # 데이터가 없으면 빈 리스트 반환

    # '평균 금리' 열의 N/A 값을 (최고 금리 + 최저 금리) / 2로 대체
    data['평균 금리'] = data.apply(
        lambda row: (row['최고 금리'] + row['최저 금리']) / 2 if pd.isna(row['평균 금리']) else row['평균 금리'], axis=1)

    # '전처리 대출 한도' 열의 N/A 값 있는 행을 제외
    data = data.dropna(subset=['전처리 대출 한도'])

    # '대출 만기 경과 건 연체이자율' 열의 '%' 기호를 제거하고 숫자로 변환
    data['전처리 대출 만기 경과 건 연체이자율'] = data['전처리 대출 만기 경과 건 연체이자율'].str.replace('%', '').astype(float)

    # 숫자형으로 변환할 수 없는 값이 있는지 확인하고 처리
    def convert_to_numeric(value):
        try:
            return float(value)
        except ValueError:
            return np.nan

    # '전처리 대출 한도' 열의 값을 숫자로 변환
    data['전처리 대출 한도'] = data['전처리 대출 한도'].apply(convert_to_numeric)

    # '전처리 대출 한도' 열의 N/A 값 있는 행을 제외
    data = data.dropna(subset=['전처리 대출 한도'])

    # 인덱스를 재설정하여 0부터 시작하도록 함
    data = data.reset_index(drop=True)

    # 사용할 수치형 컬럼만 추출
    numeric_features = ['전처리 대출 만기 경과 건 연체이자율', '전처리 대출 한도', '최저 금리', '최고 금리', '평균 금리']

    # 입력된 상품의 인덱스를 찾음
    if product_id not in data['순번'].values:
        return []  # 존재하지 않는 상품 ID일 경우 빈 리스트 반환

    loan_index = data[data['순번'] == product_id].index[0]

    # 선택된 대출 상품
    selected_loan = data.iloc[loan_index][numeric_features].values.reshape(1, -1)

    # 모든 대출 상품의 데이터
    all_loans = data[numeric_features].values

    # 코사인 유사도 계산
    similarity_scores = cosine_similarity(selected_loan, all_loans).flatten()

    # 유사도 점수에 따라 정렬된 인덱스
    similar_loan_indices = similarity_scores.argsort()[::-1][1:num_recommendations + 1]

    recommended_products = data.iloc[similar_loan_indices]

    # NaN 값을 None으로 변환 (JSON 직렬화 가능하도록)
    recommended_products = recommended_products.replace({np.nan: None})

    return recommended_products[['순번', '금융회사 명', '금융 상품명', '평균 금리']].to_dict(orient='records')

# API 엔드포인트
def get_recommendations():
    try:
        # 프론트엔드에서 전송한 JSON 데이터를 받아옴
        request_data = request.get_json()
        product_id = request_data.get('number')

        # 추천된 대출 상품 조회
        recommended_loans = get_similar_loans(product_id)

        return jsonify(recommended_loans)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
