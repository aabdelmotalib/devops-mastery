# Module 6: Practical Examples & Projects

Theory is important. But **programming is learned by doing**.

This module walks you through concrete projects, showing you the **thinking process**, design decisions, and how to apply everything you've learned.

---

## Project 1: Grade Tracker

A simple program to track and analyze student grades.

### **Requirements**

1. Store student names and their grades
2. Calculate average grade for each student
3. Calculate class average
4. Identify students who need help (below 70%)
5. Generate a report

### **Step 1: Understand the Problem**

Questions to ask yourself:
- What data do I need to store?
- What operations do I need to perform?
- How will users interact with this?
- What could go wrong?

### **Step 2: Design (Before Coding)**

```
Data Structure:
- List of students
- Each student has:
  - Name (string)
  - Grades (list of numbers)

Operations:
- Add grade for student
- Calculate average for student
- Calculate class average
- Find struggling students
- Print report

Format (simple):
- Command-line interface
- Text-based menu
```

### **Step 3: Pseudocode**

```python
# Pseudocode (not real code, just the logic)

Main program:
1. Load or create grade data
2. Show menu loop:
   - "Add grade"
   - "View student average"
   - "View class average"
   - "View struggling students"
   - "Exit"
3. Based on choice, call appropriate function

Functions:
- add_grade(name, grade)
- get_student_average(name)
- get_class_average()
- get_struggling_students()
- print_report()
```

### **Step 4: Implementation**

```python
class GradeTracker:
    """Tracks and analyzes student grades"""
    
    def __init__(self):
        """Initialize with empty students dictionary"""
        self.students = {}
    
    def add_grade(self, name, grade):
        """Add a grade for a student"""
        if not (0 <= grade <= 100):
            raise ValueError("Grade must be between 0 and 100")
        
        if name not in self.students:
            self.students[name] = []
        
        self.students[name].append(grade)
    
    def get_student_average(self, name):
        """Get average grade for a student"""
        if name not in self.students:
            raise ValueError(f"Student {name} not found")
        
        grades = self.students[name]
        if not grades:
            return 0
        
        return sum(grades) / len(grades)
    
    def get_class_average(self):
        """Get average grade for entire class"""
        all_grades = []
        for grades in self.students.values():
            all_grades.extend(grades)
        
        if not all_grades:
            return 0
        
        return sum(all_grades) / len(all_grades)
    
    def get_struggling_students(self, threshold=70):
        """Get students below threshold grade"""
        struggling = []
        
        for name in self.students:
            average = self.get_student_average(name)
            if average < threshold:
                struggling.append((name, average))
        
        return sorted(struggling, key=lambda x: x[1])
    
    def print_report(self):
        """Print comprehensive report"""
        print("\n=== Grade Report ===\n")
        
        # Individual students
        print("Student Averages:")
        for name in sorted(self.students.keys()):
            avg = self.get_student_average(name)
            print(f"  {name}: {avg:.2f}%")
        
        # Class average
        class_avg = self.get_class_average()
        print(f"\nClass Average: {class_avg:.2f}%")
        
        # Struggling students
        struggling = self.get_struggling_students()
        if struggling:
            print("\nStudents Below 70%:")
            for name, avg in struggling:
                print(f"  {name}: {avg:.2f}%")
        else:
            print("\nAll students above 70%!")


def main():
    """Main program loop"""
    tracker = GradeTracker()
    
    while True:
        print("\n=== Grade Tracker ===")
        print("1. Add grade")
        print("2. View student average")
        print("3. View class average")
        print("4. View struggling students")
        print("5. Print report")
        print("6. Exit")
        
        choice = input("Choose option: ").strip()
        
        if choice == "1":
            name = input("Student name: ").strip()
            try:
                grade = float(input("Grade (0-100): "))
                tracker.add_grade(name, grade)
                print(f"Added grade for {name}")
            except ValueError as e:
                print(f"Error: {e}")
        
        elif choice == "2":
            name = input("Student name: ").strip()
            try:
                avg = tracker.get_student_average(name)
                print(f"{name}'s average: {avg:.2f}%")
            except ValueError as e:
                print(f"Error: {e}")
        
        elif choice == "3":
            avg = tracker.get_class_average()
            print(f"Class average: {avg:.2f}%")
        
        elif choice == "4":
            struggling = tracker.get_struggling_students()
            if struggling:
                print("\nStudents below 70%:")
                for name, avg in struggling:
                    print(f"  {name}: {avg:.2f}%")
            else:
                print("All students above 70%!")
        
        elif choice == "5":
            tracker.print_report()
        
        elif choice == "6":
            print("Goodbye!")
            break
        
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()
```

### **Step 5: Testing**

```python
# Test manually
tracker = GradeTracker()

# Add some grades
tracker.add_grade("Alice", 95)
tracker.add_grade("Alice", 92)
tracker.add_grade("Bob", 65)
tracker.add_grade("Bob", 72)
tracker.add_grade("Carol", 88)

# Test calculations
assert tracker.get_student_average("Alice") == 93.5
assert tracker.get_student_average("Bob") == 68.5
assert tracker.get_class_average() == 82.8  # approximately

# Test struggling
struggling = tracker.get_struggling_students()
assert len(struggling) == 1
assert struggling[0][0] == "Bob"

print("All tests passed!")
```

### **Step 6: Improvements**

What could we add?
- Save/load from file
- Remove grades
- Update grades
- Grade letter conversion (A, B, C, etc.)
- Export report to PDF

---

## Project 2: URL Shortener

A service that converts long URLs to short codes.

### **Requirements**

1. Generate short code from long URL
2. Store mapping (short code → long URL)
3. Retrieve long URL using short code
4. Handle invalid URLs

### **Step 1: Design**

```
Data:
- Dictionary mapping short codes to URLs
- Or database table

Algorithm:
- Take long URL
- Generate unique short code (could be random, or hash-based)
- Store mapping
- Return short code

Issues to handle:
- What if URL already shortened?
- What if short code collision happens?
- What about URL validation?
```

### **Step 2: Implementation**

```python
import hashlib
import string
import random

class URLShortener:
    """Converts long URLs to short codes"""
    
    def __init__(self):
        """Initialize with empty mapping"""
        self.url_map = {}  # short_code → long_url
        self.reverse_map = {}  # long_url → short_code
    
    def _is_valid_url(self, url):
        """Validate URL format"""
        # Simple validation: just check for http(s) and domain
        return url.startswith(('http://', 'https://')) and '.' in url
    
    def _generate_short_code(self, url):
        """Generate a short code for a URL"""
        # Use first 6 characters of hash
        hash_value = hashlib.md5(url.encode()).hexdigest()
        short_code = hash_value[:6]
        
        # If collision, keep adding random characters
        while short_code in self.url_map:
            short_code += random.choice(string.ascii_letters)
        
        return short_code
    
    def shorten(self, url):
        """
        Shorten a URL
        
        Args:
            url: Long URL to shorten
        
        Returns:
            Short code
        
        Raises:
            ValueError: If URL is invalid
        """
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        # Return existing code if already shortened
        if url in self.reverse_map:
            return self.reverse_map[url]
        
        # Generate new code
        short_code = self._generate_short_code(url)
        
        # Store mapping both ways
        self.url_map[short_code] = url
        self.reverse_map[url] = short_code
        
        return short_code
    
    def expand(self, short_code):
        """
        Get original URL from short code
        
        Args:
            short_code: The short code
        
        Returns:
            Original URL
        
        Raises:
            KeyError: If short code doesn't exist
        """
        if short_code not in self.url_map:
            raise KeyError(f"Short code not found: {short_code}")
        
        return self.url_map[short_code]


# Example usage
shortener = URLShortener()

# Shorten URLs
code1 = shortener.shorten("https://www.example.com/very/long/page")
code2 = shortener.shorten("https://github.com/user/repo")

print(f"Short code 1: {code1}")
print(f"Short code 2: {code2}")

# Expand
original = shortener.expand(code1)
print(f"Original: {original}")

# Error handling
try:
    shortener.shorten("not-a-url")
except ValueError as e:
    print(f"Error: {e}")

try:
    shortener.expand("nonexistent")
except KeyError as e:
    print(f"Error: {e}")
```

---

## Project 3: Simple Chat Application

A command-line chat between two people.

### **Requirements**

1. Person A and Person B exchange messages
2. Keep conversation history
3. Display who sent each message
4. Show timestamp

### **Design**

```python
from datetime import datetime

class Message:
    """Represents a single chat message"""
    
    def __init__(self, sender, text):
        self.sender = sender
        self.text = text
        self.timestamp = datetime.now()
    
    def __str__(self):
        time_str = self.timestamp.strftime("%H:%M")
        return f"[{time_str}] {self.sender}: {self.text}"


class Chat:
    """Manages conversation between two people"""
    
    def __init__(self, person_a, person_b):
        self.person_a = person_a
        self.person_b = person_b
        self.messages = []
    
    def send_message(self, sender, text):
        """Add a message to chat"""
        if sender not in (self.person_a, self.person_b):
            raise ValueError(f"Unknown sender: {sender}")
        
        if not text.strip():
            raise ValueError("Message cannot be empty")
        
        message = Message(sender, text)
        self.messages.append(message)
    
    def get_history(self):
        """Get conversation history"""
        return [str(msg) for msg in self.messages]
    
    def print_chat(self):
        """Print formatted conversation"""
        print("\n=== Conversation History ===\n")
        for msg in self.messages:
            print(msg)
        print()


# Usage
chat = Chat("Alice", "Bob")

chat.send_message("Alice", "Hi Bob!")
chat.send_message("Bob", "Hey Alice, how are you?")
chat.send_message("Alice", "I'm doing great!")

chat.print_chat()
```

---

## How to Approach New Problems

### **1. Understand**
Read the problem 2-3 times. Ask:
- What data do I need?
- What operations are needed?
- What could go wrong?

### **2. Design (Don't code yet!)**
Draw it out, write pseudocode:
- What classes/functions do I need?
- How do they interact?
- What's the data structure?

### **3. Start Simple**
Build the simplest version first:
- Get basic functionality working
- Then add features
- Then handle edge cases

### **4. Test as You Go**
After each piece:
- Does it work?
- Does it handle errors?
- Is the output correct?

### **5. Refactor**
Once it works:
- Is it readable?
- Can I simplify?
- Are names clear?
- Is there duplication?

### **6. Add Features**
Only after basic version works:
- File persistence
- Better UI
- More features
- Optimization

---

## Common Project Mistakes

### **Mistake 1: Big Bang Approach**
❌ Try to build everything at once
✅ Build simplest version, add features incrementally

### **Mistake 2: No Design Phase**
❌ Start coding immediately
✅ Spend 15 minutes thinking before writing code

### **Mistake 3: Ignoring Edge Cases**
❌ Code works for happy path, breaks on edge cases
✅ Test with empty input, invalid input, extreme values

### **Mistake 4: No Error Handling**
❌ Code assumes everything will work
✅ Anticipate what could go wrong and handle it

### **Mistake 5: Over-Engineering**
❌ Build a complex system for simple problem
✅ Start simple, add complexity only when needed

---

## Exercises

### Exercise 1: Build Grade Tracker
Implement the GradeTracker from scratch. Add features:
- Ability to remove a grade
- Ability to view all students
- Ability to find highest/lowest grades

### Exercise 2: Extend URL Shortener
Modify the URL shortener:
- Track how many times each link is clicked
- Return most popular links
- Set expiration date for links

### Exercise 3: Chat Features
Extend the chat application:
- Ability to search messages
- Ability to delete messages
- Ability to get messages from specific person
- Message count statistics

### Exercise 4: Combine Projects
Build a system that combines grade tracker + simple storage:
- Save grades to a file
- Load grades from a file
- When user quits, save automatically

---

## Key Takeaways

✅ **Design before coding**

✅ **Start simple, add complexity gradually**

✅ **Test constantly**

✅ **Handle errors and edge cases**

✅ **Refactor once it works**

✅ **Apply all the thinking patterns you learned**

---

## What's Next?

Now it's time to **build something real**—your final project.

→ **[Final Project](../FINAL_PROJECT.md)**

