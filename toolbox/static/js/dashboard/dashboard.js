document.addEventListener('DOMContentLoaded', function(){
    // Websocket
    // This websocket is for receiving the live price updates from django that came from fastapi
    // when the user wants to close a position. this is sent to django from js with all necessary details
    // django takes snapshot of price, saves and disconnects from fastapi


    const socket = new WebSocket('ws://127.0.0.1:8000/ws/trade');

    socket.onopen = function(e) {
        console.log('Connection established');
    };

    socket.onclose = function(e) {
        console.error('Connection closed');
    };

    socket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };

    socket.onmessage = function(e) {
        console.log('Message received:', e.data);
    };


    const trade_entry_container = document.getElementById('trade_entry_container');

    document.getElementById('place_trade').addEventListener('click', function(){
        document.getElementById('action_menu').style.display = 'none';
        trade_entry_container.style.display = 'flex';
    });

    document.getElementById('trade_entry_form').addEventListener('submit', async function(e){
        e.preventDefault();

        const formData = new FormData(document.getElementById('trade_entry_form'));
        let formObj = {};
        for (let [k, v] of formData.entries()) {
            if (k != 'csrfmiddlewaretoken') {
                formObj[k] = v;
            }
        }

        formObj['user_id'] = document.getElementById('email').textContent;
        let socket_obj = {'new_order': formObj};
        socket.send(JSON.stringify(socket_obj));

//        await fetch('http://127.0.0.1:8000/dashboard/create_order', {
//            method: 'POST',
//            headers: {'Content-Type': 'application/json'},
//            body: JSON.stringify(formObj)
//        })
//        .then(response => {
//            if (response.ok) {
//                window.location.href = '/dashboard';
//                return response.json();
//            } else {
//                return response.json().then(data => {
//                    if (response.status === 401) {
//                        window.alert(data.error);
//                    } else {
//                        throw new Error(data.error);
//                    }
//                });
//            }
//        })
//        .then(data => {})
//        .catch(error => { window.alert(error.message); });
    });
});