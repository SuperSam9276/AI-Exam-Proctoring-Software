/**
 * ProctorAI Modal Component
 */

class Modal {
    static open(options) {
        const container = document.getElementById('modal-container');
        container.style.display = 'flex';
        
        container.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-content">
                <h2 class="modal-title">${options.title}</h2>
                <div class="modal-body">${options.body}</div>
                <div class="modal-footer">
                    ${options.secondaryBtn ? `<button class="btn btn-secondary" id="modal-sec-btn">${options.secondaryBtn}</button>` : ''}
                    <button class="btn btn-primary" id="modal-pri-btn">${options.primaryBtn || 'OK'}</button>
                </div>
            </div>
        `;

        const close = () => {
            container.style.display = 'none';
            container.innerHTML = '';
        };

        container.querySelector('#modal-pri-btn').onclick = () => {
            if (options.onPrimary) options.onPrimary();
            close();
        };

        if (options.secondaryBtn) {
            container.querySelector('#modal-sec-btn').onclick = () => {
                if (options.onSecondary) options.onSecondary();
                close();
            };
        }

        container.querySelector('.modal-backdrop').onclick = close;
        
        if (window.lucide) lucide.createIcons();
    }
}
