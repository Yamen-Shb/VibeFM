document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.tab-button');
    const tracksList = document.getElementById('tracks-list');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const timeRange = this.getAttribute('data-time-range');
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            fetch(`/top-tracks/${timeRange}`)
                .then(response => response.json())
                .then(data => {
                    tracksList.innerHTML = '';
                    data.forEach((track, index) => {
                        const trackElement = document.createElement('div');
                        trackElement.className = 'track-item';

                        const imageContainer = document.createElement('div');
                        imageContainer.className = 'track-image-container';

                        const trackIndex = document.createElement('div');
                        trackIndex.className = 'track-index';
                        trackIndex.textContent = index + 1;

                        const trackImage = document.createElement('img');
                        trackImage.className = 'track-image';
                        trackImage.src = track.image;

                        imageContainer.appendChild(trackIndex);
                        imageContainer.appendChild(trackImage);

                        const trackInfo = document.createElement('div');
                        trackInfo.textContent = `${track.name} by ${track.artists}`;

                        trackElement.appendChild(imageContainer);
                        trackElement.appendChild(trackInfo);

                        tracksList.appendChild(trackElement);
                    });
                });
        });
    });

    buttons[0].click();
});