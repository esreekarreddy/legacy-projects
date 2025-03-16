/**
 * Animation helpers for consistent application of animations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Apply fade-in animations to elements 
    applyFadeInAnimations();
    
    // Apply pulse animations to elements that should have them
    applyPulseAnimations();
    
    // Apply shine effect to buttons
    applyShineEffects();
});

/**
 * Apply staggered fade-in animations to elements with data-animate attribute
 */
function applyFadeInAnimations() {
    const elements = document.querySelectorAll('[data-animate="fade-in"]');
    elements.forEach((el, i) => {
        el.classList.add('fade-in');
        el.classList.add(`fade-in-${i % 9 + 1}`); // Use modulo to limit to 9 levels
    });
}

/**
 * Apply pulse animations to elements with data-animate-pulse attribute
 */
function applyPulseAnimations() {
    const elements = document.querySelectorAll('[data-animate="pulse"]');
    elements.forEach((el, i) => {
        const pulseIndex = i % 5; // We have 5 pulse variations
        el.classList.add(`pulse-${pulseIndex}`);
    });
}

/**
 * Apply shine effects to buttons
 */
function applyShineEffects() {
    const buttons = document.querySelectorAll('.btn, .button, button:not(.btn-plain)');
    buttons.forEach((btn, i) => {
        const shineIndex = i % 3; // We have 3 shine variations 
        btn.classList.add(`shine-${shineIndex}`);
    });
}
