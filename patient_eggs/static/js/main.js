// Main JS file
console.log('Prairie Homestead Loaded');

// Lightbox Logic
document.addEventListener('DOMContentLoaded', function() {
    const galleryImages = document.querySelectorAll('.gallery-img');
    const modalImage = document.getElementById('lightboxImage');
    const prevBtn = document.getElementById('lightboxPrev');
    const nextBtn = document.getElementById('lightboxNext');
    let currentIndex = 0;

    if (galleryImages.length > 0) {
        galleryImages.forEach((img, index) => {
            img.addEventListener('click', function() {
                currentIndex = index;
                updateLightbox(this.src);
                var lightbox = new bootstrap.Modal(document.getElementById('galleryModal'));
                lightbox.show();
            });
        });

        prevBtn.addEventListener('click', function() {
            currentIndex = (currentIndex > 0) ? currentIndex - 1 : galleryImages.length - 1;
            updateLightbox(galleryImages[currentIndex].src);
        });

        nextBtn.addEventListener('click', function() {
            currentIndex = (currentIndex < galleryImages.length - 1) ? currentIndex + 1 : 0;
            updateLightbox(galleryImages[currentIndex].src);
        });

        function updateLightbox(src) {
            modalImage.src = src;
        }
    }
});

