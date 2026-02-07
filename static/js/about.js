document.addEventListener('DOMContentLoaded', function() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
            } else {
                entry.target.classList.remove('is-visible');
            }
        });
    }, {
        threshold: 0.1
    });

    animatedElements.forEach(element => {
        observer.observe(element);
    });

    // Admin switcher logic
    const admins = [
      {
        name: "Dalavai Hemanth",
        photo: "/static/images/hemanth.jpg",
        role: "Lead Developer & Admin",
        desc: "Expert in backend, analytics, and system design. Passionate about sustainable technology and user empowerment.",
        skillsTechnical: ["Python", "Flask", "SQL", "Data Analytics"],
        skillsSoft: ["Leadership", "Problem Solving", "Teamwork"],
        skillsLanguages: ["English", "Telugu", "Hindi"],
      },
      {
        name: "Harshitha",
        photo: "/static/images/snitha.jpg",
        role: "Frontend Developer & Admin",
        desc: "Expert in UI/UX, frontend development, and user experience. Passionate about design and seamless user interaction.",
        skillsTechnical: ["HTML", "CSS", "JavaScript", "React"],
        skillsSoft: ["Creativity", "Communication", "Empathy"],
        skillsLanguages: ["English", "Hindi", "Telugu"],
      }
    ];
    let currentAdmin = 0;

    function updateAdminDetails() {
        const admin = admins[currentAdmin];
        document.getElementById('skills-technical').innerHTML = admin.skillsTechnical.map(skill => `<span>${skill}</span>`).join(' ');
        document.getElementById('skills-soft').innerHTML = admin.skillsSoft.map(skill => `<span>${skill}</span>`).join(' ');
        document.getElementById('skills-languages').innerHTML = admin.skillsLanguages.map(lang => `<span>${lang}</span>`).join(' ');
    }

    window.switchAdmin = function(direction) {
        const adminCards = document.querySelectorAll('.admin-card');
        adminCards[currentAdmin].style.display = 'none';
        currentAdmin = (currentAdmin + direction + admins.length) % admins.length;
        adminCards[currentAdmin].style.display = 'block';
        updateAdminDetails();
    }

    updateAdminDetails();
});
