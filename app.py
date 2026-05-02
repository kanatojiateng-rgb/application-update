from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import json


# --- データベース設定 ---
app = Flask(__name__)
# データベースファイルを 'spending_data.db' に設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.root_path + '/spending_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- データベースのモデル（テーブル構造）の定義 ---
class MonthlyExpense(db.Model):
    # テーブル名は 'monthly_expenses'
    __tablename__ = 'monthly_expenses'
    # '202401'のような整数、または Date型にして、年月を特定できるようにする
    year_month = db.Column(db.Integer, primary_key=True)
    food = db.Column(db.Integer, nullable=False)
    transport = db.Column(db.Integer, nullable=False)
    hobby = db.Column(db.Integer, nullable=False)
    other = db.Column(db.Integer, nullable=False)

# データを辞書型に変換するメソッド（JSON化してフロントに返すため）
    def to_dict(self):
        return {
            'month': self.year_month,
            'food': self.food,
            'transport': self.transport,
            'hobby': self.hobby,
            'other': self.other,
    }


#1. トップページ/入力フォーム
@app.route('/')
def index():
    # 起動時にデータベースを初期化（テーブルがなければ作成）
    with app.app_context():
        db.create_all()
    return render_template('index.html')

@app.route('/api/save_expense', methods=['POST'])
def save_expense():
    # フロントエンドから送られたJSONデータを受け取る
    data = request.json
    date_str = data.get('date') # '2024-04'
    if not date_str:
       return jsonify({"success": False, "message": "MIssing data"}), 400
    
    try:
        ym_key = int(date_str.replace('-', ''))
        expense = db.session.get(MonthlyExpense, ym_key)


        if expense is None:
            #新規作成
            expense = MonthlyExpense(
                year_month=ym_key,
                food=data['food'],
                transport=data['transport'],
                hobby=data['hobby'],
                other=data['other']
            )
            db.session.add(expense)
        else:
            # 更新
            expense.food = data['food']
            expense.transport = data['transport']
            expense.hobby = data['hobby']
            expense.other = data['other']
        
        db.session.commit()

        # --- ここから「10年制限（120件）」ロジック ---
        #1. 現在の全件数を取得
        total_count = MonthlyExpense.query.count()

        #2. 120件を超えていた場合
        if total_count > 120:
            #削除すべき件数を計算
            delete_count = total_count - 120

         # 最も古いデータを「年月（year_month)」順で取得して削除
            old_records = MonthlyExpense.query.order_by(MonthlyExpense.year_month.asc()).limit(delete_count).all()  
            for record in old_records:
                db.session.delete(record)
            db.session.commit()
            print(f"{delete_count}件の古いデータを削除しました（10年制限)")

        # 保存されたデータ件数を取得
        return jsonify({"success": True, "total_count": total_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    
   
    #ページロード時に現在のデータ件数を取得するためのAPI
@app.route('/api/get_data_count', methods=['GET'])
def get_data_count():
    try:
            total_count = db.session.query(MonthlyExpense).count()
            return jsonify({"success": True, "total_count": total_count}), 200
    except Exception as e:
            print(f"Error: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    #2. シミュレーション処理と結果表示のページ
@app.route('/simulation_result', methods=['POST'])
def simulation_result():
    #--- データの取得とシミュレーションの実行 ---
    # 例: フォームから初期投資額、積立額、年数、リターン率などを取得

    try:
        initial_investment = float(request.form.get('initial_amount', 100000))
        monthly_contribution = float(request.form.get('monthly_amount', 10000))
        years = int(request.form.get('years', 20))
        annual_return_rate = float(request.form.get('return_rate', 0.05))

    except ValueError:
        return redirect(url_for('index')) # エラー処理
    
    #投資シミュレーションの計算 (月次積立・単利)
    months = years * 12
    data = []
    current_value = initial_investment

    for m in range(1, months + 1):
        # 投資額の増加
        current_value += monthly_contribution
        # 運用益の計算（簡略化された単利計算）
        current_value *= (1 + annual_return_rate)

        data.append({
            'month' : m,
            'total_value': round(current_value, 2),
             'principal': initial_investment + (m * monthly_contribution)
        })

    # ここでは chart_labels, chart_data が未定義のため、仮の空リストを設定 (実行時のエラー回避のため)
    chart_labels = [str(m) for m in range(1, months + 1)]
    chart_data = [d['total_value'] for d in data]
    
    # --- 結果のHTMLレンダリング ---
    return render_template(
    'analysis.html',
    total_value=f"{current_value:,.2f}", #最終結果
    chart_labels=json.dumps(chart_labels),
    chart_data=json.dumps(chart_data)
    )
    
@app.route('/analysis')
def analysis():
    try:
        # 期間を取得。最大10年に制限。
        duration_years = int(request.args.get('duration_years', 1))
        if duration_years > 10:
            duration_years = 10 #10年(120か月)に制限


        limit_months = duration_years * 12

        # データベースから取得する件数を最大120件に絞る
        all_expenses = MonthlyExpense.query.order_by(MonthlyExpense.year_month.desc()).limit(limit_months).all()
        all_expenses.reverse()
        #データが全くない場合の処理
        if not all_expenses:
            return "データが登録されていません。 トップページから１か月以上のデータを入力するか、CSVを読み込んでください。"
        
        labels = [f"{e.month}月" for e in all_expenses]
        totals = [e.food + e.transport + e.hobby + e.other for e in all_expenses]
        
        #2. 平均支出の算出（入力されている全データから算出）    
        avg_expense = sum(totals) / len(totals)
        avg_expense_display = f"{round(avg_expense):,}円"

        #　--- シミュレーション計算部分 ---
        sim_data = []
        current_asset = 0
        monthly_investment = avg_expense # 平均支出をそのまま積立額と仮定

        monthly_investment = 50000

        # 3. 選択された年数(duration_years)に合わせてループ回数を変える
        # 20年なら240ヵ月分のデータを生成する
        total_months = duration_years * 12

        for m in range(1, total_months + 1):
            #月次複利計算（年利５％を想定）
            current_asset = (current_asset + monthly_investment) * (1 + 0.05 / 12)

            # グラフが細かくなりすぎないよう、１年（１２か月）ごとのデータのみ保存
            if m % 12 == 0:
                sim_data.append(round(current_asset))

        # 4. グラフ用ラベルの作成（１年目、２年目...)
        sim_labels = [f"{y}年目" for y in range(1, duration_years + 1)]
        monthly_ratio = 0
        if len(totals) >= 2:
           current_month_total = totals[-1]
           last_month_total = totals[-2]
           if last_month_total > 0:
              monthly_ratio = round(((current_month_total / last_month_total) - 1) * 100, 1)
        
        total_expense_all = sum(totals)
        total_hobby = sum([e.hobby for e in all_expenses])

        hobby_ratio = (total_hobby / total_expense_all) * 100 if total_expense_all > 0 else 0

        max_total = max(totals)
        max_month_idx = totals.index(max_total)
        max_month_name = labels[max_month_idx]

        if hobby_ratio > 30:
            advice = f"【AI分析】支出の {round(hobby_ratio)}% が趣味に充てられてます。少し見直すだけで、20年後の資産はさらに伸びます！"
        
        elif monthly_ratio <= -5:
            advice = f"【AI分析】先月より支出を {abs(monthly_ratio)}% カットできましたね！この節約分を投資に回せている今の状態は理想的です。"
        elif monthly_ratio > 10:
            advice = f"【AI分析】先月より支出が {monthly_ratio}% 増えています。特に支出の多かった {max_month_name} の使い方を振り返ってみましょう。"
        else:
            advice = "【AI分析】非常に安定した家計管理です。この調子で淡々と積立投資を継続しましょう。 " 
        
    
        return render_template('analysis.html',
                               labels=json.dumps(labels),
                               totals=json.dumps(totals),
                               sim_data=json.dumps(sim_data),
                               sim_labels=json.dumps(sim_labels),
                               duration_years=duration_years,
                               avg_expense_display=avg_expense_display,
                               advice=advice)
                               

    
    except Exception as e:
 
       return f"エラーが発生しました: {e}"

from flask import send_file
import io

@app.route('/api/download_report')
def download_report():
    # 過去10年分(120件)のデータを取得
    expenses = MonthlyExpense.query.order_by(MonthlyExpense.year_month.asc()).limit(120).all()

    # Pandasでデータフレーム化
    df = pd.DataFrame([e.to_dict() for e in expenses])
    df.columns = ['年月','食費','交通費','趣味','その他']

    # メモリ上でExcelファイルを作成
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='分析レポート')
    output.seek(0)

    return send_file(output, download_name="kakei_report.xlsx", as_attachment=True)

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True) # debug=Trueにする
