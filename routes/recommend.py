from flask import Blueprint, jsonify, request
from elasticsearch import Elasticsearch
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
from config import Config

# Blueprint 생성
loan_recommendation_bp = Blueprint('loan_recommendation', __name__)

# Elasticsearch 클라이언트 설정
es = Elasticsearch(Config.ELASTICSEARCH_URL)

# KMeans 클러스터링 모델 설정
kmeans = KMeans(n_clusters=Config.KMEANS_N_CLUSTERS,
                n_init=Config.KMEANS_N_INIT,
                random_state=Config.KMEANS_RANDOM_STATE)


# 추천 대출 상품을 위한 함수
def recommend_loans(product_id, num_recommendations=5):
    try:
        # Elasticsearch에서 데이터 조회
        query = {
            "query": {
                "match_all": {}
            },
            "size": 1000  # 필요한 만큼 데이터를 가져옵니다.
        }
        result = es.search(index="credit_loan", body=query)

        # 결과를 DataFrame으로 변환
        hits = result['hits']['hits']
        if not hits:
            return []  # Elasticsearch에서 반환된 데이터가 없을 경우 빈 리스트 반환

        data = pd.DataFrame([hit['_source'] for hit in hits])

        # 데이터 전처리 및 클러스터링
        features = data[['900점 초과', '801~900점', '701~800점', '601~700점', '501~600점',
                         '401~500점', '301~400점', '300점 이하', '평균 금리']]

        # 결측값 처리
        features = features.fillna(features.mean())

        # 데이터 표준화
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        # KMeans 클러스터링 수행
        data['cluster'] = kmeans.fit_predict(scaled_features)

        # 입력된 상품의 클러스터를 찾음
        if product_id not in data['순번'].values:
            return []  # 존재하지 않는 상품 ID일 경우 빈 리스트 반환

        product_cluster = data.loc[data['순번'] == product_id, 'cluster'].values[0]

        # 같은 클러스터에 속한 다른 상품들 추천
        recommended_products = data[data['cluster'] == product_cluster].copy()
        recommended_products = recommended_products[recommended_products['순번'] != product_id]

        # NaN 값을 None으로 변환 (JSON 직렬화 가능하도록)
        recommended_products = recommended_products.replace({np.nan: None})

        return recommended_products.head(num_recommendations).to_dict(orient='records')
    except Exception as e:
        # 예외 처리 및 로깅
        print(f"An error occurred in recommend_loans: {e}")
        return []


# API 엔드포인트
@loan_recommendation_bp.route('/api/loan_recommendations', methods=['POST'])
def recommendations():
    try:
        # 프론트엔드에서 전송한 JSON 데이터를 받아옴
        request_data = request.get_json()
        if not request_data or 'number' not in request_data:
            return jsonify({"error": "Invalid input, 'number' is required"}), 400

        product_id = request_data.get('number')

        # 추천된 대출 상품 조회
        recommended_loans = recommend_loans(product_id)

        return jsonify(recommended_loans)
    except Exception as e:
        # 예외 처리 및 로깅
        print(f"An error occurred in recommendations endpoint: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
