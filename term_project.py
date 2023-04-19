# Allanis Sumaya - 101308759
# Paolo Casison  - 101384585
import sqlite3
from datetime import datetime
import csv


class ExpenseTracker:

    def save_expenses_to_csv(self, filename):
        cursor = self.conn.execute('''
            SELECT expenses.id, categories.name, expenses.amount, expenses.date
            FROM expenses INNER JOIN categories
            ON expenses.category_id = categories.id
        ''')
        rows = cursor.fetchall()

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'category', 'amount', 'date'])
            writer.writerows(rows)

        print(f"Expenses saved to {filename}!")

    def __init__(self):
        self.conn = sqlite3.connect('expenses.db')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date DATE NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def add_category(self, name):
        self.conn.execute(
                'INSERT INTO categories (name) SELECT LOWER(?) WHERE NOT EXISTS (SELECT 1 FROM categories WHERE LOWER(name) = LOWER(?))',
                (name, name,))
        self.conn.commit()

        if self.conn.total_changes == 0:
            print(f"Category '{name}' already exists!")
        else:
            choice = input(f"Category '{name}' added successfully! Do you want to confirm (y/n)? ")
            if choice.lower() == 'y':
                print("Category added.")
            else:
                self.conn.execute('DELETE FROM categories WHERE name = ?', (name,))
                self.conn.commit()
                print("Category removed.")

    def add_expense(self, category_name=None, amount=None, date=None):
        if category_name is None:
            cursor = self.conn.execute('SELECT name FROM categories ORDER BY name')
            category_names = [row[0] for row in cursor.fetchall()]
            if not category_names:
                print("Category doesn't exist. Please add a category first.")
                return
            for i, name in enumerate(category_names):
                print(f"{i + 1}. {name}")
            choice = input("Please choose a category (1-{}): ".format(len(category_names)))
            try:
                index = int(choice) - 1
                category_name = category_names[index]
            except (ValueError, IndexError):
                print("Invalid choice.")
                return
        try:
            category_id = self.get_category_id(category_name)
            if amount is None:
                amount = float(input("Enter expense amount: "))
            if date is None:
                date_str = input("Enter the date (YYYY-MM-DD): ")
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            self.conn.execute('INSERT INTO expenses (category_id, amount, date) VALUES (?, ?, ?)',
                              (category_id, amount, date))
            self.conn.commit()
            print(f"${amount:.2f} expense for '{category_name}' on {date} added successfully!")
        except sqlite3.IntegrityError:
            print(f"Invalid category '{category_name}'!")
        except ValueError:
            print("Invalid amount or date format!")

    def get_category_id(self, name):
        cursor = self.conn.execute('SELECT id FROM categories WHERE name = ?', (name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            raise sqlite3.IntegrityError(f"Category '{name}' does not exist!")

    def get_monthly_expenses(self, month, year):
        cursor = self.conn.execute('''
            SELECT categories.name, SUM(expenses.amount)
            FROM expenses INNER JOIN categories
            ON expenses.category_id = categories.id
            WHERE strftime('%m', expenses.date) = ? AND strftime('%Y', expenses.date) = ?
            GROUP BY categories.id
        ''', (month, year))
        rows = cursor.fetchall()
        total_expense = sum([row[1] for row in rows])
        print(f"\nMonthly Expenses for {month}/{year}:")
        for row in rows:
            category_name = row[0]
            expense = row[1]
            percentage = expense / total_expense * 100
            print(f"{category_name:<15} ${expense:>10.2f} ({percentage:>5.1f}%)")
        print(f"\nTotal Monthly Expense: ${total_expense:.2f}")

    def get_average_expenses(self):
        cursor = self.conn.execute('''
            SELECT categories.name, AVG(expenses.amount)
            FROM expenses INNER JOIN categories
            ON expenses.category_id = categories.id
            GROUP BY categories.id
        ''')
        rows = cursor.fetchall()
        print("\nAverage Monthly Expenses for Each Category:")
        for row in rows:
            category_name = row[0]
            average_expense = row[1]
            print(f"{category_name:<15} ${average_expense:>10.2f}")
        print()

    def compare_monthly_expense_with_average(self, month, year):
        # Get all expenses for the specified month and year
        monthly_rows = self.conn.execute(
            "SELECT amount, date FROM expenses WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?",
            (month, year)).fetchall()

        if not monthly_rows:
            print(f"No expenses found for {month}/{year}")
            return

        # Calculate total monthly expense
        monthly_expense = sum([row[0] for row in monthly_rows])

        # Calculate average monthly expense for the given year
        avg_rows = self.conn.execute("SELECT SUM(amount)/COUNT(DISTINCT(date)) FROM expenses WHERE strftime('%Y', date) = ?",
                                   (year,)).fetchone()
        avg_expense = avg_rows[0] if avg_rows[0] else 0

        # Compare monthly expense with average expense
        difference = monthly_expense - avg_expense
        if difference > 0:
            print(f"You spent {difference:.2f} more than the monthly average of {avg_expense:.2f} for {year}")
        elif difference < 0:
            print(f"You spent {abs(difference):.2f} less than the monthly average of {avg_expense:.2f} for {year}")
        else:
            print(f"You spent exactly the monthly average for {year}")

    def menu(self):
        while True:
            print()
            print("--------- Expense Tracker Menu ---------")
            print("1. Add Category")
            print("2. Add Expense")
            print("3. Monthly Expenses Report")
            print("4. Average Monthly Expenses Report")
            print("5. Compare Monthly Expense with Average")
            print("6. Quit")
            choice = input("Enter your choice (1-6): ")
            print()
            if choice == '1':
                print("----------- Add new Category -----------")
                name = input("Enter category name: ")
                self.add_category(name)

            elif choice == '2':
                print("-------------- Add Expense -------------")
                print("Categories:")
                self.add_expense()
                self.save_expenses_to_csv('expenses.csv')

            elif choice == '3':
                month = input("Enter month (MM): ")
                year = input("Enter year (YYYY): ")
                self.get_monthly_expenses(month, year)

            elif choice == '4':
                self.get_average_expenses()

            elif choice == '5':
                month = input("Enter month (MM): ")
                year = input("Enter year (YYYY): ")
                self.compare_monthly_expense_with_average(month, year)

            elif choice == '6':
                print("Exiting...")
                break
            else:
                print("Invalid choice! Please enter a valid choice.")


if __name__ == '__main__':
    tracker = ExpenseTracker()
    tracker.menu()


