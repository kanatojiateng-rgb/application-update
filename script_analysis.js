if (!chartDataFromServer.labels || chartDataFromServer.labels.length === 0) {
    console.error("表示するデータがありません。");
    // 必要に応じて「データ不足」のメッセージを画面に出す
}

const ctx1 = document.getElementById('expenseLineChart').getContext('2d');
  new Chart(ctx1, {
    type: 'line', // 左側：折れ線
    data: {
       labels: chartDataFromServer.labels,
       datasets: [{
          label: '支出額',
          data: chartDataFromServer.totals,
          borderColor: 'plum'
       }]
    }
  });

  const ctx2 = document.getElementById('investmentChart').getContext('2d');
  new Chart(ctx2, {
      type: 'bar', // 右側：投資シミュレーション
      data: {
        labels: Array.from({length: 20}, (_, i) => `${i+1}年目`),
        datasets: [{
            label: '資産予測',
            data: chartDataFromServer.sim_data,
            backgroundColor: 'pink'
        }]
      } 
  });
