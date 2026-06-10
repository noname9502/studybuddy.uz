document.addEventListener('DOMContentLoaded', function() {
    const publishButtons = document.querySelectorAll('.btn-publish');
    publishButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            fetch(url, {
                method: 'POST'
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                      this.textContent = data.is_published ? 'Снять с публикации' : 'Опубликовать';
                  }
              });
        });
    });

    const hideButtons = document.querySelectorAll('.btn-hide');
    hideButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            fetch(url, {
                method: 'POST'
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                      this.textContent = data.is_visible ? 'Скрыть' : 'Показать';
                  }
              });
        });
    });

    const deleteModal = document.getElementById('delete-modal');
    const deleteForm = document.getElementById('delete-form');
    const deleteButtons = document.querySelectorAll('.btn-delete-modal');
    const cancelDelete = document.getElementById('cancel-delete');

    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            deleteForm.action = url;
            deleteModal.classList.remove('hidden');
        });
    });

    if (cancelDelete) {
        cancelDelete.addEventListener('click', () => {
            deleteModal.classList.add('hidden');
        });
    }

    if (deleteModal) {
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                deleteModal.classList.add('hidden');
            }
        });
    }


});
