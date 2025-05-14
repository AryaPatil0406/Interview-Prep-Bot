// static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
    // State management
    let state = {
        currentSection: 'home-section',
        isLoggedIn: false,
        username: '',
        currentInterview: {
            sessionId: null,
            questions: [],
            currentQuestionIndex: 0
        }
    };

    // Check if user is already logged in (from a previous session)
    checkLoginStatus();

    // Navigation
    function showSection(sectionId) {
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionId).classList.add('active');
        state.currentSection = sectionId;
    }

    // Event Listeners
    // Navigation buttons
    document.getElementById('login-btn').addEventListener('click', () => {
        showAuthForms('login');
    });

    document.getElementById('register-btn').addEventListener('click', () => {
        showAuthForms('register');
    });

    document.getElementById('start-practice-btn').addEventListener('click', () => {
        if (state.isLoggedIn) {
            loadCategoriesAndShowSetup();
        } else {
            showAuthForms('login');
        }
    });

    document.getElementById('history-btn').addEventListener('click', () => {
        loadUserHistory();
    });

    document.getElementById('logout-btn').addEventListener('click', () => {
        logout();
    });

    // Auth form switching
    document.getElementById('switch-to-register').addEventListener('click', (e) => {
        e.preventDefault();
        showAuthForms('register');
    });

    document.getElementById('switch-to-login').addEventListener('click', (e) => {
        e.preventDefault();
        showAuthForms('login');
    });

    // Form submissions
    document.getElementById('login-form-element').addEventListener('submit', (e) => {
        e.preventDefault();
        loginUser();
    });

    document.getElementById('register-form-element').addEventListener('submit', (e) => {
        e.preventDefault();
        registerUser();
    });

    document.getElementById('setup-form').addEventListener('submit', (e) => {
        e.preventDefault();
        startInterview();
    });

    // Interview interactions
    document.getElementById('submit-answer-btn').addEventListener('click', () => {
        submitAnswer();
    });

    document.getElementById('next-question-btn').addEventListener('click', () => {
        moveToNextQuestion();
    });

    // Results actions
    document.getElementById('try-again-btn').addEventListener('click', () => {
        loadCategoriesAndShowSetup();
    });

    document.getElementById('back-home-btn').addEventListener('click', () => {
        showSection('home-section');
    });

    document.getElementById('back-to-history-btn').addEventListener('click', () => {
        loadUserHistory();
    });

    // Helper Functions
    function showAuthForms(form) {
        showSection('auth-section');
        if (form === 'login') {
            document.getElementById('login-form').style.display = 'block';
            document.getElementById('register-form').style.display = 'none';
        } else {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'block';
        }
    }

    function updateUIForLoggedInUser() {
        document.getElementById('logged-out-nav').style.display = 'none';
        document.getElementById('logged-in-nav').style.display = 'flex';
        document.getElementById('welcome-user').textContent = `Welcome, ${state.username}!`;
    }

    function updateUIForLoggedOutUser() {
        document.getElementById('logged-out-nav').style.display = 'flex';
        document.getElementById('logged-in-nav').style.display = 'none';
    }

    // API Calls
    async function checkLoginStatus() {
        try {
            // This would typically check a session cookie or token
            // For now, we'll just check if we have stored user info in sessionStorage
            const userData = sessionStorage.getItem('userData');
            if (userData) {
                const user = JSON.parse(userData);
                state.isLoggedIn = true;
                state.username = user.username;
                updateUIForLoggedInUser();
            } else {
                state.isLoggedIn = false;
                updateUIForLoggedOutUser();
            }
        } catch (error) {
            console.error('Error checking login status:', error);
            state.isLoggedIn = false;
            updateUIForLoggedOutUser();
        }
    }

    async function loginUser() {
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store user data
                sessionStorage.setItem('userData', JSON.stringify({
                    userId: data.user_id,
                    username: data.username
                }));
                
                state.isLoggedIn = true;
                state.username = data.username;
                
                updateUIForLoggedInUser();
                showSection('home-section');
                
                // Clear form
                document.getElementById('login-form-element').reset();
                document.getElementById('login-error').textContent = '';
            } else {
                document.getElementById('login-error').textContent = data.error || 'Login failed';
            }
        } catch (error) {
            console.error('Login error:', error);
            document.getElementById('login-error').textContent = 'An error occurred. Please try again.';
        }
    }

    async function registerUser() {
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store user data
                sessionStorage.setItem('userData', JSON.stringify({
                    userId: data.user_id,
                    username: data.username
                }));
                
                state.isLoggedIn = true;
                state.username = data.username;
                
                updateUIForLoggedInUser();
                showSection('home-section');
                
                // Clear form
                document.getElementById('register-form-element').reset();
                document.getElementById('register-error').textContent = '';
            } else {
                document.getElementById('register-error').textContent = data.error || 'Registration failed';
            }
        } catch (error) {
            console.error('Registration error:', error);
            document.getElementById('register-error').textContent = 'An error occurred. Please try again.';
        }
    }

    async function logout() {
        try {
            await fetch('/api/logout', {
                method: 'POST'
            });
            
            // Clear stored user data
            sessionStorage.removeItem('userData');
            
            state.isLoggedIn = false;
            state.username = '';
            
            updateUIForLoggedOutUser();
            showSection('home-section');
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    async function loadCategoriesAndShowSetup() {
        if (!state.isLoggedIn) {
            showAuthForms('login');
            return;
        }
        
        try {
            const response = await fetch('/api/categories');
            const categories = await response.json();
            
            const categorySelect = document.getElementById('category-select');
            categorySelect.innerHTML = '<option value="">Select a category</option>';
            
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
            });
            
            showSection('setup-section');
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async function startInterview() {
        const categoryId = document.getElementById('category-select').value;
        const difficulty = document.getElementById('difficulty-select').value;
        const questionCount = document.getElementById('question-count').value;
        
        if (!categoryId) {
            alert('Please select a category');
            return;
        }
        
        try {
            const response = await fetch('/api/start-interview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category_id: categoryId,
                    difficulty: difficulty || null,
                    question_count: questionCount
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                state.currentInterview = {
                    sessionId: data.session_id,
                    questions: data.questions,
                    currentQuestionIndex: 0
                };
                
                showCurrentQuestion();
                showSection('interview-section');
            } else {
                alert(data.error || 'Failed to start interview');
            }
        } catch (error) {
            console.error('Error starting interview:', error);
            alert('An error occurred. Please try again.');
        }
    }

    function showCurrentQuestion() {
        const { questions, currentQuestionIndex } = state.currentInterview;
        const question = questions[currentQuestionIndex];
        
        document.getElementById('current-question').textContent = question.question_text;
        document.getElementById('question-category').textContent = `Category: ${question.category_name}`;
        document.getElementById('question-difficulty').textContent = `Difficulty: ${question.difficulty}`;
        document.getElementById('question-progress').textContent = `Question ${currentQuestionIndex + 1} of ${questions.length}`;
        
        // Clear previous answer and hide feedback
        document.getElementById('user-answer').value = '';
        document.getElementById('answer-feedback').style.display = 'none';
    }

    async function submitAnswer() {
        const { sessionId, questions, currentQuestionIndex } = state.currentInterview;
        const question = questions[currentQuestionIndex];
        const userAnswer = document.getElementById('user-answer').value.trim();
        
        if (!userAnswer) {
            alert('Please enter your answer');
            return;
        }
        
        try {
            const response = await fetch('/api/submit-answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    question_id: question.id,
                    user_answer: userAnswer
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Show feedback
                document.getElementById('feedback-text').textContent = data.feedback;
                document.getElementById('sample-answer-text').textContent = data.sample_answer;
                
                // Display stars for rating
                const ratingContainer = document.getElementById('answer-rating');
                ratingContainer.innerHTML = '';
                for (let i = a; i <= 5; i++) {
                    const star = document.createElement('i');
                    star.className = i <= data.rating ? 'fas fa-star' : 'far fa-star';
                    ratingContainer.appendChild(star);
                }
                
                document.getElementById('answer-feedback').style.display = 'block';
                
                // Update question in state with the rating and feedback
                question.rating = data.rating;
                question.feedback = data.feedback;
                question.user_answer = userAnswer;
                question.sample_answer = data.sample_answer;
            } else {
                alert(data.error || 'Failed to submit answer');
            }
        } catch (error) {
            console.error('Error submitting answer:', error);
            alert('An error occurred. Please try again.');
        }
    }

    function moveToNextQuestion() {
        const { questions, currentQuestionIndex } = state.currentInterview;
        
        if (currentQuestionIndex < questions.length - 1) {
            // Move to next question
            state.currentInterview.currentQuestionIndex++;
            showCurrentQuestion();
        } else {
            // Complete the interview
            completeInterview();
        }
    }

    async function completeInterview() {
        const { sessionId } = state.currentInterview;
        
        try {
            const response = await fetch('/api/complete-interview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Show results
                document.getElementById('final-score').textContent = data.score;
                
                // Generate feedback based on score
                let feedbackText = '';
                if (data.score >= 5) {
                    feedbackText = 'Excellent job! You\'re well-prepared for interviews.';
                } else if (data.score >= 4) {
                    feedbackText = 'Great job! You have a good understanding of the topics.';
                } else if (data.score >= 3) {
                    feedbackText = 'Good effort! With a bit more practice, you\'ll be fully prepared.';
                } else {
                    feedbackText = 'Keep practicing! These topics take time to master.';
                }
                
                document.getElementById('results-feedback').innerHTML = `<p>${feedbackText}</p>`;
                
                // Show question reviews
                const questionListEl = document.getElementById('question-list');
                questionListEl.innerHTML = '';
                
                data.answers.forEach((answer, index) => {
                    const questionItem = document.createElement('div');
                    questionItem.className = 'question-item';
                    
                    // Create rating stars
                    let starsHTML = '';
                    for (let i = 1; i <= 5; i++) {
                        starsHTML += `<i class="${i <= answer.rating ? 'fas' : 'far'} fa-star"></i>`;
                    }
                    
                    questionItem.innerHTML = `
                        <h4>Question ${index + 1}: ${answer.question_text}</h4>
                        <div class="question-item-rating">${starsHTML}</div>
                        <p>${answer.feedback}</p>
                        <div class="user-answer">
                            <h5>Your Answer:</h5>
                            <p>${answer.user_answer}</p>
                        </div>
                        <div class="suggested-answer">
                            <h5>Sample Answer:</h5>
                            <p>${answer.sample_answer}</p>
                        </div>
                    `;
                    
                    questionListEl.appendChild(questionItem);
                });
                
                showSection('results-section');
            } else {
                alert(data.error || 'Failed to complete interview');
            }
        } catch (error) {
            console.error('Error completing interview:', error);
            alert('An error occurred. Please try again.');
        }
    }

    async function loadUserHistory() {
        if (!state.isLoggedIn) {
            showAuthForms('login');
            return;
        }
        
        try {
            const response = await fetch('/api/user/history');
            const history = await response.json();
            
            const historyListEl = document.getElementById('history-list');
            historyListEl.innerHTML = '';
            
            if (history.length === 0) {
                document.getElementById('no-history-message').style.display = 'block';
            } else {
                document.getElementById('no-history-message').style.display = 'none';
                
                history.forEach(session => {
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    
                    // Format date
                    const date = new Date(session.created_at);
                    const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                    
                    // Check if session is completed
                    const isCompleted = session.completed_at !== null;
                    
                    historyItem.innerHTML = `
                        <div class="history-item-details">
                            <h3>${session.category_name}</h3>
                            <div class="history-item-meta">
                                <span>${formattedDate}</span>
                                <span>${session.questions_answered} questions</span>
                                <span>${isCompleted ? 'Completed' : 'In Progress'}</span>
                            </div>
                        </div>
                        <div class="history-item-score">
                            ${isCompleted ? `<div class="history-score-badge">${session.score}/5</div>` : ''}
                            <i class="fas fa-chevron-right"></i>
                        </div>
                    `;
                    
                    historyItem.addEventListener('click', () => {
                        loadSessionDetails(session.id);
                    });
                    
                    historyListEl.appendChild(historyItem);
                });
            }
            
            showSection('history-section');
        } catch (error) {
            console.error('Error loading history:', error);
            alert('An error occurred. Please try again.');
        }
    }

    async function loadSessionDetails(sessionId) {
        try {
            const response = await fetch(`/api/session/${sessionId}`);
            const data = await response.json();
            
            if (response.ok) {
                const session = data.session;
                const answers = data.answers;
                
                // Format date
                const date = new Date(session.created_at);
                const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                
                // Update session info
                document.getElementById('session-title').textContent = `${session.category_name} Interview`;
                document.getElementById('session-date').textContent = `Date: ${formattedDate}`;
                document.getElementById('session-category').textContent = `Category: ${session.category_name}`;
                document.getElementById('session-score').textContent = session.score || '0';
                
                // Show questions and answers
                const questionListEl = document.getElementById('session-question-list');
                questionListEl.innerHTML = '';
                
                answers.forEach((answer, index) => {
                    const questionItem = document.createElement('div');
                    questionItem.className = 'question-item';
                    
                    // Create rating stars
                    let starsHTML = '';
                    for (let i = 1; i <= 5; i++) {
                        starsHTML += `<i class="${i <= answer.rating ? 'fas' : 'far'} fa-star"></i>`;
                    }
                    
                    questionItem.innerHTML = `
                        <h4>Question ${index + 1}: ${answer.question_text}</h4>
                        <div class="question-item-rating">${starsHTML}</div>
                        <p>${answer.feedback}</p>
                        <div class="user-answer">
                            <h5>Your Answer:</h5>
                            <p>${answer.user_answer}</p>
                        </div>
                        <div class="suggested-answer">
                            <h5>Sample Answer:</h5>
                            <p>${answer.sample_answer}</p>
                        </div>
                    `;
                    
                    questionListEl.appendChild(questionItem);
                });
                
                showSection('session-details-section');
            } else {
                alert(data.error || 'Failed to load session details');
            }
        } catch (error) {
            console.error('Error loading session details:', error);
            alert('An error occurred. Please try again.');
        }
    }
});