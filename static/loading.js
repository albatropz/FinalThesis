// Initial search function
document.addEventListener('DOMContentLoaded', () => {
    const searchState = localStorage.getItem('searchState');
    const searchQuery = localStorage.getItem('searchQuery');
    if (searchState === 'active' && searchQuery) {
        displaySearchState(searchQuery);
    }
});
window.addEventListener('storage', (e) => {
    if (e.key === 'searchState') {
        const searchState = localStorage.getItem('searchState');
        const searchQuery = localStorage.getItem('searchQuery');
        if (searchState === 'active' && searchQuery) {
            displaySearchState(searchQuery);
        }
    }
});
function performInitialSearch() {
    const query = document.getElementById('initialSearchQuery').value.trim();
    if (!query) return;

    // Show loading state
    const loadingState = document.getElementById('loadingState');
    loadingState.style.display = 'flex';
    document.getElementById('initialState').style.display = 'none';
    
    try {
        // Set search query in search state
        document.getElementById('searchQuery').value = query;
        
        fetch(`/fetch_articles?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(articles => {
                if (articles.length > 0) {
                    // Hide loading state
                    loadingState.style.display = 'none';
                    
                    // Show search state
                    const searchState = document.getElementById('searchState');
                    searchState.style.display = 'block';
                    
                    // Display articles and create graph
                    displayArticles(articles);
                    createGraph(articles);
                } else {
                    showError('No articles found. Please try a different search.');
                    resetToInitialState();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('An error occurred. Please try again.');
                resetToInitialState();
            });
    } catch (error) {
        console.error('Error:', error);
        showError('An error occurred. Please try again.');
        resetToInitialState();
    }
}

function showError(message) {
    alert(message);
}

function resetToInitialState() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('initialState').style.display = 'flex';
    document.getElementById('searchState').style.display = 'none';
}

const searchInput = document.getElementById('initialSearchQuery');
const placeholders = [
    "Search by keywords, paper title, DOI or another identifier",
    "Try: 'Machine Learning in Healthcare'",
    "Try: '10.1038/s41586-021-03819-2'",
    "Try: 'Deep Learning Survey 2023'",
    "Try: 'arXiv:2301.04655'"
];

let currentIndex = 0;

function changePlaceholder() {
    searchInput.placeholder = placeholders[currentIndex];
    currentIndex = (currentIndex + 1) % placeholders.length;
}

// Change placeholder every 3 seconds
setInterval(changePlaceholder, 3000);