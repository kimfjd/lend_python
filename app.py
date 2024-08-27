from flask import Flask
from flask_cors import CORS
from routes.loan_recommendation import get_recommendations
from routes.recommend import recommendations
from routes.loan_similarity import get_loan_similarity
from routes.peoplefinloan import recommend_loans
from routes.directory import recommend_loan_products
from routes.jeonse import jeonse_loan
from routes.mortgage import mortgage_loan
from routes.people_finloan_recommendation import people_finloan_recommendation
from routes.rate_forecast import rate_forecast_endpoint
from routes.agesuggestion import agesuggestion_endpoint

app = Flask(__name__)
CORS(app, origins=['http://192.168.10.6:3000'])

# API 엔드포인트 등록
app.add_url_rule('/api/loan_recommendations', 'get_recommendations', get_recommendations, methods=['POST'])
app.add_url_rule('/api/recommendations', 'recommendations', recommendations, methods=['POST'])
app.add_url_rule('/api/loan_similarity', 'get_loan_similarity', get_loan_similarity, methods=['POST'])
app.add_url_rule('/api/recommend_loans', 'recommend_loans', recommend_loans, methods=['POST'])
app.add_url_rule('/api/recommend_loan_products', 'recommend_loan_products', recommend_loan_products, methods=['POST'])
app.add_url_rule('/api/jeonse_loan', 'jeonse_loan', jeonse_loan, methods=['POST'])
app.add_url_rule('/api/mortgage_loan', 'mortgage_loan', mortgage_loan, methods=['POST'])
app.add_url_rule('/api/people_finloan_recommendation', 'people_finloan_recommendation', people_finloan_recommendation, methods=['POST'])
app.add_url_rule('/api/rate_forecast_endpoint', 'rate_forecast_endpoint', rate_forecast_endpoint, methods=['POST'])
app.add_url_rule('/api/agesuggestion_endpoint', 'agesuggestion_endpoint', agesuggestion_endpoint, methods=['POST'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
