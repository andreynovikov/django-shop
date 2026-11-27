'use strict';
// Admin index page (templates/admin/index.html). Tabs: the one in the URL's #hash, else the last one opened, opens
// first; arrows, Home and End move between them. The recent actions dropdown closes on a click outside or Escape.
{
    const KEY = 'admin-index-tab';
    const tabs = Array.from(document.querySelectorAll('.sw-tabs [role="tab"]'));

    const select = (tab, remember) => {
        for (const other of tabs) {
            const selected = other === tab;
            other.setAttribute('aria-selected', selected);
            other.tabIndex = selected ? 0 : -1;
            document.getElementById(other.getAttribute('aria-controls')).hidden = !selected;
        }
        if (remember) {
            try {
                localStorage.setItem(KEY, tab.dataset.tab);
            } catch (e) {
                // private windows or blocked storage: only this page keeps the tab
            }
            history.replaceState(null, '', '#' + tab.dataset.tab);
        }
    };

    const find = (name) => tabs.find((tab) => tab.dataset.tab === name);

    if (tabs.length) {
        let saved = null;
        try {
            saved = localStorage.getItem(KEY);
        } catch (e) {
            // see above
        }
        select(find(location.hash.slice(1)) || find(saved) || tabs[0], false);

        for (const tab of tabs) {
            tab.addEventListener('click', () => select(tab, true));
        }
        tabs[0].parentElement.addEventListener('keydown', (event) => {
            const index = tabs.indexOf(document.activeElement);
            const next = {
                ArrowLeft: index - 1,
                ArrowRight: index + 1,
                Home: 0,
                End: tabs.length - 1,
            }[event.key];
            if (index < 0 || next === undefined) {
                return;
            }
            event.preventDefault();
            const tab = tabs[(next + tabs.length) % tabs.length];
            select(tab, true);
            tab.focus();
        });
        window.addEventListener('hashchange', () => {
            const tab = find(location.hash.slice(1));
            if (tab) {
                select(tab, true);
            }
        });
    }

    const recent = document.querySelector('.sw-recent');
    if (recent) {
        document.addEventListener('click', (event) => {
            if (recent.open && !recent.contains(event.target)) {
                recent.open = false;
            }
        });
        recent.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && recent.open) {
                recent.open = false;
                recent.querySelector('summary').focus();
            }
        });
    }
}
