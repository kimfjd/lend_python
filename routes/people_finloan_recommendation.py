import re
from flask import request, jsonify
from elasticsearch import Elasticsearch

# Elasticsearch 설정
es = Elasticsearch("http://localhost:9200")

def 추천_대출_상품(data, 사용자_대상, 사용자_지역, 사용자_연령, 사용자_소득, 사용자_신용점수):
    # 1. 대상 필터링
    대상_필터 = [
        item for item in data
        if '없음' in str(item['대상']) or 사용자_대상 in str(item['대상'])
    ]

    # 2. 지역 필터링
    지역_필터 = [
        item for item in 대상_필터
        if item['지역'] == '전국' or 사용자_지역 in str(item['지역'])
    ]

    # 3. 연령 필터링
    연령_필터 = [
        item for item in 지역_필터
        if item['전처리 된 연령 시작'] <= 사용자_연령 <= item['전처리 된 연령 끝']
    ]

    # 4. 소득 필터링
    소득_필터 = [
        item for item in 연령_필터
        if item['전처리 소득 시작 조건'] <= 사용자_소득 <= item['전처리 소득 끝 조건']
    ]

    # 5. 신용점수 필터링
    신용점수_필터 = [
        item for item in 소득_필터
        if item['전처리 신용점수 시작'] <= 사용자_신용점수 <= item['전처리 신용점수 이하']
    ]

    # 모든 필터링을 거친 최종 추천 대출 상품 리스트
    추천_대출_데이터 = 신용점수_필터

    # 결과를 금리에 따라 정렬하고 상위 5개만 선택
    추천_대출_데이터 = sorted(추천_대출_데이터, key=lambda x: x.get('전처리 이자율', float('inf')))[:5]

    return 추천_대출_데이터

# Flask에서 사용하는 함수
def people_finloan_recommendation():
    try:
        # 사용자로부터 입력받은 값
        request_data = request.get_json()
        사용자_대상 = request_data.get("사용자_대상")
        사용자_지역 = request_data.get("사용자_지역")
        사용자_연령 = int(request_data.get("사용자_연령"))
        사용자_소득 = int(request_data.get("사용자_소득"))
        사용자_신용점수 = int(request_data.get("사용자_신용점수"))

        # Elasticsearch에서 데이터 가져오기
        query = {
            "query": {
                "match_all": {}
            },
            "size": 10000  # 필요한 경우 조정
        }
        res = es.search(index="peoplefinloan", body=query)
        data = [hit['_source'] for hit in res['hits']['hits']]

        # 대출 상품 추천
        추천_대출 = 추천_대출_상품(data, 사용자_대상, 사용자_지역, 사용자_연령, 사용자_소득, 사용자_신용점수)

        if 추천_대출:
            return jsonify(추천_대출), 200
        else:
            return jsonify({"message": "조건에 맞는 대출 상품이 없습니다."}), 404

    except ValueError as e:
        return jsonify({"error": "입력 값이 유효하지 않습니다.", "details": str(e)}), 400
