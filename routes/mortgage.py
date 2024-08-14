import re
import numpy as np
from flask import request, jsonify
from elasticsearch import Elasticsearch

# Elasticsearch 설정
es = Elasticsearch("http://localhost:9200")

# 담보 종류 맵핑 (0: 아파트, 1: 아파트 이외)
collateral_type_mapping = {
    '아파트': 0,
    '오피스텔': 1,
    '다세대주택': 1,
    '빌라': 1,
    '기타': 1,
    # 필요시 추가
}

# 전처리 대출한도 값을 비율로 변환하는 함수
def parse_ltv(value):
    match = re.search(r'(\d+)', value)
    if match:
        return float(match.group(1)) / 100
    return np.nan

# 사용자 조건에 맞는 대출 상품 추천 함수
def recommend_loans(data, property_value, loan_amount, collateral_type, num_recommendations=5):
    # 담보 종류를 숫자로 변환
    collateral_type_numeric = collateral_type_mapping.get(collateral_type)

    if collateral_type_numeric is None:
        return []

    # 주택 매매가 대비 대출 비율 계산
    loan_to_value_ratio = loan_amount / property_value

    # 전처리 대출한도를 비율로 변환
    for item in data:
        item['전처리 대출한도'] = parse_ltv(str(item['전처리 대출한도']))

    # 사용자 입력 조건에 맞는 데이터 필터링
    filtered_data = [
        item for item in data
        if item['전처리 대출한도'] >= loan_to_value_ratio and
           item['전처리 담보종류명'] == collateral_type_numeric and
           loan_amount >= item.get('최소 대출금액', 0) and
           loan_amount <= item.get('최대 대출금액', float('inf'))
    ]

    if not filtered_data:
        return []

    # 평균 금리가 낮은 순으로 정렬하여 상위 num_recommendations 개 추천
    sorted_data = sorted(filtered_data, key=lambda x: x['평균 금리'])[:num_recommendations]

    return sorted_data

# Flask에서 사용하는 함수
def mortgage_loan():
    try:
        # 사용자로부터 입력받은 값
        request_data = request.get_json()
        property_value = float(request_data.get("property_value"))
        loan_amount = float(request_data.get("loan_amount"))
        collateral_type = request_data.get("collateral_type")

        # Elasticsearch에서 데이터 가져오기
        query = {
            "query": {
                "match_all": {}
            },
            "size": 10000  # 필요한 경우 조정
        }
        res = es.search(index="mortgage_loan", body=query)
        data = [hit['_source'] for hit in res['hits']['hits']]

        # 대출 상품 추천
        recommended_loans = recommend_loans(data, property_value, loan_amount, collateral_type)

        if not recommended_loans:
            return jsonify({"message": "조건에 맞는 대출 상품이 없습니다."}), 404

        return jsonify(recommended_loans), 200

    except ValueError as e:
        return jsonify({"error": "입력 값이 유효하지 않습니다.", "details": str(e)}), 400
