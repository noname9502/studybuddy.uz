document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('lesson-video');
    if (!video) return;

    const lessonId = window.LESSON_ID;
    const storageKey = `video_pos_${lessonId}`;

    const savedPos = localStorage.getItem(storageKey);
    if (savedPos) {
        video.currentTime = parseFloat(savedPos);
    }

    video.addEventListener('timeupdate', function() {
        localStorage.setItem(storageKey, video.currentTime.toString());

        if (video.duration && (video.currentTime / video.duration) >= 0.8) {
            markAsWatched();
        }

        updateWatchTime(Math.floor(video.currentTime));
    });

    function markAsWatched() {
        if (window.LESSON_WATCHED) return;
        fetch(`/lesson/${lessonId}/progress`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ watched: true, watch_time: Math.floor(video.currentTime) })
        }).then(() => {
            window.LESSON_WATCHED = true;
        });
    }

    function updateWatchTime(seconds) {
        fetch(`/lesson/${lessonId}/progress`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ watch_time: seconds })
        });
    }
});
