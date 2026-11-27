/*
 * Instant notices of the admin (sewingworld/notifications.py). The page keeps one connection to the stream of the
 * staff member, and of the order on an order's page (sewingworld/admin_events.py). It shows notices among Django's
 * messages and passes every event on as a 'sw:event' of the window, which other scripts of the page listen to
 * (order-lock.js). It sends {type: 'connected'} when the connection opens, after which they check their state.
 */
(function() {
    'use strict';
    var script = document.currentScript;
    if (!script || !window.EventSource) {
        return;
    }
    var url = script.dataset.url;
    var order = document.querySelector('meta[name="sw-events-order"]');
    if (order) {
        url += '?order=' + encodeURIComponent(order.content);
    }

    function dispatch(detail) {
        window.dispatchEvent(new CustomEvent('sw:event', {detail: detail}));
    }

    function messageList() {
        var list = document.querySelector('ul.messagelist');
        var content = document.getElementById('content');
        if (!list && content) {
            list = document.createElement('ul');
            list.className = 'messagelist';
            content.parentNode.insertBefore(list, content);
        }
        return list;
    }

    function showNotice(notice) {
        var list = messageList();
        if (!list) {
            return;
        }
        var item = document.createElement('li');
        item.className = notice.level || 'info';
        var text = document.createElement(notice.link ? 'a' : 'span');
        text.textContent = notice.message;
        if (notice.link) {
            text.href = notice.link;
        }
        item.appendChild(text);
        var close = document.createElement('button');
        close.type = 'button';
        close.textContent = '×';
        close.title = 'Закрыть';
        close.style.cssText = 'float: right; background: none; border: 0; cursor: pointer; font-size: 1.2em; color: inherit';
        close.addEventListener('click', function() {
            item.remove();
        });
        item.appendChild(close);
        list.appendChild(item);
    }

    function connect() {
        var source = new EventSource(url);
        source.addEventListener('open', function() {
            dispatch({type: 'connected'});
        });
        source.addEventListener('message', function(event) {
            var data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                return;
            }
            if (data.type === 'notice') {
                showNotice(data);
            }
            dispatch(data);
        });
        source.addEventListener('error', function() {
            // EventSource gives up on an error status, such as 502 while the stream's process restarts, or 204,
            // which the admin answers when it serves no stream. A minute later the page tries again.
            if (source.readyState === EventSource.CLOSED) {
                setTimeout(connect, 60000);
            }
        });
    }

    connect();
})();
