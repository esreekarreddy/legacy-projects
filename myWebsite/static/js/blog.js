/**
 * Blog functionality and interactive features
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Blog.js loaded");
    
    // Initialize welcome overlay - only shown from homepage
    initWelcomeOverlay();
    
    // Initialize side decorations
    initSideDecorations();
    
    // Handle comment form submission
    initCommentForm();
    
    // Add share functionality
    initShareButtons();
    
    // Set avatar colors
    setAvatarColors();
});

/**
 * Initialize welcome overlay for visitors coming from homepage
 */
function initWelcomeOverlay() {
    const overlay = document.getElementById('welcomeOverlay');
    if (!overlay) {
        console.log("Welcome overlay not found");
        return;
    }
    
    const continueBtn = document.getElementById('welcomeContinueBtn');
    if (!continueBtn) {
        console.log("Continue button not found");
        return;
    }
    
    // Check sessionStorage flag instead of URL parameter
    const showWelcome = sessionStorage.getItem('showWelcome') === 'true';
    
    if (showWelcome) {
        console.log("Showing overlay - from homepage");
        overlay.style.display = 'flex';
        // Remove the flag so it doesn't show again on page refresh
        sessionStorage.removeItem('showWelcome');
    } else {
        console.log("Not showing overlay");
        overlay.style.display = 'none';
    }
    
    // Handle the continue button click
    continueBtn.addEventListener('click', function() {
        console.log("Continue button clicked");
        overlay.style.display = 'none';
    });
}

/**
 * Initialize side decorations that follow scroll
 */
function initSideDecorations() {
    // Add side decorations to blog post pages
    const blogPost = document.querySelector('.blog-post');
    if (!blogPost) return;

    // Only add decorations on larger screens
    if (window.innerWidth > 1200) {
        const leftDecoration = document.createElement('div');
        leftDecoration.className = 'side-decoration side-decoration-left';
        
        const rightDecoration = document.createElement('div');
        rightDecoration.className = 'side-decoration side-decoration-right';
        
        document.body.appendChild(leftDecoration);
        document.body.appendChild(rightDecoration);
    }
}

/**
 * Initialize comment form submission and validation
 */
function initCommentForm() {
    const commentForm = document.querySelector('.comment-form');
    if (!commentForm) return;

    commentForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Basic validation
        const nameInput = this.querySelector('input[name="name"]');
        const emailInput = this.querySelector('input[name="email"]');
        const commentInput = this.querySelector('textarea[name="comment"]');
        
        if (!nameInput.value.trim() || !commentInput.value.trim()) {
            alert('Please fill in all required fields.');
            return;
        }
        
        // Here you would typically submit the form via AJAX
        console.log('Submitting comment:', {
            name: nameInput.value,
            email: emailInput.value,
            comment: commentInput.value
        });
        
        // Show a success message (in a real app, this would happen after successful submission)
        alert('Your comment has been submitted and is awaiting approval.');
        
        // Reset the form
        commentForm.reset();
    });
}

/**
 * Initialize share buttons functionality
 */
function initShareButtons() {
    const shareBtn = document.querySelector('.share-btn');
    if (!shareBtn) return;
    
    const shareOptions = document.querySelector('.share-options');
    
    // All share option links
    const shareLinks = document.querySelectorAll('.share-option');
    
    shareLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const platform = this.textContent.trim().toLowerCase();
            const url = encodeURIComponent(window.location.href);
            const title = encodeURIComponent(document.title);
            
            let shareUrl;
            switch(platform) {
                case 'twitter':
                    shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                    break;
                case 'facebook':
                    shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                    break;
                case 'linkedin':
                    shareUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${url}&title=${title}`;
                    break;
                default:
                    shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
            }
            
            window.open(shareUrl, '_blank', 'width=600,height=400');
        });
    });
}

/**
 * Set colors for avatar circles based on author names
 */
function setAvatarColors() {
    const avatarCircles = document.querySelectorAll('.avatar-circle[data-author]');
    
    avatarCircles.forEach(avatar => {
        const authorName = avatar.getAttribute('data-author') || 'Anonymous';
        const hue = (authorName.length * 25) % 360;
        avatar.style.backgroundColor = `hsl(${hue}, 70%, 60%)`;
    });
}
