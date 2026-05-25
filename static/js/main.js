document.addEventListener('DOMContentLoaded', () => {
    // 1. Sticky Navbar
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 2. Initialize AOS (Animate on Scroll)
    if(typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            once: true,
            offset: 100,
            easing: 'ease-out-cubic'
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

    // 5. GSAP Hero Animation
    if (typeof gsap !== 'undefined') {
        const heroTimeline = gsap.timeline();
        
        if (document.querySelector('.hero-title')) {
            heroTimeline.fromTo('.hero-title', 
                { opacity: 0, y: 50 },
                { opacity: 1, y: 0, duration: 1, ease: 'power3.out', delay: 0.2 }
            )
            .fromTo('.hero-subtitle', 
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' },
                "-=0.6"
            )
            .fromTo('.hero-btn', 
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out', stagger: 0.2 },
                "-=0.6"
            );
        }
        
        if (document.querySelector('.hero-bg')) {
            gsap.to('.hero-bg', {
                scale: 1,
                duration: 10,
                ease: 'power1.inOut'
            });
        }
    }

    // 6. Mouse Glow Effect on Cards
    const cards = document.querySelectorAll('.watch-card, .feature-card, .glass-effect');
    
    cards.forEach(card => {
        card.classList.add('mouse-glow');
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });
});
