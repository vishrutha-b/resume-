document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('resume');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const form = document.getElementById('screenerForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.querySelector('.btn-text');
    const btnSpinner = document.getElementById('btnSpinner');
    const errorAlert = document.getElementById('errorAlert');
    const resultsPanel = document.getElementById('resultsPanel');
    
    const clearTextBtn = document.getElementById('clearTextBtn');
    const jobDescTextarea = document.getElementById('job_desc');

    // New: Action buttons for premium preview
    const optimizeBtn = document.getElementById('optimizeBtn');
    const optimizeSpinner = document.getElementById('optimizeSpinner');
    const previewBtn = document.getElementById('previewBtn');
    let currentEvaluationId = null;

    // Update file name on selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = e.target.files[0].name;
            clearFileBtn.classList.remove('hidden');
        } else {
            fileNameDisplay.textContent = 'Drag & drop or browse .PDF / .DOCX';
            clearFileBtn.classList.add('hidden');
        }
    });

    // Clear file logic
    clearFileBtn.addEventListener('click', () => {
        fileInput.value = '';
        fileNameDisplay.textContent = 'Drag & drop or browse .PDF / .DOCX';
        clearFileBtn.classList.add('hidden');
    });

    // Job Description clear toggling
    jobDescTextarea.addEventListener('input', () => {
        if (jobDescTextarea.value.trim().length > 0) {
            clearTextBtn.classList.remove('hidden');
        } else {
            clearTextBtn.classList.add('hidden');
        }
    });
    
    // Clear Job Desc logic
    clearTextBtn.addEventListener('click', () => {
        jobDescTextarea.value = '';
        clearTextBtn.classList.add('hidden');
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI Loading State
        errorAlert.classList.add('hidden');
        resultsPanel.classList.add('hidden');
        submitBtn.disabled = true;
        btnText.textContent = 'Analyzing...';
        btnSpinner.classList.remove('loader-hidden');

        try {
            const formData = new FormData(form);
            const response = await fetch('/api/screen_resume', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            // It might return data.error inside 200 depending on backend config
            if (data.error) {
                throw new Error(data.error);
            }

            renderResults(data);

        } catch (error) {
            errorAlert.textContent = `Analysis Failed: ${error.message}`;
            errorAlert.classList.remove('hidden');
        } finally {
            // Restore UI
            submitBtn.disabled = false;
            btnText.textContent = 'Screen Candidate';
            btnSpinner.classList.add('loader-hidden');
        }
    });

    function renderResults(data) {
        const payload = data.evaluation;
        
        // Top details
        document.getElementById('resultFileName').textContent = data.file_name;
        
        // Progress Ring Animation
        const scoreRing = document.getElementById('scoreRing');
        const scoreText = document.getElementById('atsScoreValue');
        
        const score = payload.ats_score;
        // The stroke-dasharray format is "Score, 100" where 100 is max circle length.
        setTimeout(() => {
            scoreRing.setAttribute('stroke-dasharray', `${score}, 100`);
            
            // Color based on performance
            if (score >= 80) scoreRing.style.stroke = 'var(--success)';
            else if (score >= 50) scoreRing.style.stroke = 'var(--warning)';
            else scoreRing.style.stroke = 'var(--danger)';
            
            animateCounter(scoreText, score, 1500);
        }, 100);

        // Fit Badges
        updateFitBadge('domainFit', payload.domain_fit);
        updateFitBadge('expFit', payload.experience_fit);

        // Skills Grid
        const skillsGrid = document.getElementById('skillsGrid');
        skillsGrid.innerHTML = '';
        
        payload.skill_match.matched.forEach(skill => {
            skillsGrid.innerHTML += `<span class="skill-pill s-match"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> ${skill}</span>`;
        });
        payload.skill_match.partial.forEach(skill => {
            skillsGrid.innerHTML += `<span class="skill-pill s-part"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"></line></svg> ${skill}</span>`;
        });
        payload.skill_match.missing.forEach(skill => {
            skillsGrid.innerHTML += `<span class="skill-pill s-miss"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> ${skill}</span>`;
        });

        // Detail Lists
        populateList('strongPointsList', payload.strong_points);
        populateList('keyGapsList', payload.key_gaps);
        populateList('recommendationsList', payload.recommendations);

        // Show Results
        resultsPanel.classList.remove('hidden');
        resultsPanel.classList.add('fade-up');
        
        // Reset and prepare premium actions
        currentEvaluationId = data.evaluation_id;
        previewBtn.classList.add('hidden');
        optimizeBtn.classList.remove('hidden');
        optimizeBtn.disabled = false;
        optimizeBtn.querySelector('.btn-text').textContent = 'Generate Professional Resume';
        
        // Scroll to results seamlessly on mobile
        if(window.innerWidth < 1024) {
            setTimeout(() => {
                resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }

    // New: Optimization Logic
    optimizeBtn.addEventListener('click', async () => {
        if (!currentEvaluationId) return;
        
        optimizeBtn.disabled = true;
        optimizeSpinner.classList.remove('loader-hidden');
        const originalText = optimizeBtn.querySelector('.btn-text').textContent;
        optimizeBtn.querySelector('.btn-text').textContent = 'Generating Elite Resume...';
        
        try {
            const response = await fetch(`/api/evaluations/${currentEvaluationId}/optimize`, {
                method: 'POST'
            });
            const result = await response.json();
            
            if (!response.ok) throw new Error(result.error || 'Optimization failed');
            
            // Show preview button with new route
            previewBtn.href = `/evaluation/${currentEvaluationId}/resume`;
            previewBtn.classList.remove('hidden');
            optimizeBtn.querySelector('.btn-text').textContent = 'Elite Optimization Complete';
            
        } catch (error) {
            alert(`Optimization Error: ${error.message}`);
            optimizeBtn.querySelector('.btn-text').textContent = 'Retry Optimization';
            optimizeBtn.disabled = false;
        } finally {
            optimizeSpinner.classList.add('loader-hidden');
        }
    });

    function updateFitBadge(elementId, value) {
        const el = document.getElementById(elementId);
        el.textContent = value;
        el.className = 'stat-value'; // reset
        if(value.toLowerCase() === 'high') el.classList.add('val-high');
        else if(value.toLowerCase() === 'medium') el.classList.add('val-medium');
        else el.classList.add('val-low');
    }

    function populateList(elementId, items) {
        const ul = document.getElementById(elementId);
        ul.innerHTML = items.map(item => `<li>${item}</li>`).join('');
    }

    function animateCounter(element, target, duration) {
        let start = 0;
        const increment = target / (duration / 16);
        const timer = setInterval(() => {
            start += increment;
            if (start >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(start);
            }
        }, 16);
    }
});
