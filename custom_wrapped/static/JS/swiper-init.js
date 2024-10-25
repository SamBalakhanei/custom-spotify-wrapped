document.addEventListener('DOMContentLoaded', function () {
    const swiper = new Swiper('.swiper', {
        direction: 'horizontal',  // Change to 'vertical' if you prefer
        loop: true,
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        scrollbar: {
            el: '.swiper-scrollbar',
            draggable: true,
        },
    });
});
