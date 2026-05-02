// 1. グローバル変数の定義
let monthlyDataCount = 0; 
let REQUIRED_MONTHS = 120; 

// 2. 変換関数
function parseToNumber(value) {
    let str = String(value || "");
    str = str.replace(/[０-９]/g, s => String.fromCharCode(s.charCodeAt(0) - 65248)); 
    const numStr = str.replace(/[^0-9]/g, "");
    return Number(numStr) || 0; 
}

// 3. 件数チェックとUI更新関数（独立させて定義）
async function checkAndEnableAnalysis() { 
    try {
        const response = await fetch('/api/get_data_count'); 
        const data = await response.json();

        monthlyDataCount = data.total_count;
        console.log("現在のデータ件数:", monthlyDataCount);

        // HTMLのID「analysis-link-btn」に合わせて取得
        const analysisBtn = document.getElementById('analysis-link-btn');
        const warningMsg = document.getElementById('warningMessage');

        if (analysisBtn) {
            if (monthlyDataCount >= REQUIRED_MONTHS) {
                analysisBtn.classList.remove('disabled-analysis');
                analysisBtn.classList.add('enabled-analysis');
                analysisBtn.style.pointerEvents = 'auto';
                analysisBtn.style.cursor = 'pointer';
                analysisBtn.style.opacity = '1';
                analysisBtn.style.cursor = 'pointer';
            } else {
                analysisBtn.classList.add('disabled-analysis');
                analysisBtn.classList.remove('enabled-analysis');
                analysisBtn.style.pointerEvents = 'none';
                analysisBtn.style.opacity = '0.5';
                analysisBtn.style.cursor = 'not-allowed';
            }
        }
    } catch (e) {
        console.error("件数チェックに失敗しました", e);
    }
}

// 4. データ更新・保存関数
async function updateDataAndChart() {
    const food = parseToNumber(document.getElementById("food").value);
    const transport = parseToNumber(document.getElementById("transport").value);
    const hobby = parseToNumber(document.getElementById("hobby").value);  
    const other = parseToNumber(document.getElementById("other").value);

    const dataValue =document.getElementById("monthSelector").value;

    if (!dataValue) {
        alert("年月を選択してください。");
        return;
    }

    const total = food + transport + hobby + other;
    document.getElementById("total").textContent = total.toLocaleString();

    if (total === 0) {
        alert("数値を入力してください。");
        return;
    }

    const expenseData = {
        date: dataValue,
        food: food,
        transport: transport,
        hobby: hobby,
        other: other
    };

    try {
        // Python側のURL「/api/save_expense」に合わせて修正
        const response = await fetch('/api/save_expense', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(expenseData)
        });
        
        if (response.ok) {
            console.log("保存成功");
            // 保存直後に件数を再確認してボタンを更新
            checkAndEnableAnalysis();
        }
    } catch (e) {
        console.error("保存失敗", e);
    }
}

// 5. 初期化処理
window.onload = function() {
const downloadBtn = document.getElementById('downloadBtn');
    const dummyBtn = document.getElementById('dummyDataBtn');
    if (dummyBtn) {
        dummyBtn.addEventListener('click', generateDummyData);
    }

// 分析ボタンのクリック処理
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            // サーバー側でExcel生成APIが準備されていれば実行
            window.location.href = '/api/download-report';
        });
    }

        const periodSelector = document.getElementById('periodSelector');
        if(periodSelector) {
           periodSelector.addEventListener('change', function() {
        const selectedYear = this.value;
        console.log("分析期間が変更されました:", selectedYear, "年分");
        
        // 10年分(120ヶ月)が必要なら定数を更新する
        REQUIRED_MONTHS = selectedYear * 12;
        
        // 画面の表示（あと何ヶ月必要かなど）を即座に更新する
        checkAndEnableAnalysis(); 
        
        });
    
    // イベント登録
    const calculateBtn = document.getElementById('calculateBtn');
    if (calculateBtn) {
        calculateBtn.addEventListener('click', updateDataAndChart);
    }

    const analysisBtn = document.getElementById('analysis-link-btn');
    if (analysisBtn) {
        analysisBtn.addEventListener('click', function(e) {
            e.preventDefault();

    const years = document.getElementById('periodSelector').value;

    if (monthlyDataCount < REQUIRED_MONTHS) {
        // ボタンは押せるけど、足りない時だけ警告を出す
        alert(`あと ${REQUIRED_MONTHS - monthlyDataCount} ヵ月分のデータが必要です。`);
    } else {
        window.location.href = "/analysis?duration_years=" + years;
            }
        });
    }

    // 最初に一度だけサーバーから現在の件数を取得
    checkAndEnableAnalysis();

    document.getElementById('downloadBtn').addEventListener('click', function() {
     // Flaskのダウンロード用URLへリダイレクト（ブラウザがファイルを自動検知します）
     window.location.href = '/api/download-report';    
    });
};
// テスト用の10年分ダミーデータ一括保存関数
async function generateDummyData() {
    const startYear = 2014; // 10年前から開始
    const results = [];

    // 120か月分のデータを生成
    for (let i = 0; i < 120;  i++) {
        const date = new Date(startYear, i, 1);
        const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    
        const expenseData = {
            date: dateStr,
            food: Math.floor(Math.random() * 50000) + 20000,
            transport: Math.floor(Math.random() * 15000) + 5000,
            hobby: Math.floor(Math.random() * 20000) + 5000,
            other: Math.floor(Math.random() * 10000) + 2000
        };
        
        // サーバーへ送信（順次送信）
        results.push(fetch('/api/save_expense', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(expenseData)
        }));
    }
    
    try {
        await Promise.all(results);
        alert("10年分のダミーデータを生成しました!");
        checkAndEnableAnalysis();
    } catch (e) {
        console.error("生成失敗", e);
    }
}
}
