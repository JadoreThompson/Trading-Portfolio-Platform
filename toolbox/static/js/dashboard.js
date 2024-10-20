document.addEventListener('DOMContentLoaded', function(){
    let openObject = {};
    openPositions.forEach(position => { openObject[position.order_id] = position.unrealised_pnl; });

    const email = document.getElementById('email').textContent;
    const alertBox = document.getElementById('custom-alert');
    const balanceElement = document.getElementById('balance');

    const create_order_form = document.getElementById('create_order_form');
    const all_positions_table = document.getElementById('all_positions_table');
    const open_positions_table = document.getElementById('open_positions_table');
    const summary_table = document.getElementById('summary_table');


    // ----------------------------------------------
    // Socket
    // ----------------------------------------------
    const order_socket = new WebSocket('ws://' + window.location.host + `/ws/${email}/orders`);

    order_socket.onmessage = async function(e){
        const wsMsg = JSON.parse(e.data);
        if (wsMsg?.type === 'order_confirmation') {
            document.querySelector('.order-msg').textContent = wsMsg.message;
            await showAlert('Order Created');
        }

        // Adding the new placed order to the open positions table
        else if (wsMsg?.topic === 'order_created') {
            const tbody = open_positions_table.querySelector('tbody');
            const tr = document.createElement('tr');
            const cols = ['ticker', 'open_price', 'unrealised_pnl'];

            cols.forEach(col => {
                const td = document.createElement('td');

                if (col === 'ticker') {
                    td.textContent = wsMsg[col];
                    const span = document.createElement('span')
                    span.textContent = wsMsg.order_id;
                    span.style.display = 'none';
                    td.appendChild(span);
                }
                else if (col === 'unrealised_pnl') {
                    td.classList.add('upl');
                    td.textContent = wsMsg[col] ? wsMsg[col].toFixed(2) : 0.00;
                } else {
                    td.textContent = wsMsg[col];
                }
                tr.appendChild(td);
            });

            // Adding the close button
            let close = document.createElement('td');
            let i = document.createElement('i');
            i.classList.add('fa-solid', 'fa-xmark', 'close-open-order');
            close.appendChild(i);
            tr.appendChild(close);

            tbody.appendChild(tr);
            balanceElement.textContent = `$${parseFloat(wsMsg.balance).toFixed(2)}`;
            await showAlert('Order Created', 'good');
        }

        // Shifting the closed position from open positions table to all positions table
        else if (wsMsg?.topic === 'closed') {
            // Deleting from the open side
            let span = Array.from(document.querySelectorAll('span')).find(span => span.textContent.trim() === wsMsg.order_id);
            tr = span.closest('tr');
            tr.remove();

            // Adding to all positions table
            const tbody = all_positions_table.querySelector('tbody');
            tr = document.createElement('tr');

            const cols = ['ticker', 'realised_pnl', 'created_at', 'dollar_amount', 'open_price', 'close_price'];
            cols.forEach(col => {
                const td = document.createElement('td');
                td.textContent = wsMsg[col];
                if (col === 'dollar_amount') { td.classList.add('rpl');}
                tr.appendChild(td);
            });
            tbody.appendChild(tr);

            await showAlert(wsMsg.reason);

            // Update Balance and realised pnl
            const balanceElement = document.getElementById('balance');
            balanceElement.textContent = parseFloat(wsMsg.balance).toFixed(2);
            assignColor(balanceElement, false);

            let realisedSpan = document.querySelector('.rg').querySelector('span');
            let num = Number(parseFloat(realisedSpan.textContent.replace('$', '')).toFixed(2));
            num = num + wsMsg.amount;
            realisedSpan.textContent = num;
            assignColor(realisedSpan);
        }

        // Increasing the Unrealised Pnl Live
        else if (wsMsg?.topic === 'position_update') {
            let span = Array.from(document.querySelectorAll('span')).find(span => span.textContent.trim() === wsMsg.order_id);
            const tr = span?.closest('tr');

            openObject[wsMsg.order_id] = parseFloat(wsMsg.amount);
            tr.querySelector('.upl').textContent = wsMsg.amount.toFixed(2);
            calculateOpenSum();
        }
    };

    order_socket.onopen = function(e){
        document.querySelector('.connect-btn').style.backgroundColor = '#037B66';
    }
    order_socket.onclose = function(e) {
        document.querySelector('.connect-btn').style.backgroundColor = '#D60A22';
        document.querySelector('.connect-btn').nextElementSibling.textContent = 'Disconnected';
    }


    // -------------------------------------------
    //  Stat Card
    // -------------------------------------------

    // Calculate the sum of unrealised gain
    function calculateOpenSum() {
        let sum = Object.values(openObject).reduce((sum, value) => sum + value, 0).toFixed(2);
        let ugElement = document.querySelector('.ug').querySelector('span');
        sum = Object.values(openObject).reduce((sum, value) => sum + value, 0).toFixed(2);
        let str = '';
        if (sum < 0) {
            ugElement.style.color = '#D60A22';
            str = "-$" + sum.slice(1);
        } else {
            str = "+$" + sum;
            ugElement.style.color = '#037B66';
        }
        ugElement.textContent = str;
    }
    calculateOpenSum();

    // Color changes for top row stats
    function assignColor(targetStat, color=true) {
        let str = '';
        let targetNum = parseFloat(targetStat.textContent);
        if (targetNum < 0){
            if (color) {
                targetStat.style.color ='#D60A22';
                str = "-$" + String(targetNum).slice(1);
            } else { str = "$" + String(targetNum).slice(1); }
        } else {
            if (color) {
                targetStat.style.color ='#037B66';
                str = "+$" + targetNum;
            } else { str = "$" + targetNum; }
        }
        targetStat.textContent = str;
    }
    const dayChange = document.querySelector('.dc').querySelector('span');
    const realisedGain = document.querySelector('.rg').querySelector('span');
    assignColor(realisedGain);
    assignColor(dayChange);


    // ----------------------------------------------
    // Order Relating
    // ----------------------------------------------

    // Order Card
    document.getElementById('id_ticker').addEventListener('input', function(e){
        const inputValue = e.target.value.trim()
        if (inputValue.trim()) {
            fetch(`/dashboard/tickers/?q=${inputValue}`)
            .then(response => response.json())
            .then(data => {
                const suggestionsDiv = document.getElementById('suggestions');
                suggestionsDiv.innerHTML = '';
                if (data.length > 0) {
                    suggestionsDiv.style.display = 'flex';
                    data.forEach(item => {
                        const div = document.createElement('div');
                        div.classList.add("hover", "suggestion");
                        div.textContent = item;
                        suggestionsDiv.appendChild(div);
                    });

                    document.querySelectorAll('.suggestion').forEach(s => {
                        s.addEventListener('click', function() {
                            document.getElementById('id_ticker').value = s.textContent;
                        });
                    });
                }
            })
        }
    });

    // Placing an order
    document.getElementById('order-form').addEventListener('submit', async function(e){
        e.preventDefault();
        const formData = new FormData(e.target);
        let data = { action: 'open', user_id: email,...Object.fromEntries(formData.entries()) };
        order_socket.send(JSON.stringify(data));
    });

    // Closing an order
    document.querySelectorAll('.close-open-order').forEach(position => {
        position.addEventListener('click', function(){
            const order_id = this.closest('tr').querySelector('span').textContent;
            const amount = this.closest('tr').querySelector('.upl').textContent;
            order_socket.send(JSON.stringify({action: 'close', order_id: order_id, dollar_amount: amount}));
        });
    });


    // ----------------------------------------------
    // Tables
    // ----------------------------------------------
    document.querySelectorAll('.modal-section button').forEach(button => {
        button.addEventListener('click', function() {
            if (!button.classList.contains('active-modal')) {
                const activeButtons = document.querySelectorAll('.active-modal');
                if (activeButtons) {
                    activeButtons.forEach(btn => btn.classList.remove('active-modal'));
                }
                button.classList.add('active-modal');
            }
        });
    });

    // Shows the table on click of modal button
    function showTable(targetTable) {
        if (targetTable.classList.contains('inactive-table')) {
            const activeTables = document.querySelector('.table-container').children;
            if (activeTables) {
                Array.from(activeTables).forEach((table, index) => {
                    table.classList.add('inactive-table');
                });
                targetTable.classList.remove('inactive-table');
            }
        }
    }

    // Modal Activators
    document.querySelector('.open').addEventListener('click', function(){
        showTable(open_positions_table);
    });

    document.querySelector('.all').addEventListener('click', function(){

        showTable(all_positions_table);
    });

    document.querySelector('.summaries').addEventListener('click', function(){
        showTable(summary_table);
    });


    // ----------------------------------------------
    // Charts
    // ----------------------------------------------

    // Portfolio Chart
    // ------------------------------------------------

    // Toggling Interval on Portfolio Growth Chart
    const growthIntervalUrl = '/dashboard/growth-interval';

    async function getInterval(interval){
        const rsp = await fetch(`${growthIntervalUrl}/?interval=${interval}`);
        return await rsp.json();
    }

    function reloadPortfolioChart(data) {
        const cols = Object.keys(data).filter(key => key != 'starting_balance');
        const values = cols.map(key => { return Number(parseFloat(( data[key] / data['starting_balance']) * 100).toFixed(2)); })
        option['xAxis']['data'] = cols;
        option['series'][0]['data'] = values;
        pfChart.setOption(option);
    }

    document.querySelector('.week').addEventListener('click', async function(){
        const data = await getInterval('week');
        reloadPortfolioChart(data);
    });

    document.querySelector('.month').addEventListener('click', async function(){
        const data = await getInterval('month');
        reloadPortfolioChart(data);
    });

    document.querySelector('.year').addEventListener('click', async function(){
        const data = await getInterval('year');
        reloadPortfolioChart(data);
    });

    // Generating Portfolio Growth Chart
    const cols = Object.keys(balanceGrowth).filter(key => key != 'starting_balance');
    var pfChart = echarts.init(document.getElementById('portfolio-chart'));
    var option = {
      tooltip: {
        trigger: 'axis',
        formatter: function (params) {
          return 'Date: ' + params[0].name + '<br> Value: ' + params[0].value;
        }
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: cols
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value} %'
        }
      },
      series: [
        {
          name: 'Portfolio Value',
          type: 'line',
          data: cols.map(key => { return Number(parseFloat((balanceGrowth[key] / balanceGrowth['starting_balance']) * 100).toFixed(2)); }),
          smooth: true,
          symbol: 'none',
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                {
                    offset: 0,
                    color: 'rgb(142, 167, 209)'
                },
                {
                    offset: 1,
                    color: 'rgb(240, 240, 240)'
                }
            ])
          },
          itemStyle: {
            color: 'rgba(133, 157, 230)'
          }
        }
      ],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      }
    };
    pfChart.setOption(option);
    window.addEventListener('resize', function(){
        pfChart.resize();
    });


    // ----------------------------------------------
    // Alert
    // ----------------------------------------------
    async function showAlert(message, alert_type='info') {
        try {
            const span = alertBox.querySelector("span");

            alertBox.classList.add("active");
            if (alert_type === 'good' ){ alertBox.classList.add('good') ; }
            span.textContent = message;

            await sleep(3000);

            // Removing alert
            alertBox.classList.remove("active", 'good');
            span.textContent = "";

        } catch(e) {
            await showAlert(e.message);
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});