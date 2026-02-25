/**
 * DevOps Learning Progress Tracker
 * 
 * Tracks user progress across learning paths and tutorials using browser localStorage.
 * Provides progress persistence, analytics, and achievement tracking.
 * 
 * Phase 4: Session-based progress tracking
 */

class ProgressTracker {
    constructor() {
        this.storageKey = 'devops-learning-progress-v1';
        this.badgesKey = 'devops-learning-badges-v1';
        this.analyticsKey = 'devops-learning-analytics-v1';
        this.learningPaths = this.initializeLearningPaths();
        this.tutorials = this.initializeTutorials();
        this.badges = this.initializeBadges();
    }

    /**
     * Initialize learning paths configuration
     */
    initializeLearningPaths() {
        return {
            'new-to-devops': {
                name: '🎓 New to DevOps',
                duration: '60-80 hours',
                steps: [
                    { id: 'programming-fundamentals', name: 'Programming Fundamentals', order: 1 },
                    { id: 'docker-essentials', name: 'Docker Essentials', order: 2 },
                    { id: 'networking-essentials', name: 'Networking Essentials', order: 3 },
                    { id: 'kubernetes-essentials', name: 'Kubernetes Essentials', order: 4 }
                ]
            },
            'career-transition': {
                name: '💼 Career Transition',
                duration: '70-90 hours',
                steps: [
                    { id: 'aws-essentials', name: 'AWS Essentials', order: 1 },
                    { id: 'database-essentials', name: 'Database Essentials', order: 2 },
                    { id: 'docker-essentials', name: 'Docker Essentials', order: 3 },
                    { id: 'kubernetes-essentials', name: 'Kubernetes Essentials', order: 4 },
                    { id: 'capstone-projects', name: 'Capstone Projects', order: 5 }
                ]
            },
            'cka-preparation': {
                name: '🏆 Preparing for CKA',
                duration: '40-50 hours',
                steps: [
                    { id: 'kubernetes-essentials', name: 'Kubernetes Essentials (Full)', order: 1 },
                    { id: 'docker-essentials', name: 'Docker Essentials', order: 2 },
                    { id: 'practice-exam', name: 'Practice Exams', order: 3 },
                    { id: 'final-review', name: 'Final Review', order: 4 }
                ]
            },
            'building-infrastructure': {
                name: '🚀 Building Infrastructure',
                duration: '80-100 hours',
                steps: [
                    { id: 'aws-essentials', name: 'AWS Essentials', order: 1 },
                    { id: 'database-essentials', name: 'Database Essentials', order: 2 },
                    { id: 'docker-essentials', name: 'Docker Essentials', order: 3 },
                    { id: 'kubernetes-essentials', name: 'Kubernetes Essentials', order: 4 },
                    { id: 'observability-essentials', name: 'Observability Essentials', order: 5 },
                    { id: 'capstone-projects', name: 'Capstone Projects', order: 6 }
                ]
            },
            'distributed-systems': {
                name: '🌐 Going Deep on Distributed Systems',
                duration: '75-90 hours',
                steps: [
                    { id: 'networking-essentials', name: 'Networking Essentials', order: 1 },
                    { id: 'distributed-systems', name: 'Distributed Systems', order: 2 },
                    { id: 'kubernetes-essentials', name: 'Kubernetes Essentials', order: 3 },
                    { id: 'observability-essentials', name: 'Observability Essentials', order: 4 },
                    { id: 'capstone-distributed', name: 'Capstone: Distributed Systems', order: 5 }
                ]
            },
            'interview-prep': {
                name: '🎤 Interview Preparation',
                duration: '15-40 hours',
                steps: [
                    { id: 'capstone-projects', name: 'Capstone Projects Overview', order: 1 },
                    { id: 'interview-questions', name: 'System Design Questions', order: 2 },
                    { id: 'practical-problems', name: 'Practical Problems', order: 3 },
                    { id: 'interview-prep', name: 'Final Prep', order: 4 }
                ]
            }
        };
    }

    /**
     * Initialize tutorial metadata
     */
    initializeTutorials() {
        return {
            'programming-fundamentals': {
                name: 'Programming Fundamentals',
                difficulty: 'beginner',
                estimatedHours: 35,
                category: 'FOUNDATIONS'
            },
            'docker-essentials': {
                name: 'Docker Essentials',
                difficulty: 'beginner',
                estimatedHours: 45,
                category: 'FOUNDATIONS'
            },
            'networking-essentials': {
                name: 'Networking Essentials',
                difficulty: 'intermediate',
                estimatedHours: 45,
                category: 'FOUNDATIONS'
            },
            'aws-essentials': {
                name: 'AWS Essentials',
                difficulty: 'intermediate',
                estimatedHours: 45,
                category: 'CLOUD'
            },
            'kubernetes-essentials': {
                name: 'Kubernetes Essentials',
                difficulty: 'intermediate',
                estimatedHours: 55,
                category: 'CLOUD'
            },
            'database-essentials': {
                name: 'Database Essentials',
                difficulty: 'intermediate',
                estimatedHours: 40,
                category: 'DATA'
            },
            'observability-essentials': {
                name: 'Observability Essentials',
                difficulty: 'intermediate',
                estimatedHours: 45,
                category: 'OPERATIONS'
            },
            'distributed-systems': {
                name: 'Distributed Systems',
                difficulty: 'advanced',
                estimatedHours: 45,
                category: 'ADVANCED'
            },
            'capstone-projects': {
                name: 'Capstone Projects',
                difficulty: 'advanced',
                estimatedHours: 40,
                category: 'CAPSTONE'
            },
            'cicd-essentials': {
                name: 'CI/CD Essentials',
                difficulty: 'intermediate',
                estimatedHours: 42,
                category: 'OPERATIONS'
            }
        };
    }

    /**
     * Initialize badges configuration
     */
    initializeBadges() {
        return {
            'first-tutorial': {
                id: 'first-tutorial',
                name: '🚀 Getting Started',
                description: 'Completed your first tutorial',
                icon: '🚀',
                color: '#10b981',
                requirement: { type: 'tutorial-completion', count: 1 }
            },
            'path-starter': {
                id: 'path-starter',
                name: '🎯 Path Starter',
                description: 'Started a learning path',
                icon: '🎯',
                color: '#3b82f6',
                requirement: { type: 'path-started', paths: 1 }
            },
            'path-completer': {
                id: 'path-completer',
                name: '🏆 Path Master',
                description: 'Completed an entire learning path',
                icon: '🏆',
                color: '#f59e0b',
                requirement: { type: 'path-completion', paths: 1 }
            },
            'five-tutorials': {
                id: 'five-tutorials',
                name: '⭐ Momentum',
                description: 'Completed 5 tutorials',
                icon: '⭐',
                color: '#8b5cf6',
                requirement: { type: 'tutorial-completion', count: 5 }
            },
            'all-paths-started': {
                id: 'all-paths-started',
                name: '🌟 Explorer',
                description: 'Started all 6 learning paths',
                icon: '🌟',
                color: '#ec4899',
                requirement: { type: 'path-started', paths: 6 }
            },
            'cka-ready': {
                id: 'cka-ready',
                name: '📜 CKA Ready',
                description: 'Completed CKA preparation path',
                icon: '📜',
                color: '#06b6d4',
                requirement: { type: 'path-completion', pathId: 'cka-preparation' }
            },
            'week-warrior': {
                id: 'week-warrior',
                name: '⚡ Week Warrior',
                description: 'Logged in for 7 consecutive days',
                icon: '⚡',
                color: '#ef4444',
                requirement: { type: 'streak', days: 7 }
            },
            'knowledge-architect': {
                id: 'knowledge-architect',
                name: '🏗️ Knowledge Architect',
                description: 'Completed 3 learning paths',
                icon: '🏗️',
                color: '#14b8a6',
                requirement: { type: 'path-completion', paths: 3 }
            }
        };
    }

    /**
     * Mark a tutorial as visited/started
     */
    visitTutorial(tutorialId, timeSpent = 0) {
        const progress = this.getProgress();
        const now = new Date().toISOString();

        if (!progress.tutorials) progress.tutorials = {};
        if (!progress.tutorials[tutorialId]) {
            progress.tutorials[tutorialId] = {
                visitCount: 0,
                firstVisit: now,
                completed: false,
                timeSpent: 0,
                lastVisit: now,
                sessions: []
            };
        }

        progress.tutorials[tutorialId].visitCount++;
        progress.tutorials[tutorialId].lastVisit = now;
        progress.tutorials[tutorialId].timeSpent += timeSpent;
        progress.tutorials[tutorialId].sessions.push({
            date: now,
            duration: timeSpent
        });

        this.saveProgress(progress);
        this.checkBadgeAchievement();

        return progress.tutorials[tutorialId];
    }

    /**
     * Mark a tutorial as completed
     */
    completeTutorial(tutorialId) {
        const progress = this.getProgress();
        const tutorial = progress.tutorials?.[tutorialId];

        if (tutorial) {
            tutorial.completed = true;
            tutorial.completedDate = new Date().toISOString();
            this.saveProgress(progress);
            this.checkBadgeAchievement();

            // Track in analytics
            this.trackEvent('tutorial-completed', {
                tutorialId,
                timeSpent: tutorial.timeSpent,
                visitCount: tutorial.visitCount
            });

            return true;
        }
        return false;
    }

    /**
     * Enroll user in a learning path
     */
    enrollPath(pathId) {
        const progress = this.getProgress();

        if (!progress.paths) progress.paths = {};
        if (!progress.paths[pathId]) {
            progress.paths[pathId] = {
                enrolled: true,
                enrolledDate: new Date().toISOString(),
                currentStep: 0,
                completedSteps: [],
                completedDate: null,
                progress: 0
            };
        }

        this.saveProgress(progress);
        this.checkBadgeAchievement();

        return progress.paths[pathId];
    }

    /**
     * Mark a path step as completed
     */
    completePathStep(pathId, stepIndex) {
        const progress = this.getProgress();

        if (progress.paths?.[pathId]) {
            const path = progress.paths[pathId];
            if (!path.completedSteps.includes(stepIndex)) {
                path.completedSteps.push(stepIndex);
            }
            path.currentStep = Math.max(path.currentStep, stepIndex + 1);

            // Calculate path progress percentage
            const totalSteps = this.learningPaths[pathId].steps.length;
            path.progress = Math.round((path.completedSteps.length / totalSteps) * 100);

            // Check if path is complete
            if (path.completedSteps.length === totalSteps) {
                path.completedDate = new Date().toISOString();
            }

            this.saveProgress(progress);
            this.checkBadgeAchievement();

            this.trackEvent('path-step-completed', {
                pathId,
                stepIndex,
                pathProgress: path.progress
            });

            return path;
        }
        return null;
    }

    /**
     * Get current progress
     */
    getProgress() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            return stored ? JSON.parse(stored) : this.getDefaultProgress();
        } catch {
            return this.getDefaultProgress();
        }
    }

    /**
     * Get default progress structure
     */
    getDefaultProgress() {
        return {
            userId: this.generateUserId(),
            startDate: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            tutorials: {},
            paths: {},
            totalTimeSpent: 0,
            streakDays: 0,
            lastActivityDate: null
        };
    }

    /**
     * Save progress to localStorage
     */
    saveProgress(progress) {
        progress.lastUpdated = new Date().toISOString();
        localStorage.setItem(this.storageKey, JSON.stringify(progress));
    }

    /**
     * Check and award badges
     */
    checkBadgeAchievement() {
        const progress = this.getProgress();
        const badges = this.getAchievedBadges();
        const newBadges = [];

        Object.values(this.badges).forEach(badge => {
            if (!badges.includes(badge.id) && this.isBadgeEarned(badge, progress)) {
                badges.push(badge.id);
                newBadges.push(badge);
            }
        });

        this.saveAchievedBadges(badges);
        return newBadges;
    }

    /**
     * Check if badge requirements are met
     */
    isBadgeEarned(badge, progress) {
        const req = badge.requirement;

        switch (req.type) {
            case 'tutorial-completion':
                const completedTutorials = Object.values(progress.tutorials || {}).filter(t => t.completed).length;
                return completedTutorials >= req.count;

            case 'path-started':
                const startedPaths = Object.keys(progress.paths || {}).length;
                return startedPaths >= req.paths;

            case 'path-completion':
                if (req.pathId) {
                    return progress.paths?.[req.pathId]?.completedDate !== null;
                }
                const completedPaths = Object.values(progress.paths || {})
                    .filter(p => p.completedDate !== null).length;
                return completedPaths >= req.paths;

            case 'streak':
                return progress.streakDays >= req.days;

            default:
                return false;
        }
    }

    /**
     * Get achieved badges
     */
    getAchievedBadges() {
        try {
            const stored = localStorage.getItem(this.badgesKey);
            return stored ? JSON.parse(stored) : [];
        } catch {
            return [];
        }
    }

    /**
     * Save achieved badges
     */
    saveAchievedBadges(badges) {
        localStorage.setItem(this.badgesKey, JSON.stringify(badges));
    }

    /**
     * Get badge details
     */
    getBadgeDetails(badgeId) {
        return this.badges[badgeId] || null;
    }

    /**
     * Track analytics event
     */
    trackEvent(eventType, data) {
        try {
            const analytics = JSON.parse(localStorage.getItem(this.analyticsKey) || '{"events":[]}');
            analytics.events.push({
                type: eventType,
                timestamp: new Date().toISOString(),
                data
            });
            localStorage.setItem(this.analyticsKey, JSON.stringify(analytics));
        } catch (e) {
            console.error('Failed to track event:', e);
        }
    }

    /**
     * Get analytics summary
     */
    getAnalyticsSummary() {
        try {
            const analytics = JSON.parse(localStorage.getItem(this.analyticsKey) || '{"events":[]}');
            const progress = this.getProgress();

            const completedTutorials = Object.values(progress.tutorials || {}).filter(t => t.completed);
            const completedPaths = Object.values(progress.paths || {}).filter(p => p.completedDate !== null);

            let totalTimeSpent = 0;
            Object.values(progress.tutorials || {}).forEach(t => {
                totalTimeSpent += t.timeSpent || 0;
            });

            return {
                totalTutorialsCompleted: completedTutorials.length,
                totalPathsCompleted: completedPaths.length,
                totalTimeSpent: Math.round(totalTimeSpent / 3600), // Convert to hours
                badgesEarned: this.getAchievedBadges().length,
                accountAge: this.getDaysSinceStart(progress.startDate),
                longestStreak: this.calculateLongestStreak(analytics),
                mostRecentActivity: progress.lastActivityDate,
                tutorials: progress.tutorials,
                paths: progress.paths,
                rawEvents: analytics.events
            };
        } catch (e) {
            console.error('Failed to get analytics:', e);
            return null;
        }
    }

    /**
     * Calculate longest streak
     */
    calculateLongestStreak(analytics) {
        const dates = new Set();
        analytics.events?.forEach(e => {
            const date = new Date(e.timestamp).toDateString();
            dates.add(date);
        });

        if (dates.size === 0) return 0;

        const sorted = Array.from(dates).map(d => new Date(d)).sort((a, b) => a - b);
        let maxStreak = 1;
        let currentStreak = 1;

        for (let i = 1; i < sorted.length; i++) {
            const dayDiff = (sorted[i] - sorted[i - 1]) / (1000 * 60 * 60 * 24);
            if (dayDiff === 1) {
                currentStreak++;
                maxStreak = Math.max(maxStreak, currentStreak);
            } else if (dayDiff > 1) {
                currentStreak = 1;
            }
        }

        return maxStreak;
    }

    /**
     * Get days since start
     */
    getDaysSinceStart(startDate) {
        const start = new Date(startDate);
        const now = new Date();
        return Math.floor((now - start) / (1000 * 60 * 60 * 24));
    }

    /**
     * Generate unique user ID
     */
    generateUserId() {
        return `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Clear all progress (for testing)
     */
    clearAllProgress() {
        localStorage.removeItem(this.storageKey);
        localStorage.removeItem(this.badgesKey);
        localStorage.removeItem(this.analyticsKey);
    }

    /**
     * Export progress as JSON
     */
    exportProgress() {
        return {
            progress: this.getProgress(),
            badges: this.getAchievedBadges(),
            analytics: this.getAnalyticsSummary()
        };
    }
}

// Initialize globally
window.progressTracker = new ProgressTracker();
