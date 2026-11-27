/*
 * The indicators of the admin's top bar: the 1C import (#stocks_status) and the health of the integrations and of
 * Celery (.sw-health, see shop/health.py). Their changes come instantly with the admin's events (admin-events.js,
 * as 'sw:event' of the window): {type: 'import'} and {type: 'health'}. The page also asks for them when its event
 * stream (re)connects, since it may have missed some, and every POLL milliseconds, which is all it has where the
 * events are off and what shows a health check that stopped publishing.
 */
(function() {
    'use strict';
    var POLL = 300000;
    var IMPORT_COLORS = {copying: 'red', running: 'gold', idle: 'limegreen'};

    function showImport(status) {
        var indicator = document.getElementById('import1c_status');
        if (indicator) {
            indicator.style.color = IMPORT_COLORS[status.copying ? 'copying' : status.running ? 'running' : 'idle'];
        }
        var date = document.getElementById('import1c_date');
        if (date && status.last) {
            date.textContent = status.last;
        }
    }

    function showHealth(group, status) {
        var indicator = document.querySelector('.sw-health[data-group="' + group + '"]');
        if (indicator) {
            indicator.querySelector('.sw-level').style.color = status.color;
            indicator.title = status.title;
        }
    }

    function get(url, show) {
        if (!url) {
            return;
        }
        fetch(url, {credentials: 'same-origin', headers: {'Accept': 'application/json'}}).then(function(response) {
            return response.ok ? response.json() : null;
        }).then(function(data) {
            if (data) {
                show(data);
            }
        }).catch(function(error) {
            console.log(error);
        });
    }

    function refresh() {
        var stocks = document.getElementById('stocks_status');
        get(stocks && stocks.dataset.url, showImport);
        var health = document.querySelector('.sw-health');
        get(health && health.dataset.url, function(groups) {
            Object.keys(groups).forEach(function(group) {
                showHealth(group, groups[group]);
            });
        });
    }

    window.addEventListener('sw:event', function(event) {
        var data = event.detail || {};
        if (data.type === 'import') {
            showImport(data);
        } else if (data.type === 'health') {
            showHealth(data.group, data);
        } else if (data.type === 'connected') {
            refresh();
        }
    });

    setInterval(refresh, POLL);
})();
