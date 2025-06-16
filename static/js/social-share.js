/**
 * Social sharing functionality for agent and recipe cards
 */

function shareOnTwitter(title, description, url) {
    const text = `${title}\n\n${description}`;
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    window.open(twitterUrl, '_blank', 'width=550,height=420');
}

function shareOnLinkedIn(title, description, url) {
    const linkedinUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
    window.open(linkedinUrl, '_blank', 'width=550,height=420');
}

function shareOnFacebook(url) {
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    window.open(facebookUrl, '_blank', 'width=550,height=420');
}

function copyToClipboard(url) {
    navigator.clipboard.writeText(url).then(function() {
        // Show temporary success message
        showCopySuccess();
    }).catch(function(err) {
        console.error('Failed to copy URL: ', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = url;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showCopySuccess();
    });
}

function showCopySuccess() {
    // Create and show temporary success message
    const message = document.createElement('div');
    message.textContent = 'Link copied to clipboard!';
    message.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-opacity';
    document.body.appendChild(message);
    
    // Remove message after 2 seconds
    setTimeout(() => {
        message.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(message);
        }, 300);
    }, 2000);
}

function shareAgent(agentName, agentCreator, agentDescription, agentUrl) {
    const title = `${agentName} by ${agentCreator}`;
    const description = agentDescription;
    const url = agentUrl;
    
    return {
        twitter: () => shareOnTwitter(title, description, url),
        linkedin: () => shareOnLinkedIn(title, description, url),
        facebook: () => shareOnFacebook(url),
        copy: () => copyToClipboard(url)
    };
}

function shareRecipe(recipeName, recipeDescription, recipeUrl) {
    const title = `AI Agent Recipe: ${recipeName}`;
    const description = recipeDescription;
    const url = recipeUrl;
    
    return {
        twitter: () => shareOnTwitter(title, description, url),
        linkedin: () => shareOnLinkedIn(title, description, url),
        facebook: () => shareOnFacebook(url),
        copy: () => copyToClipboard(url)
    };
}

function toggleShareDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    const isHidden = dropdown.classList.contains('hidden');
    
    // Close all other dropdowns first
    document.querySelectorAll('[id$="-share"]').forEach(d => {
        if (d.id !== dropdownId) {
            d.classList.add('hidden');
        }
    });
    
    // Toggle current dropdown
    if (isHidden) {
        dropdown.classList.remove('hidden');
    } else {
        dropdown.classList.add('hidden');
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const isShareButton = event.target.closest('[onclick*="toggleShareDropdown"]');
    const isInsideDropdown = event.target.closest('[id$="-share"]');
    
    if (!isShareButton && !isInsideDropdown) {
        document.querySelectorAll('[id$="-share"]').forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
    }
});