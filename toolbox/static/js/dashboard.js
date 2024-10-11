document.addEventListener('DOMContentLoaded', function(){
    const email = document.getElementById('email').textContent;
    const alertBox = document.getElementById('custom-alert');

    const create_order_form = document.getElementById('create_order_form');
    const all_positions_table = document.getElementById('all_positions_table');
    const open_positions_table = document.getElementById('open_positions_table');


    // Socket
    const order_socket = new WebSocket('ws://' + window.location.host + `/ws/${email}/orders`);

    order_socket.onmessage = async function(e){
        wsMsg = JSON.parse(e.data)
//        document.getElementById('placeholder').textContent = wsMsg.amount;

        if (wsMsg.type === 'order_confirmation') { document.querySelector('.order-msg').textContent = wsMsg.message; }
        if (wsMsg.type === 'close_order_confirmation') { await showAlert('Order Closed'); }
    }

    order_socket.onopen = function(e){
        console.log('Connection open');
    }


    // Order Relating
    document.getElementById('close-order').addEventListener('click', function(){
        document.getElementById('order-container').style.display = 'none';
    });
    document.getElementById('create-order-btn').addEventListener('click', function(){
        console.log('clicked');
        document.getElementById('order-container').style.display = 'flex';
    });

    document.getElementById('id_ticker').addEventListener('input', function(e){
        const inputValue = e.target.value.trim()
        if (inputValue.trim()) {
            console.log(`${window.location.host}/dashboard/tickers/?q=${inputValue}`);
            fetch(`/dashboard/tickers/?q=${inputValue}`)
            .then(response => response.json())
            .then(data => {
                const suggestionsDiv = document.getElementById('suggestions');
                suggestionsDiv.innerHTML = '';
                if (data.length > 0) {
                    suggestionsDiv.style.display = 'flex';
                    data.forEach(item => {
                        console.log(item);
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
            const amount = this.closest('tr').querySelector('#upl').textContent;
            order_socket.send(JSON.stringify({action: 'close', order_id: order_id, dollar_amount: amount}));
        });
    });


    // Table
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

    function showTable(targetTable) {
        if (!targetTable.classList.contains('active-table')) {
            const activeTables = document.querySelectorAll('.active-table');
            if (activeTables) {
                activeTables.forEach(table => {
                    table.classList.remove('active-table');
                    table.classList.add('inactive-table');
                });
            }
            targetTable.classList.remove('inactive-table');
            targetTable.classList.add('active-table');
        }
    }

    document.querySelector('.open').addEventListener('click', function(){
        showTable(open_positions_table);
    });

    document.querySelector('.all').addEventListener('click', function(){
        showTable(all_positions_table);
    });


    // Portfolio Chart
    var chart = echarts.init(document.getElementById('portfolio-chart'));
    var option = {
//      title: {
//        text: 'Balance ' + document.getElementById('balance').textContent //'Portfolio Growth'
//      },
      tooltip: {
        trigger: 'axis',
        formatter: function (params) {
          return 'Date: ' + params[0].name + '<br> Value: ' + params[0].value;
        }
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04', '2024-10-05', '2024-10-06', '2024-10-07']
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value} USD'
        }
      },
      series: [
        {
          name: 'Portfolio Value',
          type: 'line',
          data: [1000, 1500, 1200, 1800, 2500, 2200, 2700],
          smooth: true,
          areaStyle: {},
          itemStyle: {
            color: '#5470C6'
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

    // Set the options for the chart
    chart.setOption(option);


    // Alert
    async function showAlert(message) {
        try {
            const span = alertBox.querySelector("span");

            alertBox.classList.add("active");
            span.textContent = message;

            await sleep(3000);

            // Removing alert
            alertBox.classList.remove("active");
            span.textContent = "";

        } catch(e) {
            await showAlert(e.message);
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});