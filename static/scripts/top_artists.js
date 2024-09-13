document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.tab-button');
    const artistsList = document.getElementById('artists-list');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const timeRange = this.getAttribute('data-time-range');
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            fetch(`/top-artists/${timeRange}`)
                .then(response => response.json())
                .then(data => {
                    artistsList.innerHTML = '';
                    data.forEach((artist, index) => {
                        const artistElement = document.createElement('div');
                        artistElement.className = 'artist-item';

                        const imageContainer = document.createElement('div');
                        imageContainer.className = 'artist-image-container';

                        const artistIndex = document.createElement('div');
                        artistIndex.className = 'artist-index';
                        artistIndex.textContent = index + 1;

                        const artistImage = document.createElement('img');
                        artistImage.className = 'artist-image';
                        artistImage.src = artist.image;

                        imageContainer.appendChild(artistIndex);
                        imageContainer.appendChild(artistImage);

                        const artistInfo = document.createElement('div');
                        artistInfo.textContent = artist.name;

                        artistElement.appendChild(imageContainer);
                        artistElement.appendChild(artistInfo);

                        artistsList.appendChild(artistElement);
                    });
                });
        });
    });

    buttons[0].click();
});