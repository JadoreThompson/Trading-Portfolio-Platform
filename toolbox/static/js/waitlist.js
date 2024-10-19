document.addEventListener('DOMContentLoaded', async function(){
    const params = new URLSearchParams(window.location.search);
    const currency = params.get('q');

    const data = {positive: 0.6, negative: 0.4};

    async function getSentiment() {
        try {
            const r = await fetch(`http://127.0.0.1:80/sentiment?currency=${currency.split('-')[0]}`)
              .then(response => {
                if (!response.ok) {
                  throw new Error('Network response was not ok');
                }
                return response.json();
              })
              .then(data => {
                const bullishBar = document.querySelector('.bullish.progress-bar').parentElement;
                bullishBar.style.width = data['positive'] * 100 + '%';
                bullishBar.ariaValueNow = `${data['positive'] * 100}`;

                const bearishBar = document.querySelector('.bearish.progress-bar').parentElement;
                bearishBar.style.width = data['negative'] * 100 + '%';
                bearishBar.ariaValueNow = `${data['negative'] * 100}`;
              })
              .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
              });

        } catch(e) {
            console.log(e);
        }
    }
//    await getSentiment();
});