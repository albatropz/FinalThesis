let network = null;
// let articleData;

document.addEventListener('DOMContentLoaded', function() {
    // Theme switching functionality
    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.addEventListener('change', () => {
        document.body.setAttribute('data-theme', 
            themeToggle.checked ? 'dark' : 'light'
        );
    });

    // Search button click handlers
    document.querySelector('.search-container button').addEventListener('click', searchArticles);
    
    // Search input enter key handlers
    document.getElementById('searchQuery').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchArticles();
        }
    });

    document.getElementById('initialSearchQuery').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performInitialSearch();
        }
    });

    // Visualization controls
    document.getElementById('zoomIn').addEventListener('click', () => {
        if (network) {
            network.moveTo({
                scale: network.getScale() * 1.2
            });
        }
    });

    document.getElementById('zoomOut').addEventListener('click', () => {
        if (network) {
            network.moveTo({
                scale: network.getScale() * 0.8
            });
        }
    });

    document.getElementById('resetView').addEventListener('click', () => {
        if (network) {
            network.fit();
        }
    });

    // Metadata close button handler with event propagation prevention
    // Update the close button event listener in the DOMContentLoaded section
});
document.querySelector('#metadata .close-btn').addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    const metadata = document.getElementById('metadata');
    metadata.style.display = 'none';
});
// Centralized metadata display function
function showMetadata(article) {
    document.getElementById('meta-title').textContent = article.title;
    document.getElementById('meta-year').textContent = article.year || 'Unknown Year';
    document.getElementById('meta-authors').textContent = Array.isArray(article.authors) ? article.authors.join(', ') : 'Unknown Author';
    document.getElementById('meta-abstract').textContent = article.abstract || 'No Abstract Available';
    document.getElementById('meta-classifications').textContent = article.classifications.join(', ');
    
    const sourceLink = document.getElementById('meta-link');
    if (article.link) {
        sourceLink.href = article.link;
        sourceLink.textContent = article.source || 'View Source';
        sourceLink.style.display = 'inline-block';
    } else {
        sourceLink.style.display = 'none';
    }

    const pdfContainer = document.getElementById('pdf-container');
    const pdfLink = document.getElementById('pdf-link');
    if (article.pdf_url) {
        pdfContainer.style.display = 'block';
        pdfLink.href = article.pdf_url;
    } else {
        pdfContainer.style.display = 'none';
    }
    
    document.getElementById('metadata').style.display = 'block';
}

// Rest of your existing functions (performInitialSearch, resetToInitialState, searchArticles, etc.)

async function performInitialSearch() {
    const query = document.getElementById('initialSearchQuery').value.trim();
    if (!query) {
        alert('Please enter a search term');
        return;
    }

    try {
        // Save search state to localStorage
        localStorage.setItem('searchState', 'active');
        localStorage.setItem('searchQuery', query);

        document.getElementById('initialState').style.display = 'none';
        document.getElementById('loadingState').style.display = 'flex';
        document.getElementById('searchState').style.display = 'none';

        const response = await fetch(`/fetch_articles?query=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const articles = await response.json();
        if (articles && articles.length > 0) {
            document.getElementById('loadingState').style.display = 'none';
            document.getElementById('searchState').style.display = 'block';
            document.getElementById('searchQuery').value = query;
            
            // Save articles data to localStorage
            localStorage.setItem('searchResults', JSON.stringify(articles));
            
            displayArticles(articles);
            createGraph(articles);
        } else {
            throw new Error('No articles found');
        }
    } catch (error) {
        console.error('Search error:', error);
        alert(error.message || 'An error occurred while searching. Please try again.');
        resetToInitialState();
    }
}

function resetToInitialState() {
    // Clear localStorage when resetting
    localStorage.removeItem('searchState');
    localStorage.removeItem('searchQuery');
    localStorage.removeItem('searchResults');
    
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('initialState').style.display = 'flex';
    document.getElementById('searchState').style.display = 'none';
}

// Add this function to check state on page load
window.addEventListener('load', () => {
    const searchState = localStorage.getItem('searchState');
    const searchQuery = localStorage.getItem('searchQuery');
    const searchResults = localStorage.getItem('searchResults');

    if (searchState === 'active' && searchQuery && searchResults) {
        document.getElementById('initialState').style.display = 'none';
        document.getElementById('searchState').style.display = 'block';
        document.getElementById('searchQuery').value = searchQuery;
        
        const articles = JSON.parse(searchResults);
        displayArticles(articles);
        createGraph(articles);
    }
});
async function searchArticles() {
    const query = document.getElementById('searchQuery').value.trim();
    if (!query) return;

    try {
        const response = await fetch(`/fetch_articles?query=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const articles = await response.json();
        if (articles.length > 0) {
            displayArticles(articles);
            createGraph(articles);
        } else {
            alert('No articles found. Please try a different search.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while searching. Please try again.');
    }
}

function displayArticles(articles) {
    const articlesContainer = document.getElementById('articles');
    articlesContainer.innerHTML = '';

    if (!Array.isArray(articles) || articles.length === 0) {
        articlesContainer.innerHTML = '<p>No articles found.</p>';
        return;
    }
    
    articles.forEach((article) => {
        articleData = {
            title: article.title || 'Untitled',
            year: article.year || 'Unknown Year',
            authors: Array.isArray(article.authors) ? article.authors.join(', ') : 'Unknown Author',
            link: article.link || null
        };

        const articleCard = document.createElement('div');
        articleCard.className = 'article-card';
        articleCard.innerHTML = `
            <div class="article-header">
                <h3><i class="fas fa-file-alt"></i> ${articleData.title}</h3>
                <div class="article-actions">
                    <button class="action-btn bookmark"><i class="far fa-bookmark"></i></button>
                    <button class="action-btn like"><i class="far fa-thumbs-up"></i></button>
                    <button class="action-btn dislike"><i class="far fa-thumbs-down"></i></button>
                </div>
            </div>
            <p class="year"><i class="far fa-calendar-alt"></i> Year: ${articleData.year}</p>
            <p class="authors"><i class="fas fa-users"></i> Authors: ${articleData.authors}</p>
            ${articleData.link ? `<a href="${articleData.link}" target="_blank" class="read-more"><i class="fas fa-external-link-alt"></i> Read More</a>` : ''}
        `;

        // Add click handlers for action buttons
        const bookmark = articleCard.querySelector('.bookmark');
        const like = articleCard.querySelector('.like');
        const dislike = articleCard.querySelector('.dislike');


        bookmark.onclick = (e) => {
            e.stopPropagation();
            bookmark.querySelector('i').classList.toggle('fas');
            bookmark.querySelector('i').classList.toggle('far');
            
            
        };

        
        like.onclick = (e) => {
            e.stopPropagation();
            like.querySelector('i').classList.toggle('fas');
            like.querySelector('i').classList.toggle('far');
            if (like.querySelector('i').classList.contains('fas')) {
                dislike.querySelector('i').classList.replace('fas', 'far');
            }
        };

        dislike.onclick = (e) => {
            e.stopPropagation();
            dislike.querySelector('i').classList.toggle('fas');
            dislike.querySelector('i').classList.toggle('far');
            if (dislike.querySelector('i').classList.contains('fas')) {
                like.querySelector('i').classList.replace('fas', 'far');
            }
        };

        // Original click handler for metadata
        articleCard.onclick = () => {
            document.getElementById('meta-title').textContent = article.title;
            document.getElementById('meta-year').textContent = article.year || 'Unknown Year';
            document.getElementById('meta-authors').textContent = Array.isArray(article.authors) ? article.authors.join(', ') : 'Unknown Author';
            document.getElementById('meta-abstract').textContent = article.abstract || 'No Abstract Available';
            document.getElementById('meta-classifications').textContent = article.classifications.join(', ');
            
            const sourceLink = document.getElementById('meta-link');
            if (article.link) {
                sourceLink.href = article.link;
                sourceLink.textContent = article.source || 'View Source';
                sourceLink.style.display = 'inline-block';
            } else {
                sourceLink.style.display = 'none';
            }
        
            const pdfContainer = document.getElementById('pdf-container');
            const pdfLink = document.getElementById('pdf-link');
            if (article.pdf_url) {
                pdfContainer.style.display = 'block';
                pdfLink.href = article.pdf_url;
            } else {
                pdfContainer.style.display = 'none';
            }
            
            document.getElementById('metadata').style.display = 'block';
        };

        articlesContainer.appendChild(articleCard);
    });
}

// export function getArticleData() {
//     if (!articleData) {
//         console.error('Article data is not available yet.');
//         return null;
//     }
//     return articleData;
// }


function getColorByClassification(classification) {
    if (!classification) {
        return '#A9A9A9';
    }

    const cleanClassification = classification.replace(/[\[\]']/g, '').trim();
    switch (cleanClassification) {
        case 'Engineering and Technology, Mathematics and Statistics':
            return '#FF6B6B';
        case 'Engineering and Technology, Physical Science':
            return '#4ECDC4';
        case 'Engineering and Technology':
            return '#45B7D1';
        case 'Life Science':
            return '#98D8C8';
        case 'Physical Science':
            return '#F7B801';
        case 'Social Science':
            return '#F06292';
        default:
            return '#A9A9A9';
    }
}


function createGraph(articles) {
    const validArticles = articles.filter(article => 
        article.abstract && article.abstract !== 'No Abstract Available'
    );

    const nodes = new vis.DataSet(
        validArticles.map((article, index) => ({
            id: index,
            label: article.title,
            shape: 'box',
            color: {
                background: getColorByClassification(article.classifications[0]),
                border: '#666666',
                highlight: {
                    background: getColorByClassification(article.classifications[0]),
                    border: '#000000'
                }
            },
            font: { color: 'black' }
        }))
    );

    const edges = new vis.DataSet();
    validArticles.forEach((article, index) => {
        validArticles.forEach((otherArticle, otherIndex) => {
            if (index !== otherIndex && article.year === otherArticle.year) {
                edges.add({
                    from: index,
                    to: otherIndex,
                    smooth: { type: 'curvedCW', roundness: 0.2 }
                });
            }
        });
    });

    const options = {
        nodes: {
            shape: 'box',
            margin: 10,
            widthConstraint: { maximum: 200 }
        },
        edges: {
            width: 0.5,
            arrows: { to: { enabled: true, scaleFactor: 0.1 } }
        },
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -26,
                springLength: 250,
                springConstant: 0.18,
                damping: 0.4
            },
            stabilization: { iterations: 200 }
        },
        layout: {
            improvedLayout: true,
            hierarchical: { enabled: false }
        },
        interaction: {
            hover: true,
            tooltipDelay: 300,
            zoomView: true,
            dragView: true
        }
    };

    const container = document.getElementById('network');
    const data = { nodes, edges };
    network = new vis.Network(container, data, options);

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const article = validArticles[nodeId];
            
            document.getElementById('meta-title').textContent = article.title;
            document.getElementById('meta-year').textContent = article.year || 'Unknown Year';
            document.getElementById('meta-authors').textContent = Array.isArray(article.authors) ? article.authors.join(', ') : 'Unknown Author';
            document.getElementById('meta-abstract').textContent = article.abstract || 'No Abstract Available';
            document.getElementById('meta-classifications').textContent = article.classifications.join(', ');
            
            const sourceLink = document.getElementById('meta-link');
            if (article.link) {
                sourceLink.href = article.link;
                sourceLink.textContent = article.source || 'View Source';
                sourceLink.style.display = 'inline-block';
            } else {
                sourceLink.style.display = 'none';
            }

            const pdfContainer = document.getElementById('pdf-container');
            const pdfLink = document.getElementById('pdf-link');
            if (article.pdf_url) {
                pdfContainer.style.display = 'block';
                pdfLink.href = article.pdf_url;
            } else {
                pdfContainer.style.display = 'none';
            }
            
            document.getElementById('metadata').style.display = 'block';
        }
    });

    network.on('hoverNode', function() {
        container.style.cursor = 'pointer';
    });

    network.on('blurNode', function() {
        container.style.cursor = 'default';
    });

    return network;
}s