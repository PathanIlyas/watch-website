document.addEventListener('DOMContentLoaded', () => {
    // 1. Sticky Navbar
    const navbar = document.querySelector('.navbar');

    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }, { passive: true });
    }

    // 2. Initialize AOS (Animate on Scroll)
    if(typeof AOS !== 'undefined') {
        AOS.init({
            duration: 650,
            once: true,
            offset: 60,
            easing: 'ease-out-cubic',
            disable: () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
        });
    }

    // 3. Initialize Swiper for Trending Watches
    if (document.querySelector('.trending-slider')) {
        new Swiper('.trending-slider', {
            slidesPerView: 1,
            spaceBetween: 30,
            loop: true,
            autoplay: {
                delay: 4000,
                disableOnInteraction: false,
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            breakpoints: {
                640: {
                    slidesPerView: 2,
                },
                992: {
                    slidesPerView: 3,
                },
                1200: {
                    slidesPerView: 4,
                }
            }
        });
    }

    // 4. Initialize Swiper for Testimonials
    if (document.querySelector('.testimonial-slider')) {
        new Swiper('.testimonial-slider', {
            slidesPerView: 1,
            spaceBetween: 30,
            loop: true,
            autoplay: {
                delay: 5000,
                disableOnInteraction: false,
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            breakpoints: {
                768: {
                    slidesPerView: 2,
                }
            }
        });
    }

    // 5. Mouse Glow Effect on Cards
    const cards = document.querySelectorAll('.watch-card, .feature-card, .glass-effect');

    if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
        cards.forEach(card => {
            let pendingFrame = null;
            let latestEvent = null;

            card.classList.add('mouse-glow');
            card.addEventListener('pointermove', e => {
                latestEvent = e;
                if (pendingFrame) return;

                pendingFrame = requestAnimationFrame(() => {
                    const rect = card.getBoundingClientRect();
                    const x = latestEvent.clientX - rect.left;
                    const y = latestEvent.clientY - rect.top;
                    card.style.setProperty('--mouse-x', `${x}px`);
                    card.style.setProperty('--mouse-y', `${y}px`);
                    pendingFrame = null;
                });
            }, { passive: true });
        });
    }
});
