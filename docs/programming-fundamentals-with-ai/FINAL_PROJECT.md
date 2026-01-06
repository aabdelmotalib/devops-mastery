# Final Project: Build a Todo List Application

Now it's time to apply **everything** you've learned.

You'll build a complete Todo List application that:
- Stores todos with title, description, and completion status
- Allows adding, removing, and marking todos complete
- Can save/load from file
- Handles errors gracefully
- Is well-organized and documented

---

## Requirements

### **Functional Requirements**

1. **Add todo** - User can create a new todo
2. **List todos** - Show all todos with status
3. **Mark complete** - Toggle a todo as done/not done
4. **Delete todo** - Remove a todo
5. **Persistence** - Save to file, load from file
6. **Search** - Find todos by keyword
7. **Statistics** - Show completion statistics

### **Non-Functional Requirements**

1. **Clean code** - Readable, well-named, documented
2. **Error handling** - Handle invalid input gracefully
3. **Architecture** - Separate concerns (data, logic, UI)
4. **Testing** - Test main functions

---

## Part 1: Design (Plan Before Coding!)

### **Data Structure**

```
Todo:
  - id (unique identifier)
  - title (required, string)
  - description (optional, string)
  - completed (boolean, default False)
  - created_date (datetime)
  - due_date (optional, datetime)

Storage:
  - JSON file to persist todos
```

### **Architecture**

```
todo_app/
├── main.py              # CLI interface
├── todo.py              # Todo class
├── todo_manager.py      # Business logic
├── storage.py           # File I/O
└── todos.json           # Data file
```

### **Components**

1. **Todo class** - Represents a single todo
2. **TodoManager class** - Manages list of todos (add, delete, search, etc.)
3. **Storage class** - Handles saving/loading from file
4. **CLI** - User interface (command-line menu)

---

## Part 2: Implementation

### **Step 1: Todo Class**

```python
# todo.py
from datetime import datetime
from typing import Optional

class Todo:
    """Represents a single todo item"""
    
    def __init__(self, id: int, title: str, description: str = "", 
                 due_date: Optional[str] = None):
        """
        Create a new todo
        
        Args:
            id: Unique identifier
            title: Todo title (required)
            description: Longer description (optional)
            due_date: Due date in format YYYY-MM-DD (optional)
        
        Raises:
            ValueError: If title is empty
        """
        if not title.strip():
            raise ValueError("Title cannot be empty")
        
        self.id = id
        self.title = title
        self.description = description
        self.completed = False
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.due_date = due_date
    
    def toggle_completed(self):
        """Mark as complete if not, incomplete if complete"""
        self.completed = not self.completed
    
    def to_dict(self):
        """Convert to dictionary for JSON storage"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_date": self.created_date,
            "due_date": self.due_date
        }
    
    @staticmethod
    def from_dict(data: dict):
        """Create Todo from dictionary"""
        todo = Todo(data["id"], data["title"], data["description"], 
                   data.get("due_date"))
        todo.completed = data.get("completed", False)
        todo.created_date = data.get("created_date", "")
        return todo
    
    def __str__(self):
        """String representation"""
        status = "✓" if self.completed else "✗"
        return f"[{status}] {self.id}: {self.title}"
    
    def __repr__(self):
        """For debugging"""
        return f"Todo({self.id}, '{self.title}', {self.completed})"
```

### **Step 2: Storage Class**

```python
# storage.py
import json
from pathlib import Path
from typing import List, Dict

class Storage:
    """Handles saving and loading todos from file"""
    
    def __init__(self, filename: str = "todos.json"):
        self.filename = filename
        self.filepath = Path(filename)
    
    def load(self) -> List[Dict]:
        """
        Load todos from file
        
        Returns:
            List of todo dictionaries
        """
        if not self.filepath.exists():
            return []
        
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Could not parse todos file")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []
    
    def save(self, todos: List[Dict]) -> bool:
        """
        Save todos to file
        
        Args:
            todos: List of todo dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.filepath, "w") as f:
                json.dump(todos, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
```

### **Step 3: TodoManager Class**

```python
# todo_manager.py
from todo import Todo
from storage import Storage
from typing import List, Optional

class TodoManager:
    """Manages todos and business logic"""
    
    def __init__(self, storage: Storage):
        """Initialize with storage backend"""
        self.storage = storage
        self.todos = []
        self.next_id = 1
        self.load_todos()
    
    def load_todos(self):
        """Load todos from storage"""
        data = self.storage.load()
        self.todos = [Todo.from_dict(item) for item in data]
        
        if self.todos:
            self.next_id = max(todo.id for todo in self.todos) + 1
    
    def add_todo(self, title: str, description: str = "", 
                due_date: Optional[str] = None) -> Todo:
        """
        Add a new todo
        
        Args:
            title: Todo title
            description: Optional description
            due_date: Optional due date
        
        Returns:
            Created Todo object
        
        Raises:
            ValueError: If title is invalid
        """
        todo = Todo(self.next_id, title, description, due_date)
        self.todos.append(todo)
        self.next_id += 1
        self.save()
        return todo
    
    def get_todo(self, todo_id: int) -> Optional[Todo]:
        """Get todo by ID"""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def update_todo(self, todo_id: int, title: str = None, 
                   description: str = None) -> bool:
        """Update todo details"""
        todo = self.get_todo(todo_id)
        if not todo:
            return False
        
        if title:
            todo.title = title
        if description is not None:
            todo.description = description
        
        self.save()
        return True
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo by ID"""
        todo = self.get_todo(todo_id)
        if todo:
            self.todos.remove(todo)
            self.save()
            return True
        return False
    
    def toggle_complete(self, todo_id: int) -> bool:
        """Mark a todo as complete/incomplete"""
        todo = self.get_todo(todo_id)
        if todo:
            todo.toggle_completed()
            self.save()
            return True
        return False
    
    def search(self, keyword: str) -> List[Todo]:
        """Find todos matching keyword"""
        keyword = keyword.lower()
        return [todo for todo in self.todos 
                if keyword in todo.title.lower() 
                or keyword in todo.description.lower()]
    
    def get_all(self) -> List[Todo]:
        """Get all todos"""
        return self.todos
    
    def get_completed(self) -> List[Todo]:
        """Get completed todos"""
        return [todo for todo in self.todos if todo.completed]
    
    def get_incomplete(self) -> List[Todo]:
        """Get incomplete todos"""
        return [todo for todo in self.todos if not todo.completed]
    
    def get_statistics(self) -> Dict:
        """Get statistics about todos"""
        total = len(self.todos)
        completed = len(self.get_completed())
        incomplete = len(self.get_incomplete())
        
        return {
            "total": total,
            "completed": completed,
            "incomplete": incomplete,
            "completion_percentage": (completed / total * 100) if total > 0 else 0
        }
    
    def save(self):
        """Save todos to storage"""
        data = [todo.to_dict() for todo in self.todos]
        self.storage.save(data)
```

### **Step 4: CLI Interface**

```python
# main.py
from todo_manager import TodoManager
from storage import Storage

def print_menu():
    """Display main menu"""
    print("\n=== Todo List ===")
    print("1. Add todo")
    print("2. List all todos")
    print("3. Mark complete")
    print("4. Delete todo")
    print("5. Search todos")
    print("6. Show statistics")
    print("7. Exit")
    print()

def display_todos(todos):
    """Format and display todos"""
    if not todos:
        print("No todos to display")
        return
    
    for todo in todos:
        status = "✓" if todo.completed else "○"
        print(f"  [{status}] #{todo.id}: {todo.title}")
        if todo.description:
            print(f"       {todo.description}")
        if todo.due_date:
            print(f"       Due: {todo.due_date}")

def add_todo_interactive(manager):
    """Interactive todo creation"""
    title = input("Todo title: ").strip()
    if not title:
        print("Title cannot be empty")
        return
    
    description = input("Description (optional): ").strip()
    due_date = input("Due date YYYY-MM-DD (optional): ").strip()
    
    try:
        manager.add_todo(title, description if description else "", 
                        due_date if due_date else None)
        print("✓ Todo added!")
    except ValueError as e:
        print(f"✗ Error: {e}")

def mark_complete_interactive(manager):
    """Mark todo as complete"""
    try:
        todo_id = int(input("Todo ID to toggle: "))
        if manager.toggle_complete(todo_id):
            todo = manager.get_todo(todo_id)
            status = "completed" if todo.completed else "incomplete"
            print(f"✓ Todo marked as {status}")
        else:
            print("✗ Todo not found")
    except ValueError:
        print("✗ Invalid ID")

def delete_todo_interactive(manager):
    """Delete a todo"""
    try:
        todo_id = int(input("Todo ID to delete: "))
        if manager.delete_todo(todo_id):
            print("✓ Todo deleted!")
        else:
            print("✗ Todo not found")
    except ValueError:
        print("✗ Invalid ID")

def search_interactive(manager):
    """Search todos"""
    keyword = input("Search keyword: ").strip()
    if not keyword:
        print("Search term cannot be empty")
        return
    
    results = manager.search(keyword)
    print(f"\nFound {len(results)} result(s):")
    display_todos(results)

def show_statistics(manager):
    """Display statistics"""
    stats = manager.get_statistics()
    print("\n=== Statistics ===")
    print(f"Total: {stats['total']}")
    print(f"Completed: {stats['completed']}")
    print(f"Incomplete: {stats['incomplete']}")
    print(f"Progress: {stats['completion_percentage']:.1f}%")

def main():
    """Main program loop"""
    storage = Storage("todos.json")
    manager = TodoManager(storage)
    
    print("Welcome to Todo List!")
    
    while True:
        print_menu()
        choice = input("Choose option (1-7): ").strip()
        
        if choice == "1":
            add_todo_interactive(manager)
        
        elif choice == "2":
            todos = manager.get_all()
            print("\n=== All Todos ===")
            display_todos(todos)
        
        elif choice == "3":
            mark_complete_interactive(manager)
        
        elif choice == "4":
            delete_todo_interactive(manager)
        
        elif choice == "5":
            search_interactive(manager)
        
        elif choice == "6":
            show_statistics(manager)
        
        elif choice == "7":
            print("Goodbye!")
            break
        
        else:
            print("✗ Invalid option")

if __name__ == "__main__":
    main()
```

---

## Part 3: Testing

```python
# test_todo_manager.py
from todo_manager import TodoManager
from storage import Storage
from pathlib import Path

def test_add_todo():
    """Test adding todos"""
    storage = Storage("test_todos.json")
    manager = TodoManager(storage)
    
    # Add todo
    todo = manager.add_todo("Test todo", "Description")
    assert todo is not None
    assert todo.title == "Test todo"
    assert not todo.completed
    print("✓ test_add_todo passed")

def test_toggle_complete():
    """Test marking complete"""
    storage = Storage("test_todos.json")
    manager = TodoManager(storage)
    
    todo = manager.add_todo("Task")
    assert not todo.completed
    
    manager.toggle_complete(todo.id)
    updated = manager.get_todo(todo.id)
    assert updated.completed
    print("✓ test_toggle_complete passed")

def test_search():
    """Test search functionality"""
    storage = Storage("test_todos.json")
    manager = TodoManager(storage)
    
    manager.add_todo("Buy milk")
    manager.add_todo("Buy bread")
    manager.add_todo("Fix bug")
    
    results = manager.search("buy")
    assert len(results) == 2
    print("✓ test_search passed")

def test_delete():
    """Test deletion"""
    storage = Storage("test_todos.json")
    manager = TodoManager(storage)
    
    todo = manager.add_todo("Temp todo")
    assert len(manager.get_all()) == 1
    
    manager.delete_todo(todo.id)
    assert len(manager.get_all()) == 0
    print("✓ test_delete passed")

def cleanup():
    """Clean up test files"""
    Path("test_todos.json").unlink(missing_ok=True)

if __name__ == "__main__":
    try:
        test_add_todo()
        test_toggle_complete()
        test_search()
        test_delete()
        print("\n✓ All tests passed!")
    finally:
        cleanup()
```

---

## Part 4: Improvements

After the basic version works, consider adding:

### **Easy**
- Filter by date
- Show todos due soon
- Priority levels
- Color output

### **Intermediate**
- Recurring todos
- Tags/categories
- Export to CSV
- Undo/redo

### **Advanced**
- Web interface
- Database instead of JSON
- Sync across devices
- Collaborative todos

---

## Submission Checklist

Before considering this done:

- [ ] Code is organized (separate files, clear structure)
- [ ] Functions have docstrings
- [ ] Variable names are clear
- [ ] Error handling is present
- [ ] Code is tested
- [ ] README exists explaining how to use
- [ ] All requirements are implemented
- [ ] Code is refactored (no obvious improvements)

---

## Key Lessons Applied

✅ **Decomposition** - Split into TodoManager, Storage, CLI

✅ **Separation of Concerns** - Data, logic, UI are separate

✅ **Error Handling** - Invalid input is caught and handled

✅ **Testing** - Core functions are tested

✅ **Documentation** - Docstrings explain what functions do

✅ **Naming** - Clear, descriptive variable and function names

✅ **Persistence** - Todos are saved and loaded

✅ **Architecture** - Well-organized, not everything in one file

---

## Next Steps

Congratulations! You've built a complete application.

Now:
- Add features from the "Improvements" section
- Build something similar for a different problem
- Refactor for better organization
- Share your code and ask for feedback

You're a programmer now. Keep building!

