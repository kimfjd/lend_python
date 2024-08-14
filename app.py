from flask import Flask
from flask_cors import CORS
from routes.loan_recommendation import get_recommendations
from routes.recommend import recommendations
from routes.loan_similarity import get_loan_similarity
from routes.peoplefinloan import recommend_loans
from routes.directory import recommend_loan_products


app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

# API 엔드포인트 등록
app.add_url_rule('/api/loan_recommendations', 'get_recommendations', get_recommendations, methods=['POST'])
app.add_url_rule('/api/recommendations', 'recommendations', recommendations, methods=['POST'])
app.add_url_rule('/api/loan_similarity', 'get_loan_similarity', get_loan_similarity, methods=['POST'])
app.add_url_rule('/api/recommend_loans', 'recommend_loans', recommend_loans, methods=['POST'])
app.add_url_rule('/api/recommend_loan_products', 'recommend_loan_products', recommend_loan_products, methods=['POST'])



if __name__ == '__main__':
    app.run(debug=True)
