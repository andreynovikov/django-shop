/*
 * Keeps the lock of the order's page, see shop/order_lock.py. The page renews its lease every config.heartbeat
 * seconds, and gives the lock up when it is left unsaved or when nobody has used it for config.idle seconds, warning
 * config.idle_warning seconds before. When the page loses the lock, by its renewal or a 'lock-lost' notice
 * (admin-events.js), it says why and can't be saved: the server would refuse it anyway.
 */
(function() {
    'use strict';
    var configElement = document.getElementById('order-lock-config');
    var form = document.getElementById('order_form');
    if (!configElement || !form) {
        return;
    }
    var config = JSON.parse(configElement.textContent);
    var csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
    var lost = false;
    var submitting = false;
    var lastInput = Date.now();
    var warning = null;

    function lockData() {
        var data = new FormData();
        data.append('csrfmiddlewaretoken', csrf);
        data.append(config.field, config.token);
        return data;
    }

    function post(url) {
        return fetch(url, {method: 'POST', body: lockData(), credentials: 'same-origin', keepalive: true});
    }

    function banner(text, background, color, buttonText, onClick) {
        var element = document.createElement('div');
        element.style.cssText = 'position: sticky; top: 0; z-index: 1000; display: flex; align-items: center; gap: 1em; ' +
            'padding: 10px 15px; margin-bottom: 10px; font-weight: bold; background: ' + background + '; color: ' + color;
        var message = document.createElement('span');
        message.textContent = text;
        element.appendChild(message);
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'button';
        button.style.marginLeft = 'auto';
        button.textContent = buttonText;
        button.addEventListener('click', onClick);
        element.appendChild(button);
        var main = document.getElementById('content-main') || form.parentNode;
        main.insertBefore(element, main.firstChild);
        return element;
    }

    function hideWarning() {
        if (warning) {
            warning.remove();
            warning = null;
        }
    }

    function showWarning() {
        if (!warning) {
            warning = banner('Блокировка заказа будет снята через ' + Math.ceil(config.idle_warning / 60) +
                ' мин. из-за бездействия.', '#fff3cd', '#664d03', 'Продолжить', active);
        }
    }

    function lose(message) {
        if (lost) {
            return;
        }
        lost = true;
        clearInterval(timer);
        hideWarning();
        form.querySelectorAll('input[type=submit], button[type=submit]').forEach(function(button) {
            button.disabled = true;
        });
        banner(message + ' Несохранённые изменения на этой странице не сохранить.', '#ba2121', '#fff', 'Обновить',
            function() {
                window.location.reload();
            });
    }

    function active() {
        lastInput = Date.now();
        hideWarning();
    }

    function heartbeat() {
        if (lost || submitting) {
            return;
        }
        var idle = (Date.now() - lastInput) / 1000;
        if (idle >= config.idle) {
            post(config.unlock_url).catch(function() {});
            lose('Блокировка заказа снята из-за бездействия.');
            return;
        }
        if (idle >= config.idle - config.idle_warning) {
            showWarning();
        }
        post(config.lock_url).then(function(response) {
            return response.ok ? response.json() : null;
        }).then(function(result) {
            if (result && !result.held) {
                lose(result.message);
            }
        }).catch(function() {});  // offline: the lease holds a while, the next renewal tries again
    }

    var timer = setInterval(heartbeat, config.heartbeat * 1000);

    ['input', 'change', 'keydown', 'mousedown', 'wheel', 'touchstart'].forEach(function(type) {
        document.addEventListener(type, active, {capture: true, passive: true});
    });

    window.addEventListener('sw:event', function(event) {
        var data = event.detail;
        if (data.type === 'lock-lost' && data.token === config.token) {
            lose(data.message);
        } else if (data.type === 'connected') {
            heartbeat();  // what the page may have missed before the stream connected
        }
    });

    form.addEventListener('submit', function(event) {
        if (lost) {
            event.preventDefault();
            return;
        }
        submitting = true;  // the save gives the lock up or keeps it, see OrderAdmin.change_view()
    });

    // Leaving the page unsaved gives the lock up. A page that the browser keeps to show again on "Back" has given it
    // up too, so it opens anew.
    window.addEventListener('pagehide', function() {
        if (!submitting && !lost) {
            navigator.sendBeacon(config.unlock_url, lockData());
        }
    });
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            window.location.reload();
        }
    });
})();
