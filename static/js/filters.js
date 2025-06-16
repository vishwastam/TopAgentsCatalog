/**
 * JavaScript for handling filters and search functionality
 * Updated for Tailwind CSS and Lucide icons
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    initializeSearch();
    initializeLucideIcons();
    initializeAgentCards();
});

/**
 * Initialize filter functionality
 */
function initializeFilters() {
    const filterSelects = document.querySelectorAll('select[name]');
    
    // Auto-submit form when any filter changes
    filterSelects.forEach(select => {
        if (!select.hasAttribute('onchange')) {
            select.addEventListener('change', function() {
                // Add a small delay to allow for multiple rapid changes
                setTimeout(() => {
                    this.form.submit();
                }, 100);
            });
        }
    });
    
    // Handle clear individual filter badges
    const filterBadges = document.querySelectorAll('.inline-flex a');
    filterBadges.forEach(badge => {
        badge.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = this.href;
        });
    });
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[name="q"]');
    
    searchInputs.forEach(searchInput => {
        // Handle Enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.form.submit();
            }
        });
        
        // Add debounced input handling for future enhancements
        searchInput.addEventListener('input', debounce(function() {
            // Could implement live search suggestions here
            if (this.value.length > 2) {
                console.log('Search query:', this.value);
            }
        }, 300));
    });
}

/**
 * Initialize Lucide icons after dynamic content loads
 */
function initializeLucideIcons() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Debounce function to limit rapid function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Smooth scroll to filters section
 */
function scrollToFilters() {
    const filtersSection = document.getElementById('filters-section');
    if (filtersSection) {
        filtersSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

/**
 * Handle agent card interactions
 */
function initializeAgentCards() {
    const agentCards = document.querySelectorAll('a[href*="/agent/"]');
    
    agentCards.forEach(card => {
        // Add keyboard navigation
        card.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
        
        // Add hover effects
        const cardElement = card.querySelector('div');
        if (cardElement) {
            card.addEventListener('mouseenter', function() {
                cardElement.classList.add('hover-lift');
            });
            
            card.addEventListener('mouseleave', function() {
                cardElement.classList.remove('hover-lift');
            });
        }
    });
}

/**
 * Handle loading states for better UX
 */
function showLoadingState() {
    const main = document.querySelector('main');
    if (main) {
        main.classList.add('loading');
    }
}

function hideLoadingState() {
    const main = document.querySelector('main');
    if (main) {
        main.classList.remove('loading');
    }
}

/**
 * Copy URL to clipboard (for sharing)
 */
function copyToClipboard(text = window.location.href) {
    if (navigator.clipboard) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            return successful ? Promise.resolve() : Promise.reject();
        } catch (err) {
            document.body.removeChild(textArea);
            return Promise.reject(err);
        }
    }
}

/**
 * Initialize all components when page loads
 */
window.addEventListener('load', function() {
    hideLoadingState();
    initializeLucideIcons();
});

/**
 * Handle form submissions with loading states
 */
document.addEventListener('submit', function(e) {
    if (e.target.tagName === 'FORM') {
        showLoadingState();
    }
});

/**
 * Handle page visibility changes
 */
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        initializeLucideIcons();
    }
});

/**
 * Export functions for global use
 */
window.TopAgents = {
    scrollToFilters,
    copyToClipboard,
    showLoadingState,
    hideLoadingState,
    initializeLucideIcons,
    debounce
};
