/* Film Translator Generator Documentation JS */
document.addEventListener('DOMContentLoaded', function() {
    // Handle FAQ expand/collapse
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('h3');
        const answer = item.querySelector('.faq-answer');
        
        if (question && answer) {
            // Initially collapse all answers
            answer.style.maxHeight = '0';
            answer.style.overflow = 'hidden';
            answer.style.transition = 'max-height 0.3s ease-in-out';
            
            // Add indicator for expandable items
            question.innerHTML += '<span class="faq-toggle">+</span>';
            question.style.cursor = 'pointer';
            
            // Toggle functionality
            question.addEventListener('click', function() {
                const isOpen = answer.style.maxHeight !== '0px' && answer.style.maxHeight !== '';
                
                if (isOpen) {
                    // Close this answer
                    answer.style.maxHeight = '0';
                    this.querySelector('.faq-toggle').textContent = '+';
                } else {
                    // Open this answer
                    answer.style.maxHeight = answer.scrollHeight + 'px';
                    this.querySelector('.faq-toggle').textContent = '−';
                }
            });
        }
    });
    
    // Add smooth scrolling for anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
                
                // Update URL without reloading page
                history.pushState(null, null, targetId);
            }
        });
    });
    
    // Handle theme preference
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            
            // Save preference
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme-preference', isDark ? 'dark' : 'light');
            
            // Update button text
            this.textContent = isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        });
        
        // Apply saved preference on load
        const savedTheme = localStorage.getItem('theme-preference');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.textContent = 'Switch to Light Mode';
        }
    }
    
    // Handle mobile navigation menu
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const navMenu = document.querySelector('nav ul');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('show');
            this.setAttribute('aria-expanded', navMenu.classList.contains('show'));
        });
    }
    
    // Handle code block highlighting
    document.querySelectorAll('pre code').forEach(block => {
        // Add copy button to code blocks
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.textContent = 'Copy';
        
        // Place button above the code block
        block.parentNode.insertBefore(copyButton, block);
        
        copyButton.addEventListener('click', function() {
            const code = block.textContent;
            navigator.clipboard.writeText(code).then(() => {
                // Visual feedback
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
    });
    
    // Check if we need to open a specific FAQ based on URL hash
    if (location.hash && location.hash.startsWith('#')) {
        const targetElement = document.querySelector(location.hash);
        if (targetElement && targetElement.classList.contains('faq-item')) {
            const question = targetElement.querySelector('h3');
            if (question) question.click();
        }
    }
}); 