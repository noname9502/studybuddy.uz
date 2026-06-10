document.addEventListener('DOMContentLoaded', function() {
    const widget = document.getElementById('rating-widget');
    if (!widget) return;

    const stars = widget.querySelectorAll('.star');
    const lessonId = window.LESSON_ID;
    let currentRating = window.USER_RATING || 0;

    function setRating(rating) {
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('filled');
            } else {
                star.classList.remove('filled');
            }
        });
    }

    setRating(currentRating);

    stars.forEach((star, index) => {
        star.addEventListener('mouseover', () => setRating(index + 1));
        star.addEventListener('mouseout', () => setRating(currentRating));
        star.addEventListener('click', () => {
            const score = index + 1;
            fetch(`/lesson/${lessonId}/rate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ score: score })
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                      currentRating = score;
                      setRating(currentRating);
                      document.getElementById('avg-rating').textContent = data.new_avg;
                      document.getElementById('total-ratings').textContent = data.total;
                      showToast('Оценка сохранена!');
                  }
              });
        });
    });



    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'alert alert-success';
        toast.textContent = message;
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
});
