'use strict';
// The file browser: upload by drop or choice, copy URLs, and in the picker's popup insert a file into its field.
(function () {
    const LAST_DIR_KEY = 'filemanager-dir';

    function remember(dir) {
        try {
            window.localStorage.setItem(LAST_DIR_KEY, dir);
        } catch (e) {
            // storage may be unavailable, the picker then opens the root folder
        }
    }

    function setupUpload() {
        const form = document.getElementById('filemanager-upload');
        if (!form) {
            return;
        }
        const input = form.querySelector('input[type=file]');
        const drop = form.querySelector('.filemanager-drop');
        const names = new Set(JSON.parse(document.getElementById('filemanager-names').textContent));

        function submit(files) {
            if (!files.length) {
                return;
            }
            const existing = Array.from(files, (file) => file.name).filter((name) => names.has(name));
            form.elements.overwrite.value = '';
            if (existing.length) {
                if (!form.dataset.canReplace) {
                    window.alert(form.dataset.cannotReplace + '\n\n' + existing.join('\n'));
                    input.value = '';
                    return;
                }
                if (!window.confirm(form.dataset.exists + '\n\n' + existing.join('\n'))) {
                    input.value = '';
                    return;
                }
                form.elements.overwrite.value = '1';
            }
            drop.classList.add('dragover');
            form.submit();
        }

        input.addEventListener('change', () => submit(input.files));
        ['dragenter', 'dragover'].forEach((type) => drop.addEventListener(type, (event) => {
            event.preventDefault();
            drop.classList.add('dragover');
        }));
        ['dragleave', 'drop'].forEach((type) => drop.addEventListener(type, () => drop.classList.remove('dragover')));
        drop.addEventListener('drop', (event) => {
            event.preventDefault();
            input.files = event.dataTransfer.files;
            submit(input.files);
        });
    }

    function setupButtons() {
        document.querySelectorAll('.filemanager-copy').forEach((button) => button.addEventListener('click', () => {
            navigator.clipboard.writeText(button.dataset.url).then(() => {
                const text = button.textContent;
                button.textContent = button.dataset.copied;
                setTimeout(() => { button.textContent = text; }, 1500);
            });
        }));

        const params = new URLSearchParams(window.location.search);
        const target = params.get('_target');
        document.querySelectorAll('.filemanager-insert').forEach((button) => button.addEventListener('click', () => {
            if (window.opener && window.opener.filemanagerInsert) {
                window.opener.filemanagerInsert(target, button.dataset);
                window.close();
            }
        }));
    }

    document.addEventListener('DOMContentLoaded', () => {
        const path = document.querySelector('.filemanager-path');
        if (path && document.body.classList.contains('popup')) {
            remember(path.dataset.dir);
        }
        setupUpload();
        setupButtons();
    });
})();
