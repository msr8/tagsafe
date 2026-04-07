/**
 * main.js
 * Contains shared frontend logic, initializations, and toast notifications.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Function to show toast messages using Toastify
    window.showToast = function(message, category = 'info') {
        if (typeof Toastify === 'undefined') return;

        let bgColor = "rgba(9, 9, 14, 0.8)"; // Default dark
        
        // Match Python flash categories to colors
        if (category === 'success') bgColor = "rgba(16, 185, 129, 0.9)";
        if (category === 'error' || category === 'danger') bgColor = "rgba(239, 68, 68, 0.9)";
        if (category === 'warning') bgColor = "rgba(245, 158, 11, 0.9)";

        Toastify({
            text: message,
            duration: 4000,
            gravity: "bottom", // `top` or `bottom`
            position: "right", // `left`, `center` or `right`
            stopOnFocus: true, // Prevents dismissing of toast on hover
            style: {
                background: bgColor,
            }
        }).showToast();
    };

    // Any flash messages rendered from Flask can be captured and shown here
    // Look out for hidden inputs or a script tag inserted into base.html templates
});

// Function to toggle repo details
function toggleRepo(repoId) {
    const card = document.getElementById(`repo-${repoId}`);
    if (card) card.classList.toggle('expanded');
}

// Function to save user config
function savePreferences() {
    const email = document.getElementById('pref-email').value;
    const severity = document.getElementById('pref-severity').value;

    fetch('/api/change-config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            severity_threshold: parseInt(severity)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message || 'Preferences updated!', 'success');
        } else {
            showToast(data.message || 'Error updating preferences.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('A network error occurred.', 'error');
    });
}

// Function to toggle individual finding details
function toggleFinding(findingId) {
    const wrapper = document.getElementById(findingId);
    if (!wrapper) return;
    
    // Find the closest finding-item parent
    const item = wrapper.closest('.finding-item');
    if (item) {
        item.classList.toggle('expanded');
        
        // Also rotate icon via inline style for safety, though CSS is preferred
        const icon = document.getElementById(findingId.replace('find-', 'find-icon-'));
        if (icon) {
            icon.style.transform = item.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }
}

// Function to switch tabs between Pull Requests and Commits
function switchTab(repoId, tabId) {
    // Deactivate all buttons in this repo's tabs
    const tabsContainer = document.querySelector(`#details-${repoId} .repo-tabs`);
    if (tabsContainer) {
        const tabBtns = tabsContainer.querySelectorAll(`.tab-btn`);
        tabBtns.forEach(btn => btn.classList.remove('active'));
    }

    // Hide all tab contents in this repo
    const tabContents = document.querySelectorAll(`#details-${repoId} > .repo-details-inner > .tab-content`);
    tabContents.forEach(content => content.classList.remove('active'));

    // Activate the clicked button
    const targetBtn = tabsContainer ? tabsContainer.querySelector(`button[onclick="switchTab('${repoId}', '${tabId}')"]`) : null;
    if (targetBtn) targetBtn.classList.add('active');

    // Show the targeted tab
    const targetContent = document.getElementById(tabId);
    if (targetContent) targetContent.classList.add('active');
}

// Function to reload repos
function reloadRepos() {
    const btn = document.getElementById('reload-repos-btn');
    const icon = btn ? btn.querySelector('svg') : null;
    
    // Optional: Add spinning animation
    if (icon) icon.classList.add('lucide-spin');
    
    fetch('/api/reload-repos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (icon) icon.classList.remove('lucide-spin');
        if (data.status === 'success') {
            showToast(data.message || 'Repositories reloaded!', 'success');
            // Reload the page to show the updated repos
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.message || 'Error reloading repositories.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (icon) icon.classList.remove('lucide-spin');
        showToast('A network error occurred while reloading repositories.', 'error');
    });
}
