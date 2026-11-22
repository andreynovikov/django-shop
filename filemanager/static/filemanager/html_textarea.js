'use strict';
// HTMLTextarea: text areas that grow with their text, and the "Insert file" button that opens the file browser in
// a popup. The browser calls filemanagerInsert() with the chosen file, which goes into the text at the cursor.
(function () {
    const LAST_DIR_KEY = 'filemanager-dir';
    const FIELDS = 'textarea[data-autosize]';

    function resize(field) {
        if (!field.offsetParent) {
            return;  // hidden, such as in a collapsed fieldset: resized when shown
        }
        const scroll = window.scrollY;  // shrinking to measure would scroll the page
        const style = window.getComputedStyle(field);
        field.style.height = 'auto';
        let height = field.scrollHeight;
        if (style.boxSizing === 'border-box') {
            height += parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
        } else {
            height -= parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
        }
        field.style.height = height + 'px';  // max-height, if set, still applies
        window.scrollTo(window.scrollX, scroll);
    }

    function resizeAll(root) {
        root.querySelectorAll(FIELDS).forEach(resize);
    }

    function escape(text) {
        return text.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function markup(file) {
        const url = escape(file.url);
        if (file.kind === 'image') {
            return '<img src="' + url + '" alt="">';
        }
        if (file.kind === 'video') {
            return '<video src="' + url + '" controls></video>';
        }
        return '<a href="' + url + '">' + escape(file.name) + '</a>';
    }

    window.filemanagerInsert = function (target, file) {
        const field = document.getElementById(target);
        if (!field) {
            return;
        }
        field.focus();
        field.setRangeText(markup(file), field.selectionStart, field.selectionEnd, 'end');
        field.dispatchEvent(new Event('input', { bubbles: true }));
    };

    function openBrowser(button) {
        const field = button.closest('.filemanager-html').querySelector('textarea');
        const params = new URLSearchParams({ _popup: '1', _target: field.id });
        try {
            const dir = window.localStorage.getItem(LAST_DIR_KEY);
            if (dir) {
                params.set('dir', dir);
            }
        } catch (e) {
            // no storage, open the root folder
        }
        const popup = window.open(button.dataset.url + '?' + params, 'filemanager', 'width=1000,height=700,resizable,scrollbars');
        if (popup) {
            popup.focus();
        }
    }

    document.addEventListener('click', (event) => {
        const button = event.target.closest('.filemanager-insert-file');
        if (button) {
            openBrowser(button);
        }
    });
    document.addEventListener('input', (event) => {
        if (event.target.matches(FIELDS)) {
            resize(event.target);
        }
    });
    document.addEventListener('focusin', (event) => {
        if (event.target.matches(FIELDS)) {
            resize(event.target);
        }
    });
    document.addEventListener('toggle', (event) => resizeAll(event.target), true);  // <details> of collapsed fieldsets
    document.addEventListener('formset:added', (event) => resizeAll(event.target));
    document.addEventListener('DOMContentLoaded', () => resizeAll(document));
    let pending = false;
    window.addEventListener('resize', () => {
        if (!pending) {
            pending = true;
            window.requestAnimationFrame(() => {
                pending = false;
                resizeAll(document);
            });
        }
    });
})();
