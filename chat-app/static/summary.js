document.addEventListener('DOMContentLoaded', () => {
    const summaryTextElement = document.getElementById('summary-text');
    
    // Retrieve the summary from session storage, where it was placed by the main chat page.
    const summary = sessionStorage.getItem('chatSummary');

    if (summaryTextElement) {
        if (summary) {
            // Display the summary text.
            summaryTextElement.textContent = summary;
            // Clean up the storage so the summary isn't accidentally shown again.
            sessionStorage.removeItem('chatSummary');
        } else {
            // This is a fallback in case the user navigates to this page directly.
            summaryTextElement.textContent = "No summary available. Please go back to the chat and generate one.";
        }
    }
});
