/**
 * Logo loader for AI agents
 * Loads authentic logos from official sources or CDNs
 */

// Mapping of agent names to their reliable logo URLs using working CDN sources
const AGENT_LOGOS = {
    'ChatGPT': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/openai/openai-original.svg',
    'OpenAI GPT-4 API': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/openai/openai-original.svg',
    'ChatGPT Deep Research': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/openai/openai-original.svg',
    'DALL-E 3': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/openai/openai-original.svg',
    'Google Gemini (Bard)': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/google/google-original.svg',
    'Gemini Code Assist (Duet AI)': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/google/google-original.svg',
    'Socratic by Google': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/google/google-original.svg',
    'Claude 3': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/anthropic.svg',
    'Perplexity': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/perplexity.svg',
    'Microsoft Bing Chat (Copilot)': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/microsoft/microsoft-original.svg',
    'Microsoft 365 Copilot': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/microsoft/microsoft-original.svg',
    'Bing Image Creator': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/microsoft/microsoft-original.svg',
    'GitHub Copilot': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/github/github-original.svg',
    'Amazon CodeWhisperer': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/amazonwebservices/amazonwebservices-original.svg',
    'Slack AI (Slack GPT)': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/slack/slack-original.svg',
    'Notion AI': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/notion.svg',
    'Grammarly': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/grammarly.svg',
    'HubSpot AI (Content Assistant)': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/hubspot.svg',
    'Mailchimp AI': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/mailchimp/mailchimp-original.svg',
    'Midjourney': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/midjourney.svg',
    'Adobe Firefly': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/adobe/adobe-original.svg',
    'Canva Magic Write': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/canva.svg',
    'Character.AI': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23007ACC"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">C.AI</text></svg>',
    'Copy.ai': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2300D4AA"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="8" font-weight="bold">Copy</text></svg>',
    'Writesonic': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23A855F7"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">WS</text></svg>',
    'Jasper (formerly Jarvis)': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23FF6B35"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">J</text></svg>',
    'Tabnine': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23007ACC"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">Tab</text></svg>',
    'Codeium': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2309B6F2"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">C</text></svg>',
    'Replit Ghostwriter': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23F26207"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="8" font-weight="bold">Repl</text></svg>',
    'Otter.ai': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2300A4FF"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="8" font-weight="bold">Otter</text></svg>',
    'Fathom AI': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23FF4081"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">F</text></svg>'
};

// Fallback logos based on company/creator using working GitHub raw URLs
const CREATOR_LOGOS = {
    'OpenAI': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/openai/openai-original.svg',
    'Google': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/google/google-original.svg',
    'Google/DeepMind': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/google/google-original.svg',
    'Google Cloud': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/googlecloud/googlecloud-original.svg',
    'Anthropic': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/anthropic.svg',
    'Microsoft': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/microsoft/microsoft-original.svg',
    'GitHub': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/github/github-original.svg',
    'GitHub/Microsoft': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/github/github-original.svg',
    'Amazon Web Services': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/amazonwebservices/amazonwebservices-original.svg',
    'Salesforce/Slack': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/slack/slack-original.svg',
    'Meta': 'https://github.com/simple-icons/simple-icons/raw/develop/icons/meta.svg',
    'Adobe': 'https://github.com/devicons/devicon/raw/v2.16.0/icons/adobe/adobe-original.svg'
};

/**
 * Get logo URL for an agent
 * @param {string} agentName - Name of the agent
 * @param {string} creator - Creator/company name
 * @returns {string} Logo URL or null if not found
 */
function getAgentLogo(agentName, creator) {
    // First try exact agent name match
    if (AGENT_LOGOS[agentName]) {
        return AGENT_LOGOS[agentName];
    }
    
    // Then try creator match
    if (CREATOR_LOGOS[creator]) {
        return CREATOR_LOGOS[creator];
    }
    
    // Try partial matches for creator
    for (const [key, url] of Object.entries(CREATOR_LOGOS)) {
        if (creator.toLowerCase().includes(key.toLowerCase()) || 
            key.toLowerCase().includes(creator.toLowerCase())) {
            return url;
        }
    }
    
    return null;
}

/**
 * Load logo for an agent element
 * @param {HTMLElement} element - Element to add logo to
 * @param {string} agentName - Name of the agent
 * @param {string} creator - Creator name
 */
function loadAgentLogo(element, agentName, creator) {
    const logoUrl = getAgentLogo(agentName, creator);
    
    if (logoUrl) {
        const img = document.createElement('img');
        img.src = logoUrl;
        img.alt = `${agentName} logo`;
        img.className = 'w-8 h-8 rounded-md object-contain bg-white p-1 border border-gray-200';
        img.style.minWidth = '32px';
        img.style.minHeight = '32px';
        
        // Handle loading errors - keep existing icon instead of creating fallback
        img.onerror = function() {
            // Keep the existing Lucide icon if logo fails to load
            console.log(`Failed to load logo for ${agentName}, keeping default icon`);
        };
        
        // Replace existing icon with logo when it loads successfully
        img.onload = function() {
            const existingIcon = element.querySelector('i[data-lucide]');
            if (existingIcon) {
                existingIcon.parentNode.replaceChild(img, existingIcon);
            } else {
                element.prepend(img);
            }
        };
    }
}

/**
 * Initialize logos for all agent elements on the page
 */
function initializeLogos() {
    // Find all agent elements with data attributes
    const agentElements = document.querySelectorAll('[data-agent-name]');
    
    agentElements.forEach(element => {
        const agentName = element.getAttribute('data-agent-name');
        const creator = element.getAttribute('data-agent-creator');
        
        if (agentName && creator) {
            loadAgentLogo(element, agentName, creator);
        }
    });
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeLogos);

// Export for manual use
window.AgentLogos = {
    getAgentLogo,
    loadAgentLogo,
    initializeLogos
};