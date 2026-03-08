// Smooth scroll and animations
document.addEventListener('DOMContentLoaded', () => {
    // Scroll reveal logic
    const sections = document.querySelectorAll('section');

    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal');
            }
        });
    }, observerOptions);

    sections.forEach(section => {
        observer.observe(section);
    });

    // Auto-hide flash messages
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-20px)';
            setTimeout(() => flash.remove(), 500);
        }, 4000); // Set to 4 seconds
    });

    // Table Availability Check
    const dateInput = document.getElementById('date');
    const timeInput = document.getElementById('time');
    const durationInput = document.getElementById('duration');
    const tableSelect = document.getElementById('table_number');
    const statusDiv = document.getElementById('availability-status');

    if (dateInput && timeInput && tableSelect) {
        function checkAvailability() {
            if (dateInput.value && timeInput.value) {
                const duration = durationInput ? durationInput.value : 1;
                fetch(`/check_availability?date=${dateInput.value}&time=${timeInput.value}&duration=${duration}`)
                    .then(res => res.json())
                    .then(data => {
                        const bookedTables = data.booked_tables;
                        tableSelect.disabled = false;

                        // Reset options and enable all
                        Array.from(tableSelect.options).forEach(option => {
                            if (option.value === "") {
                                option.text = "Choose a Table";
                                return;
                            }

                            if (bookedTables.includes(option.value)) {
                                option.disabled = true;
                                option.text = `${option.value} (จองแล้ว/Booked)`;
                            } else {
                                option.disabled = false;
                                option.text = option.value;
                            }
                        });

                        // Show status
                        // Removed status message as per user request
                    })
                    .catch(err => console.error('Error checking availability:', err));
            }
        }

        [dateInput, timeInput, durationInput].forEach(input => {
            if (input) input.addEventListener('change', checkAvailability);
        });
    }

    // Menu Slider Logic
    const menuSlider = document.getElementById('menu-slider');
    const prevBtn = document.getElementById('menu-prev');
    const nextBtn = document.getElementById('menu-next');

    if (menuSlider && prevBtn && nextBtn) {
        const scrollAmount = 432; // card (400) + gap (32)

        const updateButtons = () => {
            const scrollLeft = menuSlider.scrollLeft;
            const maxScroll = menuSlider.scrollWidth - menuSlider.clientWidth;

            // Prev button visibility
            prevBtn.style.opacity = scrollLeft <= 10 ? '0' : '1';
            prevBtn.style.pointerEvents = scrollLeft <= 10 ? 'none' : 'auto';

            // Next button visibility
            nextBtn.style.opacity = scrollLeft >= maxScroll - 10 ? '0' : '1';
            nextBtn.style.pointerEvents = scrollLeft >= maxScroll - 10 ? 'none' : 'auto';
        };

        nextBtn.addEventListener('click', () => {
            menuSlider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            setTimeout(updateButtons, 500);
        });

        prevBtn.addEventListener('click', () => {
            menuSlider.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            setTimeout(updateButtons, 500);
        });

        menuSlider.addEventListener('scroll', updateButtons);
        window.addEventListener('resize', updateButtons);
        setTimeout(updateButtons, 100);
    }

    // Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    const navLinkItems = document.querySelectorAll('.nav-links a');

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            mobileMenuBtn.querySelector('i').classList.toggle('fa-bars');
            mobileMenuBtn.querySelector('i').classList.toggle('fa-times');
        });

        // Close menu when link is clicked
        navLinkItems.forEach(item => {
            item.addEventListener('click', () => {
                navLinks.classList.remove('active');
                mobileMenuBtn.querySelector('i').classList.add('fa-bars');
                mobileMenuBtn.querySelector('i').classList.remove('fa-times');
            });
        });
    }
});
