// File Upload Handling
const fileInput = document.getElementById('fileInput');
const fileInputArea = document.getElementById('fileInputArea');
const fileLabel = document.querySelector('.file-input p');

// Drag and drop functionality
fileInputArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileInputArea.classList.add('drag-active');
});

fileInputArea.addEventListener('dragleave', () => {
    fileInputArea.classList.remove('drag-active');
});

fileInputArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileInputArea.classList.remove('drag-active');
    const files = e.dataTransfer.files;
    if (files.length && files[0].type === 'application/pdf') {
        fileInput.files = files;
        updateFileName(files[0].name);
    }
});

// Click to upload
fileInputArea.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        updateFileName(e.target.files[0].name);
    }
});

function updateFileName(name) {
    fileLabel.textContent = name;
}

// Form submission handling
const citationForm = document.getElementById('citationForm');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');

citationForm.addEventListener('submit', (e) => {
    loadingIndicator.style.display = 'block';
    errorMessage.textContent = '';
});

// Citation style handling
const citationStyleSelect = document.getElementById('citation-style');
citationStyleSelect.addEventListener('change', () => {
    // This will be handled server-side
    citationForm.submit();
});
