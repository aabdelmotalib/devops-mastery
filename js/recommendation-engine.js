/**
 * DevOps Learning Recommendation Engine
 * 
 * Provides intelligent recommendations for next modules, learning paths,
 * and adaptive difficulty suggestions based on user progress.
 * 
 * Phase 4: AI-powered recommendations
 */

class RecommendationEngine {
    constructor(progressTracker) {
        this.tracker = progressTracker;
        this.weights = {
            pathProgression: 0.4,
            timeAvailability: 0.2,
            difficulty: 0.2,
            relatedSkills: 0.2
        };
    }

    /**
     * Get recommended next step in current path
     */
    getNextPathStep(pathId) {
        const progress = this.tracker.getProgress();
        const pathData = progress.paths?.[pathId];

        if (!pathData) return null;

        const pathConfig = this.tracker.learningPaths[pathId];
        const nextStepIndex = pathData.currentStep;

        if (nextStepIndex >= pathConfig.steps.length) {
            return {
                type: 'path-complete',
                message: '🎉 You\'ve completed this learning path!',
                nextOption: this.recommendNextPath(pathId)
            };
        }

        const nextStep = pathConfig.steps[nextStepIndex];
        return {
            type: 'next-step',
            step: nextStep,
            progress: `${pathData.completedSteps.length + 1}/${pathConfig.steps.length}`,
            url: this.getTutorialUrl(nextStep.id)
        };
    }

    /**
     * Recommend best learning path for user
     */
    recommendPath() {
        const progress = this.tracker.getProgress();
        const recommendations = [];

        // Score each path
        Object.entries(this.tracker.learningPaths).forEach(([pathId, pathConfig]) => {
            // Check if already completed
            if (progress.paths?.[pathId]?.completedDate) {
                return;
            }

            let score = 100;

            // Prerequisite check
            const prerequisites = this.getPathPrerequisites(pathId);
            for (const prereq of prerequisites) {
                if (!progress.tutorials?.[prereq]?.completed) {
                    score -= 30;
                }
            }

            // Path progression
            const currentProgress = progress.paths?.[pathId]?.progress || 0;
            if (currentProgress > 0) {
                score += currentProgress * 0.5; // Boost in-progress paths
            }

            // Time availability estimate
            const tutorialsCompleted = Object.values(progress.tutorials || {}).filter(t => t.completed).length;
            if (tutorialsCompleted === 0) {
                score += 20; // Beginner boost for first-time users
            }

            // Category diversity
            const pathCategories = new Set();
            pathConfig.steps.forEach(step => {
                const tutorial = this.tracker.tutorials[step.id];
                if (tutorial) pathCategories.add(tutorial.category);
            });

            if (pathCategories.size >= 3) {
                score += 10; // Diversity bonus
            }

            recommendations.push({
                pathId,
                name: pathConfig.name,
                score,
                duration: pathConfig.duration,
                progress: currentProgress,
                nextTutorial: this.getNextPathTutorial(pathId),
                reason: this.explainRecommendation(pathId, currentProgress, prerequisites, progress)
            });
        });

        // Sort by score
        recommendations.sort((a, b) => b.score - a.score);
        return recommendations;
    }

    /**
     * Recommend next tutorial based on progress
     */
    recommendNextTutorial() {
        const progress = this.tracker.getProgress();
        const recommendations = [];

        // Check enrolled paths
        const enrolledPaths = Object.entries(progress.paths || {})
            .filter(([_, path]) => path.enrolled && !path.completedDate);

        // Priority 1: Continue in-progress paths
        for (const [pathId, pathData] of enrolledPaths) {
            if (pathData.progress < 100) {
                const nextStep = this.getNextPathStep(pathId);
                if (nextStep?.type === 'next-step') {
                    recommendations.push({
                        priority: 1,
                        pathId,
                        tutorialId: nextStep.step.id,
                        name: `Continue: ${nextStep.step.name} (${pathId})`,
                        reason: 'Complete your current learning path',
                        progress: nextStep.progress
                    });
                }
            }
        }

        // Priority 2: Start recommended path if no path in progress
        if (recommendations.length === 0) {
            const recommended = this.recommendPath();
            if (recommended.length > 0) {
                const path = recommended[0];
                if (path.nextTutorial) {
                    recommendations.push({
                        priority: 2,
                        pathId: path.pathId,
                        tutorialId: path.nextTutorial,
                        name: `Start: ${path.name}`,
                        reason: path.reason,
                        score: path.score
                    });
                }
            }
        }

        // Priority 3: Related tutorials
        if (recommendations.length === 0) {
            const related = this.getRelatedTutorials();
            recommendations.push(...related);
        }

        return recommendations[0] || null;
    }

    /**
     * Get related tutorials based on completed work
     */
    getRelatedTutorials(limit = 5) {
        const progress = this.tracker.getProgress();
        const completed = Object.keys(progress.tutorials || {})
            .filter(id => progress.tutorials[id].completed);

        if (completed.length === 0) {
            return this.getBeginnerRecommendations();
        }

        const recommendations = [];
        const completedCategories = new Set();
        const completedDifficulties = new Set();

        // Analyze completed tutorials
        completed.forEach(id => {
            const tutorial = this.tracker.tutorials[id];
            if (tutorial) {
                completedCategories.add(tutorial.category);
                completedDifficulties.add(tutorial.difficulty);
            }
        });

        // Find similar tutorials not completed
        Object.entries(this.tracker.tutorials).forEach(([id, tutorial]) => {
            if (!progress.tutorials?.[id]?.completed) {
                let score = 0;

                // Same category bonus
                if (completedCategories.has(tutorial.category)) {
                    score += 40;
                }

                // Progressive difficulty
                if (this.isDifficultyProgressable(tutorial.difficulty, completedDifficulties)) {
                    score += 30;
                }

                // Avoid huge jumps in difficulty
                if (!this.isDifficultyTooHard(tutorial.difficulty, completedDifficulties)) {
                    score += 20;
                }

                if (score > 0) {
                    recommendations.push({
                        tutorialId: id,
                        name: tutorial.name,
                        difficulty: tutorial.difficulty,
                        category: tutorial.category,
                        score
                    });
                }
            }
        });

        recommendations.sort((a, b) => b.score - a.score);
        return recommendations.slice(0, limit);
    }

    /**
     * Get beginner recommendations for new users
     */
    getBeginnerRecommendations() {
        return [
            {
                tutorialId: 'programming-fundamentals',
                name: 'Programming Fundamentals',
                reason: 'Perfect starting point for new developers',
                priority: 1
            },
            {
                tutorialId: 'docker-essentials',
                name: 'Docker Essentials',
                reason: 'Foundation for modern DevOps',
                priority: 2
            },
            {
                tutorialId: 'aws-essentials',
                name: 'AWS Essentials',
                reason: 'Essential cloud infrastructure knowledge',
                priority: 3
            }
        ];
    }

    /**
     * Check if difficulty is progressable
     */
    isDifficultyProgressable(newDifficulty, completedDifficulties) {
        if (completedDifficulties.has('advanced')) return true; // Advanced users can do anything
        if (completedDifficulties.has('intermediate')) {
            return newDifficulty === 'intermediate' || newDifficulty === 'advanced';
        }
        return newDifficulty === 'beginner' || newDifficulty === 'intermediate';
    }

    /**
     * Check if difficulty is too hard
     */
    isDifficultyTooHard(newDifficulty, completedDifficulties) {
        if (completedDifficulties.size === 0) return newDifficulty === 'advanced';
        if (completedDifficulties.has('advanced')) return false;
        if (completedDifficulties.has('intermediate')) {
            return newDifficulty === 'advanced' && completedDifficulties.size < 2;
        }
        return newDifficulty === 'advanced' || newDifficulty === 'intermediate';
    }

    /**
     * Get tutorial URL
     */
    getTutorialUrl(tutorialId) {
        const urlMap = {
            'programming-fundamentals': '../programming-fundamentals-with-ai/START_HERE.md',
            'docker-essentials': '../docker-essentials-tutorial/START_HERE.md',
            'networking-essentials': '../networking-essentials-tutorial/START_HERE.md',
            'aws-essentials': '../aws-essentials-tutorial/START_HERE.md',
            'kubernetes-essentials': '../kubernetes-essentials-tutorial/START_HERE.md',
            'database-essentials': '../database-essentials-tutorial/START_HERE.md',
            'observability-essentials': '../observability-essentials-tutorial/START_HERE.md',
            'distributed-systems': '../distributed-systems-tutorial/START_HERE.md',
            'capstone-projects': '../devops-capstone-projects/README_START_HERE.md'
        };
        return urlMap[tutorialId] || '#';
    }

    /**
     * Get path prerequisites
     */
    getPathPrerequisites(pathId) {
        const prereqMap = {
            'cka-preparation': ['docker-essentials'],
            'kubernetes-essentials': ['docker-essentials'],
            'building-infrastructure': ['aws-essentials'],
            'distributed-systems': ['networking-essentials'],
            'career-transition': ['aws-essentials', 'docker-essentials']
        };
        return prereqMap[pathId] || [];
    }

    /**
     * Get next tutorial in path
     */
    getNextPathTutorial(pathId) {
        const pathConfig = this.tracker.learningPaths[pathId];
        const progress = this.tracker.getProgress();
        const pathData = progress.paths?.[pathId];

        if (!pathData || !pathConfig) return null;

        const nextStepIndex = pathData.currentStep;
        if (nextStepIndex < pathConfig.steps.length) {
            return pathConfig.steps[nextStepIndex].id;
        }
        return null;
    }

    /**
     * Explain why a path is recommended
     */
    explainRecommendation(pathId, currentProgress, prerequisites, progress) {
        const reasons = [];

        if (currentProgress > 0) {
            reasons.push(`You're ${currentProgress}% through this path`);
        } else if (prerequisites.every(p => progress.tutorials?.[p]?.completed)) {
            reasons.push('You have all prerequisites');
        } else {
            reasons.push('Recommended for your skill level');
        }

        return reasons.join(' • ');
    }

    /**
     * Get adaptive difficulty recommendations
     */
    getAdaptiveDifficultyPath(currentDifficulty) {
        const next = {
            'beginner': 'intermediate',
            'intermediate': 'advanced',
            'advanced': 'advanced' // Stay advanced
        };

        const nextDifficulty = next[currentDifficulty] || currentDifficulty;

        const suitable = Object.entries(this.tracker.tutorials)
            .filter(([_, t]) => t.difficulty === nextDifficulty)
            .map(([id, t]) => ({
                tutorialId: id,
                name: t.name,
                difficulty: t.difficulty,
                hours: t.estimatedHours
            }));

        return suitable;
    }

    /**
     * Get skill gaps analysis
     */
    getSkillGaps() {
        const progress = this.tracker.getProgress();
        const completed = Object.values(progress.tutorials || {})
            .filter(t => t.completed);

        const categories = {};
        completed.forEach(t => {
            const tutorial = this.tracker.tutorials[Object.keys(this.tracker.tutorials)
                .find(id => this.tracker.tutorials[id].name === t.name)];
            if (tutorial) {
                categories[tutorial.category] = (categories[tutorial.category] || 0) + 1;
            }
        });

        const allCategories = ['FOUNDATIONS', 'CLOUD', 'OPERATIONS', 'DATA', 'ADVANCED', 'CAPSTONE'];
        const gaps = allCategories.filter(cat => !categories[cat]);

        return {
            completedCategories: Object.keys(categories),
            missingCategories: gaps,
            suggestions: gaps.map(gap => this.getCategoryRecommendation(gap))
        };
    }

    /**
     * Get recommendation for missing category
     */
    getCategoryRecommendation(category) {
        const recommendations = {
            'FOUNDATIONS': 'Programming Fundamentals, Docker Essentials, Networking Essentials',
            'CLOUD': 'AWS Essentials, Kubernetes Essentials',
            'OPERATIONS': 'CI/CD Essentials, Observability Essentials',
            'DATA': 'Database Essentials',
            'ADVANCED': 'Distributed Systems, Modern DevOps Patterns',
            'CAPSTONE': 'Capstone Projects'
        };
        return recommendations[category] || '';
    }
}

// Initialize globally
window.recommendationEngine = null;
if (window.progressTracker) {
    window.recommendationEngine = new RecommendationEngine(window.progressTracker);
}
